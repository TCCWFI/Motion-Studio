# Motion Studio

Motion graphics videos written as code. Each video is one HTML file; the renderer turns it into an MP4.

## Folders

- `videos/` — one HTML file per video
- `brand.css` — shared colors and fonts (load with `<link rel="stylesheet" href="../brand.css">`)
- `assets/` — logos, photos and music (reference as `../assets/...`)
- `tools/make-beat.py` — makes an original Caribbean (calypso / steel pan) beat: `python3 tools/make-beat.py 30 assets/audio/caribbean-beat.wav`
- `out/` — rendered MP4s (`out/stills/` holds preview images and is not committed)
- `src/` — the first TCSPS promo, made before the studio format existed

## A video file

```html
<script>
  window.DURATION = 3;            // seconds
  window.SIZE = [1920, 1080];     // width, height
  window.render = (t) => {        // draw the exact frame at time t (may be async)
    // set styles, transforms, canvas drawing... from t only
  };
  window.AUDIO = '../assets/audio/caribbean-beat.wav';   // optional soundtrack
</script>
```

Rules: no CSS animations, transitions, timers or `requestAnimationFrame`. Everything must come from `t`.
The renderer also blocks CSS animations, fixes `Math.random` to one seed, and freezes the clock, so the same file always renders the same video.

Common sizes: `[1080, 1920]` vertical (TikTok, Reels, Shorts), `[1920, 1080]` wide (YouTube, LinkedIn), `[1080, 1080]` square.

## Render

```bash
node render.mjs videos/hello.html --stills 3
```
Saves 3 evenly spaced preview images to `out/stills/`.

```bash
node render.mjs videos/hello.html
```
Renders every frame at 30 fps to `out/hello.mp4` (H.264 + AAC). Uses `window.AUDIO` as the soundtrack, trimmed or padded to the video length; without it, the MP4 gets a silent track.

Needs Node.js, ffmpeg and Playwright with Chromium.
