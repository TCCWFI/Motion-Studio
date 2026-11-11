#!/usr/bin/env node
// Motion studio renderer.
//   node render.mjs videos/hello.html             -> out/hello.mp4
//   node render.mjs videos/hello.html --stills 3  -> out/stills/hello-*.png
//
// A video is an HTML file that sets:
//   window.DURATION = seconds
//   window.SIZE     = [width, height]
//   window.render   = (t) => { ...draw the exact frame at time t... }
// render(t) may be async. No CSS animations, transitions or timers.

import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

// Find Playwright: local node_modules first, then the pre-installed global copy.
const require = createRequire(import.meta.url);
function loadPlaywright() {
  const tries = ['playwright', '/opt/node-tools/node_modules/playwright',
                 ...(process.env.NODE_PATH || '').split(':').filter(Boolean).map(p => path.join(p, 'playwright'))];
  for (const t of tries) { try { return require(t); } catch {} }
  console.error('Playwright not found. Install it with: npm i -D playwright');
  process.exit(1);
}
const { chromium } = loadPlaywright();

const FPS = 30;
const args = process.argv.slice(2);
const file = args.find(a => !a.startsWith('--') && a.endsWith('.html'));
const stillsIdx = args.indexOf('--stills');
const stills = stillsIdx >= 0 ? Math.max(1, parseInt(args[stillsIdx + 1] || '3', 10)) : 0;
if (!file) {
  console.error('Usage: node render.mjs videos/<name>.html [--stills N]');
  process.exit(1);
}

const root = path.dirname(new URL(import.meta.url).pathname);
const name = path.basename(file, '.html');
const outDir = path.join(root, 'out');
mkdirSync(path.join(outDir, 'stills'), { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ deviceScaleFactor: 1 });

// Determinism guards, applied before any page script runs:
// a fixed random seed, a frozen clock, and no CSS animations or transitions.
await page.addInitScript(() => {
  let s = 1234567;
  Math.random = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  const T0 = Date.UTC(2026, 0, 1);
  Date.now = () => T0;
  performance.now = () => 0;
  document.addEventListener('DOMContentLoaded', () => {
    const st = document.createElement('style');
    st.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}';
    document.head.appendChild(st);
  });
});

await page.goto('file://' + path.resolve(file));
const meta = await page.evaluate(() => ({
  duration: window.DURATION, size: window.SIZE, hasRender: typeof window.render === 'function',
}));
if (!meta.hasRender || !(meta.duration > 0) || !Array.isArray(meta.size)) {
  console.error(`${file} must set window.DURATION, window.SIZE and window.render(t).`);
  await browser.close();
  process.exit(1);
}
const [W, H] = meta.size;
await page.setViewportSize({ width: W, height: H });

// Wait for fonts and every image before drawing the first frame.
await page.evaluate(async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map(img => img.decode().catch(() => {})));
});

const drawAt = (t) => page.evaluate(async (t) => { await window.render(t); }, t);

if (stills) {
  // Evenly spaced inside the video, e.g. 3 stills of 3s -> 0.75s, 1.5s, 2.25s.
  for (let i = 1; i <= stills; i++) {
    const t = +(meta.duration * i / (stills + 1)).toFixed(2);
    await drawAt(t);
    const p = path.join(outDir, 'stills', `${name}-${t.toFixed(2)}s.png`);
    await page.screenshot({ path: p });
    console.log('still', path.relative(root, p));
  }
  await browser.close();
  process.exit(0);
}

const frames = Math.round(meta.duration * FPS);
const outFile = path.join(outDir, `${name}.mp4`);
const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
  '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',   // silent track: some apps reject video-only files
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', outFile],
  { stdio: ['pipe', 'inherit', 'inherit'] });
const ffDone = new Promise((res, rej) => ff.on('close', c => c === 0 ? res() : rej(new Error('ffmpeg exit ' + c))));

const t0 = Date.now();
for (let i = 0; i < frames; i++) {
  await drawAt(i / FPS);
  const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (i % FPS === 0) process.stdout.write(`\rframe ${i}/${frames}`);
}
ff.stdin.end();
await ffDone;
await browser.close();
console.log(`\rwrote ${path.relative(root, outFile)}  (${W}x${H}, ${meta.duration}s, ${frames} frames, ${((Date.now() - t0) / 1000).toFixed(1)}s)`);
