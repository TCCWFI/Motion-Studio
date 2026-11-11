// Usage: node src/render.js <html> <width> <height> <seconds> <out.mp4> [--stills]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

(async () => {
  const [html, w, h, secs, out] = process.argv.slice(2);
  const stills = process.argv.includes('--stills');
  const W = +w, H = +h, FPS = 30, N = Math.round(+secs * FPS);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(html) + `?w=${W}&h=${H}`);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForLoadState('networkidle');

  if (stills) {
    for (const t of [2.5, 6.5, 11.5, 16, 19.5]) {
      await page.evaluate((t) => window.seek(t), t);
      await page.screenshot({ path: `${out}-${t}.png` });
    }
    await browser.close();
    return;
  }

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k', '-shortest', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });

  for (let i = 0; i < N; i++) {
    await page.evaluate((t) => window.seek(t), i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  await browser.close();
  console.log('wrote', out);
})();
