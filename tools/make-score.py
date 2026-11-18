#!/usr/bin/env python3
"""Original warm cinematic score: piano, soft strings, cello and a low swell.

    python3 tools/make-score.py [out.wav]

80 BPM, 13 bars of 4/4 = 39 s exactly (one bar = 3 s), in D major.
Key moments: 12 s (bar 5) low boom + full strings for the title reveal,
30 s (bar 11) soft boom for the end card, final chord rings out to 39 s.
Same input -> same file. All sounds are generated here; nothing to license.
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 80
BEAT = 60 / BPM            # 0.75 s
BAR = 4 * BEAT             # 3 s
BARS = 13
SECONDS = BARS * BAR       # 39 s
OUT = sys.argv[1] if len(sys.argv) > 1 else 'assets/audio/thanksgiving-score.wav'
N = int(SECONDS * SR)
L = np.zeros(N); R = np.zeros(N)

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N: return
    sig = sig[: N - i]
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(sig)] += sig * gain * gl * 1.414
    R[i:i + len(sig)] += sig * gain * gr * 1.414

# ---------- instruments ----------
def piano(m, dur=3.0, vel=0.6):
    f = hz(m); n = int(dur * SR); t = np.arange(n) / SR
    tau0 = 2.4 * (262 / f) ** 0.35
    s = np.zeros(n)
    bright = 0.5 + vel                                  # louder notes are brighter
    for k in range(1, 9):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)        # slight string stiffness
        if fk > 16000: break
        a = (1 / k ** 1.4) * (bright ** (k - 1) if k > 1 else 1) * 0.8 ** (k - 1)
        tau = tau0 / k ** 0.7
        s += a * (np.sin(2*np.pi*fk*t) + 0.6*np.sin(2*np.pi*fk*1.0006*t + k)) * np.exp(-t / tau)
    att = np.minimum(1, t / 0.004)
    rel = np.clip((dur - t) / 0.25, 0, 1)               # damper at the end
    return s * att * rel * vel

def strings(m, dur, attack=1.2, release=1.4, bright=1.0):
    f = hz(m); n = int((dur + release) * SR); t = np.arange(n) / SR
    vib = 1 + 0.0025 * np.sin(2*np.pi*5.2*t) * np.minimum(1, t / 1.5)
    s = np.zeros(n)
    for det in (-0.0035, 0.0, 0.0041):                  # three slightly detuned players
        ph = 2*np.pi*f*(1+det)*np.cumsum(vib)/SR
        for k in range(1, 11):
            if f * k > 9000: break
            s += np.sin(k * ph + det * 900 * k) / k ** (1.9 - 0.4 * bright)
    env = np.minimum(1, t / attack) * np.clip((dur + release - t) / release, 0, 1)
    return s * env / 3

def cello(m, dur):
    return strings(m, dur, attack=0.5, release=1.6, bright=0.7)

def boom(dur=4.0):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 38 + 30 * np.exp(-t / 0.08)
    s = np.sin(2*np.pi*np.cumsum(f)/SR) * np.exp(-t / 1.1)
    noise = np.random.default_rng(3).standard_normal(n)
    X = np.fft.rfft(noise); fr = np.fft.rfftfreq(n, 1/SR); X[fr > 180] = 0
    rumble = np.fft.irfft(X, n); rumble /= np.abs(rumble).max()
    return (s + 0.35 * rumble * np.exp(-t / 0.7)) * np.minimum(1, t / 0.01)

def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = np.random.default_rng(5).standard_normal(n)
    X = np.fft.rfft(noise); fr = np.fft.rfftfreq(n, 1/SR)
    X *= np.exp(-((fr - 1500) / 1800) ** 2)            # soft "air" band
    s = np.fft.irfft(X, n); s /= np.abs(s).max()
    return s * (t / dur) ** 2.2

# ---------- the music ----------
# chord: (bass root, quality) ; quality 'M' major or 'm' minor
D, Bm, G, A = (50, 'M'), (47, 'm'), (43, 'M'), (45, 'M')
chords = [D, Bm, G, A,  D, A, Bm, G,  D, A, G, A,  D]
pad_voicing = {50: [62, 66, 69], 47: [59, 62, 66], 43: [59, 62, 67], 45: [57, 61, 64]}

# Melody in beats from bar 5 (index 4): (beat, MIDI, length in beats)
melody = {
  4:  [(0,78,2),(2,76,1),(3,74,1)],
  5:  [(0,76,3),(3,73,1)],
  6:  [(0,74,2),(2,78,2)],
  7:  [(0,79,3),(3,78,1)],
  8:  [(0,78,2),(2,81,2)],
  9:  [(0,81,2),(2,76,2)],
  10: [(0,79,2),(2,78,1),(3,76,1)],
  11: [(0,76,3),(3,73,1)],
  12: [(0,74,4)],
}

for b, (root, q) in enumerate(chords):
    t0 = b * BAR
    third = 4 if q == 'M' else 3
    last = (b == BARS - 1)

    # Piano: gentle broken chord in eighths (left hand)
    if not last:
        r = root
        pattern = [r, r+7, r+12, r+12+third, r+19, r+12+third, r+12, r+7]
        vel = 0.30 if b < 2 else (0.38 if b < 4 else 0.42)
        for i, m in enumerate(pattern):
            add(piano(m, dur=2.2, vel=vel * (1.0 if i % 4 == 0 else 0.8)), t0 + i * BEAT / 2, 0.55, -0.15)
    else:
        # Final rolled chord, low to high, ringing out
        for i, m in enumerate([root, root+7, root+12, root+12+third, root+19, root+24]):
            add(piano(m, dur=8.0, vel=0.45), t0 + i * 0.06, 0.55, -0.15 + 0.06 * i)

    # Melody (right hand), from the title reveal on
    for beat, m, ln in melody.get(b, []):
        add(piano(m, dur=ln * BEAT + (6 if last else 1.2), vel=0.55), t0 + beat * BEAT, 0.6, 0.2)

    # Strings pad: enters at bar 3, full from bar 5, small lift at bar 10
    if b >= 2:
        g = 0.10 if b < 4 else (0.17 if b != 9 else 0.20)
        dur = BAR if not last else 7.5
        for k, m in enumerate(pad_voicing[root]):
            add(strings(m, dur, attack=1.0 if b != 4 else 0.25), t0, g, (-0.5, 0.0, 0.5)[k])

    # Cello on the root from the title reveal
    if b >= 4:
        add(cello(root - 12 if root > 45 else root, BAR if not last else 7.5), t0, 0.16, 0.0)

# Swells and booms
add(riser(1.8), 4 * BAR - 1.8, 0.10, 0.0)        # into the title (12 s)
add(boom(), 4 * BAR, 0.55)                        # title reveal
add(riser(1.5), 10 * BAR - 1.5, 0.07, 0.0)       # into the end card (30 s)
add(boom(), 10 * BAR, 0.32)                       # end card

# ---------- big warm reverb ----------
ir_n = int(3.0 * SR); tir = np.arange(ir_n) / SR
def ir(seed):
    r = np.random.default_rng(seed).standard_normal(ir_n) * np.exp(-tir / 0.75)
    r[: int(.02 * SR)] = 0
    return r / np.sqrt(np.sum(r ** 2))
def conv(x, h):
    n = 1 << int(np.ceil(np.log2(len(x) + len(h))))
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(h, n), n)[: len(x)]
L = L + 0.32 * conv(L, ir(21))
R = R + 0.32 * conv(R, ir(22))

# ---------- master: fades, soft limit, high cut, true-peak normalize ----------
t = np.arange(N) / SR
fade = np.minimum(1, t / 0.05) * np.clip((SECONDS - t) / 2.5, 0, 1)
L *= fade; R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(1.3 * L / peak); R = np.tanh(1.3 * R / peak)
def high_cut(x, start=12000, stop=16000):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= np.clip((stop - f) / (stop - start), 0, 1) ** 2
    return np.fft.irfft(X, len(x))
L = high_cut(L); R = high_cut(R)
def true_peak(x, over=4):
    return np.abs(np.fft.irfft(np.fft.rfft(x), len(x) * over) * over).max()
g = 10 ** (-2 / 20) / max(true_peak(L), true_peak(R))
g *= 10 ** (-3 / 20)          # sit near -15 LUFS, a calm level for an emotional piece
pcm = (np.stack([L, R], axis=1) * g * 32767).astype('<i2')
with wave.open(OUT, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'wrote {OUT}  ({SECONDS:.0f}s, {BPM} BPM, {BARS} bars)')
