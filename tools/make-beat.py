#!/usr/bin/env python3
"""Original Caribbean (calypso / steel pan) beat, synthesized from scratch.

    python3 tools/make-beat.py [seconds] [out.wav]

Default: 30 s at 96 BPM = exactly 12 bars of 4/4, written to
assets/audio/caribbean-beat.wav. Same input -> same file (fixed random seed).
Instruments: steel pan melody, pan chord strums, bass, kick, rim clave, shaker.
All sounds are generated here, so there is no licensing to worry about.
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 96
SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
OUT = sys.argv[2] if len(sys.argv) > 2 else 'assets/audio/caribbean-beat.wav'

BEAT = 60.0 / BPM          # 0.625 s
EIGHTH = BEAT / 2
BAR = BEAT * 4             # 2.5 s
N = int(SECONDS * SR)
rng = np.random.default_rng(7)

L = np.zeros(N); R = np.zeros(N)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(sig, t0, gain=1.0, pan=0.0):
    """Mix a mono signal in at time t0. pan -1 = left, +1 = right."""
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i]
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gain * gl * 1.414
    R[i:i + len(sig)] += sig * gain * gr * 1.414

def env(n, attack, tau):
    t = np.arange(n) / SR
    return np.minimum(1, t / attack) * np.exp(-t / tau)

# ---------- instruments ----------
def steel_pan(m, dur=0.9, bright=1.0):
    f = hz(m); n = int(dur * SR); t = np.arange(n) / SR
    # Pan notes ring with a strong octave and a slightly sharp twelfth.
    s  = 1.00 * np.sin(2*np.pi*f*t)           * env(n, .003, .42)
    s += 0.55 * np.sin(2*np.pi*2*f*t + .3)    * env(n, .002, .26) * bright
    s += 0.18 * np.sin(2*np.pi*3.01*f*t)      * env(n, .002, .12) * bright
    s += 0.08 * np.sin(2*np.pi*4.2*f*t)       * env(n, .001, .05) * bright
    return s * (1 + 0.04 * np.sin(2*np.pi*5.5*t))   # light shimmer

def bass(m, dur=0.5):
    f = hz(m); n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2*np.pi*f*t) + 0.3*np.sin(2*np.pi*2*f*t) + 0.1*np.sin(2*np.pi*3*f*t)
    return np.tanh(1.4 * s) * env(n, .005, .32)

def kick():
    n = int(.35 * SR); t = np.arange(n) / SR
    f = 50 + 90 * np.exp(-t / .03)
    return np.sin(2*np.pi*np.cumsum(f)/SR) * env(n, .001, .12)

def rim():
    n = int(.12 * SR); t = np.arange(n) / SR
    noise = np.diff(rng.standard_normal(n + 1))          # bright noise
    return (0.6*np.sin(2*np.pi*1750*t) + 0.25*noise) * env(n, .0005, .018)

def shaker():
    n = int(.08 * SR)
    noise = np.diff(np.diff(rng.standard_normal(n + 2)))  # very bright noise
    return noise * env(n, .004, .022) * 0.25

# ---------- the song: 12 bars ----------
C, F, G, Am = 'C', 'F', 'G', 'Am'
chords = [C, F, G, C,  Am, F, G, C,  C, F, G, C]
triad = {C: [60, 64, 67], F: [60, 65, 69], G: [59, 62, 67], Am: [57, 60, 64]}
root  = {C: 36, F: 41, G: 43, Am: 45}

# Melody per bar: (eighth position, MIDI note, length in eighths)
mel = {
  'C1': [(0,76,1),(2,79,1),(3,81,1),(5,79,1),(6,76,2)],
  'F':  [(0,77,1),(2,81,1),(3,84,1),(5,81,1),(6,77,2)],
  'G':  [(0,79,1),(2,83,1),(3,86,1),(5,83,1),(6,81,1),(7,79,1)],
  'C2': [(0,76,1),(2,72,1),(3,76,2),(6,79,2)],
  'Am': [(0,76,1),(2,81,1),(3,84,1),(5,81,1),(6,76,2)],
  'END':[(0,84,8)],
}
melody_bars = ['C1','F','G','C2', 'Am','F','G','C2', 'C1','F','G','END']

# Son clave (3-2) over two bars, in eighths.
clave = [0, 3, 6, 10, 12]

bars = int(round(SECONDS / BAR))
for b in range(bars):
    t0 = b * BAR
    ch = chords[b % 12]
    last = (b == bars - 1)

    # Steel pan melody (slightly right)
    for pos, m, ln in mel[melody_bars[b % 12]]:
        add(steel_pan(m, dur=max(.5, ln * EIGHTH + .5)), t0 + pos * EIGHTH, 0.30, 0.25)

    # Pan chord strums on the off-beats (left), quick little roll between notes
    if not last:
        for pos in (1, 3, 5, 7):
            for k, m in enumerate(triad[ch]):
                add(steel_pan(m, .35, bright=.6), t0 + pos*EIGHTH + k*.012, 0.07, -0.45)

    # Bass: tresillo (1, the "and" of 2, 4) on root, root, fifth
    if not last:
        for pos, iv in ((0, 0), (3, 0), (6, 7)):
            add(bass(root[ch] + iv), t0 + pos * EIGHTH, 0.36, 0.0)
    else:
        add(bass(root[ch], 2.0), t0, 0.36, 0.0)

    # Drums: kick on every beat (soca pulse), rim clave, 16th shaker
    beats = (0,) if last else (0, 1, 2, 3)
    for i in beats:
        add(kick(), t0 + i * BEAT, 0.55 if i % 2 == 0 else 0.38, 0.0)
    if not last:
        for pos in clave:
            if (b % 2) * 8 <= pos < (b % 2) * 8 + 8:
                add(rim(), t0 + (pos - (b % 2) * 8) * EIGHTH, 0.22, -0.2)
        for s in range(16):
            add(shaker(), t0 + s * BEAT / 4, 1.0 if s % 2 else 0.55, 0.5)

# ---------- reverb (FFT convolution with a decaying noise tail) ----------
ir_n = int(1.3 * SR)
tir = np.arange(ir_n) / SR
def ir(seed):
    r = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-tir / .32)
    r[: int(.012 * SR)] = 0      # short pre-delay
    return r / np.sqrt(np.sum(r ** 2))
def conv(x, h):
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[: len(x)]
L = L + 0.18 * conv(L, ir(11))
R = R + 0.18 * conv(R, ir(12))

# ---------- master: fade in/out, soft limit, high cut, normalize by TRUE peak ----------
t = np.arange(N) / SR
fade = np.minimum(1, t / 0.08) * np.clip((SECONDS - t) / 1.2, 0, 1)
L *= fade; R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(1.2 * L / peak); R = np.tanh(1.2 * R / peak)

def high_cut(x, start=12000, stop=16000):
    """Smooth FFT low-pass: full level below start, silent above stop."""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= np.clip((stop - f) / (stop - start), 0, 1) ** 2
    return np.fft.irfft(X, len(x))
L = high_cut(L); R = high_cut(R)

def true_peak(x, over=4):
    """Peak between samples, found by 4x FFT upsampling (what encoders and meters see)."""
    X = np.fft.rfft(x); n = len(x) * over
    return np.abs(np.fft.irfft(X, n) * over).max()
# Target -2 dBTP so the AAC-encoded file stays below 0 dB.
g = 10 ** (-2 / 20) / max(true_peak(L), true_peak(R))
pcm = (np.stack([L, R], axis=1) * g * 32767).astype('<i2')

with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'wrote {OUT}  ({SECONDS:.1f}s, {BPM} BPM, {bars} bars)')
