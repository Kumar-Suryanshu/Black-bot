import fs from 'fs';
import path from 'path';

const PORT = 9222;

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  console.log('Testing mobile viewport 390x844...');
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

  // Emulate iPhone / mobile screen
  await send('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 2,
    mobile: true,
  });

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Page.navigate', { url: 'http://127.0.0.1:5173/' });
  await sleep(1500);

  const shot = await send('Page.captureScreenshot', {
    format: 'png',
    captureBeyondViewport: false,
  });

  const buffer = Buffer.from(shot.data, 'base64');
  const outPath = path.resolve('docs/screens/mobile-390.png');
  fs.writeFileSync(outPath, buffer);
  console.log(`Saved mobile screenshot: ${outPath} (${buffer.length} bytes)`);

  ws.close();
  await fetch(`http://127.0.0.1:${PORT}/json/close/${targetId}`);
  process.exit(0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
