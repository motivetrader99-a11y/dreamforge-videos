"""Dreamforge Kids — Number shapes: how to write 6 to 10.
Pastel spring garden. Each number is written on a big wooden garden sign: a dotted guide
appears, a green start dot pulses, and a little original ladybug walks the path leaving a
thick colorful trail while Twinkle (in the caption box, bottom-left) says the writing rhyme.
Then that many daisies bloom in the grass (two rows of five) to count. Outro: 6-10 bounce
on the sign. Original art & music (music-box waltz in G + soft bird chirps)."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/writing_numbers_6_to_10.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (70, 50, 70)
random.seed(610)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
def bez(p0, p1, p2, n):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in [k / n for k in range(n + 1)]]
def eight(n=72):
    pts = []
    for k in range(n + 1):
        u = 2 * math.pi * k / n; s = math.sin(2 * u)
        pts.append((0.5 - 0.42 * math.copysign(abs(s) ** 0.6, s), 0.5 - 0.5 * math.cos(u)))
    return pts
DIGITS = {
    6: [bez((0.78, 0.03), (0.14, 0.08), (0.15, 0.72), 20)[:-1] + arc(0.5, 0.72, 0.35, 0.28, 180, -180, 34)],
    7: [[(0.1, 0.0), (0.9, 0.0), (0.38, 1.0)]],
    8: [eight()],
    9: [arc(0.47, 0.28, 0.35, 0.28, 0, -360, 34) + [(0.8, 1.0)]],
    10: [[(0.02, 0.17), (0.2, 0.0), (0.2, 1.0)], arc(0.68, 0.5, 0.27, 0.5, -90, -450, 40)],
}
BX, BY, BW, BH = 300, 400, 380, 500
COLS = {6: (240, 110, 150), 7: (250, 150, 70), 8: (60, 175, 160), 9: (110, 130, 235), 10: (190, 100, 210)}
NUMS = [6, 7, 8, 9, 10]

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
INTRO, RD, OUTRO = 4.6, 8.6, 6.0
R = [INTRO + i * RD for i in range(5)]
T_OUT = INTRO + 5 * RD
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)
T_GUIDE, T_TR0, T_TR1, T_DONE = 0.15, 0.9, 4.1, 4.25
T_SH, SGAP = 4.55, 0.34

RHYME = {6: "Six: curve down, then roll into a loop!",
         7: "Seven: go across, then slide down!",
         8: "Eight: make an S, then go back up!",
         9: "Nine: a little circle, then a line down!",
         10: "Ten: a one, then a big round zero!"}
def count_line(n): return f"Let's count the flowers up to {n}!"
LINES = [(0.3, INTRO - 0.15, "Hi! I'm Twinkle! Let's write 6 to 10!")]
for i, n in enumerate(NUMS):
    LINES.append((R[i] + 0.15, R[i] + T_SH - 0.1, RHYME[n]))
    LINES.append((R[i] + T_SH, R[i] + RD - 0.15, count_line(n)))
LINES.append((T_OUT + 0.3, T_OUT + 3.1, "You can write 6, 7, 8, 9, 10!"))
LINES.append((T_OUT + 3.2, TOTAL - 0.3, "Try it in the air with your finger!"))
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
SCHED = {n: stroke_schedule(n) for n in NUMS}

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
    for p in pts[::3] + [pts[-1]]:
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

def make_ladybug(step):
    s = 180; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = 90
    for side in (-1, 1):
        for k in range(3):
            off = 6 if (k + step) % 2 else -6
            y0 = c - 10 + k * 22
            d.line([c + side * 30, y0, c + side * 60, y0 + off + 8], fill=(60, 45, 60), width=6)
    d.ellipse([c - 52, c - 42, c + 52, c + 58], fill=(60, 45, 60))
    d.ellipse([c - 48, c - 38, c + 48, c + 54], fill=(240, 80, 90))
    d.line([c, c - 36, c, c + 52], fill=(60, 45, 60), width=5)
    for (dx, dy, rr) in [(-26, -8, 10), (24, -4, 9), (-20, 26, 9), (26, 28, 10)]:
        d.ellipse([c + dx - rr, c + dy - rr, c + dx + rr, c + dy + rr], fill=(60, 45, 60))
    hl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - 36, c - 30, c - 12, c - 12], fill=(255, 255, 255, 120))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(4))); d = ImageDraw.Draw(im)
    d.ellipse([c - 34, c - 78, c + 34, c - 26], fill=(60, 45, 60))
    for dx in (-13, 13):
        d.line([c + dx, c - 72, c + dx * 2, c - 92], fill=(60, 45, 60), width=4)
        d.ellipse([c + dx * 2 - 6, c - 98, c + dx * 2 + 6, c - 86], fill=(60, 45, 60))
        d.ellipse([c + dx - 10, c - 66, c + dx + 10, c - 44], fill=(255, 255, 255))
        d.ellipse([c + dx - 5, c - 60, c + dx + 4, c - 48], fill=(40, 30, 50))
        d.ellipse([c + dx - 3, c - 59, c + dx, c - 56], fill=(255, 255, 255))
    d.arc([c - 10, c - 50, c + 10, c - 34], 20, 160, fill=(255, 170, 180), width=4)
    return im

def make_daisy(col, r=46):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    dark = tuple(max(0, v - 40) for v in col)
    for k in range(8):
        a = k * math.pi / 4
        px, py = c + math.cos(a) * r * 0.62, c + math.sin(a) * r * 0.62
        d.ellipse([px - r * 0.42, py - r * 0.42, px + r * 0.42, py + r * 0.42], fill=col, outline=dark, width=3)
    d.ellipse([c - r * 0.42, c - r * 0.42, c + r * 0.42, c + r * 0.42], fill=(255, 205, 70), outline=(230, 160, 40), width=4)
    for dx in (-r * 0.14, r * 0.14):
        d.ellipse([c + dx - 4, c - 8, c + dx + 4, c + 2], fill=(70, 45, 55))
    d.arc([c - 10, c - 4, c + 10, c + 12], 20, 160, fill=(70, 45, 55), width=3)
    return im

def background():
    arr = np.zeros((H, W, 4), np.uint8); arr[..., 3] = 255
    g = np.clip(np.arange(H) / 1000, 0, 1)[:, None]
    arr[:, :, :3] = (np.array([200, 190, 245]) * (1 - g) + np.array([255, 220, 205]) * g)[:, None, :].astype(np.uint8)
    bg = Image.fromarray(arr, "RGBA"); d = ImageDraw.Draw(bg)
    # soft clouds
    for (x, y, s) in [(160, 300, 0.8), (860, 250, 1.0)]:
        for dx, rr in [(-55, 36), (0, 52), (55, 38), (25, 30)]:
            d.ellipse([x + dx * s - rr * s, y - rr * s, x + dx * s + rr * s, y + rr * s], fill=(255, 250, 255))
    # rolling hills
    d.ellipse([-400, 800, 700, 1500], fill=(170, 220, 160))
    d.ellipse([400, 760, 1500, 1500], fill=(150, 210, 150))
    d.rectangle([0, 1000, W, H], fill=(135, 200, 135))
    rnd = random.Random(8)
    for _ in range(260):
        x, y = rnd.randint(0, W), rnd.randint(1000, H)
        d.line([x, y, x - 4, y - 16], fill=(110, 180, 115), width=4)
    # sign posts + board
    for px in (BX + 20, BX + BW - 40):
        d.rounded_rectangle([px - 4, 780, px + 40, 1060], radius=10, fill=(170, 115, 75))
    d.rounded_rectangle([BX - 120, BY - 70, BX + BW + 120, BY + BH + 70], radius=48, fill=(175, 120, 80))
    d.rounded_rectangle([BX - 104, BY - 54, BX + BW + 104, BY + BH + 54], radius=38, fill=(255, 246, 228))
    # little vines on the sign corners
    for (vx, vy) in [(BX - 110, BY - 60), (BX + BW + 110, BY + BH + 60)]:
        for k in range(4):
            a = k * 1.3
            lx, ly = vx + math.cos(a) * 26, vy + math.sin(a) * 26
            d.ellipse([lx - 16, ly - 10, lx + 16, ly + 10], fill=(120, 190, 120))
    # caption panel
    d.rounded_rectangle([40, 1290, 930, 1545], radius=44, fill=(255, 252, 246), outline=(200, 150, 220), width=8)
    return bg

BG = background()
TWK = [make_twinkle(78, False), make_twinkle(78, True)]
TWK_BIG = [make_twinkle(150, False), make_twinkle(150, True)]
BUG = [make_ladybug(0), make_ladybug(1)]
DAISY_COLS = [(255, 255, 255), (255, 200, 220), (210, 225, 255), (255, 230, 190), (225, 210, 255)]
DAISIES = [make_daisy(c) for c in DAISY_COLS]

def flower_pos(k):
    row, col = divmod(k, 5)
    return 160 + col * 155, 1110 + row * 120

def draw_butterfly(d, t):
    x = 120 + (t * 45) % 780; y = 285 + math.sin(t * 1.3) * 18
    flap = abs(math.sin(t * 9))
    for side in (-1, 1):
        wx = 26 * flap + 6
        d.ellipse([x + side * wx - 18, y - 22, x + side * wx + 18, y + 6], fill=(255, 190, 120))
        d.ellipse([x + side * wx * 0.8 - 12, y, x + side * wx * 0.8 + 12, y + 20], fill=(255, 160, 190))
    d.ellipse([x - 5, y - 20, x + 5, y + 20], fill=(90, 60, 80))

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
            sz = 62; lines = wrap(d, txt, sz, 620)
            while len(lines) > 3: sz -= 4; lines = wrap(d, txt, sz, 620)
            lh = sz * 1.22; y0 = 1418 - lh * len(lines) / 2 - 6
            for k, ln in enumerate(lines):
                f = font(sz); w = d.textlength(ln, font=f)
                d.text((575 - w / 2, y0 + k * lh), ln, font=f, fill=INK + (int(255 * al),))
            break
    tk = talking(t); mo = tk and int(t * 8) % 2 == 0
    bob = math.sin(t * 3) * 6 + (abs(math.sin(t * 11)) * -10 if tk else 0)
    paste(im, TWK[mo], 158, 1418 + bob, 1.0, math.sin(t * 2) * 5)

def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, 0, 0.35), fill=(255, 215, 120, int(255 * max(0, min(1, a)))))

def draw_guide(d, n, alpha):
    for s, L, _, _ in SCHED[n]:
        k = 0.0
        while k <= L:
            p = partial(s, k)[-1]
            d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=(215, 190, 160, int(255 * alpha)))
            k += 34

def draw_round(im, i, lt, t):
    n = NUMS[i]; col = COLS[n]
    d = ImageDraw.Draw(im)
    text_c(d, f"Let's write  {n}", 470, 120, 104, (255, 255, 255), stroke=col, sw=10, maxw=780)
    draw_guide(d, n, ease((lt - T_GUIDE) / 0.5))
    sched = SCHED[n]; pen = None; moving = False
    for j, (s, L, a, b) in enumerate(sched):
        if lt < a and lt > T_GUIDE + 0.4:
            p = s[0]; pr = 20 + 6 * math.sin(t * 8)
            d.ellipse([p[0] - pr - 8, p[1] - pr - 8, p[0] + pr + 8, p[1] + pr + 8], fill=(120, 220, 130, 110))
            d.ellipse([p[0] - 20, p[1] - 20, p[0] + 20, p[1] + 20], fill=(70, 190, 100), outline=(255, 255, 255), width=5)
    parts = []
    for j, (s, L, a, b) in enumerate(sched):
        if lt < a:
            if pen is None and j > 0: pen = sched[j - 1][0][-1]
            continue
        u = ease((lt - a) / (b - a)) if lt < b else 1
        parts.append(partial(s, L * u))
        if a <= lt < b: pen = parts[-1][-1]; moving = True
    for p in parts: thick(d, p, (250, 220, 235), 76)
    for p in parts: thick(d, p, col, 54)
    if pen is None: pen = sched[-1][0][-1] if lt >= T_DONE else sched[0][0][0]
    if lt < T_TR0:
        u = ease((lt - 0.1) / 0.7); sx, sy = 470, 1080
        cx, cy = sx + (pen[0] - sx) * u, sy + (pen[1] - sy) * u
    elif lt < T_DONE + 0.2:
        cx, cy = pen
    else:
        u = ease((lt - T_DONE - 0.2) / 0.8)
        cx, cy = pen[0] + (1000 - pen[0]) * u, pen[1] + (1060 - pen[1]) * u
    if lt < T_DONE + 1.0:
        step = int(t * 10) % 2 if (moving or lt < T_TR0 or lt > T_DONE + 0.2) else 0
        paste(im, BUG[step], cx, cy - 40, 0.7, math.sin(t * 12) * 7 if moving else 0)
    d = ImageDraw.Draw(im)
    if lt >= T_DONE:
        k = lt - T_DONE
        for m in range(10):
            ang = m * 2 * math.pi / 10 + t
            rr = 120 + k * 180
            if rr < 400: sparkle(d, BX + BW / 2 + math.cos(ang) * rr, BY + BH / 2 + math.sin(ang) * rr * 1.1, 16, 1 - rr / 400)
    for k in range(n):
        st = T_SH + k * SGAP
        if lt >= st:
            x, y = flower_pos(k)
            grow = ease((lt - st) / 0.3)
            d.line([x, 1250 - 0, x, 1250 - (1250 - y) * grow], fill=(80, 160, 90), width=8)
            paste(im, DAISIES[k % 5], x, y, 0.95 * pop((lt - st) / 0.45), math.sin(t * 2 + k) * 6)
            d = ImageDraw.Draw(im)
            if lt - st > 0.2:
                f = font(46); c = str(k + 1); cw = d.textlength(c, font=f)
                d.text((x - cw / 2, y - 30), c, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=INK)

def draw_outro(im, lt, t):
    d = ImageDraw.Draw(im)
    if lt > 0.3: text_c(d, "Great writing!", 470, 120, 104, (255, 255, 255), stroke=(170, 110, 200), sw=10, maxw=780)
    for i, n in enumerate(NUMS):
        st = 0.4 + i * 0.3
        if lt < st: continue
        s = pop((lt - st) / 0.5) * 0.3
        cx = 170 + i * 150; cy = 820 - abs(math.sin(t * 3 + i)) * 26
        box = (cx - BW * s / 2, cy - BH * s / 2, BW * s, BH * s)
        for sp in DIGITS[n]: thick(d, to_px(sp, box), (250, 220, 235), max(4, int(76 * s)))
        for sp in DIGITS[n]: thick(d, to_px(sp, box), COLS[n], max(3, int(54 * s)))
    mo = talking(t) and int(t * 8) % 2 == 0
    paste(im, TWK_BIG[mo], 470, 530 + math.sin(t * 3) * 10 - abs(math.sin(t * 4)) * 14, pop(lt / 0.8), math.sin(t * 3) * 7)
    for k in range(10):
        st = 0.8 + k * 0.12
        if lt >= st:
            x, y = flower_pos(k)
            paste(im, DAISIES[k % 5], x, y, 0.95 * pop((lt - st) / 0.45), math.sin(t * 3 + k) * 10)
    d = ImageDraw.Draw(im)
    if lt > 2.0:
        for k in range(12):
            ang = k * math.pi / 6 + t * 0.8
            sparkle(d, 470 + math.cos(ang) * 330, 650 + math.sin(ang) * 300, 14 + 6 * math.sin(t * 5 + k), 0.9)

def render_frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    draw_butterfly(d, t)
    if t < INTRO:
        if t > 0.6: text_c(d, "Write 6 to 10", 470, 120, 110, (255, 255, 255), stroke=(170, 110, 200), sw=10, maxw=800)
        mo = talking(t) and int(t * 8) % 2 == 0
        paste(im, TWK_BIG[mo], 470, 560 + math.sin(t * 3) * 14, pop(t / 0.8), math.sin(t * 2) * 6)
        d = ImageDraw.Draw(im)
        for i, n in enumerate(NUMS):
            if t > 1.6 + i * 0.3:
                f = font(100 * pop((t - 1.6 - i * 0.3) / 0.5)); c = str(n); cw = d.textlength(c, font=f)
                x = 170 + i * 150
                d.text((x - cw / 2, 790 - abs(math.sin(t * 3 + i)) * 20), c, font=f, fill=COLS[n], stroke_width=8, stroke_fill=(255, 255, 255))
        paste(im, BUG[int(t * 10) % 2], -100 + min(1, max(0, (t - 2.0) / 1.8)) * 1000, 1150, 0.7, 90 * 0 - 90)
    elif t >= T_OUT:
        draw_outro(im, t - T_OUT, t)
    else:
        i = min(4, int((t - INTRO) // RD)); draw_round(im, i, t - R[i], t)
    d = ImageDraw.Draw(im)
    draw_caption(im, d, t)
    if t < 0.4 or t > TOTAL - 0.6:
        k = min(t / 0.4, (TOTAL - t) / 0.6)
        im = Image.blend(Image.new("RGBA", (W, H), (240, 225, 250, 255)), im, max(0, min(1, k)))
    return im

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

    # ---------- audio: original music-box waltz in G + bird chirps ----------
    N = int(TOTAL * SR); audio = np.zeros(N); rng = np.random.default_rng(10)
    def mbox(freq, dur, vol=0.1, decay=3.5):
        tt = np.arange(int(dur * SR)) / SR
        sig = np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 3.01 * tt) * np.exp(-9 * tt)
        return vol * sig * np.exp(-decay * tt) * np.minimum(1, tt * 500)
    def soft(freq, dur, vol=0.06):
        tt = np.arange(int(dur * SR)) / SR
        env = np.minimum(1, tt / 0.15) * np.minimum(1, (dur - tt) / 0.4)
        return vol * (np.sin(2 * np.pi * freq * tt) + 0.2 * np.sin(4 * np.pi * freq * tt)) * env
    def chirp(at):
        tt = np.arange(int(0.12 * SR)) / SR
        f = 2600 + 1400 * tt / 0.12
        sig = 0.03 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / 0.12)
        add(sig, at); add(sig, at + 0.16)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N: audio[i:j] += sig[:j - i]
    NT = {"G2": 98.0, "C3": 130.81, "D3": 146.83, "E3": 164.81, "G3": 196.0, "B3": 246.94, "C4": 261.63,
          "D4": 293.66, "E4": 329.63, "F#4": 369.99, "G4": 392.0, "A4": 440.0, "B4": 493.88, "D5": 587.33, "E5": 659.25}
    prog = [("G2", ["G3", "B3", "D4"]), ("E3", ["E4", "G4", "B3"]), ("C3", ["C4", "E4", "G4"]), ("D3", ["D4", "F#4", "A4"])]
    mel = ["B4", "D5", "B4", "G4", "A4", "B4", "E5", "D5", "B4", "C4", "E4", "G4", "A4", "F#4", "D4", "G4", None, None]
    beat = 0.42; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 3) % 4; root, ch = prog[bar]
        if k % 3 == 0: add(soft(NT[root], beat * 3, 0.07), k * beat)
        else: add(mbox(NT[ch[k % 3]], 0.8, 0.04, 5), k * beat)
        m = mel[k % 18]
        if m and (k // 36) % 2 == 0: add(mbox(NT[m], 1.4, 0.09), k * beat)
        k += 1
    for tc in np.arange(2.0, TOTAL - 2, 5.3): chirp(tc + rng.uniform(0, 1))
    for i, n in enumerate(NUMS):
        for (s, L, a, b) in SCHED[n]: add(mbox(783.99, 0.4, 0.05, 8), R[i] + a)
        for j, f in enumerate([587.33, 783.99, 987.77, 1174.66]): add(mbox(f, 0.9, 0.06, 4), R[i] + T_DONE + j * 0.08)
        sc = [392.0, 440.0, 493.88, 523.25, 587.33, 659.25, 739.99, 783.99, 880.0, 987.77]
        for k2 in range(n): add(mbox(sc[k2], 0.4, 0.09, 7), R[i] + T_SH + k2 * SGAP)
    for j, f in enumerate([392.0, 493.88, 587.33, 783.99, 987.77]): add(mbox(f, 1.2, 0.08, 3), T_OUT + 0.4 + j * 0.3)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
