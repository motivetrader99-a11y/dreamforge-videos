"""The rainbow order -- Dreamforge Kids lesson Short (Twinkle narrates)."""
import math, random, subprocess, wave
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/rainbow_order.mp4"
TMPV, TMPA = "/tmp/_rb_v.mp4", "/tmp/_rb_a.wav"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
random.seed(21)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

COLORS = [("Red", (240, 70, 70)), ("Orange", (255, 150, 50)), ("Yellow", (255, 215, 60)),
          ("Green", (90, 195, 95)), ("Blue", (70, 145, 235)), ("Indigo", (85, 75, 175)),
          ("Violet", (170, 100, 210))]

# ---------- script / timeline ----------
LINES = [
    (0.0, 5.5, "Hi friends! I'm Twinkle. Let's build a rainbow!"),
    (5.5, 10.5, "Red comes first, at the very top."),
    (10.5, 17.0, "Then orange... and then yellow."),
    (17.0, 23.5, "Next comes green... then blue."),
    (23.5, 30.5, "Then indigo... and violet at the end."),
    (30.5, 40.0, "Red, orange, yellow, green, blue, indigo, violet!"),
    (40.0, 46.0, "Now you know the rainbow order!"),
]
TOTAL = 46.0
NFR = int(TOTAL * FPS)
BAND_T = [6.3, 11.4, 14.2, 18.0, 20.8, 24.4, 27.4]        # when each band paints in
RECAP0, RECAP_GAP = 31.6, 1.15                              # recap highlight timing

# ---------- geometry ----------
CX, CY = 470, 1160          # rainbow centre (shifted left, away from Shorts UI)
R_OUT, BAND = 430, 46       # outer radius, band thickness

def background():
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([150, 205, 245]), np.array([235, 245, 255])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # soft rolling hills + flowers
    d.ellipse([-400, 1440, 700, 2300], fill=(150, 215, 140))
    d.ellipse([350, 1480, 1500, 2350], fill=(125, 200, 125))
    for _ in range(26):
        x, y = random.randint(20, 1060), random.randint(1560, 1900)
        c = random.choice([(255, 255, 255), (255, 200, 220), (255, 235, 140)])
        for a in range(5):
            ang = a * 2 * math.pi / 5
            px, py = x + 9 * math.cos(ang), y + 9 * math.sin(ang)
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=c)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 190, 60))
    return bg

def cloud(w, h, shade=(255, 255, 255)):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([0, h * 0.35, w * 0.45, h], fill=shade + (255,))
    d.ellipse([w * 0.2, 0, w * 0.7, h * 0.85], fill=shade + (255,))
    d.ellipse([w * 0.5, h * 0.25, w, h], fill=shade + (255,))
    d.rectangle([w * 0.2, h * 0.6, w * 0.8, h], fill=shade + (255,))
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([w * 0.1, h * 0.75, w * 0.9, h * 1.05], fill=(200, 215, 235, 140))
    im.alpha_composite(sh)
    return im

def band_layer(i, glow=False):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    ro = R_OUT - i * BAND; ri = ro - BAND
    col = COLORS[i][1]
    if glow:
        d.pieslice([CX - ro - 18, CY - ro - 18, CX + ro + 18, CY + ro + 18], 180, 360, fill=(255, 255, 255, 210))
        d.pieslice([CX - ri + 18, CY - ri + 18, CX + ri - 18, CY + ri - 18], 180, 360, fill=(0, 0, 0, 0))
        im = im.filter(ImageFilter.GaussianBlur(10))
        return im
    d.pieslice([CX - ro, CY - ro, CX + ro, CY + ro], 180, 360, fill=col + (255,))
    d.pieslice([CX - ri, CY - ri, CX + ri, CY + ri], 180, 360, fill=(0, 0, 0, 0))
    # light shine line on each band
    rm = ro - BAND * 0.3
    d.arc([CX - rm, CY - rm, CX + rm, CY + rm], 195, 260, fill=(255, 255, 255, 90), width=6)
    return im

def sweep_mask(frac):
    """mask revealing the arc from the left foot (180 deg) clockwise to 180+180*frac."""
    m = Image.new("L", (W, H), 0)
    if frac > 0:
        ImageDraw.Draw(m).pieslice([CX - R_OUT - 5, CY - R_OUT - 5, CX + R_OUT + 5, CY + R_OUT + 5],
                                   180, 180 + 180 * min(1, frac), fill=255)
    return m

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    pts = []
    for k in range(10):
        a = rot - math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts

def twinkle(r, mouth_open):
    s = int(r * 2.7); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(star_poly(s / 2, s / 2, r * 1.08), fill=(255, 230, 120, 130))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(s / 2, s / 2 + r * 0.04, r), fill=(230, 170, 30))
    d.polygon(star_poly(s / 2, s / 2, r), fill=(255, 210, 60))
    cx, cy, e = s / 2, s / 2 + r * 0.06, r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([cx + dx - e, cy - e * 1.35, cx + dx + e, cy + e * 1.35], fill=(60, 40, 70))
        d.ellipse([cx + dx - e * 0.45, cy - e * 1.05, cx + dx + e * 0.15, cy - e * 0.35], fill=(255, 255, 255))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([cx + dx - r * 0.1, cy + r * 0.1, cx + dx + r * 0.1, cy + r * 0.22], fill=(255, 130, 150))
    if mouth_open:
        d.ellipse([cx - r * 0.13, cy + r * 0.12, cx + r * 0.13, cy + r * 0.34], fill=(150, 50, 70))
        d.ellipse([cx - r * 0.07, cy + r * 0.24, cx + r * 0.07, cy + r * 0.33], fill=(255, 130, 140))
    else:
        d.arc([cx - r * 0.17, cy + r * 0.02, cx + r * 0.17, cy + r * 0.28], 20, 160, fill=(60, 40, 70), width=max(3, int(r * 0.05)))
    return im

def paste(canvas, sp, cx, cy, scale=1.0, rot=0):
    if scale <= 0.02: return
    if scale != 1.0:
        sp = sp.resize((max(2, int(sp.width * scale)), max(2, int(sp.height * scale))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BILINEAR, expand=True)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.15 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.2 * (1 - x)

def wrap(d, txt, f, maxw):
    words, lines, cur = txt.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def caption(im, txt, alpha):
    d = ImageDraw.Draw(im)
    f = font(64); lines = wrap(d, txt, f, 830)
    lh = 80; bh = lh * len(lines) + 46; y0 = 1278
    box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([50, y0, 930, y0 + bh], 40, fill=(255, 255, 255, int(225 * alpha)),
                                          outline=(120, 90, 180, int(255 * alpha)), width=6)
    im.alpha_composite(box); d = ImageDraw.Draw(im)
    for k, ln in enumerate(lines):
        w = d.textlength(ln, font=f)
        d.text((490 - w / 2, y0 + 22 + k * lh), ln, font=f, fill=(70, 45, 120, int(255 * alpha)))

def big_word(im, txt, col, y, sc):
    if sc <= 0.02: return
    f = font(130 * sc); d = ImageDraw.Draw(im)
    w = d.textlength(txt, font=f)
    d.text((630 - w / 2, y - 65 * sc), txt, font=f, fill=col, stroke_width=max(2, int(10 * sc)), stroke_fill=(255, 255, 255))

# ---------- assets ----------
BG = background()
BANDS = [band_layer(i) for i in range(7)]
GLOWS = [band_layer(i, glow=True) for i in range(7)]
CLOUD_BIG = cloud(330, 190)
CLOUD_SM = cloud(220, 120)
CLOUD_GREY = cloud(300, 160, (190, 200, 215))
TW = [twinkle(105, False), twinkle(105, True)]
SUN = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
sd = ImageDraw.Draw(SUN)
for k in range(12):
    a = k * math.pi / 6
    sd.line([150 + 80 * math.cos(a), 150 + 80 * math.sin(a), 150 + 135 * math.cos(a), 150 + 135 * math.sin(a)], fill=(255, 210, 80), width=14)
sd.ellipse([70, 70, 230, 230], fill=(255, 215, 90))
DROPS = [(random.randint(0, W), random.randint(0, H), random.uniform(500, 800)) for _ in range(70)]

def speaking(t):
    for st, en, _ in LINES:
        if st <= t < en:
            return (t - st) < (en - st) * 0.75, st, en
    return False, 0, TOTAL

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                         "-crf", "20", "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
for fi in range(NFR):
    t = fi / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    # sun comes out after the rain
    sun_y = 520 - 380 * ease((t - 1.0) / 2.5)
    paste(im, SUN, 930, sun_y, 1.0, t * 8)
    # drifting clouds in sky
    paste(im, CLOUD_SM, (120 + t * 12) % 1300 - 150, 640)
    # rain at the start, clearing away
    rain_a = 1 - ease((t - 2.0) / 1.5)
    if rain_a > 0:
        paste(im, CLOUD_GREY, 640, 260 - 200 * (1 - rain_a))
        for x, y, sp in DROPS:
            yy = (y + t * sp) % H
            d.line([x, yy, x - 4, yy + 26], fill=(110, 160, 220, int(200 * rain_a)), width=5)
    # rainbow bands
    for i in range(7):
        bt = BAND_T[i]
        if t < bt: continue
        frac = ease((t - bt) / 1.3)
        layer = BANDS[i] if frac >= 1 else Image.composite(BANDS[i], Image.new("RGBA", (W, H), (0, 0, 0, 0)), sweep_mask(frac))
        im.alpha_composite(layer)
    # recap highlight (glow pulse on each band in turn)
    for i in range(7):
        rt = RECAP0 + i * RECAP_GAP
        if rt <= t < rt + RECAP_GAP:
            a = math.sin((t - rt) / RECAP_GAP * math.pi)
            g = GLOWS[i].copy(); g.putalpha(g.getchannel("A").point(lambda v, a=a: int(v * a)))
            im.alpha_composite(g); im.alpha_composite(BANDS[i])
    # celebration: whole rainbow shimmers
    if t >= 40.0:
        for i in range(7):
            a = (math.sin(t * 4 - i * 0.8) + 1) / 2 * 0.5
            g = GLOWS[i].copy(); g.putalpha(g.getchannel("A").point(lambda v, a=a: int(v * a)))
            im.alpha_composite(g)
        for i in range(7):
            im.alpha_composite(BANDS[i])
    # clouds at the rainbow feet
    paste(im, CLOUD_BIG, CX - R_OUT + 110, CY + 10)
    paste(im, CLOUD_BIG, CX + R_OUT - 110, CY + 10)
    # current color word + swatch (top right of Twinkle)
    word, wcol, wsc = None, None, 0
    for i in range(7):
        st = BAND_T[i]; en = BAND_T[i + 1] if i < 6 else 30.5
        if st <= t < en:
            word, wcol, wsc = COLORS[i][0], COLORS[i][1], pop((t - st) / 0.6)
    for i in range(7):
        rt = RECAP0 + i * RECAP_GAP
        if rt <= t < rt + RECAP_GAP:
            word, wcol, wsc = COLORS[i][0], COLORS[i][1], pop((t - rt) / 0.45)
    if word:
        big_word(im, word, wcol, 330, wsc)
    # order counter dots under the word (shows position 1-7)
    shown = sum(1 for bt in BAND_T if t >= bt)
    if 5.5 <= t < 40:
        for i in range(7):
            x = 400 + i * 78; y = 480
            if i < shown:
                c = COLORS[i][1]; r = 26
                active = word == COLORS[i][0]
                if active: r = 32 + 4 * math.sin(t * 8)
                d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=(255, 255, 255), width=5)
                nf = font(30); n = str(i + 1); nw = d.textlength(n, font=nf)
                d.text((x - nw / 2, y - 21), n, font=nf, fill=(255, 255, 255))
            else:
                d.ellipse([x - 20, y - 20, x + 20, y + 20], outline=(255, 255, 255), width=5)
    if t >= 40.0:
        sc = pop((t - 40.0) / 0.7)
        if sc > 0:
            f = font(96 * sc); txt = "Great job!"; w = d.textlength(txt, font=f)
            d.text((630 - w / 2, 300), txt, font=f, fill=(255, 120, 160), stroke_width=max(2, int(9 * sc)), stroke_fill=(255, 255, 255))
        if t > 41.5:
            f = font(52); txt = "Subscribe for more!"; w = d.textlength(txt, font=f)
            d.text((630 - w / 2, 450), txt, font=f, fill=(70, 45, 120), stroke_width=5, stroke_fill=(255, 255, 255))
    # Twinkle, top-left, bouncing & talking
    talk, st, en = speaking(t)
    mouth = talk and (int(t * 7) % 2 == 0)
    bounce = (abs(math.sin(t * 7)) * 14) if talk else math.sin(t * 2.5) * 6
    tsc = pop(t / 0.8)
    paste(im, TW[1 if mouth else 0], 190, 330 - bounce, tsc, math.sin(t * 2) * 6)
    # caption
    for st, en, txt in LINES:
        if st <= t < en:
            a = min(1, (t - st) / 0.25, (en - t) / 0.25)
            caption(im, txt, max(0, a))
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio (original gentle music) ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, kind="sine", decay=5):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if kind == "bell": w += 0.35 * np.sin(2 * np.pi * freq * 2 * tt) + 0.12 * np.sin(2 * np.pi * freq * 3.01 * tt)
    if kind == "soft": w += 0.2 * np.sin(2 * np.pi * freq * 2 * tt)
    return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 150)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]

# light rain hiss at the start
rain = np.random.default_rng(3).normal(0, 1, int(3.5 * SR))
rain = np.convolve(rain, np.ones(30) / 30, mode="same") * 0.05 * np.linspace(1, 0, len(rain))
add(rain, 0)
# lilting 3/4 waltz in F major (original pattern)
F = {"F3": 174.61, "C3": 130.81, "Bb2": 116.54, "D3": 146.83,
     "A4": 440.0, "C5": 523.25, "F5": 698.46, "G4": 392.0, "Bb4": 466.16, "D5": 587.33, "E5": 659.25, "F4": 349.23}
chords = [("F3", ["A4", "C5", "F5"]), ("Bb2", ["Bb4", "D5", "F5"]), ("C3", ["G4", "C5", "E5"]), ("F3", ["A4", "C5", "F4"])]
beat = 0.45; bar = 3 * beat; b = 0
while b * bar < TOTAL - 1.5:
    root, ups = chords[b % 4]
    add(tone(F[root], bar * 1.2, 0.08, "soft", 1.8), b * bar)
    for k in range(3):
        add(tone(F[ups[(k + b) % 3]], 0.7, 0.035, "bell", 4), b * bar + k * beat)
    b += 1
# sparkle sweep for each rainbow band (rising scale)
scale = [523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77]
for i, bt in enumerate(BAND_T):
    for k in range(4):
        add(tone(scale[i] * (1 + k * 0.25), 0.5, 0.06, "bell", 7), bt + k * 0.18)
for i in range(7):
    add(tone(scale[i], 0.6, 0.12, "bell", 6), RECAP0 + i * RECAP_GAP + 0.05)
for k, f_ in enumerate([698.46, 880.0, 1046.5, 1396.9]):
    add(tone(f_, 1.2, 0.12, "bell", 3), 40.1 + k * 0.16)
fade = np.ones(N); fl = int(1.8 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open(TMPA, "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", TOTAL)
