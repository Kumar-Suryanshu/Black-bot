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
  // Create a clean new tab pointing to the main landing page
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

  await send('Page.navigate', { url: 'http://127.0.0.1:5173/' });
  await sleep(2000);

  // Compute exact layout offsets from the page
  const metrics = await send('Runtime.evaluate', {
    expression: `(() => {
      if ('scrollRestoration' in history) {
        history.scrollRestoration = 'manual';
      }
      window.scrollTo(0, 0);
      const vh = window.innerHeight;
      // Scene 0: cover dwell 40, tear 100 -> start 0, tearStart 0.4*vh, end 1.4*vh
      // Scene 1: problem dwell 70, tear 100 -> start 1.4*vh, tearStart 2.1*vh, end 3.1*vh
      // Scene 2: how-it-works dwell 80, tear 100 -> start 3.1*vh, tearStart 3.9*vh, end 4.9*vh
      const coverTearStart = 0.40 * vh;
      const tear = 1.00 * vh;
      return {
        vh,
        m01: 0,
        m02: Math.round(coverTearStart + 0.07 * tear),
        m03: Math.round(coverTearStart + 0.45 * tear),
        m04: Math.round(1.40 * vh + 50), // at rest on problem postcard
        m05: Math.round(3.10 * vh + 50), // at rest on field notes
      };
    })()`,
    returnByValue: true
  });

  const m = metrics.result.value;
  console.log('Target offsets for Phase 3:', m);

  const targets = [
    { name: 'match-01-cover.png', scrollY: m.m01, label: 'Scene 1: Cover at scrollY 0' },
    { name: 'match-02-tear-begins.png', scrollY: m.m02, label: 'Tear begins (t = 0.07)' },
    { name: 'match-03-tear-midway.png', scrollY: m.m03, label: 'Tear midway (t = 0.45)' },
    { name: 'match-04-postcard.png', scrollY: m.m04, label: 'Scene 2: Problem Postcard' },
    { name: 'match-05-field-notes.png', scrollY: m.m05, label: 'Scene 3: Field Notes' },
  ];

  const screensDir = path.resolve('docs/screens');
  fs.mkdirSync(screensDir, { recursive: true });

  for (const t of targets) {
    console.log(`Setting scrollY = ${t.scrollY} (${t.label})...`);
    await send('Runtime.evaluate', {
      expression: `window.scrollTo({ top: ${t.scrollY}, left: 0, behavior: 'instant' });`,
    });
    // Wait for rAF update and paint
    await sleep(500);

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
  console.log('Tab closed, all 5 Phase 3 screenshots saved successfully.');
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
