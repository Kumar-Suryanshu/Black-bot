import fs from 'fs';
import path from 'path';

const VIEWPORT_W = 1920;
const VIEWPORT_H = 993;
const PORT = 9222;

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('Connecting to Chrome CDP on port', PORT);
  const targetRes = await fetch(`http://127.0.0.1:${PORT}/json/new?http://127.0.0.1:5173/`, {
    method: 'PUT'
  });
  const target = await targetRes.json();
  const targetId = target.id;
  const wsUrl = target.webSocketDebuggerUrl;

  const ws = new WebSocket(wsUrl);
  let id = 1;
  const pending = new Map();

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(msg.error);
      else resolve(msg.result);
    }
  };

  const send = (method, params = {}) => {
    return new Promise((resolve, reject) => {
      const reqId = id++;
      pending.set(reqId, { resolve, reject });
      ws.send(JSON.stringify({ id: reqId, method, params }));
    });
  };

  await new Promise(r => { ws.onopen = r; });
  await send('Emulation.setDeviceMetricsOverride', {
    width: VIEWPORT_W,
    height: VIEWPORT_H,
    deviceScaleFactor: 1,
    mobile: false,
  });

  await send('Page.enable');
  await send('Runtime.enable');

  await send('Page.navigate', { url: 'http://127.0.0.1:5173/' });
  await sleep(1500);

  // Compute the exact release point: track height - vh
  const metrics = await send('Runtime.evaluate', {
    expression: `(() => {
      const track = document.querySelector('.track');
      const trackTop = track.offsetTop;
      const trackH = track.offsetHeight;
      const vh = window.innerHeight;
      const releaseY = trackTop + trackH - vh;
      return {
        trackTop,
        trackH,
        vh,
        releaseY,
        before: Math.round(releaseY - 30),
        after: Math.round(releaseY + 120),
      };
    })()`,
    returnByValue: true
  });

  const m = metrics.result.value;
  console.log('Seam metrics:', m);

  const targets = [
    { name: 'seam-before.png', scrollY: m.before, label: 'Just before sticky stage release' },
    { name: 'seam-after.png', scrollY: m.after, label: 'Just after sticky stage release into normal flow' },
  ];

  const screensDir = path.resolve('docs/screens');
  fs.mkdirSync(screensDir, { recursive: true });

  for (const t of targets) {
    console.log(`Setting scrollY = ${t.scrollY} (${t.label})...`);
    await send('Runtime.evaluate', {
      expression: `window.scrollTo({ top: ${t.scrollY}, left: 0, behavior: 'instant' });`,
    });
    await sleep(400);

    const shot = await send('Page.captureScreenshot', {
      format: 'png',
      captureBeyondViewport: false,
    });

    const buffer = Buffer.from(shot.data, 'base64');
    const outPath = path.join(screensDir, t.name);
    fs.writeFileSync(outPath, buffer);
    console.log(`Saved screenshot: ${outPath} (${buffer.length} bytes)`);
  }

  ws.close();
  await fetch(`http://127.0.0.1:${PORT}/json/close/${targetId}`);
  console.log('Seam test complete.');
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
