"""Dreamforge Kids — Counting fish 11 to 20.
Under the sea: ten orange fish fill the first coral frame (ten), then new colourful
fish swim in one by one to a second frame: 10 + 1 = 11 ... 10 + 10 = 20.
Twinkle the star narrates. Original art & music."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/counting_fish_11_to_20.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (20, 50, 90)
random.seed(11)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

WORDS = {10: "Ten", 11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen",
         16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen", 20: "Twenty"}
NEWCOL = [(255, 110, 150), (120, 200, 255), (160, 230, 110), (200, 150, 255), (255, 215, 70),
          (90, 225, 200), (255, 150, 90), (240, 130, 220), (130, 160, 255), (255, 120, 110)]
ORANGE = (255, 160, 60)

# ---------- timeline ----------
INTRO, TENSEG, SEG, OUTRO = 5.0, 4.4, 3.6, 6.0
T_TEN = INTRO
T_N = T_TEN + TENSEG                   # start of 11
def nstart(n): return T_N + (n - 11) * SEG
T_OUT = nstart(21)
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

LINES = [
    (0.3, INTRO - 0.2, "Hi! I'm Twinkle! Let's count fish in the sea!"),
    (T_TEN + 0.2, T_N - 0.2, "Here are ten orange fish. Ten!"),
    (nstart(11) + 0.2, nstart(12) - 0.1, "Ten and one more fish makes eleven!"),
    (nstart(12) + 0.2, nstart(16) - 0.2, "Twelve, thirteen, fourteen, fifteen!"),
    (nstart(16) + 0.2, nstart(20) - 0.2, "Sixteen, seventeen, eighteen, nineteen!"),
    (nstart(20) + 0.2, T_OUT - 0.1, "Ten and ten make twenty fish!"),
    (T_OUT + 0.3, TOTAL - 0.4, "You did it! Bye bye, fishy friends!"),
]
# when Twinkle's mouth moves (approximate talking windows)
TALK = [(0.3, 3.4), (T_TEN + 0.2, T_TEN + 2.6), (nstart(11) + 0.2, nstart(11) + 2.6)]
for n in range(12, 21):
    TALK.append((nstart(n) + 0.3, nstart(n) + 1.4))
TALK.append((nstart(20) + 1.5, nstart(20) + 3.0))
TALK.append((T_OUT + 0.3, T_OUT + 3.3))
def talking(t): return any(a <= t < b for a, b in TALK)

# ---------- layout ----------
CELL = 140
FX0 = 160                     # frame left x (5 cells -> ends ~880, away from right 150px)
F1Y, F2Y = 610, 975           # frame top y
def slot(frame, i):
    r, c = divmod(i, 5)
    y0 = F1Y if frame == 0 else F2Y
    return (FX0 + 20 + c * CELL + CELL / 2, y0 + 20 + r * CELL + CELL / 2)

# ---------- art ----------
def vgrad(w, h, top, bot):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, w, axis=1))

def make_bg():
    im = vgrad(W, H, (120, 215, 240), (30, 90, 160)).convert("RGBA")
    rays = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rays)
    for x in (120, 380, 640, 900):
        rd.polygon([(x - 40, 0), (x + 60, 0), (x + 260, 1500), (x + 60, 1500)], fill=(255, 255, 230, 28))
    rays = rays.filter(ImageFilter.GaussianBlur(30)); im.alpha_composite(rays)
    d = ImageDraw.Draw(im)
    # sand
    d.ellipse([-400, 1560, 700, 2200], fill=(240, 215, 160))
    d.ellipse([350, 1590, 1500, 2250], fill=(230, 200, 145))
    for _ in range(80):
        x, y = random.randint(0, W), random.randint(1640, H)
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(210, 180, 130))
    # shells & pebbles
    for x, y, c in ((230, 1700, (255, 190, 200)), (620, 1760, (255, 230, 200)), (860, 1690, (250, 200, 170))):
        d.pieslice([x - 34, y - 30, x + 34, y + 30], 180, 360, fill=c)
        for k in range(-2, 3): d.line([(x, y), (x + k * 14, y - 26)], fill=(200, 140, 150), width=3)
    # coral clumps (sides)
    for bx, col in ((40, (255, 130, 150)), (1010, (255, 170, 110))):
        for k in range(4):
            x = bx + (k - 1.5) * 26
            d.rounded_rectangle([x - 11, 1450 - k * 30, x + 11, 1640], 11, fill=col)
            d.ellipse([x - 18, 1440 - k * 30, x + 18, 1476 - k * 30], fill=col)
    return im

def make_fish(color, L=118):
    s = int(L * 1.5); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy = s * 0.55, s / 2
    dark = tuple(max(0, c - 55) for c in color)
    light = tuple(min(255, c + 60) for c in color)
    bw, bh = L * 0.42, L * 0.30
    # tail (left side, fish faces right)
    d.polygon([(cx - bw * 0.8, cy), (cx - bw * 1.45, cy - bh * 0.95), (cx - bw * 1.3, cy), (cx - bw * 1.45, cy + bh * 0.95)], fill=dark)
    # top fin
    d.polygon([(cx - bw * 0.3, cy - bh * 0.8), (cx + bw * 0.1, cy - bh * 1.35), (cx + bw * 0.35, cy - bh * 0.8)], fill=dark)
    d.ellipse([cx - bw, cy - bh, cx + bw, cy + bh], fill=color)
    d.ellipse([cx - bw * 0.6, cy - bh * 0.1, cx + bw * 0.6, cy + bh * 0.9], fill=light)
    # stripe
    d.arc([cx - bw * 0.55, cy - bh, cx - bw * 0.05, cy + bh], 250, 110, fill=(255, 255, 255), width=max(3, int(L * 0.05)))
    # side fin
    d.ellipse([cx - bw * 0.15, cy + bh * 0.1, cx + bw * 0.25, cy + bh * 0.5], fill=dark)
    # big shiny eye
    ex, ey, er = cx + bw * 0.45, cy - bh * 0.18, L * 0.1
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(255, 255, 255))
    d.ellipse([ex - er * 0.65, ey - er * 0.6, ex + er * 0.65, ey + er * 0.75], fill=(30, 30, 60))
    d.ellipse([ex - er * 0.35, ey - er * 0.45, ex + er * 0.05, ey - er * 0.05], fill=(255, 255, 255))
    # smile + blush
    d.arc([cx + bw * 0.55, cy + bh * 0.05, cx + bw * 0.9, cy + bh * 0.45], 90, 200, fill=(40, 30, 60), width=max(2, int(L * 0.03)))
    d.ellipse([cx + bw * 0.2, cy + bh * 0.2, cx + bw * 0.42, cy + bh * 0.38], fill=(255, 130, 150, 140))
    return im

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def make_twinkle(r, mouth_open):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(star_poly(s / 2, s / 2, r * 1.06), fill=(255, 240, 150, 140))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(s / 2, s / 2 + r * 0.04, r), fill=(225, 165, 30))
    d.polygon(star_poly(s / 2, s / 2, r), fill=(255, 210, 60))
    cx, cy, e = s / 2, s / 2 + r * 0.05, r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([cx + dx - e, cy - e * 1.35, cx + dx + e, cy + e * 1.35], fill=(60, 40, 70))
        d.ellipse([cx + dx - e * 0.45, cy - e * 1.0, cx + dx + e * 0.15, cy - e * 0.3], fill=(255, 255, 255))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([cx + dx - r * 0.09, cy + r * 0.1, cx + dx + r * 0.09, cy + r * 0.22], fill=(255, 120, 150, 150))
    if mouth_open:
        d.ellipse([cx - r * 0.12, cy + r * 0.12, cx + r * 0.12, cy + r * 0.34], fill=(120, 40, 60))
        d.ellipse([cx - r * 0.07, cy + r * 0.24, cx + r * 0.07, cy + r * 0.33], fill=(255, 130, 150))
    else:
        d.arc([cx - r * 0.16, cy + r * 0.04, cx + r * 0.16, cy + r * 0.28], 20, 160, fill=(60, 40, 70), width=max(3, int(r * 0.05)))
    return im

BG = make_bg()
ORANGE_FISH = make_fish(ORANGE)
NEW_FISH = [make_fish(c) for c in NEWCOL]
TW_SMALL = [make_twinkle(80, False), make_twinkle(80, True)]
TW_BIG = [make_twinkle(170, False), make_twinkle(170, True)]

def paste(canvas, sp, cx, cy, scale=1.0, rot=0.0):
    if scale <= 0.02: return
    if scale != 1.0:
        sp = sp.resize((max(2, int(sp.width * scale)), max(2, int(sp.height * scale))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BILINEAR, expand=False)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def text_c(d, txt, y, sz, fill, cx=W / 2, stroke=INK, sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def wrap(txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    dd = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if dd.textlength(tst, font=f) <= maxw: cur = tst
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def caption(im, t):
    for a, b, txt in LINES:
        if a <= t < b: break
    else: return
    al = min(1, (t - a) / 0.25, (b - t) / 0.25)
    lines = wrap(txt, 62, 780)
    lh = 80; bh = lh * len(lines) + 40
    y0 = 1545 - bh
    box = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([90, y0, 930, y0 + bh], 40, fill=(255, 255, 255, int(225 * al)), outline=(255, 200, 60, int(255 * al)), width=6)
    for i, ln in enumerate(lines):
        f = font(62); w = bd.textlength(ln, font=f)
        bd.text((510 - w / 2, y0 + 20 + i * lh), ln, font=f, fill=INK + (int(255 * al),))
    im.alpha_composite(box)

def draw_frame(d, y0, highlight):
    x1, y1 = FX0 + 5 * CELL + 40, y0 + 2 * CELL + 40
    d.rounded_rectangle([FX0, y0, x1, y1], 36, fill=(255, 255, 255, 70),
                        outline=(255, 235, 140) if highlight else (230, 245, 255), width=8 if highlight else 6)
    for c in range(1, 5):
        x = FX0 + 20 + c * CELL
        d.line([(x, y0 + 26), (x, y1 - 26)], fill=(230, 245, 255, 150), width=4)
    d.line([(FX0 + 26, y0 + 20 + CELL), (x1 - 26, y0 + 20 + CELL)], fill=(230, 245, 255, 150), width=4)

# bubbles
BUB = [(random.uniform(40, 900), random.uniform(0, 1), random.uniform(6, 18), random.uniform(60, 140)) for _ in range(26)]

def seaweed(d, t):
    for bx, hgt, col in ((110, 330, (70, 170, 110)), (170, 250, (90, 190, 120)), (880, 300, (70, 170, 110)), (940, 220, (90, 190, 120))):
        pts = []
        for k in range(12):
            yy = 1650 - k * hgt / 11
            xx = bx + math.sin(t * 1.6 + k * 0.5 + bx) * (k * 2.2)
            pts.append((xx, yy))
        d.line(pts, fill=col, width=22, joint="curve")

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

ARRIVE = 0.9   # seconds for a new fish to swim in
for fi in range(NFR):
    t = fi / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    seaweed(d, t)
    for x, ph, r, sp in BUB:
        y = 1650 - ((t * sp + ph * 1700) % 1700)
        xx = x + math.sin(t * 2 + ph * 9) * 10
        d.ellipse([xx - r, y - r, xx + r, y + r], outline=(235, 250, 255, 190), width=3)
        d.ellipse([xx - r * 0.5, y - r * 0.6, xx - r * 0.1, y - r * 0.2], fill=(255, 255, 255, 170))
    mouth = talking(t) and (int(t * 8) % 2 == 0)

    if t < INTRO:
        bob = math.sin(t * 3) * 14; tb = 8 if mouth else 0
        paste(im, TW_BIG[mouth], W / 2 - 30, 560 + bob - tb, pop(t / 0.9), math.sin(t * 2) * 5)
        # a little parade of fish crossing
        for k in range(5):
            fx = -200 + ((t * 260 + k * 230) % 1300)
            paste(im, NEW_FISH[k * 2], fx, 1210 + math.sin(t * 3 + k) * 20, 0.8)
        d = ImageDraw.Draw(im)
        if t > 0.9: text_c(d, "Count the Fish!", 820, 116, (255, 230, 110), cx=510, sw=10)
        if t > 1.6: text_c(d, "Numbers 11 to 20", 975, 70, (255, 255, 255), cx=510, sw=7)
    elif t < T_OUT:
        # Twinkle narrator, top-left
        bob = math.sin(t * 3) * 8 - (10 if mouth else 0)
        paste(im, TW_SMALL[mouth], 150, 300 + bob, 1.0, math.sin(t * 2) * 4)
        d = ImageDraw.Draw(im)
        cur_n = 10 if t < T_N else min(20, 11 + int((t - T_N) // SEG))
        lt = (t - T_TEN) if t < T_N else (t - nstart(cur_n))
        draw_frame(d, F1Y, t < T_N)
        draw_frame(d, F2Y, t >= T_N)
        # ten orange fish
        for i in range(10):
            at = T_TEN + 0.25 + i * 0.22
            if t < at: continue
            x, y = slot(0, i)
            p = ease((t - at) / 0.6)
            sx = -120 + (x + 120) * p
            wig = math.sin(t * 4 + i) * 5
            paste(im, ORANGE_FISH, sx, y + wig + (1 - p) * math.sin(p * 9) * 30, 1.0)
        # extra fish
        for j in range(10):
            n = 11 + j
            if t < nstart(n): continue
            x, y = slot(1, j)
            p = ease((t - nstart(n)) / ARRIVE)
            sx = -120 + (x + 120) * p
            sy = y + (1 - p) * math.sin(p * 10) * 45 + math.sin(t * 4 + j) * 5
            sc = 1.0 + (0.18 * math.sin(min(1, (t - nstart(n) - ARRIVE) / 0.5) * math.pi) if t - nstart(n) > ARRIVE else 0)
            paste(im, NEW_FISH[j], sx, sy, sc)
        d = ImageDraw.Draw(im)
        # count bubble above newest fish
        if t >= T_N and 0.8 < lt < 2.3:
            x, y = slot(1, cur_n - 11)
            a = int(255 * min(1, (2.3 - lt) / 0.4))
            bx, by, br = x + 46, y - 44, 34
            d.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, a), outline=INK + (a,), width=4)
            cf = font(38); c = str(cur_n); cw = d.textlength(c, font=cf)
            d.text((bx - cw / 2, by - 27), c, font=cf, fill=INK + (a,))
        # big number + word + equation
        ns = pop(lt / 0.6) if (t < T_N and lt > 2.6) or t >= T_N else 0
        if t < T_N: ns = pop((lt - 2.4) / 0.6)
        if ns > 0:
            col = ORANGE if cur_n == 10 else NEWCOL[cur_n - 11]
            f = font(220 * ns); txt = str(cur_n); w = d.textlength(txt, font=f)
            d.text((560 - w / 2, 120 + (220 - 220 * ns) / 2), txt, font=f, fill=col, stroke_width=12, stroke_fill=INK)
            if ns > 0.9:
                text_c(d, WORDS[cur_n], 395, 84, (255, 255, 255), cx=560, sw=8)
                eq = "10" if cur_n == 10 else f"10 + {cur_n - 10} = {cur_n}"
                text_c(d, eq, 500, 60, (255, 240, 150), cx=560, sw=6)
    else:
        lt = t - T_OUT; bob = math.sin(t * 3) * 14; tb = 8 if mouth else 0
        paste(im, TW_BIG[mouth], W / 2 - 30, 520 + bob - tb, pop(lt / 0.9), math.sin(t * 4) * 8)
        # fish circle dance
        for k in range(20):
            a = t * 0.7 + k * 2 * math.pi / 20
            fx, fy = 510 + math.cos(a) * 380, 560 + math.sin(a) * 300
            sp = ORANGE_FISH if k % 2 == 0 else NEW_FISH[k // 2]
            if fy > 520: paste(im, sp, fx, fy, 0.55)
        d = ImageDraw.Draw(im)
        if lt > 0.7: text_c(d, "Great counting!", 930, 110, (255, 230, 110), cx=510, sw=10)
        if lt > 1.5: text_c(d, "You counted 20 fish!", 1075, 64, (255, 255, 255), cx=510, sw=7)
        if lt > 3.2: text_c(d, "Subscribe for more!", 1170, 56, (200, 240, 255), cx=510, sw=6)
    caption(im, t)
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle 3/4 waltz, marimba-like ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, kind="marimba", decay=6):
    tt = np.arange(int(dur * SR)) / SR
    if kind == "marimba":
        w = np.sin(2 * np.pi * freq * tt) + 0.25 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-30 * tt)
    elif kind == "pad":
        w = np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt)
    else:
        w = np.sin(2 * np.pi * freq * tt)
    env = np.exp(-decay * tt) * np.minimum(1, tt * 150)
    return vol * w * env
def bloop(at, f0=300, f1=900, vol=0.18):
    tt = np.arange(int(0.18 * SR)) / SR
    f = f0 + (f1 - f0) * (tt / 0.18)
    sig = vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-10 * tt)
    add(sig, at)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]

F = {"F": 349.23, "G": 392.0, "A": 440.0, "C": 523.25, "D": 587.33, "F2": 698.46, "A2": 880.0}
melody = ["A", "C", "D", "C", "A", "G", "F", "G", "A", "D", "C", "A", "G", "A", "C", "F2", "D", "C",
          "A", "G", "A", "C", "G", "F"]
roots = [87.31, 116.54, 130.81, 87.31]   # F, Bb, C, F
beat = 0.42; k = 0
while k * beat < TOTAL - 1.0:
    add(tone(F[melody[k % len(melody)]], 0.8, 0.045, "marimba", 5), k * beat)
    if k % 3 == 0: add(tone(roots[(k // 6) % 4], 2.4, 0.07, "pad", 1.2), k * beat)
    k += 1
for kk in range(6): bloop(0.2 + kk * 0.35, 250 + kk * 60, 700 + kk * 80, 0.12)
for i in range(10): bloop(T_TEN + 0.25 + i * 0.22 + 0.5, 400, 800, 0.1)
chime = [523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5, 1174.66, 1318.5]
for n in range(11, 21):
    bloop(nstart(n) + ARRIVE - 0.1, 300, 1000, 0.16)
    add(tone(chime[n - 11], 0.6, 0.16, "marimba", 6), nstart(n) + ARRIVE)
for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
    add(tone(f, 1.2, 0.15, "marimba", 3), T_OUT + 0.1 + i * 0.18)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", round(TOTAL, 1))
