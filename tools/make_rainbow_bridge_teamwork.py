"""Petal Valley (Anime Adventures): The rainbow bridge is broken — lesson: teamwork.
Original characters, art and music. Renders kids/rainbow_bridge_teamwork.mp4 (captions + music, no voice).
Character designs match make_hana_says_sorry.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/rainbow_bridge_teamwork.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(2718)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "In Petal Valley, the rainbow bridge is broken! Three planks fell in the stream."),
    ("Hana", "I will push a plank back up! Hmmm... it's too heavy for me."),
    ("Mochi", "I will lift one! Up, up... oh no, I can't do it alone."),
    ("Professor Owlbert", "Big jobs are easy when we work together. That is teamwork!"),
    ("Hana", "Mochi, you lift and I will push. Ready, set, go!"),
    ("Mochi", "Hooray! We fixed the bridge together!"),
    ("Narrator", "Teamwork makes big jobs easy!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.4, 4.6
LINES, t = [], INTRO
for spk, txt in SCRIPT:
    words = len(txt.split())
    talk = words * 0.34 + 0.4
    dur = max(5.2, talk + 1.6)
    LINES.append((spk, txt, t, dur, talk)); t += dur
T_OUTRO = t
TOTAL = t + OUTRO
NFR = int(TOTAL * FPS)
print("total", round(TOTAL, 1))

def line_at(tt):
    for i, (spk, txt, st, dur, talk) in enumerate(LINES):
        if st <= tt < st + dur: return i, tt - st
    return None, 0

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
def hana(mo, arms_up, blink, sad=False):
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
    if sad and not blink:
        p.line([(138, 236), (184, 222)], HAIR_D, 5); p.line([(282, 236), (236, 222)], HAIR_D, 5)
    mouth(p, 210, 338, 34, mo, sad=sad)
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


# ================= rainbow bridge scene (new for this episode) =================
PLANK_COL = [(255, 160, 165), (255, 195, 140), (255, 230, 135), (165, 222, 160),
             (145, 200, 245), (165, 165, 235), (210, 165, 235)]
MISSING = [2, 3, 4]
BCX, BCY, BRX, BRY, A0, A1 = 540, 1065, 405, 285, 190, 350
PW, PH = 136, 54

def arc_pt(a, lift=0):
    r = math.radians(a)
    return BCX + BRX * math.cos(r), BCY + BRY * math.sin(r) - lift

def arc_rot(a):
    r = math.radians(a)
    tx, ty = -BRX * math.sin(r), BRY * math.cos(r)
    return math.degrees(math.atan2(-ty, tx))

def slot_a(i): return A0 + (i + 0.5) * (A1 - A0) / 7
def bound_a(i): return A0 + i * (A1 - A0) / 7

@lru_cache(None)
def plank(i):
    col = PLANK_COL[i]; dk = tuple(max(0, c - 40) for c in col)
    p = P(PW + 12, PH + 12)
    p.rrect(6, 6, 6 + PW, 6 + PH, 16, col, LINE, 4)
    p.rrect(12, 6 + PH * 0.62, PW, 2 + PH, 10, dk)
    p.rrect(22, 14, PW - 30, 22, 4, (255, 255, 255))
    for x in (22, PW - 10): p.circ(x, 6 + PH * 0.5, 5, (140, 110, 150))
    return p.done()

@lru_cache(None)
def plank_rot(i, ang, sc=100):
    sp = plank(i)
    if sc != 100: sp = sp.resize((int(sp.width * sc / 100), int(sp.height * sc / 100)), Image.LANCZOS)
    return sp.rotate(ang, resample=Image.BICUBIC, expand=True)

FLOAT = {2: (455, 1290, 12), 3: (605, 1365, -14), 4: (495, 1450, 6)}

def make_bg():
    bg = vgrad(W, H, [(0, (255, 226, 214)), (0.28, (238, 222, 250)), (0.52, (212, 236, 230)), (1, (212, 236, 230))]).convert("RGBA")
    t = P(W, H)
    # soft sun + puffy clouds
    t.circ(860, 600, 90, (255, 244, 205)); 
    for cx, cy, s in ((180, 700, 1.0), (700, 800, 0.8), (420, 600, 0.6)):
        for dx, dy, r in ((0, 0, 55), (-55, 15, 40), (55, 15, 42), (25, -30, 40)):
            t.circ(cx + dx * s, cy + dy * s, r * s, (255, 255, 255))
    # distant hills
    t.poly([(-50, 900), (120, 740), (300, 820), (480, 720), (700, 830), (900, 730), (1130, 900)], (218, 205, 242))
    t.poly([(-50, 930), (200, 820), (430, 880), (650, 810), (880, 870), (1130, 820), (1130, 930)], (190, 225, 205))
    bg.alpha_composite(t.done())
    d = ImageDraw.Draw(bg)
    # meadow banks
    d.rectangle([0, 900, W, H], fill=(185, 225, 178))
    # stream (perspective, widening toward us)
    d.polygon([(500, 900), (580, 900), (820, H), (260, H)], fill=(160, 212, 240))
    d.polygon([(520, 900), (560, 900), (700, H), (380, H)], fill=(178, 222, 245))
    # bank edges
    d.line([(500, 900), (260, H)], fill=(150, 200, 150), width=10)
    d.line([(580, 900), (820, H)], fill=(150, 200, 150), width=10)
    # round blossom trees on far banks
    t = P(W, H)
    for cx, cy, r, col in ((70, 830, 62, (255, 200, 220)), (300, 860, 45, (215, 235, 190)),
                           (1010, 820, 66, (255, 210, 225)), (790, 865, 42, (220, 210, 250))):
        t.rrect(cx - 9, cy + r * 0.5, cx + 9, cy + r + 40, 6, (190, 150, 125))
        t.circ(cx, cy, r + 4, tuple(max(0, c - 30) for c in col)); t.circ(cx, cy, r, col)
        t.circ(cx - r * 0.35, cy - r * 0.35, r * 0.22, (255, 255, 255))
    # stone bridge feet on both banks
    for x0 in (100, 900):
        t.rrect(x0, 995, x0 + 86, 1080, 22, (225, 215, 235), LINE, 4)
        t.rrect(x0 + 12, 1008, x0 + 40, 1024, 8, (245, 240, 250))
    # mossy stump for Owlbert (right bank)
    t.ell(700, 1520, 920, 1590, (180, 140, 115), LINE, 4)
    t.rrect(710, 1460, 910, 1560, 20, (200, 158, 125), LINE, 4)
    t.ell(710, 1432, 910, 1492, (230, 200, 160), LINE, 4)
    t.ell(750, 1446, 870, 1478, (240, 215, 180)); t.arc(770, 1452, 850, 1474, 0, 360, (215, 180, 140), 3)
    t.ell(700, 1430, 780, 1462, (160, 210, 150))
    bg.alpha_composite(t.done())
    d = ImageDraw.Draw(bg)
    # foreground flowers
    rnd = random.Random(11)
    for _ in range(60):
        y = rnd.randint(1250, 1900); x = rnd.randint(10, W - 10)
        fr = (y - 900) / 1020
        if 460 - 200 * fr < x < 600 + 200 * fr: continue
        r = 3 + (y - 1250) / 110
        c = rnd.choice([(255, 255, 255), (255, 210, 230), (225, 210, 255), (255, 240, 175)])
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + math.cos(a) * r - r * .55, y + math.sin(a) * r - r * .55, x + math.cos(a) * r + r * .55, y + math.sin(a) * r + r * .55], fill=c)
        d.ellipse([x - r * .4, y - r * .4, x + r * .4, y + r * .4], fill=(255, 205, 110))
    return bg

BG = make_bg()
PETALS = [(random.uniform(0, W), random.uniform(0, 1), random.uniform(0.5, 1.2), random.uniform(0, 6)) for _ in range(16)]

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)

def star4(d, x, y, r, col):
    d.polygon([(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28), (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)], fill=col)

def blinking(t, off): return ((t + off) % 3.9) < 0.13

L = [ln[2] for ln in LINES]
HX, HB = 210, 1560
OX, OB = 810, 1452
MHX, MHB = 540, 1110                     # Mochi hovers under the arch
CARRY0, CSTEP, CDUR = L[4] + 1.7, 1.2, 0.85
DROP = L[2] + LINES[2][4] + 0.1            # Mochi's plank splashes back
DONE = CARRY0 + 2 * CSTEP + CDUR

def plank_pose(i, t):
    """(x, y, angle, scale%) of a missing plank"""
    fx, fy, fa = FLOAT[i]
    bob = math.sin(t * 2.2 + i) * 6
    sa = slot_a(i); sx, sy = arc_pt(sa); srot = arc_rot(sa)
    j = MISSING.index(i); c0 = CARRY0 + j * CSTEP
    if t >= c0 + CDUR: return sx, sy, srot, 100
    if t >= c0:
        q = ease((t - c0) / CDUR)
        return lerp(fx, sx, q), lerp(fy, sy, q) - math.sin(q * math.pi) * 110, lerp(fa, srot, q), int(lerp(85, 100, q))
    x, y, a = fx, fy + bob, fa + math.sin(t * 1.7 + i) * 4
    if i == 2 and LINES[1][2] + 1.0 < t < LINES[1][2] + LINES[1][4]:      # Hana pushes: jiggle only
        x += math.sin(t * 30) * 5
    if i == 3 and LINES[2][2] + 1.0 < t < DROP + 0.6:                     # Mochi lifts alone, then drops
        st = LINES[2][2] + 1.0
        if t < DROP: y -= min(1, (t - st) / 1.2) * 45 + math.sin(t * 25) * 5; a += math.sin(t * 18) * 8
        else: y -= 45 * (1 - ease((t - DROP) / 0.3))
    return x, y, a, 85

def plank_in(i, t):
    if i not in MISSING: return True
    return t >= CARRY0 + MISSING.index(i) * CSTEP + CDUR

def draw_bridge(im, t, done_glow):
    d = ImageDraw.Draw(im)
    # railing segments (only above planks that are in place)
    for i in range(7):
        if not plank_in(i, t): continue
        pts = [arc_pt(bound_a(i) + (bound_a(i + 1) - bound_a(i)) * k / 6, 78) for k in range(7)]
        d.line(pts, fill=LINE, width=14); d.line(pts, fill=(255, 250, 255), width=8)
        for a in (bound_a(i), bound_a(i + 1)):
            x0, y0 = arc_pt(a, 20); x1, y1 = arc_pt(a, 80)
            d.line([(x0, y0), (x1, y1)], fill=LINE, width=12); d.line([(x0, y0), (x1, y1)], fill=(255, 250, 255), width=6)
            d.ellipse([x1 - 9, y1 - 9, x1 + 9, y1 + 9], fill=(255, 215, 120), outline=LINE, width=3)
    for i in range(7):
        if i in MISSING and not plank_in(i, t): continue
        sa = slot_a(i); x, y = arc_pt(sa)
        paste_c(im, plank_rot(i, int(round(arc_rot(sa)))), x, y)
    if done_glow > 0:
        # shimmer travelling across the rainbow
        k = (t * 0.7) % 1.4
        a = A0 + (A1 - A0) * min(1, k)
        x, y = arc_pt(a, 10)
        put_glow(im, x, y, 90, (255, 255, 240), 0.8 * done_glow)
        d = ImageDraw.Draw(im)
        for m in range(7):
            aa = slot_a(m); xx, yy = arc_pt(aa, 60 + 20 * math.sin(t * 3 + m))
            tw = (math.sin(t * 4 + m * 1.3) + 1) / 2
            star4(d, xx, yy - 40, (10 + 10 * tw) * done_glow, (255, 245, 200, int(220 * done_glow)))

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

def mochi_pos(t, ph, lt):
    hover = (MHX + math.sin(t * 1.3) * 30, MHB - abs(math.sin(t * 2)) * 12)
    if ph == 2:
        fx, fy, _ = FLOAT[3]; tgt = (fx, fy - 20)
        if t < DROP:
            q = ease((lt - 0.2) / 0.9); return lerp(hover[0], tgt[0], q), lerp(hover[1], tgt[1], q) - (math.sin(t * 25) * 6 if lt > 1.1 else 0)
        q = ease((t - DROP - 0.8) / 1.0); return lerp(tgt[0], hover[0], q), lerp(tgt[1], hover[1], q)
    if ph == 4 or (ph == 5 and t < DONE + 0.4):
        if t < CARRY0:
            fx, fy, _ = FLOAT[2]; q = ease((t - (CARRY0 - 1.1)) / 1.0)
            return lerp(hover[0], fx, q), lerp(hover[1], fy - 20, q)
        for j, i in enumerate(MISSING):
            c0 = CARRY0 + j * CSTEP
            if t < c0 + CDUR:
                if t < c0:     # gliding back down to the next plank
                    pi = MISSING[j - 1]; sx, sy = arc_pt(slot_a(pi)); fx, fy, _ = FLOAT[i]
                    q = ease((t - (c0 - CSTEP + CDUR)) / (CSTEP - CDUR))
                    return lerp(sx, fx, q), lerp(sy - 30, fy - 20, q)
                x, y, _, _ = plank_pose(i, t); return x, y - 30
        sx, sy = arc_pt(slot_a(4)); q = ease((t - DONE) / 0.4)
        return lerp(sx, hover[0], q), lerp(sy - 30, hover[1], q)
    if ph >= 7:      # bouncy joy under the arch while the goodbye card shows
        return MHX + math.sin(t * 2) * 60, MHB - abs(math.sin(t * 4)) * 30
    if ph >= 5:      # happy loop over the finished bridge
        a = (t - DONE) * 2.2
        return MHX + math.cos(a) * 200, 745 - abs(math.sin(a)) * 50
    return hover

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
    # stream ripples drifting toward us
    for k in range(10):
        q = ((t * 0.12 + k / 10) % 1)
        y = 920 + q * 960; half = 30 + 140 * q
        cx = 540 + math.sin(k * 2.1) * 60 * q
        d.rounded_rectangle([cx - half * 0.4, y, cx + half * 0.4, y + 6 + 4 * q], radius=5, fill=(235, 248, 255, int(200 * (1 - q * 0.5))))
    done_glow = ease((t - DONE) / 0.8) if t > DONE else 0
    draw_bridge(im, t, done_glow)
    d = ImageDraw.Draw(im)
    # floating / carried planks + splash rings
    for pi in MISSING:
        if plank_in(pi, t): continue
        x, y, a, sc = plank_pose(pi, t)
        if sc == 85:
            d.ellipse([x - 70, y + 14, x + 70, y + 36], outline=(235, 248, 255), width=4)
        paste_c(im, plank_rot(pi, int(round(a)), sc), x, y)
    d = ImageDraw.Draw(im)
    if DROP <= t < DROP + 1.0:
        q = (t - DROP) / 1.0; fx, fy, _ = FLOAT[3]
        for k in range(8):
            a = k * 2 * math.pi / 8; r = 30 + 90 * q
            d.ellipse([fx + r * math.cos(a) - 12, fy + 10 + r * 0.45 * math.sin(a) - 12, fx + r * math.cos(a) + 12, fy + 10 + r * 0.45 * math.sin(a) + 12],
                      fill=(225, 245, 255, int(230 * (1 - q))))
    # falling petals
    for px, py0, sp, off in PETALS:
        y = ((py0 + t * 0.05 * sp) % 1) * 1500 + 500
        x = (px + math.sin(t * sp + off) * 50 + t * 20) % W
        d.ellipse([x - 9, y - 5, x + 9, y + 5], fill=(255, 190, 215, 200))

    # ---- Owlbert on the stump ----
    om, ob = talking("Professor Owlbert", t)
    owing = 0.0
    if ph == 3: owing = (math.sin(t * 6) + 1) / 2 * 0.6
    if ph >= 5: owing = (math.sin(t * 5) + 1) / 2 * 0.5
    if ph == 3 and lt > 0.5:
        for k in range(5):
            a = t * 1.8 + k * 1.256
            star4(d, OX + 150 * math.cos(a), OB - 170 + 110 * math.sin(a), 11, (255, 225, 120, 220))
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob)

    # ---- Hana ----
    hm, hb = talking("Hana", t)
    sad, arms, hop, hx = False, False, 0, HX
    if ph == 1:
        q = ease(lt / 1.0); hx = lerp(HX, 300, q)
        arms = 1.0 < lt < LINES[1][4] - 0.6
        hop = abs(math.sin(t * 14)) * 6 if arms else 0
        sad = lt >= LINES[1][4] - 0.6
    elif ph in (2, 3):
        hx = lerp(300, HX, ease(lt / 1.0)) if ph == 2 else HX; sad = ph == 2 or lt < 1.2
    elif ph == 4:
        hx = lerp(HX, 290, ease(lt / 1.0)); arms = lt > 1.4; hop = abs(math.sin(t * 7)) * 12 if arms else 0
    elif ph >= 5:
        hx = 290 if t < DONE + 1 else lerp(290, HX + 40, ease((t - DONE - 1) / 1)); arms = True; hop = abs(math.sin(t * 6)) * 14
    shadow(im, hx, HB - 4, 0.75)
    paste(im, hana(hm, arms, blinking(t, 0.0) and not sad, sad), hx, HB - hb - hop, 0.9, 0.9)
    d = ImageDraw.Draw(im)
    if ph == 1 and sad:
        d.ellipse([hx + 70, 1070, hx + 92, 1100], fill=(160, 210, 245)); d.polygon([(hx + 72, 1080), (hx + 90, 1080), (hx + 81, 1056)], fill=(160, 210, 245))
    # teamwork sparkles: from Hana's hands to the plank being carried
    if t >= CARRY0 - 0.2 and t < DONE:
        for j, pi in enumerate(MISSING):
            c0 = CARRY0 + j * CSTEP
            if c0 - 0.2 <= t < c0 + CDUR:
                px, py, _, _ = plank_pose(pi, t)
                for k in range(5):
                    q = ((t * 1.8 + k / 5) % 1)
                    star4(d, lerp(hx + 90, px, q), lerp(1100, py, q) - math.sin(q * math.pi) * 60, 10, (255, 150, 190, 230))

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    mx, mbot = mochi_pos(t, ph, lt)
    wing = math.sin(t * 5) * 0.4; expr = "happy"
    if ph == 2 and lt > 1.1: wing = math.sin(t * 14)
    if ph == 2 and t > DROP: expr = "sad"; wing = -0.5
    if ph == 3 and lt < 1.2: expr = "sad"
    if ph == 4 and t >= CARRY0: wing = math.sin(t * 12); expr = "joy"
    if ph >= 5: expr = "joy"; wing = math.sin(t * 9)
    paste(im, mochi(mm, round(wing * 4) / 4, expr, blinking(t, 2.3) and expr != "joy"), mx, mbot + 40 - mb, 0.8, 0.8)
    d = ImageDraw.Draw(im)
    if ph >= 6:
        for k in range(6):
            q = ((t - L[6]) * 0.35 + k / 6) % 1
            heart(d, 330 + (k % 3) * 190 + math.sin(t * 2 + k) * 25, 1200 - q * 300, 18 + 6 * (k % 2), (255, 130, 170, int(230 * (1 - q))))

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "The Rainbow Bridge", 88, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (130, 180, 240), "Let's work together!", 96, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle waltz in F major (3/4), kalimba + soft pad ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "pluck": w = w + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt) + 0.2 * np.sin(2 * np.pi * freq * 3 * tt) * np.exp(-12 * tt)
    if shape == "bell": w = w + 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 4.02 * tt)
    if shape == "kal": w = w + 0.25 * np.sin(2 * np.pi * freq * 5.4 * tt) * np.exp(-14 * tt)
    if shape == "pad": w = w + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt); env = np.minimum(1, tt * 2.0) * np.minimum(1, (dur - tt) * 2.0)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at, buf=None):
    buf = audio if buf is None else buf
    i0 = int(at * SR)
    if i0 >= N: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
# original waltz melody, 6 eighth-notes per bar (None = rest)
mel = [72, None, 69, None, 72, 74,   77, None, 76, None, 74, None,   72, None, 70, 69, 67, None,   69, None, None, None, None, None,
       70, None, 74, None, 72, 70,   69, None, 72, None, 77, None,   76, 74, 72, None, 67, None,   65, None, None, None, None, None]
chords = [(53, 57, 60), (50, 53, 58), (48, 52, 55), (53, 57, 60), (50, 53, 58), (53, 57, 60), (48, 52, 55), (53, 57, 60)]
e8 = 0.27; music = np.zeros(N); k = 0
while k * e8 < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 0.9, 0.05, "kal", 4.0), k * e8, music)
    bar = k // 6; ch = chords[bar % len(chords)]
    if k % 6 == 0:
        for n_ in ch: add(tone(f(n_), e8 * 6, 0.02, "pad"), k * e8, music)
        add(tone(f(ch[0] - 12), 0.7, 0.035, "pluck", 5), k * e8, music)
    elif k % 2 == 0:
        add(tone(f(ch[1]), 0.35, 0.018, "pluck", 9), k * e8, music); add(tone(f(ch[2]), 0.35, 0.018, "pluck", 9), k * e8, music)
    k += 1
duck = np.ones(N)
for spk, txt, st, dur, talk in LINES:
    a, b_ = int((st + 0.2) * SR), int((st + 0.4 + talk) * SR); duck[a:b_] = 0.6
duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
audio += music * duck
base = {"Hana": 620, "Mochi": 820, "Professor Owlbert": 330}
rnd = random.Random(5)
for spk, txt, st, dur, talk in LINES:
    if spk not in base: continue
    tt = st + 0.3
    while tt < st + 0.3 + talk:
        add(tone(base[spk] * rnd.choice([1, 1.12, 1.25, 0.9]), 0.09, 0.03, "sine", 25), tt); tt += 0.286
# sfx
for j, m in enumerate([72, 76, 79, 84]): add(tone(f(m), 0.9, 0.1, "bell", 3), 0.1 + j * 0.15)
for j in range(4): add(tone(f(48 + j), 0.2, 0.06, "pluck", 12), LINES[1][2] + 1.2 + j * 0.35)     # heavy push
add(tone(f(55), 0.5, 0.08, "pluck", 6), DROP)
for j in range(6): add(tone(f(84 - j * 3), 0.25, 0.04, "bell", 10), DROP + 0.03 + j * 0.06)      # splash drips
for j, m in enumerate([77, 81, 84, 89]): add(tone(f(m), 1.0, 0.07, "bell", 3.5), L[3] + 0.5 + j * 0.18)   # idea
for j in range(3): add(tone(f([72, 76, 79][j]), 0.6, 0.09, "pluck", 6), CARRY0 + j * CSTEP + CDUR)   # plank clicks in
for j, m in enumerate([72, 74, 76, 77, 79, 81, 84]): add(tone(f(m), 1.0, 0.07, "bell", 3.5), DONE + 0.1 + j * 0.1)  # rainbow
for j, m in enumerate([77, 81, 84, 89, 93]): add(tone(f(m), 1.4, 0.08, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
