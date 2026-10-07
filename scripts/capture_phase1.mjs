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
  // Create a clean new tab
  const targetRes = await fetch(`http://127.0.0.1:${PORT}/json/new?http://127.0.0.1:5173/dev/tear?debug=tear`, {
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
  console.log('Connected to target tab:', targetId);

  // Set precise device metrics
  await send('Emulation.setDeviceMetricsOverride', {
    width: VIEWPORT_W,
    height: VIEWPORT_H,
    deviceScaleFactor: 1,
    mobile: false,
  });

  await send('Page.enable');
  await send('Runtime.enable');

  // Navigate and disable scroll restoration
  await send('Page.navigate', { url: 'http://127.0.0.1:5173/dev/tear?debug=tear' });
  await sleep(1500);

  // Read innerHeight and setup manual scroll restoration
  const metrics = await send('Runtime.evaluate', {
    expression: `(() => {
      if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
      }
      window.scrollTo(0, 0);
      const vh = window.innerHeight;
      const tearStart = 0.40 * vh;
      const tear = 1.00 * vh;
      return {
        vh,
        t0: Math.round(tearStart),
        t007: Math.round(tearStart + 0.07 * tear),
        t045: Math.round(tearStart + 0.45 * tear),
        t100: Math.round(tearStart + 1.00 * tear),
      };
    })()`,
    returnByValue: true
  });

  const m = metrics.result.value;
  console.log('Metrics and targets:', m);

  const targets = [
    { name: 'tear-t0.png', scrollY: m.t0, label: 't = 0.00 (sheets touching at tearStart)' },
    { name: 'tear-t007.png', scrollY: m.t007, label: 't = 0.07 (gap begins to open)' },
    { name: 'tear-t045.png', scrollY: m.t045, label: 't = 0.45 (midway, next scene rising)' },
    { name: 'tear-t100.png', scrollY: m.t100, label: 't = 1.00 (tear complete, at rest)' },
  ];

  const screensDir = path.resolve('docs/screens');
  fs.mkdirSync(screensDir, { recursive: true });

  for (const t of targets) {
    console.log(`Setting scrollY = ${t.scrollY} (${t.label})...`);
    await send('Runtime.evaluate', {
      expression: `
        window.scrollTo({ top: ${t.scrollY}, left: 0, behavior: 'instant' });
      `,
    });
    // Wait for rAF update and paint
    await sleep(400);

    // Verify current scrollY
    const cur = await send('Runtime.evaluate', {
      expression: `window.scrollY`,
      returnByValue: true
    });
    console.log(`Verified scrollY: ${cur.result.value}`);

    const shot = await send('Page.captureScreenshot', {
      format: 'png',
      captureBeyondViewport: false,
    });

    const buffer = Buffer.from(shot.data, 'base64');
    const outPath = path.join(screensDir, t.name);
    fs.writeFileSync(outPath, buffer);
    console.log(`Saved screenshot: ${outPath} (${buffer.length} bytes)`);
  }

  // Cleanup: close tab
  ws.close();
  await fetch(`http://127.0.0.1:${PORT}/json/close/${targetId}`);
  console.log('Tab closed, all screenshots saved successfully.');
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
