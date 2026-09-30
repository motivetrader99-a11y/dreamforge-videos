"""Petal Valley (Anime Adventures): Sharing the last dumpling — lesson: sharing.
Original characters, art and music. Renders kids/sharing_last_dumpling.mp4 (captions + music, no voice).
Character designs match make_lost_baby_star.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/sharing_last_dumpling.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(88)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "It was picnic time in Petal Valley, under the pink blossom tree."),
    ("Mochi", "Yum, dumplings! Oh no... there is only one dumpling left."),
    ("Hana", "I want it too! But Mochi wants it. Hmm, what can we do?"),
    ("Professor Owlbert", "When there is only one, we can share it. Let's cut it in half!"),
    ("Hana", "Here you go, Mochi! One half for you, and one half for me."),
    ("Mochi", "Thank you, Hana! Sharing makes it taste even better!"),
    ("Narrator", "Everyone was happy. When we share, we all smile!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.4, 4.6
LINES, t = [], INTRO
for spk, txt in SCRIPT:
    words = len(txt.split())
    talk = words * 0.34 + 0.4
    dur = max(5.0, talk + 1.5)
    LINES.append((spk, txt, t, dur, talk)); t += dur
T_OUTRO = t
TOTAL = t + OUTRO
NFR = int(TOTAL * FPS)
print("total", round(TOTAL, 1))

def line_at(tt):
    for i, (spk, txt, st, dur, talk) in enumerate(LINES):
        if st <= tt < st + dur: return i, tt - st
    return None, 0

# ---------- drawing helper (2x supersampled) ----------
S = 2
class P:
    def __init__(s, w, h):
        s.w, s.h = w, h
        s.im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
    def _b(s, b): return [v * S for v in b]
    def ell(s, x0, y0, x1, y1, fill=None, outline=None, width=0):
        s.d.ellipse(s._b([x0, y0, x1, y1]), fill=fill, outline=outline, width=int(width * S))
    def circ(s, cx, cy, r, fill=None, outline=None, width=0): s.ell(cx - r, cy - r, cx + r, cy + r, fill, outline, width)
    def poly(s, pts, fill=None, outline=None, width=0):
        s.d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=outline, width=int(width * S))
    def line(s, pts, fill, width):
        s.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")
        for x, y in (pts[0], pts[-1]): s.circ(x, y, width / 2, fill)
    def arc(s, x0, y0, x1, y1, a0, a1, fill, width):
        s.d.arc(s._b([x0, y0, x1, y1]), a0, a1, fill=fill, width=int(width * S))
    def chord(s, x0, y0, x1, y1, a0, a1, fill):
        s.d.chord(s._b([x0, y0, x1, y1]), a0, a1, fill=fill)
    def rrect(s, x0, y0, x1, y1, r, fill=None, outline=None, width=0):
        s.d.rounded_rectangle(s._b([x0, y0, x1, y1]), radius=r * S, fill=fill, outline=outline, width=int(width * S))
    def done(s): return s.im.resize((s.w, s.h), Image.LANCZOS)

WHITE = (255, 255, 255)
def eye(p, cx, cy, w, h, iris, blink=False, happy=False):
    if blink or happy:
        p.arc(cx - w / 2, cy - h * 0.25, cx + w / 2, cy + h * 0.35, 200 if happy else 20, 340 if happy else 160, (60, 40, 75), 5)
        return
    p.ell(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, (55, 40, 75))
    p.ell(cx - w * 0.38, cy - h * 0.18, cx + w * 0.38, cy + h * 0.44, iris)
    lt = tuple(min(255, c + 60) for c in iris)
    p.ell(cx - w * 0.25, cy + h * 0.18, cx + w * 0.25, cy + h * 0.42, lt)
    p.ell(cx - w * 0.18, cy - h * 0.04, cx + w * 0.18, cy + h * 0.26, (40, 28, 60))
    p.ell(cx - w * 0.40, cy - h * 0.40, cx + w * 0.02, cy - h * 0.02, WHITE)
    p.ell(cx + w * 0.08, cy + h * 0.16, cx + w * 0.28, cy + h * 0.34, WHITE)

def mouth(p, cx, cy, w, open_, sad=False):
    if open_:
        p.ell(cx - w * 0.45, cy - w * 0.15, cx + w * 0.45, cy + w * 0.55, (170, 60, 90))
        p.ell(cx - w * 0.28, cy + w * 0.2, cx + w * 0.28, cy + w * 0.52, (255, 140, 160))
    elif sad:
        p.arc(cx - w / 2, cy, cx + w / 2, cy + w * 0.7, 200, 340, (120, 60, 90), 5)
    else:
        p.arc(cx - w / 2, cy - w * 0.35, cx + w / 2, cy + w * 0.35, 20, 160, (120, 60, 90), 5)

# ---------- Hana ----------
SKIN = (255, 226, 205); HAIR = (255, 155, 195); HAIR_D = (235, 120, 170)
@lru_cache(None)
def hana(mo, arms_up, blink):
    p = P(420, 620)
    # legs + shoes
    for x in (175, 225):
        p.rrect(x, 520, x + 24, 598, 10, SKIN, LINE, 3)
        p.ell(x - 10, 585, x + 34, 612, (180, 140, 230), LINE, 3)
    # arms
    for sgn in (-1, 1):
        sx = 210 + sgn * 52
        if arms_up: hx, hy = 210 + sgn * 120, 330
        else: hx, hy = 210 + sgn * 88, 505
        p.line([(sx, 425), (hx, hy)], LINE, 24); p.line([(sx, 425), (hx, hy)], SKIN, 18)
        p.circ(hx, hy, 17, SKIN, LINE, 3)
    # dress
    p.poly([(158, 405), (262, 405), (312, 545), (108, 545)], (195, 225, 255), LINE, 4)
    p.poly([(116, 525), (304, 525), (312, 545), (108, 545)], (170, 205, 250))
    for x in (160, 210, 260): p.circ(x, 485, 9, WHITE)
    # hair back + buns
    for bx in (100, 320):
        p.circ(bx, 140, 58, HAIR, LINE, 4); p.circ(bx - 12, 128, 16, (255, 200, 225))
    p.ell(80, 108, 340, 380, HAIR, LINE, 4)
    # face
    p.ell(105, 160, 315, 382, SKIN, LINE, 4)
    # bangs
    for bx0, by0 in ((96, 128), (160, 116), (224, 128)):
        p.ell(bx0, by0, bx0 + 100, by0 + 104, HAIR)
    p.arc(98, 170, 190, 250, 20, 150, HAIR_D, 4); p.arc(230, 170, 322, 250, 30, 160, HAIR_D, 4)
    p.ell(150, 132, 200, 150, (255, 205, 225))
    # eyes, blush, mouth
    eye(p, 163, 272, 54, 70, (150, 95, 200), blink)
    eye(p, 257, 272, 54, 70, (150, 95, 200), blink)
    for bx in (140, 280): p.ell(bx - 20, 318, bx + 20, 334, (255, 160, 180))
    mouth(p, 210, 338, 34, mo)
    # scarf
    p.rrect(140, 372, 280, 408, 18, (255, 212, 70), LINE, 4)
    p.poly([(245, 395), (285, 395), (292, 470), (262, 462)], (255, 212, 70), LINE, 4)
    p.line([(250, 420), (284, 424)], (240, 180, 40), 4)
    return p.done()

# ---------- Mochi (round cloud dragon) ----------
MB = (150, 210, 255); MB_L = (215, 238, 255); ML = (90, 140, 200)
@lru_cache(None)
def mochi(mo, wing, expr, blink):
    """wing in [-1,1] (down..up); expr: happy/sad/wow"""
    p = P(340, 320)
    cx, cy = 170, 175
    # tail
    p.line([(80, 230), (45, 215), (35, 185), (55, 172)], ML, 22); p.line([(80, 230), (45, 215), (35, 185), (55, 172)], MB, 16)
    # wings
    for sgn in (-1, 1):
        bx = cx + sgn * 88; by = cy - 10
        a = math.radians(-20 - wing * 40)
        tipx = bx + sgn * 78 * math.cos(a); tipy = by + 78 * math.sin(a)
        midx = bx + sgn * 60 * math.cos(a + 0.55); midy = by + 60 * math.sin(a + 0.55)
        p.poly([(bx, by - 18), (tipx, tipy), (midx, midy), (bx, by + 22)], (235, 248, 255), ML, 4)
    # horns
    for sgn in (-1, 1):
        hx = cx + sgn * 38
        p.poly([(hx - 14, 92), (hx + sgn * 8, 40), (hx + 14, 92)], (255, 240, 200), ML, 4)
    # cloud body: outline pass then fill pass
    puffs = [(cx, cy, 92), (cx - 62, cy - 42, 42), (cx, cy - 72, 46), (cx + 62, cy - 42, 42),
             (cx - 84, cy + 20, 36), (cx + 84, cy + 20, 36)]
    for x, y, r in puffs: p.circ(x, y, r + 4, ML)
    for x, y, r in puffs: p.circ(x, y, r, MB)
    p.ell(cx - 58, cy + 5, cx + 58, cy + 88, MB_L)
    p.circ(cx - 30, cy - 90, 12, (235, 248, 255))
    # face
    ey = cy - 12
    eye(p, cx - 36, ey, 46, 58, (70, 110, 210), blink, happy=(expr == "joy"))
    eye(p, cx + 36, ey, 46, 58, (70, 110, 210), blink, happy=(expr == "joy"))
    if expr == "sad":
        p.line([(cx - 56, ey - 34), (cx - 22, ey - 46)], (80, 110, 170), 5)
        p.line([(cx + 56, ey - 34), (cx + 22, ey - 46)], (80, 110, 170), 5)
    for bx in (cx - 66, cx + 66): p.ell(bx - 16, ey + 24, bx + 16, ey + 38, (255, 170, 200))
    mouth(p, cx, ey + 38, 28, mo, sad=(expr == "sad"))
    return p.done()

# ---------- Professor Owlbert ----------
OW = (200, 160, 125); OW_D = (160, 120, 90); OW_L = (248, 232, 205)
@lru_cache(None)
def owl(mo, wing, blink):
    p = P(260, 330)
    cx = 130
    # feet
    for x in (100, 160): p.ell(x - 18, 305, x + 18, 325, (255, 175, 90), LINE, 3)
    # wings (behind body edge)
    for sgn in (-1, 1):
        a = wing * 0.9
        bx, by = cx + sgn * 88, 185
        tipx = bx + sgn * (30 + 60 * a); tipy = by + 110 - 150 * a
        p.poly([(bx - sgn * 6, by - 40), (bx + sgn * 26, by - 10), (tipx, tipy), (bx - sgn * 10, by + 70)], OW_D, LINE, 4)
    # ear tufts
    for sgn in (-1, 1):
        p.poly([(cx + sgn * 45, 70), (cx + sgn * 88, 22), (cx + sgn * 85, 90)], OW_D, LINE, 4)
    # body
    p.ell(cx - 100, 45, cx + 100, 318, OW, LINE, 4)
    p.ell(cx - 62, 170, cx + 62, 305, OW_L)
    for row, y in enumerate((200, 232, 264)):
        for k in range(-1 if row % 2 else -2, 2 if row % 2 else 3):
            x = cx + k * 26 + (13 if row % 2 else 0) - (13 if row % 2 else 0)
            p.arc(x - 12, y - 8, x + 12, y + 12, 20, 160, (215, 185, 150), 3)
    # face discs + fluffy white brows
    for sgn in (-1, 1): p.circ(cx + sgn * 42, 125, 44, OW_L)
    # eyes + round glasses
    for sgn in (-1, 1):
        eye(p, cx + sgn * 42, 125, 40, 48, (220, 150, 60), blink)
        p.circ(cx + sgn * 42, 125, 36, None, (120, 85, 60), 6)
    p.line([(cx - 8, 118), (cx + 8, 118)], (120, 85, 60), 6)
    for sgn in (-1, 1): p.line([(cx + sgn * 20, 76), (cx + sgn * 62, 70)], WHITE, 10)
    # beak
    if mo:
        p.poly([(cx - 14, 158), (cx + 14, 158), (cx, 172)], (255, 170, 80), LINE, 3)
        p.ell(cx - 11, 172, cx + 11, 188, (170, 60, 90))
        p.poly([(cx - 11, 186), (cx + 11, 186), (cx, 198)], (255, 170, 80), LINE, 3)
    else:
        p.poly([(cx - 14, 158), (cx + 14, 158), (cx, 186)], (255, 170, 80), LINE, 3)
    # mint bow tie
    p.poly([(cx, 212), (cx - 30, 198), (cx - 30, 226)], (150, 225, 200), LINE, 3)
    p.poly([(cx, 212), (cx + 30, 198), (cx + 30, 226)], (150, 225, 200), LINE, 3)
    p.circ(cx, 212, 8, (120, 200, 175), LINE, 2)
    return p.done()
@lru_cache(None)
def glow(radius, col, strength):
    g = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    yy, xx = np.mgrid[0:radius * 2, 0:radius * 2]
    d = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2 * 255 * strength
    arr = np.zeros((radius * 2, radius * 2, 4), np.uint8); arr[..., :3] = col; arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr)

def put_glow(im, x, y, radius, col, strength):
    g = glow(int(radius), col, round(strength, 2)); im.alpha_composite(g, (int(x - radius), int(y - radius)))
def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, 3))
    for c in range(3): arr[:, c] = np.interp(ys, [s for s, _ in stops], [col[c] for _, col in stops])
    return Image.fromarray(np.repeat(arr.astype(np.uint8)[:, None, :], w, axis=1))
SHADOW = Image.new("RGBA", (240, 50), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).ellipse([0, 0, 239, 49], fill=(60, 70, 110, 80))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(5))

def paste(canvas, sp, cx, bottom, sx=1.0, sy=1.0):
    if sx != 1 or sy != 1:
        sp = sp.resize((max(2, int(sp.width * sx)), max(2, int(sp.height * sy))), Image.BILINEAR)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(bottom - sp.height)))

def paste_c(canvas, sp, cx, cy):
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def shadow(canvas, cx, y, s):
    sp = SHADOW.resize((max(2, int(240 * s)), max(2, int(50 * s))))
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(y - sp.height / 2)))

def wrap(d, txt, sz, maxw):
    f = font(sz); out, cur = [], ""
    for w in txt.split():
        tr = (cur + " " + w).strip()
        if d.textlength(tr, font=f) <= maxw: cur = tr
        else: out.append(cur); cur = w
    out.append(cur); return out

BX0, BX1, BY0 = 60, 920, 150
def bubble(im, name, col, txt, sz, pop=1.0, sub=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    lines = wrap(d, txt, sz, BX1 - BX0 - 90)
    lh = sz * 1.22
    sublines = wrap(d, sub, 50, BX1 - BX0 - 90) if sub else []
    hgt = 70 + len(lines) * lh + len(sublines) * 64 + 40
    d.rounded_rectangle([BX0, BY0, BX1, BY0 + hgt], radius=44, fill=(255, 255, 255, 240), outline=col, width=7)
    cxm = (BX0 + BX1) / 2
    y = BY0 + 50
    for ln in lines:
        w = d.textlength(ln, font=font(sz)); d.text((cxm - w / 2, y), ln, font=font(sz), fill=INK); y += lh
    for ln in sublines:
        w = d.textlength(ln, font=font(50)); d.text((cxm - w / 2, y + 6), ln, font=font(50), fill=(150, 120, 200)); y += 64
    if name:
        f = font(42); nw = d.textlength(name, font=f)
        d.rounded_rectangle([BX0 + 40, BY0 - 34, BX0 + 40 + nw + 50, BY0 + 30], radius=32, fill=col)
        d.text((BX0 + 65, BY0 - 32), name, font=f, fill=WHITE)
    if pop < 1:
        s = 0.7 + 0.3 * pop
        lay = lay.resize((int(W * s), int(H * s)), Image.BILINEAR)
        cxp, cyp = (BX0 + BX1) / 2, BY0 + hgt / 2
        big = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        big.alpha_composite(lay, (int(cxp - cxp * s), int(cyp - cyp * s)))
        a = np.array(big); a[:, :, 3] = (a[:, :, 3] * pop).astype(np.uint8); lay = Image.fromarray(a)
    im.alpha_composite(lay)

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def blinking(t, off): return ((t + off) % 3.7) < 0.13

# ================= picnic scene (new for this episode) =================
DOUGH = (255, 250, 240); DOUGH_S = (235, 222, 205); DOUGH_L = (175, 150, 135)

@lru_cache(None)
def dumpling(r, happy):
    """a round steamed dumpling with pleats and a tiny sleepy face"""
    p = P(int(r * 2.6), int(r * 2.3)); c = r * 1.3; cy = r * 1.3
    p.ell(c - r, cy - r * 0.78, c + r, cy + r * 0.72, DOUGH, DOUGH_L, max(2, r / 16))
    p.ell(c - r * 0.8, cy + r * 0.2, c + r * 0.8, cy + r * 0.68, DOUGH_S)
    for k in range(-2, 3):
        x = c + k * r * 0.2
        p.arc(x - r * 0.5, cy - r * 0.95, x + r * 0.5, cy - r * 0.15, 250 + k * 10, 290 + k * 10, DOUGH_L, max(2, r / 20))
    p.circ(c, cy - r * 0.72, r * 0.12, DOUGH, DOUGH_L, max(2, r / 20))
    ey = cy + r * 0.05
    for sgn in (-1, 1):
        if happy: p.arc(c + sgn * r * 0.3 - r * 0.1, ey - r * 0.06, c + sgn * r * 0.3 + r * 0.1, ey + r * 0.12, 200, 340, (90, 65, 80), max(2, r / 22))
        else: p.circ(c + sgn * r * 0.3, ey, r * 0.07, (90, 65, 80))
        p.ell(c + sgn * r * 0.48 - r * 0.1, ey + r * 0.1, c + sgn * r * 0.48 + r * 0.1, ey + r * 0.2, (255, 185, 190))
    p.arc(c - r * 0.1, ey + r * 0.05, c + r * 0.1, ey + r * 0.22, 20, 160, (90, 65, 80), max(2, r / 22))
    return p.done()

@lru_cache(None)
def half_dumpling(r, side):
    """side -1 = left half, 1 = right half (cut face shows sweet red-bean filling)"""
    full = dumpling(r, True)
    w, h = full.size
    a = np.array(full)
    if side < 0: a[:, w // 2:, 3] = 0
    else: a[:, :w // 2, 3] = 0
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im); c = w // 2; cy = r * 1.3
    x0 = c - r * 0.14 if side < 0 else c
    d.rounded_rectangle([x0, cy - r * 0.62, x0 + r * 0.14, cy + r * 0.6], radius=int(r * 0.07), fill=(250, 238, 222))
    d.ellipse([c - r * 0.1, cy - r * 0.3, c + r * 0.1, cy + r * 0.3], fill=(170, 95, 105))
    return im

@lru_cache(None)
def plate():
    p = P(360, 130)
    p.ell(10, 20, 350, 120, (215, 235, 250), LINE, 4)
    p.ell(50, 36, 310, 100, (240, 250, 255))
    p.arc(50, 36, 310, 100, 20, 160, (190, 215, 235), 4)
    return p.done()

@lru_cache(None)
def basket():
    p = P(230, 200)
    p.arc(40, 10, 190, 150, 180, 360, (190, 140, 100), 12)
    p.rrect(18, 80, 212, 190, 26, (225, 180, 130), LINE, 4)
    for y in (110, 140, 168): p.line([(30, y), (200, y)], (200, 150, 105), 4)
    for x in (70, 115, 160): p.line([(x, 88), (x, 184)], (200, 150, 105), 4)
    p.rrect(18, 78, 212, 104, 12, (255, 190, 205), LINE, 3)
    return p.done()

@lru_cache(None)
def teacup():
    p = P(110, 90)
    p.arc(62, 22, 104, 64, 270, 90, LINE, 7)
    p.ell(10, 10, 80, 30, (255, 230, 200), LINE, 3)
    p.chord(8, -22, 82, 82, 0, 180, (160, 220, 200)); p.arc(8, -22, 82, 82, 0, 180, LINE, 3)
    p.ell(14, 12, 76, 28, (210, 170, 120))
    return p.done()

def make_bg():
    bg = vgrad(W, H, [(0, (170, 215, 250)), (0.4, (210, 232, 250)), (0.62, (255, 236, 240)), (1, (255, 236, 240))]).convert("RGBA")
    t = P(W, H)
    # soft sun + clouds (mid sky, below caption area)
    t.circ(860, 720, 70, (255, 244, 190))
    for cx, cy, s in ((240, 640, 1.0), (640, 800, 0.8)):
        for dx, dy, r in ((-60, 10, 40), (0, -10, 55), (60, 10, 42), (0, 20, 45)):
            t.circ(cx + dx * s, cy + dy * s, r * s, (255, 255, 255))
    bg.alpha_composite(t.done())
    d = ImageDraw.Draw(bg)
    # rolling hills
    d.ellipse([-450, 1060, 700, 1560], fill=(195, 230, 190)); d.ellipse([350, 1020, 1550, 1560], fill=(180, 222, 185))
    # little windmill-cottage far away
    d.rectangle([860, 1060, 905, 1110], fill=(255, 240, 225)); d.polygon([(850, 1062), (882, 1030), (915, 1062)], fill=(240, 160, 180))
    d.rectangle([876, 1080, 890, 1096], fill=(180, 210, 240))
    # meadow
    d.ellipse([-600, 1200, 1700, 2300], fill=(170, 220, 170)); d.rectangle([0, 1480, W, H], fill=(170, 220, 170))
    d.ellipse([-300, 1420, 1400, 2600], fill=(160, 212, 165))
    rnd = random.Random(21)
    for _ in range(90):
        x, y = rnd.randint(10, W - 10), rnd.randint(1260, 1900)
        c = rnd.choice([(255, 255, 255), (255, 210, 225), (255, 240, 170), (220, 205, 255)])
        r = 3 + (y - 1260) / 110
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + math.cos(a) * r - r * 0.55, y + math.sin(a) * r - r * 0.55, x + math.cos(a) * r + r * 0.55, y + math.sin(a) * r + r * 0.55], fill=c)
        d.ellipse([x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4], fill=(255, 205, 110))
    # blossom tree (left) — trunk + big pink canopy
    t = P(W, H)
    t.poly([(95, 1300), (120, 1000), (100, 880), (150, 900), (170, 1000), (210, 860), (245, 880), (205, 1020), (215, 1300)], (190, 140, 120), LINE, 4)
    for cx, cy, r in ((40, 820, 120), (170, 760, 140), (300, 830, 110), (90, 930, 100), (250, 930, 95)):
        t.circ(cx, cy, r + 5, (225, 150, 185))
    for cx, cy, r in ((40, 820, 120), (170, 760, 140), (300, 830, 110), (90, 930, 100), (250, 930, 95)):
        t.circ(cx, cy, r, (255, 195, 220))
    for cx, cy, r in ((150, 720, 60), (280, 800, 45), (30, 790, 50)):
        t.circ(cx, cy, r, (255, 220, 235))
    # tree stump for Owlbert (right)
    t.rrect(700, 1250, 880, 1350, 20, (200, 155, 125), LINE, 4)
    t.ell(700, 1232, 880, 1272, (240, 215, 180), LINE, 4)
    t.ell(740, 1242, 840, 1262, (225, 195, 160))
    # picnic blanket (checkered, perspective)
    bg.alpha_composite(t.done())
    bl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bl)
    TL, TR, BL_, BR = (250, 1380), (830, 1380), (130, 1560), (950, 1560)
    n = 8
    for i in range(n):
        for j in range(3):
            def pt(u, v):
                x0 = TL[0] + (BL_[0] - TL[0]) * v; x1 = TR[0] + (BR[0] - TR[0]) * v
                return (x0 + (x1 - x0) * u, TL[1] + (BL_[1] - TL[1]) * v)
            q = [pt(i / n, j / 3), pt((i + 1) / n, j / 3), pt((i + 1) / n, (j + 1) / 3), pt(i / n, (j + 1) / 3)]
            bd.polygon(q, fill=(255, 175, 190) if (i + j) % 2 == 0 else (255, 250, 245))
    bd.line([TL, TR, BR, BL_, TL], fill=LINE, width=5)
    bg.alpha_composite(bl)
    bg.alpha_composite(basket(), (745, 1330))
    return bg

BG = make_bg()
PETALS = [(random.uniform(0, 930), random.uniform(0, 1), random.uniform(0.5, 1.2), random.uniform(0, 6), random.uniform(7, 12)) for _ in range(22)]
BUTTERFLY = (random.uniform(0, 6),)

def petal(d, x, y, r, a):
    pts = []
    for k in range(12):
        th = k * math.pi / 6
        rx, ry = r * math.cos(th), r * 0.55 * math.sin(th)
        pts.append((x + rx * math.cos(a) - ry * math.sin(a), y + rx * math.sin(a) + ry * math.cos(a)))
    d.polygon(pts, fill=(255, 180, 210, 220))

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)

def blinking(t, off): return ((t + off) % 3.9) < 0.13

HX, HB = 250, 1480        # Hana
MX, MB0 = 745, 1470       # Mochi (bottom of sprite)
OX, OB = 790, 1262        # Owlbert on stump
PX, PY = 505, 1478        # plate centre
DR = 80                   # dumpling radius
L = [ln[2] for ln in LINES]

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

PREVIEW = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x]
FRAMES = [int(x * FPS) for x in PREVIEW] if PREVIEW else range(NFR)
proc = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in FRAMES:
    t = fi / FPS
    i, lt = line_at(t)
    ph = 7 if t >= T_OUTRO else (-1 if i is None else i)
    im = BG.copy(); d = ImageDraw.Draw(im)
    # falling blossom petals (behind characters)
    for x0, y0, sp, off, r in PETALS:
        y = 560 + ((y0 * 1000 + t * 60 * sp) % 1000)
        x = x0 + math.sin(t * sp + off) * 40
        petal(d, x, y, r, t * sp + off)
    # butterfly flutter near tree
    bx = 330 + math.sin(t * 0.7 + BUTTERFLY[0]) * 120; by = 1120 + math.sin(t * 1.3) * 60
    fl = abs(math.sin(t * 12)) * 0.8 + 0.2
    for sgn in (-1, 1):
        d.ellipse([bx + sgn * 4 - (sgn < 0) * 26 * fl, by - 22, bx + sgn * 4 + (sgn > 0) * 26 * fl, by + 4], fill=(200, 170, 255))
        d.ellipse([bx + sgn * 4 - (sgn < 0) * 18 * fl, by, bx + sgn * 4 + (sgn > 0) * 18 * fl, by + 18], fill=(255, 200, 230))
    d.line([(bx, by - 18), (bx, by + 14)], fill=LINE, width=4)

    # ---- Owlbert on the stump ----
    om, ob = talking("Professor Owlbert", t)
    owing = 0.0
    if ph == 3 and 3.2 < lt < 5.0: owing = (math.sin(t * 9) + 1) / 2   # "cut it in half" wave
    if ph >= 6: owing = (math.sin(t * 5) + 1) / 2 * 0.5
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob)

    # ---- Hana ----
    hm, hb = talking("Hana", t)
    arms = ph >= 6 or (ph == 2 and 3.0 < lt < 4.4)
    hop = abs(math.sin(t * 6)) * 12 if ph >= 6 else 0
    hbot = HB - hb - hop
    shadow(im, HX, HB - 4, 0.8)
    paste(im, hana(hm, arms, blinking(t, 0.0)), HX, hbot)

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    wing = math.sin(t * 5) * 0.4; expr = "happy"
    mbot = MB0 - abs(math.sin(t * 3)) * 8
    if ph == 1 and lt > 2.2: expr = "sad"
    if ph == 2: expr = "sad"
    if ph == 3 and lt > 3.5: expr = "happy"
    if ph == 4 and lt > 3.2: expr = "joy"
    if ph == 5: expr = "joy"; wing = math.sin(t * 10) * 0.8; mbot -= abs(math.sin(t * 5)) * 16
    if ph >= 6: expr = "joy"; wing = math.sin(t * 9); mbot = MB0 - 30 - abs(math.sin(t * 4)) * 22
    shadow(im, MX, MB0 - 6, 0.8)
    paste(im, mochi(mm, round(wing * 4) / 4, expr, blinking(t, 2.3) and expr != "joy"), MX, mbot + 50 - mb)

    # ---- plate + dumpling(s) ----
    paste_c(im, plate(), PX, PY)
    d = ImageDraw.Draw(im)
    hand_h = (HX + 88, hbot - 620 + 505)
    mochi_mouth = (MX, mbot + 50 - mb - 320 + 175 + 26)
    if ph <= 0:
        # intro + line 0: three dumplings on the plate (steam wisps)
        n_left = 3
        if ph == 0 and lt > 2.5: n_left = 2
        if ph == 0 and lt > 3.8: n_left = 1
        spots = [(PX - 120, PY - 34), (PX + 120, PY - 34), (PX, PY - 50)]
        for k in range(3 - n_left, 3):
            paste_c(im, dumpling(DR if k == 2 else 66, False), *spots[k])
        for k in range(3):
            sx = PX - 50 + k * 50; sy = PY - 120 - ((t * 40 + k * 30) % 70)
            a = int(150 * (1 - ((t * 40 + k * 30) % 70) / 70))
            d.arc([sx - 14, sy - 20, sx + 14, sy + 20], 250, 110, fill=(255, 255, 255, a), width=5)
    elif ph in (1, 2) or (ph == 3 and lt < 3.2):
        bob = math.sin(t * 2.5) * 4
        put_glow(im, PX, PY - 40, 110, (255, 245, 200), 0.5)
        paste_c(im, dumpling(DR, False), PX, PY - 44 + bob)
        if ph == 1 and lt < 2.2:   # sparkle "yum"
            for k in range(4):
                a = k * math.pi / 2 + t * 2; rr = 95
                x, y = PX + rr * math.cos(a), PY - 44 + rr * 0.6 * math.sin(a)
                d.polygon([(x, y - 14), (x + 4, y - 4), (x + 14, y), (x + 4, y + 4), (x, y + 14), (x - 4, y + 4), (x - 14, y), (x - 4, y - 4)], fill=(255, 225, 120))
        if ph == 2:  # thinking dots
            for k in range(3):
                a = 0.5 + 0.5 * math.sin(t * 5 - k)
                d.ellipse([PX - 40 + k * 40 - 10, PY - 170 - 10, PX - 40 + k * 40 + 10, PY - 170 + 10], fill=(150, 130, 220, int(120 + 135 * a)))
    else:
        # the dumpling is cut in half and shared
        if ph == 3:
            k = ease((lt - 3.2) / 0.8)
            gap = 38 * k
            lp = (PX - 4 - gap, PY - 44); rp = (PX + 4 + gap, PY - 44)
            if lt < 3.9:
                for q in range(6):  # little "pop" sparkles along the cut
                    y = PY - 90 + q * 18; a = int(255 * (1 - k))
                    d.ellipse([PX - 6, y - 6, PX + 6, y + 6], fill=(255, 235, 150, a))
        elif ph == 4:
            k1 = ease((lt - 1.4) / 1.2); k2 = ease((lt - 2.8) / 1.2)
            lp = (lerp(PX - 42, hand_h[0], k1), lerp(PY - 44, hand_h[1] - 20, k1) - 60 * math.sin(k1 * math.pi))
            rp = (lerp(PX + 42, MX - 70, k2), lerp(PY - 44, mochi_mouth[1] + 40, k2) - 60 * math.sin(k2 * math.pi))
        else:
            lp = (hand_h[0], hand_h[1] - 20)
            rp = (MX - 70, mochi_mouth[1] + 40 + math.sin(t * 5) * 4)
        show_l = not (ph >= 6 and t - L[6] > 1.5) and ph != 7
        show_r = not (ph == 5 and lt > 2.8) and ph < 6
        if show_l: paste_c(im, half_dumpling(DR, -1), lp[0] + DR * 0.3 * 0, lp[1])
        if show_r:
            sc = 1.0 if ph != 5 else max(0.35, 1 - max(0, lt - 1.2) / 1.6 * 0.65)
            sp = half_dumpling(DR, 1)
            if sc < 1: sp = sp.resize((int(sp.width * sc), int(sp.height * sc)), Image.BILINEAR)
            paste_c(im, sp, rp[0], rp[1])
        # hearts float up when sharing happens
        if ph >= 4 and not (ph == 4 and lt < 3.6):
            base_t = L[4] + 3.6
            for k in range(6):
                q = ((t - base_t) * 0.35 + k / 6) % 1
                hx = 470 + (k % 3) * 90 + math.sin(t * 2 + k) * 25
                hy = 1250 - q * 380
                heart(d, hx, hy, 18 + 6 * (k % 2), (255, 130, 170, int(230 * (1 - q))))
    # munch crumbs when Mochi eats
    if ph == 5 and 1.2 < lt < 3.0:
        for k in range(5):
            q = ((lt * 2 + k / 5) % 1)
            d.ellipse([MX - 60 + k * 14 - 5, mochi_mouth[1] + 60 + q * 60 - 5, MX - 60 + k * 14 + 5, mochi_mouth[1] + 60 + q * 60 + 5], fill=(255, 245, 225, int(255 * (1 - q))))

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "Sharing the Last Dumpling", 76, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (240, 130, 170), "Sharing is caring!", 104, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle waltz (3/4) in F major, plucked + soft pad ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "pluck": w = w + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt) + 0.2 * np.sin(2 * np.pi * freq * 3 * tt) * np.exp(-12 * tt)
    if shape == "bell": w = w + 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 4.02 * tt)
    if shape == "pad": w = w + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt); env = np.minimum(1, tt * 2.5) * np.minimum(1, (dur - tt) * 2.5)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at, buf=None):
    buf = audio if buf is None else buf
    i0 = int(at * SR)
    if i0 >= N: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
# melody as MIDI numbers per beat (None = rest); 3 beats per bar
mel = [72, None, 69, 70, 72, 74, 72, None, None, 65, 67, 69,
       70, None, 67, 69, 70, 72, 69, None, None, None, None, None,
       72, None, 77, 76, 74, 72, 74, None, 70, 69, 67, 65,
       67, None, 69, 70, 67, 64, 65, None, None, None, None, None]
bass = [53, 53, 58, 53, 48, 48, 58, 53, 53, 53, 58, 58, 48, 48, 53, 53]
beat = 0.42; music = np.zeros(N); k = 0
while k * beat < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 1.0, 0.06, "pluck", 3.5), k * beat, music)
    bar = k // 3
    if k % 3 == 0:
        add(tone(f(bass[bar % len(bass)] - 12), beat * 3, 0.05, "pad"), k * beat, music)
    else:
        add(tone(f(bass[bar % len(bass)] + 7), 0.4, 0.022, "pluck", 7), k * beat, music)
    k += 1
duck = np.ones(N)
for spk, txt, st, dur, talk in LINES:
    a, b_ = int((st + 0.2) * SR), int((st + 0.4 + talk) * SR); duck[a:b_] = 0.6
duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
audio += music * duck
# soft character "babble" blips so kids hear who is talking
base = {"Hana": 620, "Mochi": 820, "Professor Owlbert": 330}
rnd = random.Random(5)
for spk, txt, st, dur, talk in LINES:
    if spk not in base: continue
    tt = st + 0.3
    while tt < st + 0.3 + talk:
        add(tone(base[spk] * rnd.choice([1, 1.12, 1.25, 0.9]), 0.09, 0.03, "sine", 25), tt); tt += 0.286
# sfx
add(tone(f(77), 0.8, 0.12, "bell", 3), 0.1); add(tone(f(84), 1.0, 0.12, "bell", 3), 0.5)
add(tone(f(72), 0.2, 0.1, "pluck", 12), L[0] + 2.5); add(tone(f(74), 0.2, 0.1, "pluck", 12), L[0] + 3.8)   # nom nom
for j, m in enumerate([84, 81, 77]): add(tone(f(m), 0.6, 0.07, "bell", 5), L[1] + 2.2 + j * 0.18)          # "oh no"
for j, m in enumerate([72, 76, 79]): add(tone(f(m), 0.5, 0.07, "bell", 5), L[2] + 3.4 + j * 0.3)           # thinking
add(tone(f(88), 0.5, 0.12, "bell", 6), L[3] + 3.3); add(tone(f(84), 0.6, 0.1, "bell", 5), L[3] + 3.45)      # cut!
for j, m in enumerate([77, 81, 84, 89]): add(tone(f(m), 0.9, 0.08, "bell", 4), L[4] + 3.6 + j * 0.12)       # shared
for j in range(4): add(tone(f(76 + (j % 2) * 3), 0.15, 0.08, "pluck", 14), L[5] + 1.3 + j * 0.35)           # munch
for j, m in enumerate([77, 81, 84, 89, 93]): add(tone(f(m), 1.4, 0.09, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = audio * fade
pk = np.abs(audio).max(); audio = audio / pk * 0.8 if pk > 0.8 else audio
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
os.remove("_video_v.mp4"); os.remove("_audio_v.wav")
print("done", OUT, round(TOTAL, 1))
