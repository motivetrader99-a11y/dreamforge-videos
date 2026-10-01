"""Petal Valley (Anime Adventures): A new friend who looks different — lesson: kindness.
Original characters, art and music. Renders kids/new_friend_looks_different.mp4 (captions + music, no voice).
Character designs match make_garden_needs_water.py (Hana, Mochi, Professor Owlbert); Pip is a new original guest."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/new_friend_looks_different.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(7272)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "One day, a new friend named Pip came to Petal Valley."),
    ("Mochi", "Pip has spots and long ears. Pip looks different!"),
    ("Hana", "Pip is all alone. Maybe Pip feels shy."),
    ("Professor Owlbert", "We all look different, and that is wonderful!"),
    ("Hana", "Hello, Pip! I'm Hana. Do you want to play with us?"),
    ("Mochi", "Yay! Now we have a brand new friend!"),
    ("Narrator", "Be kind to everyone. Different is special!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.4, 4.6
LINES, t = [], INTRO
for spk, txt in SCRIPT:
    words = len(txt.split())
    talk = words * 0.34 + 0.4
    dur = max(5.2, talk + 1.8)
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

# ================= lily-pond meadow at golden afternoon (new for this episode) =================
def fx_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def mix(a, b, k): return tuple(int(lerp(a[i], b[i], k)) for i in range(3))

# ---------- Pip: new original guest (fuzzy lavender puff, mint spots, floppy ears, leaf sprout) ----------
PV = (205, 180, 240); PV_D = (150, 120, 200); PV_L = (235, 222, 252); SPOT = (165, 230, 205)
@lru_cache(None)
def pip(expr, blink, ear):
    """expr: shy / happy / joy ; ear: -2..2 wiggle step"""
    p = P(340, 360)
    cx, cy = 170, 215
    e = ear * 4
    # floppy ears (behind body), hanging down the sides
    for sgn in (-1, 1):
        x0 = cx + sgn * 70
        pts = [(x0 - 18, 120), (x0 + 18, 118), (x0 + sgn * 70 + 14, 205 + e * sgn), (x0 + sgn * 62, 250 + e * sgn), (x0 + sgn * 40, 240 + e * sgn)]
        p.poly(pts, PV, PV_D, 4)
        p.circ(x0 + sgn * 58, 238 + e * sgn, 20, SPOT, PV_D, 3)
    # little tail tuft
    p.circ(cx + 112, 280, 20, PV_L, PV_D, 3)
    # feet
    for sgn in (-1, 1): p.ell(cx + sgn * 48 - 30, 318, cx + sgn * 48 + 30, 350, PV_D, LINE, 3)
    # fuzzy body: ring of puffs (outline pass, then fill)
    ring = [(cx + math.cos(a) * 112, cy + 20 + math.sin(a) * 104) for a in np.linspace(0, 2 * math.pi, 22, endpoint=False)]
    for x, y in ring: p.circ(x, y, 24, PV_D)
    p.ell(cx - 118, cy - 88, cx + 118, cy + 128, PV_D)
    for x, y in ring: p.circ(x, y, 20, PV)
    p.ell(cx - 114, cy - 84, cx + 114, cy + 124, PV)
    p.ell(cx - 66, cy + 50, cx + 66, cy + 122, PV_L)
    # mint spots
    for x, y, r in ((cx - 82, cy - 30, 16), (cx + 86, cy - 22, 13), (cx - 70, cy + 70, 12), (cx + 76, cy + 74, 17), (cx - 14, cy - 76, 11)):
        p.circ(x, y, r, SPOT)
    # leaf sprout on head
    p.line([(cx, cy - 86), (cx + 4, cy - 118)], (90, 160, 110), 6)
    p.poly([(cx + 4, cy - 116), (cx + 40, cy - 140), (cx + 30, cy - 108)], (140, 215, 150), (90, 160, 110), 3)
    p.poly([(cx + 2, cy - 112), (cx - 30, cy - 132), (cx - 22, cy - 102)], (140, 215, 150), (90, 160, 110), 3)
    # face
    ey = cy + 5
    look = -6 if expr == "shy" else 0
    eye(p, cx - 42, ey + 4, 54, 66, (70, 175, 160), blink, happy=(expr == "joy"))
    eye(p, cx + 42, ey + 4, 54, 66, (70, 175, 160), blink, happy=(expr == "joy"))
    bl = (255, 150, 185) if expr == "shy" else (255, 175, 200)
    for sgn in (-1, 1): p.ell(cx + sgn * 76 - 18, ey + 38, cx + sgn * 76 + 18, ey + 54, bl)
    if expr == "shy":
        p.arc(cx - 12, ey + 46, cx + 12, ey + 62, 200, 340, (120, 60, 90), 4)       # tiny unsure mouth
        p.line([(cx - 64, ey - 44), (cx - 26, ey - 36)], PV_D, 5); p.line([(cx + 64, ey - 44), (cx + 26, ey - 36)], PV_D, 5)
    elif expr == "joy":
        p.chord(cx - 20, ey + 34, cx + 20, ey + 68, 0, 180, (190, 80, 110))
        p.ell(cx - 10, ey + 52, cx + 10, ey + 66, (255, 150, 170))
    else:
        p.arc(cx - 16, ey + 30, cx + 16, ey + 58, 20, 160, (120, 60, 90), 5)
    return p.done()

SKY = vgrad(W, H, [(0, (255, 214, 200)), (0.25, (250, 222, 236)), (0.48, (232, 226, 250)), (0.62, (205, 235, 215)), (1, (190, 230, 195))]).convert("RGBA")
POND = (160, 210, 235)
BUSH_X, BUSH_Y = 800, 1565

def make_land():
    t = P(W, H)
    # far lilac hills
    t.poly([(-60, 1010), (200, 930), (430, 990), (700, 910), (930, 980), (1140, 930), (1140, 1150), (-60, 1150)], (215, 205, 238))
    t.poly([(-60, 1070), (300, 1010), (620, 1060), (900, 1000), (1140, 1050), (1140, 1200), (-60, 1200)], (190, 225, 190))
    # meadow
    t.poly([(-60, 1120), (1140, 1110), (1140, H + 10), (-60, H + 10)], (180, 225, 170))
    # pond with reflections and lily pads
    t.ell(260, 1180, 1000, 1330, (140, 190, 215))
    t.ell(268, 1186, 992, 1322, POND)
    for x, w_ in ((420, 120), (650, 160), (820, 90)): t.rrect(x, 1240, x + w_, 1248, 4, (220, 240, 252))
    for x, y in ((360, 1260), (560, 1210), (900, 1250)):
        t.chord(x - 44, y - 20, x + 44, y + 20, 30, 330, (140, 200, 140))
        t.circ(x + 6, y - 6, 12, (255, 190, 215)); t.circ(x + 6, y - 6, 5, (255, 235, 140))
    # cherry-blossom tree (left) with branch for Owlbert
    t.poly([(70, 1260), (100, 760), (150, 760), (175, 1260)], (190, 145, 125), LINE, 4)
    t.poly([(130, 960), (360, 925), (362, 950), (140, 1000)], (190, 145, 125), LINE, 4)
    for x, y, r in ((40, 640, 120), (160, 580, 130), (290, 660, 110), (90, 760, 100), (230, 760, 90), (-20, 760, 90)):
        t.circ(x, y, r + 4, (235, 160, 190)); t.circ(x, y, r, (255, 200, 222))
    for x, y in ((60, 600), (180, 540), (280, 640), (120, 720), (220, 700), (10, 700)):
        t.circ(x, y, 14, (255, 230, 240))
    # picnic blanket (left foreground)
    t.poly([(40, 1600), (380, 1560), (440, 1700), (60, 1760)], (255, 236, 236), LINE, 3)
    for k in range(4):
        u = (k + 0.5) / 4
        t.line([(lerp(40, 380, u), lerp(1600, 1560, u)), (lerp(60, 440, u), lerp(1760, 1700, u))], (255, 170, 190), 10)
    im = t.done()
    d = ImageDraw.Draw(im)
    rnd = random.Random(23)
    for _ in range(80):
        x, y = rnd.randint(10, W - 10), rnd.randint(1140, 1900)
        if 255 < x < 1005 and 1175 < y < 1335: continue
        c = rnd.choice([(150, 205, 140), (200, 238, 180), (255, 255, 255), (255, 210, 230)])
        if c in ((255, 255, 255), (255, 210, 230)):
            for a in range(5):
                aa = a * 1.2566; d.ellipse([x + math.cos(aa) * 6 - 4, y + math.sin(aa) * 6 - 4, x + math.cos(aa) * 6 + 4, y + math.sin(aa) * 6 + 4], fill=c)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 215, 110))
        else:
            d.line([(x - 6, y), (x - 9, y - 12)], fill=c, width=4); d.line([(x, y), (x, y - 15)], fill=c, width=4); d.line([(x + 6, y), (x + 9, y - 12)], fill=c, width=4)
    return im
LAND = make_land()

@lru_cache(None)
def bush():
    p = P(380, 300)
    puffs = [(190, 190, 110), (90, 200, 80), (290, 200, 80), (130, 120, 78), (250, 120, 78), (190, 80, 70)]
    for x, y, r in puffs: p.circ(x, y, r + 4, (110, 170, 120))
    for x, y, r in puffs: p.circ(x, y, r, (150, 210, 150))
    rnd = random.Random(4)
    for _ in range(16):          # hydrangea blossoms
        x, y = rnd.randint(50, 330), rnd.randint(50, 250)
        col = rnd.choice([(190, 180, 245), (170, 210, 250), (255, 190, 220)])
        for a in range(4):
            aa = a * math.pi / 2 + 0.4
            p.circ(x + math.cos(aa) * 10, y + math.sin(aa) * 10, 9, col)
        p.circ(x, y, 4, (255, 255, 255))
    return p.done()

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)

def petal(d, x, y, r, a, col):
    pts = []
    for j in range(12):
        th = j * math.pi / 6
        rr = r * (1 - 0.35 * abs(math.sin(th)))
        px, py = math.cos(th) * rr, math.sin(th) * rr * 0.6
        pts.append((x + px * math.cos(a) - py * math.sin(a), y + px * math.sin(a) + py * math.cos(a)))
    d.polygon(pts, fill=col)

@lru_cache(None)
def ball(rot):
    p = P(120, 120)
    p.circ(60, 60, 50, (255, 250, 240), LINE, 4)
    for k, col in enumerate([(255, 170, 190), (150, 205, 250), (255, 220, 120)]):
        a0 = rot * 15 + k * 120
        p.d.pieslice([10 * S + 8, 10 * S + 8, 110 * S - 8, 110 * S - 8], a0, a0 + 60, fill=col)
    p.circ(60, 60, 12, (255, 255, 255))
    p.circ(42, 40, 9, (255, 255, 255))
    return p.done()

def friend_blob(d, x, y, kind):
    """little smiling icons for Owlbert's card: all different, all friends."""
    cols = [(255, 175, 200), (150, 205, 250), (170, 225, 170), (215, 190, 250)]
    c = cols[kind]
    if kind == 0: d.ellipse([x - 48, y - 48, x + 48, y + 48], fill=c)
    elif kind == 1: d.rounded_rectangle([x - 44, y - 44, x + 44, y + 44], radius=18, fill=c)
    elif kind == 2: d.polygon([(x, y - 56), (x + 52, y + 40), (x - 52, y + 40)], fill=c)
    else:
        d.ellipse([x - 48, y - 46, x + 48, y + 50], fill=c)
        for sx, sy in ((-26, -20), (24, 24), (28, -26)): d.ellipse([x + sx - 8, y + sy - 8, x + sx + 8, y + sy + 8], fill=SPOT)
    ey = y + (8 if kind == 2 else 0)
    for sgn in (-1, 1): d.ellipse([x + sgn * 16 - 6, ey - 12, x + sgn * 16 + 6, ey + 4], fill=(70, 50, 80))
    d.chord([x - 14, ey + 4, x + 14, ey + 26], 0, 180, fill=(190, 80, 110))

L = [ln[2] for ln in LINES]
HX, HB, HS = 205, 1555, 0.85
OX, OB, OS = 265, 948, 0.78
PB = 1560

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

def pip_state(t, ph, lt):
    """returns x, bottom, expr, hop"""
    if ph < 0: return 880, PB, "shy", 0                          # hidden behind the bush
    if ph == 0:
        q = ease((lt - 1.2) / 1.0); return lerp(880, 770, q), PB, "shy", 0      # peeks out
    if ph <= 3: return 770 + math.sin(t * 0.8) * 6, PB, "shy", 0
    if ph == 4:
        q = ease((lt - 3.2) / 1.4)
        return lerp(770, 590, q), PB, ("shy" if lt < 3.6 else "happy"), abs(math.sin(lt * 7)) * 18 * q * (1 - q) * 4
    hop = abs(math.sin(t * 5)) * 26
    return 590, PB, "joy", hop

PETALS = [(random.uniform(0, W), random.uniform(0, 1), random.uniform(0.6, 1.2), random.uniform(0, 6)) for _ in range(16)]

PREVIEW = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x]
FRAMES = [int(x * FPS) for x in PREVIEW] if PREVIEW else range(NFR)
proc = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

BALL0 = L[5] + 0.6
for fi in FRAMES:
    t = fi / FPS
    i, lt = line_at(t)
    ph = 7 if t >= T_OUTRO else (-1 if i is None else i)
    im = SKY.copy(); d = ImageDraw.Draw(im)
    # soft afternoon sun low behind the hills + drifting clouds
    put_glow(im, 860, 900, 230, (255, 235, 200), 0.7)
    d = ImageDraw.Draw(im)
    d.ellipse([800, 840, 920, 960], fill=(255, 230, 180))
    for cx0, cy0, s, sp in ((200, 560, 1.0, 10), (700, 620, 0.8, 7)):
        x = (cx0 + t * sp) % (W + 300) - 150
        for dx, dy, r in ((0, 0, 50), (-55, 12, 36), (55, 12, 38), (25, -25, 34)):
            d.ellipse([x + dx * s - r * s, cy0 + dy * s - r * s, x + dx * s + r * s, cy0 + dy * s + r * s], fill=(255, 250, 252))
    im.alpha_composite(LAND)
    d = ImageDraw.Draw(im)
    # pond shimmer
    for k in range(6):
        x = 330 + k * 110 + math.sin(t * 1.3 + k) * 20
        a = int(120 + 100 * math.sin(t * 2 + k))
        d.line([(x, 1290 - (k % 2) * 30), (x + 40, 1290 - (k % 2) * 30)], fill=(235, 248, 255), width=4)

    # ---- Owlbert on the blossom branch ----
    om, ob = talking("Professor Owlbert", t)
    owing = (math.sin(t * 5) + 1) / 2 * 0.6 if ph == 3 else ((math.sin(t * 4) + 1) / 2 * 0.35 if ph >= 6 else 0.0)
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob, OS, OS)

    # ---- Pip (behind the bush) ----
    px, pb, pexpr, phop = pip_state(t, ph, lt)
    ear = int(round(math.sin(t * 3) * 2)) if pexpr != "shy" else int(round(math.sin(t * 1.2)))
    if px < 700: shadow(im, px, pb - 4, 0.75)
    paste(im, pip(pexpr, blinking(t, 0.6) and pexpr != "joy", ear), px, pb - phop, 0.92, 0.92)
    paste(im, bush(), BUSH_X + 90, BUSH_Y + 20)
    d = ImageDraw.Draw(im)
    if ph in (1, 2) and lt > 0.5:                                          # gentle "..." shy dots
        for j in range(3):
            if (lt * 2) % 3 >= j:
                d.ellipse([px - 40 + j * 34 - 9, pb - 330 - 9, px - 40 + j * 34 + 9, pb - 330 + 9], fill=(150, 120, 200))

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    if ph >= 5:
        a = (t - L[5]) * 1.6
        mx, mbot = 520 + math.sin(a) * 70, 1200 + math.sin(a * 2) * 25 - abs(math.sin(t * 3)) * 14
        mexpr = "joy" if not mm else "happy"
    else:
        mx, mbot = 520 + math.sin(t * 1.1) * 30, 1220 - abs(math.sin(t * 2)) * 14
        mexpr = "happy"
    mwing = math.sin(t * (9 if ph >= 5 else 5)) * (0.8 if ph >= 5 else 0.5)
    shadow(im, mx, 1420, 0.45)
    paste(im, mochi(mm, round(mwing * 4) / 4, mexpr, blinking(t, 2.3) and mexpr != "joy"), mx, mbot - mb, 0.68, 0.68)
    d = ImageDraw.Draw(im)

    # ---- Hana ----
    hm, hb = talking("Hana", t)
    waving = ph == 4 and lt < 3.4 and int(lt * 3) % 2 == 0
    harms = waving or ph >= 6 or (ph == 5 and lt > 3.6)
    hsad = ph == 2 and not hm
    shadow(im, HX, HB - 4, 0.7)
    hop = abs(math.sin(t * 6)) * 14 if ph >= 6 else 0
    paste(im, hana(hm, harms, blinking(t, 0.0), hsad), HX, HB - hb - hop, HS, HS)
    d = ImageDraw.Draw(im)

    # ---- the ball game: Hana and Pip roll a ball back and forth ----
    if ph == 5 or ph == 6:
        u = (t - BALL0) / 1.4
        if u > 0:
            k = int(u); fr = u - k
            a_x, b_x = 320, 490
            if k % 2: a_x, b_x = b_x, a_x
            bx_ = lerp(a_x, b_x, fr); by_ = 1490 - math.sin(fr * math.pi) * 230
            shadow(im, bx_, 1545, 0.3)
            paste_c(im, ball(int(u * 8) % 24), bx_, by_)
            d = ImageDraw.Draw(im)

    # Owlbert's picture card: all different, all friends
    if ph == 3 or (ph == 4 and lt < 0.5):
        q = ease(lt / 0.5) if ph == 3 else 1 - ease(lt / 0.5)
        lay = fx_layer(); dl = ImageDraw.Draw(lay)
        x0, y0, x1, y1 = 400, 560, 910, 830
        dl.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=(255, 255, 255, 238), outline=(190, 140, 90), width=6)
        for k in range(4):
            bob = math.sin(t * 4 + k) * 6
            friend_blob(dl, 470 + k * 123, 662 + bob, k)
        lab = "all different!"
        w_ = dl.textlength(lab, font=font(48)); dl.text(((x0 + x1) / 2 - w_ / 2, 748), lab, font=font(48), fill=(150, 110, 80))
        if q < 1:
            a_ = np.array(lay); a_[:, :, 3] = (a_[:, :, 3] * q).astype(np.uint8); lay = Image.fromarray(a_)
        im.alpha_composite(lay); d = ImageDraw.Draw(im)

    # Mochi's curious "?" on line 1
    if ph == 1 and lt > 0.5:
        q = ease((lt - 0.5) / 0.4)
        w_ = d.textlength("?", font=font(int(90 * q) + 4))
        d.text((mx + 70 - w_ / 2, mbot - 300), "?", font=font(int(90 * q) + 4), fill=(90, 150, 230))

    # falling blossom petals all the time; hearts + sparkles at the happy end
    lay = fx_layer(); dl = ImageDraw.Draw(lay)
    for x0, y0, sp, off in PETALS:
        y = 520 + ((y0 + t * 0.06 * sp) % 1) * 1050
        x = x0 + math.sin(t * sp + off) * 40
        petal(dl, x % 930, y, 13, t * sp + off, (255, 190, 215, 220))
    if ph >= 5:
        for k in range(6):
            q = ((t - L[5]) * 0.35 + k / 6) % 1
            heart(dl, 200 + k * 120 + math.sin(t * 2 + k) * 18, 1080 - q * 220, 18 + 5 * (k % 2), (255, 150, 190, int(230 * (1 - q))))
    im.alpha_composite(lay)

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "The New Friend", 92, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (180, 150, 230), "Be kind to every friend!", 86, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle lullaby-pop in D major (4/4), music box + kalimba + soft pad ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "box": w = w + 0.35 * np.sin(2 * np.pi * freq * 3.01 * tt) * np.exp(-6 * tt) + 0.1 * np.sin(2 * np.pi * freq * 5.4 * tt) * np.exp(-12 * tt)
    if shape == "pluck": w = w + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt)
    if shape == "bell": w = w + 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 4.02 * tt)
    if shape == "pad": w = w + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt); env = np.minimum(1, tt * 1.2) * np.minimum(1, (dur - tt) * 1.2)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at, buf=None):
    buf = audio if buf is None else buf
    i0 = int(at * SR)
    if i0 >= N: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
# 8th-note melody (None = rest), 4 bars x 8, original
mel = [74, None, 78, 76, 74, None, 71, None,   73, 74, 76, None, 69, None, None, None,
       71, None, 74, 73, 71, None, 67, None,   69, 71, 73, 76, 74, None, None, None,
       78, None, 81, 79, 78, None, 74, None,   76, 78, 79, None, 73, None, None, None,
       71, 73, 74, None, 76, 73, 69, None,     74, None, None, None, None, None, None, None]
chords = [(50, 54, 57), (45, 49, 52), (43, 47, 50), (45, 49, 52), (50, 54, 57), (45, 49, 52), (43, 47, 50), (50, 54, 57)]
e8 = 0.27; music = np.zeros(N); k = 0
while k * e8 < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 1.0, 0.045, "box", 3.5), k * e8, music)
    bar = k // 8; ch = chords[bar % len(chords)]
    if k % 8 == 0:
        for n_ in ch: add(tone(f(n_), e8 * 8, 0.014, "pad"), k * e8, music)
        add(tone(f(ch[0] - 12), 0.9, 0.035, "pluck", 3), k * e8, music)
    if k % 2 == 1: add(tone(f(ch[(k // 2) % 3] + 12), 0.25, 0.012, "pluck", 10), k * e8, music)
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
for j, m in enumerate([74, 78, 81, 86]): add(tone(f(m), 1.0, 0.07, "bell", 3), 0.1 + j * 0.18)          # title
for j, m in enumerate([81, 83]): add(tone(f(m), 0.4, 0.04, "sine", 6), L[0] + 1.3 + j * 0.2)            # Pip peeks
for j, m in enumerate([86, 90, 93]): add(tone(f(m), 0.7, 0.05, "bell", 4), L[4] + 3.6 + j * 0.13)      # Pip comes out
u = 0
while BALL0 + u * 1.4 < T_OUTRO:
    add(tone(f(62), 0.25, 0.06, "pluck", 14), BALL0 + u * 1.4 + 1.4); u += 1                           # ball bounces
for j, m in enumerate([74, 78, 81, 86, 90]): add(tone(f(m), 1.4, 0.07, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
