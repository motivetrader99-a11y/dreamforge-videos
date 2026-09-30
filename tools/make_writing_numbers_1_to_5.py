"""Dreamforge Kids — Number shapes: how to write 1 to 5.
Sunny beach scene. For each number a dotted guide appears in the sand, a green start
dot pulses, and a little original crab scuttles along the path leaving a thick colorful
trail, stroke by stroke, while Twinkle says the writing rhyme. Then that many seashells
pop up to count. Outro: all five numbers dance in a row. Original art & music
(plucked ukulele-style lullaby + soft waves)."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/writing_numbers_1_to_5.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (60, 50, 80)
random.seed(15)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- digit paths (normalized box 0..1) ----------
def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
DIGITS = {
    1: [[(0.3, 0.16), (0.52, 0.0), (0.52, 1.0)]],
    2: [arc(0.5, 0.27, 0.36, 0.27, -165, 40, 26) + [(0.1, 1.0), (0.9, 1.0)]],
    3: [arc(0.47, 0.24, 0.34, 0.24, -160, 90, 26) + arc(0.47, 0.73, 0.4, 0.27, -90, 160, 28)[1:]],
    4: [[(0.24, 0.0), (0.12, 0.62), (0.9, 0.62)], [(0.7, 0.0), (0.7, 1.0)]],
    5: [[(0.3, 0.0), (0.252, 0.467)] + arc(0.5, 0.69, 0.37, 0.3, -132, 150, 28)[1:], [(0.3, 0.0), (0.86, 0.0)]],
}
BX, BY, BW, BH = 180, 640, 380, 520
COLS = {1: (255, 110, 120), 2: (255, 165, 60), 3: (80, 190, 120), 4: (70, 150, 240), 5: (175, 110, 230)}
WORD = ["zero", "one", "two", "three", "four", "five"]

def to_px(pts, box=(BX, BY, BW, BH)):
    x, y, w, h = box
    return [(x + px * w, y + py * h) for px, py in pts]
def plen(p): return sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1))
def partial(p, L):
    out = [p[0]]; acc = 0
    for i in range(len(p) - 1):
        s = math.dist(p[i], p[i + 1])
        if acc + s >= L:
            u = (L - acc) / s if s else 0
            out.append((p[i][0] + (p[i + 1][0] - p[i][0]) * u, p[i][1] + (p[i + 1][1] - p[i][1]) * u))
            return out
        out.append(p[i + 1]); acc += s
    return out

# ---------- timeline ----------
INTRO, RD, OUTRO = 4.6, 8.4, 6.2
R = [INTRO + i * RD for i in range(5)]
T_OUT = INTRO + 5 * RD
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)
T_GUIDE, T_TR0, T_TR1, T_DONE = 0.15, 0.9, 4.1, 4.25
T_SH, SGAP = 4.6, 0.45

RHYME = {1: "One: a little flag, then straight down!",
         2: "Two: curve around, slide down, go across!",
         3: "Three: around one bump, then around again!",
         4: "Four: down, across, then one long line down!",
         5: "Five: down, a round belly, then a hat!"}
def count_line(n): return "Count: " + ", ".join(WORD[1:n + 1]) + "!" if n > 1 else "Count: one shell!"
LINES = [(0.3, INTRO - 0.15, "Hi! I'm Twinkle! Let's write numbers 1 to 5!")]
for i in range(5):
    n = i + 1
    LINES.append((R[i] + 0.15, R[i] + T_SH - 0.1, RHYME[n]))
    LINES.append((R[i] + T_SH, R[i] + RD - 0.15, count_line(n)))
LINES.append((T_OUT + 0.3, T_OUT + 3.2, "You can write 1, 2, 3, 4, 5!"))
LINES.append((T_OUT + 3.3, TOTAL - 0.3, "Trace them with your finger!"))
TALK = [(a, a + min(b - a - 0.2, len(txt.split()) * 0.42 + 0.4)) for a, b, txt in LINES]
def talking(t): return any(a <= t < b for a, b in TALK)

def stroke_schedule(n):
    strokes = [to_px(s) for s in DIGITS[n]]
    lens = [plen(s) for s in strokes]; pause = 0.3
    avail = (T_TR1 - T_TR0) - pause * (len(strokes) - 1)
    sched, t = [], T_TR0
    for s, L in zip(strokes, lens):
        d = avail * L / sum(lens); sched.append((s, L, t, t + d)); t += d + pause
    return sched
SCHED = {n: stroke_schedule(n) for n in range(1, 6)}

# ---------- helpers ----------
def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)
def paste(canvas, sp, cx, cy, s=1.0, rot=0):
    if s <= 0.02: return
    if s != 1.0: sp = sp.resize((max(2, int(sp.width * s)), max(2, int(sp.height * s))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))
def text_c(d, txt, cx, y, sz, fill, stroke=INK, sw=8, maxw=None):
    f = font(sz)
    if maxw:
        while d.textlength(txt, font=f) > maxw and sz > 20: sz -= 2; f = font(sz)
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]
def thick(d, pts, col, w):
    if len(pts) < 2: return
    d.line(pts, fill=col, width=w, joint="curve")
    for p in (pts[0], pts[-1]):
        d.ellipse([p[0] - w / 2 + 1, p[1] - w / 2 + 1, p[0] + w / 2 - 1, p[1] + w / 2 - 1], fill=col)

# ---------- art ----------
def make_twinkle(r, mouth_open):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c = s / 2
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(c, c, r * 1.08), fill=(255, 225, 90, 130))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15))); d = ImageDraw.Draw(im)
    d.polygon(star_poly(c, c + r * 0.05, r), fill=(225, 165, 30)); d.polygon(star_poly(c, c, r), fill=(255, 210, 60))
    e = r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([c + dx - e, c - e * 1.4, c + dx + e, c + e * 1.2], fill=(70, 40, 60))
        d.ellipse([c + dx - e * 0.5, c - e * 1.1, c + dx + e * 0.1, c - e * 0.4], fill=(255, 255, 255))
    if mouth_open:
        d.ellipse([c - r * 0.13, c + r * 0.12, c + r * 0.13, c + r * 0.34], fill=(150, 50, 60))
        d.ellipse([c - r * 0.07, c + r * 0.24, c + r * 0.07, c + r * 0.33], fill=(255, 130, 140))
    else:
        d.arc([c - r * 0.16, c + r * 0.05, c + r * 0.16, c + r * 0.28], 20, 160, fill=(70, 40, 60), width=max(3, int(r * 0.06)))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([c + dx - r * 0.1, c + r * 0.1, c + dx + r * 0.1, c + r * 0.22], fill=(255, 130, 150, 150))
    return im

def make_crab(leg):
    s = 200; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 100
    body, dark = (255, 120, 80), (215, 85, 55)
    for side in (-1, 1):
        for k in range(3):
            off = (4 if (k + leg) % 2 else -4)
            x0 = c + side * 38; y0 = c + 12 + k * 10
            d.line([x0, y0, x0 + side * 34, y0 + 18 + off], fill=dark, width=8)
        # claws
        d.line([c + side * 42, c - 2, c + side * 66, c - 26], fill=dark, width=9)
        d.ellipse([c + side * 66 - 17, c - 46, c + side * 66 + 17, c - 14], fill=body)
        d.polygon([(c + side * 66, c - 32), (c + side * 84, c - 50), (c + side * 76, c - 26)], fill=(0, 0, 0, 0))
    d.ellipse([c - 50, c - 22, c + 50, c + 40], fill=dark); d.ellipse([c - 48, c - 26, c + 48, c + 34], fill=body)
    for dx in (-18, 18):
        d.line([c + dx, c - 18, c + dx, c - 44], fill=dark, width=6)
        d.ellipse([c + dx - 13, c - 64, c + dx + 13, c - 36], fill=(255, 255, 255))
        d.ellipse([c + dx - 7, c - 56, c + dx + 5, c - 42], fill=(50, 40, 60))
        d.ellipse([c + dx - 4, c - 54, c + dx, c - 50], fill=(255, 255, 255))
    d.arc([c - 14, c - 4, c + 14, c + 16], 20, 160, fill=(120, 40, 40), width=5)
    for dx in (-30, 30): d.ellipse([c + dx - 8, c + 2, c + dx + 8, c + 12], fill=(255, 170, 170))
    return im

def make_shell(col, r=50):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    dark = tuple(max(0, v - 45) for v in col)
    pts = [(c + math.cos(math.radians(a)) * r, c + 8 + math.sin(math.radians(a)) * r * 0.95) for a in range(190, 351, 5)]
    fan = [(c, c + r * 0.72)] + pts
    d.polygon(fan, fill=col, outline=dark, width=4)
    for a in range(200, 350, 22):
        d.line([c, c + r * 0.72, c + math.cos(math.radians(a)) * r * 0.95, c + 8 + math.sin(math.radians(a)) * r * 0.9], fill=dark, width=3)
    d.polygon([(c - 22, c + r * 0.62), (c + 22, c + r * 0.62), (c + 14, c + r * 0.9), (c - 14, c + r * 0.9)], fill=dark)
    hl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r * 0.6, c - r * 0.7, c - r * 0.1, c - r * 0.35], fill=(255, 255, 255, 110))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(5)))
    return im

def background():
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    arr = np.zeros((H, W, 4), np.uint8); arr[..., 3] = 255
    g = np.clip(np.arange(440) / 440, 0, 1)[:, None]
    arr[:440, :, :3] = (np.array([120, 200, 250]) * (1 - g) + np.array([205, 238, 255]) * g)[:, None, :].astype(np.uint8)
    g2 = np.clip(np.arange(120) / 120, 0, 1)[:, None]
    arr[440:560, :, :3] = (np.array([60, 170, 215]) * (1 - g2) + np.array([110, 215, 225]) * g2)[:, None, :].astype(np.uint8)
    g3 = np.clip(np.arange(H - 560) / (H - 560), 0, 1)[:, None]
    arr[560:, :, :3] = (np.array([252, 232, 185]) * (1 - g3) + np.array([240, 210, 160]) * g3)[:, None, :].astype(np.uint8)
    bg = Image.fromarray(arr, "RGBA"); d = ImageDraw.Draw(bg)
    # sun
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([10, -20, 230, 200], fill=(255, 245, 190, 150))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(bg)
    d.ellipse([55, 25, 185, 155], fill=(255, 225, 110))
    # clouds
    for (x, y, s) in [(760, 110, 1.0), (520, 360, 0.7)]:
        for dx, rr in [(-55, 36), (0, 52), (55, 38), (25, 30)]:
            d.ellipse([x + dx * s - rr * s, y - rr * s, x + dx * s + rr * s, y + rr * s], fill=(255, 255, 255))
    # sand speckles
    rnd = random.Random(3)
    for _ in range(700):
        x, y = rnd.randint(0, W), rnd.randint(600, H)
        d.ellipse([x, y, x + 4, y + 4], fill=(225, 195, 140))
    # beach umbrella (right, behind shells)
    d.line([905, 470, 880, 640], fill=(160, 120, 90), width=10)
    for k in range(6):
        a0 = 180 + k * 30
        col = (255, 120, 130) if k % 2 == 0 else (255, 250, 240)
        d.pieslice([770, 400, 1040, 560], a0, a0 + 30, fill=col)
    d.line([775, 480, 1035, 480], fill=(230, 100, 110), width=5)
    # caption panel
    d.rounded_rectangle([40, 1290, 930, 1545], radius=44, fill=(255, 252, 244), outline=(90, 190, 210), width=8)
    return bg

BG = background()
TWK = [make_twinkle(80, False), make_twinkle(80, True)]
TWK_BIG = [make_twinkle(160, False), make_twinkle(160, True)]
CRAB = [make_crab(0), make_crab(1)]
SHELLS = [make_shell(c) for c in [(255, 190, 200), (255, 215, 150), (200, 225, 255), (210, 240, 200), (230, 205, 255)]]

def draw_waves(d, t):
    for k, (y, amp, col) in enumerate([(548, 7, (255, 255, 255)), (570, 5, (235, 250, 250))]):
        pts = [(x, y + math.sin(x / 55 + t * 1.6 + k) * amp) for x in range(0, W + 20, 20)]
        d.line(pts, fill=col, width=8 - k * 2, joint="curve")

def wrap(d, txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw: cur = trial
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def draw_caption(im, d, t):
    for a, b, txt in LINES:
        if a <= t < b:
            al = min(1, (t - a) / 0.25, (b - t) / 0.25)
            sz = 62; lines = wrap(d, txt, sz, 610)
            while len(lines) > 3: sz -= 4; lines = wrap(d, txt, sz, 610)
            lh = sz * 1.22; y0 = 1418 - lh * len(lines) / 2 - 6
            for k, ln in enumerate(lines):
                f = font(sz); w = d.textlength(ln, font=f)
                d.text((375 - w / 2, y0 + k * lh), ln, font=f, fill=INK + (int(255 * al),))
            break
    tk = talking(t); mo = tk and int(t * 8) % 2 == 0
    bob = math.sin(t * 3) * 6 + (abs(math.sin(t * 11)) * -10 if tk else 0)
    paste(im, TWK[mo], 805, 1418 + bob, 1.0, math.sin(t * 2) * 5)

def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, 0, 0.35), fill=(255, 250, 200, int(255 * max(0, min(1, a)))))

def draw_guide(d, n, alpha):
    for s, L, _, _ in SCHED[n]:
        k = 0.0
        while k <= L:
            p = partial(s, k)[-1]
            d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=(200, 165, 115, int(255 * alpha)))
            k += 34

def draw_round(im, i, lt, t):
    n = i + 1; col = COLS[n]
    d = ImageDraw.Draw(im)
    text_c(d, f"Let's write  {n}", 470, 150, 104, (255, 255, 255), stroke=col, sw=10, maxw=760)
    draw_guide(d, n, ease((lt - T_GUIDE) / 0.5))
    sched = SCHED[n]
    pen = None; moving = False
    # start dots (green) for strokes not yet begun
    for j, (s, L, a, b) in enumerate(sched):
        if lt < a and lt > T_GUIDE + 0.4:
            p = s[0]; pr = 20 + 6 * math.sin(t * 8)
            d.ellipse([p[0] - pr - 8, p[1] - pr - 8, p[0] + pr + 8, p[1] + pr + 8], fill=(120, 220, 130, 110))
            d.ellipse([p[0] - 20, p[1] - 20, p[0] + 20, p[1] + 20], fill=(70, 190, 100), outline=(255, 255, 255), width=5)
    for j, (s, L, a, b) in enumerate(sched):
        if lt < a:
            if pen is None and j > 0: pen = sched[j - 1][0][-1]
            continue
        u = ease((lt - a) / (b - a)) if lt < b else 1
        part = partial(s, L * u)
        thick(d, part, (255, 255, 255), 78)
    for j, (s, L, a, b) in enumerate(sched):
        if lt < a: continue
        u = ease((lt - a) / (b - a)) if lt < b else 1
        part = partial(s, L * u)
        thick(d, part, col, 56)
        if a <= lt < b: pen = part[-1]; moving = True
    if pen is None: pen = sched[-1][0][-1] if lt >= T_DONE else sched[0][0][0]
    # crab tracer: arrives before tracing, leaves after
    if lt < T_TR0:
        u = ease((lt - 0.1) / 0.7); sx = -120
        cx, cy = sx + (pen[0] - sx) * u, pen[1] - 30
    elif lt < T_DONE + 0.2:
        cx, cy = pen[0], pen[1] - 30
    else:
        u = ease((lt - T_DONE - 0.2) / 0.8)
        cx, cy = pen[0] + (-160 - pen[0]) * u, pen[1] - 30 + 60 * u
    if lt < T_DONE + 1.1:
        leg = int(t * 10) % 2 if (moving or lt < T_TR0 or lt > T_DONE + 0.2) else 0
        paste(im, CRAB[leg], cx, cy + math.sin(t * 20) * 3, 0.85, math.sin(t * 12) * 6 if moving else 0)
    d = ImageDraw.Draw(im)
    if lt >= T_DONE:
        k = lt - T_DONE
        for m in range(10):
            ang = m * 2 * math.pi / 10 + t
            rr = 100 + k * 180
            if rr < 380: sparkle(d, BX + BW / 2 + math.cos(ang) * rr, BY + BH / 2 + math.sin(ang) * rr * 1.1, 16, 1 - rr / 380)
    # shells to count
    for k in range(n):
        st = T_SH + k * SGAP
        if lt >= st:
            y = 650 + k * 130 + (5 - n) * 65
            hop = math.sin((lt - st) / 0.35 * math.pi) * 25 if lt - st < 0.35 else 0
            paste(im, SHELLS[k], 745, y - hop, 1.2 * pop((lt - st) / 0.4))
            d = ImageDraw.Draw(im)
            f = font(60); c = str(k + 1); cw = d.textlength(c, font=f)
            if lt - st > 0.2: d.text((745 - cw / 2, y - 28), c, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=INK)

def draw_outro(im, lt, t):
    d = ImageDraw.Draw(im)
    if lt > 0.3: text_c(d, "Great writing!", 470, 150, 104, (255, 255, 255), stroke=(90, 170, 210), sw=10, maxw=780)
    for n in range(1, 6):
        st = 0.4 + (n - 1) * 0.3
        if lt < st: continue
        s = pop((lt - st) / 0.5) * 0.36
        cx = 150 + (n - 1) * 160; cy = 1010 - abs(math.sin(t * 3 + n)) * 30
        box = (cx - BW * s / 2, cy - BH * s / 2, BW * s, BH * s)
        for st_pts in DIGITS[n]:
            thick(d, to_px(st_pts, box), (255, 255, 255), max(4, int(78 * s)))
        for st_pts in DIGITS[n]:
            thick(d, to_px(st_pts, box), COLS[n], max(3, int(56 * s)))
    mo = talking(t) and int(t * 8) % 2 == 0
    paste(im, TWK_BIG[mo], 470, 620 + math.sin(t * 3) * 12 - abs(math.sin(t * 4)) * 16, pop(lt / 0.8), math.sin(t * 3) * 7)
    d = ImageDraw.Draw(im)
    if lt > 2.0:
        for k in range(12):
            ang = k * math.pi / 6 + t * 0.8
            sparkle(d, 470 + math.cos(ang) * 250, 620 + math.sin(ang) * 210, 14 + 6 * math.sin(t * 5 + k), 0.9)

def render_frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    draw_waves(d, t)
    if t < INTRO:
        text_c(d, "Write 1 to 5", 470, 150, 110, (255, 255, 255), stroke=(90, 170, 210), sw=10) if t > 0.6 else None
        mo = talking(t) and int(t * 8) % 2 == 0
        paste(im, TWK_BIG[mo], 470, 760 + math.sin(t * 3) * 14, pop(t / 0.8), math.sin(t * 2) * 6)
        d = ImageDraw.Draw(im)
        for n in range(1, 6):
            if t > 1.6 + n * 0.3:
                f = font(110 * pop((t - 1.6 - n * 0.3) / 0.5)); c = str(n); cw = d.textlength(c, font=f)
                x = 150 + (n - 1) * 160
                d.text((x - cw / 2, 990 - abs(math.sin(t * 3 + n)) * 20), c, font=f, fill=COLS[n], stroke_width=8, stroke_fill=(255, 255, 255))
        cr = int(t * 10) % 2
        paste(im, CRAB[cr], -100 + min(1, max(0, (t - 2.0) / 1.5)) * 900, 1210, 0.85)
    elif t >= T_OUT:
        draw_outro(im, t - T_OUT, t)
    else:
        i = min(4, int((t - INTRO) // RD)); draw_round(im, i, t - R[i], t)
    d = ImageDraw.Draw(im)
    draw_caption(im, d, t)
    if t < 0.4 or t > TOTAL - 0.6:
        k = min(t / 0.4, (TOTAL - t) / 0.6)
        im = Image.blend(Image.new("RGBA", (W, H), (205, 238, 255, 255)), im, max(0, min(1, k)))
    return im

# ---------- render ----------
if __name__ == "__main__":
    import sys
    only = [float(x) for x in sys.argv[1:]]
    if only:
        for tt in only: render_frame(tt).convert("RGB").save(f"_preview_{tt:.1f}.png")
        sys.exit(0)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(render_frame(fi / FPS).convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()

    # ---------- audio: original plucked lullaby in F major + soft waves ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    rng = np.random.default_rng(5)
    def pluck(freq, dur, vol=0.2):
        n = int(dur * SR); p = max(2, int(SR / freq))
        buf = rng.uniform(-1, 1, p); out = np.zeros(n); pos = 0
        while pos < n:
            m = min(p, n - pos); out[pos:pos + m] = buf[:m]
            buf = 0.996 * 0.5 * (buf + np.roll(buf, -1)); pos += m
        env = np.minimum(1, np.arange(n) / 60) * np.linspace(1, 0.6, n)
        return vol * out * env
    def bell(freq, dur, vol=0.1, decay=6):
        tt = np.arange(int(dur * SR)) / SR
        return vol * np.sin(2 * np.pi * freq * tt) * np.exp(-decay * tt) * np.minimum(1, tt * 400)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N: audio[i:j] += sig[:j - i]
    NT = {"F2": 87.31, "Bb2": 116.54, "C3": 130.81, "D3": 146.83, "F3": 174.61, "A3": 220.0, "Bb3": 233.08,
          "C4": 261.63, "D4": 293.66, "F4": 349.23, "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33}
    prog = [("F2", ["F3", "A3", "C4"]), ("D3", ["D4", "F4", "A4"]), ("Bb2", ["Bb3", "D4", "F4"]), ("C3", ["C4", "G4", "C5"])]
    mel = ["A4", None, "C5", None, "D5", "C5", "A4", None, "F4", None, "G4", "A4", "G4", None, None, None]
    beat = 0.55; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 4) % 4; root, ch = prog[bar]
        if k % 4 == 0: add(pluck(NT[root], 2.0, 0.16), k * beat)
        add(pluck(NT[ch[k % 3]], 0.9, 0.06), k * beat + beat / 2)
        m = mel[k % 16]
        if m and (k // 16) % 2 == 0: add(pluck(NT[m], 1.2, 0.08), k * beat)
        k += 1
    # soft waves: filtered noise swelling slowly
    noise = rng.normal(0, 1, N); kern = np.ones(400) / 400
    wav = np.convolve(noise, kern, mode="same") * 3
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * np.arange(N) / SR / 6.0)
    audio += 0.05 * wav * swell
    for i in range(5):
        n = i + 1
        for (s, L, a, b) in SCHED[n]:
            add(bell(783.99, 0.4, 0.05, 8), R[i] + a)
        for j, f in enumerate([523.25, 659.25, 783.99, 1046.5]): add(bell(f, 0.9, 0.07, 4), R[i] + T_DONE + j * 0.08)
        sc = [523.25, 587.33, 659.25, 698.46, 783.99]
        for k2 in range(n): add(bell(sc[k2], 0.4, 0.12, 7), R[i] + T_SH + k2 * SGAP)
    for j, f in enumerate([523.25, 659.25, 783.99, 1046.5, 1318.5]): add(bell(f, 1.2, 0.09, 3), T_OUT + 0.4 + j * 0.3)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
