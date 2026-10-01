"""Petal Valley (Anime Adventures): Mochi is afraid of the dark — lesson: being brave.
Original characters, art and music. Renders kids/mochi_afraid_of_the_dark.mp4 (captions + music, no voice).
Character designs match make_hana_says_sorry.py / make_rainbow_bridge_teamwork.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/mochi_afraid_of_the_dark.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(4242)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "The sun went to sleep, and night came to Petal Valley."),
    ("Mochi", "Oh no, it's so dark! I feel scared."),
    ("Hana", "I'm right here, Mochi. Let's take a big breath together."),
    ("Professor Owlbert", "The dark is not scary. Look, the fireflies come out to play!"),
    ("Mochi", "So many little lights! And the moon is smiling at me!"),
    ("Hana", "You were so brave, Mochi!"),
    ("Narrator", "Being brave means trying, even when you feel a little scared."),
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



# ================= night meadow scene (new for this episode) =================
HORIZON = 1000

def sky(stops): return vgrad(W, H, stops).convert("RGBA")
SKY_DUSK = sky([(0, (255, 190, 175)), (0.33, (255, 214, 190)), (0.52, (255, 232, 200)), (1, (255, 232, 200))])
SKY_NIGHT = sky([(0, (30, 36, 92)), (0.33, (52, 54, 120)), (0.52, (96, 84, 150)), (1, (96, 84, 150))])

def make_land(night):
    t = P(W, H)
    # far hills
    t.poly([(-60, 1010), (110, 880), (330, 950), (520, 860), (740, 950), (930, 870), (1140, 1000), (1140, 1100), (-60, 1100)], (205, 190, 235))
    t.poly([(-60, 1060), (220, 960), (470, 1020), (720, 950), (960, 1010), (1140, 960), (1140, 1150), (-60, 1150)], (175, 215, 190))
    # round cottage on the far hill (left)
    cx, cy = 190, 960
    t.ell(cx - 70, cy - 70, cx + 70, cy + 50, (255, 225, 210), LINE, 4)
    t.poly([(cx - 92, cy - 40), (cx, cy - 135), (cx + 92, cy - 40)], (240, 150, 170), LINE, 4)
    win = (255, 222, 120) if night else (150, 140, 175)
    t.circ(cx - 28, cy - 12, 17, win, LINE, 3); t.circ(cx + 28, cy - 12, 17, win, LINE, 3)
    t.rrect(cx - 14, cy + 6, cx + 14, cy + 50, 12, (190, 140, 120), LINE, 3)
    # meadow
    t.poly([(-60, 1120), (300, 1060), (700, 1090), (1140, 1050), (1140, H + 10), (-60, H + 10)], (180, 222, 170))
    # winding path
    t.poly([(500, 1080), (560, 1080), (700, 1400), (820, H + 10), (380, H + 10), (470, 1400)], (240, 220, 190))
    # puffy trees
    for x, y, r, col in ((60, 1060, 70, (200, 230, 175)), (980, 1030, 62, (215, 205, 245)), (880, 1080, 46, (255, 205, 220))):
        t.rrect(x - 10, y + r * 0.4, x + 10, y + r + 50, 6, (180, 140, 120))
        t.circ(x, y, r + 4, tuple(max(0, c - 35) for c in col)); t.circ(x, y, r, col)
        t.circ(x - r * 0.35, y - r * 0.35, r * 0.2, (255, 255, 255))
    # Owlbert's mushroom stool (right)
    t.rrect(758, 1400, 842, 1490, 22, (250, 240, 225), LINE, 4)
    t.ell(690, 1340, 910, 1440, (190, 170, 235), LINE, 4)
    for x, y, r in ((740, 1372, 14), (800, 1360, 18), (860, 1385, 12)): t.circ(x, y, r, (250, 245, 255))
    im = t.done()
    d = ImageDraw.Draw(im)
    rnd = random.Random(7)
    for _ in range(55):
        y = rnd.randint(1150, 1900); x = rnd.randint(10, W - 10)
        r = 4 + (y - 1150) / 90
        c = rnd.choice([(255, 255, 255), (255, 210, 230), (225, 210, 255), (255, 240, 175)])
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + math.cos(a) * r - r * .55, y + math.sin(a) * r - r * .55, x + math.cos(a) * r + r * .55, y + math.sin(a) * r + r * .55], fill=c)
        d.ellipse([x - r * .4, y - r * .4, x + r * .4, y + r * .4], fill=(255, 205, 110))
    if night:
        a = np.array(im).astype(np.float32)
        a[..., 0] = a[..., 0] * 0.42 + 12; a[..., 1] = a[..., 1] * 0.46 + 14; a[..., 2] = a[..., 2] * 0.72 + 40
        a = np.clip(a, 0, 255).astype(np.uint8)
        # keep cottage windows warm
        im2 = Image.fromarray(a); dd = ImageDraw.Draw(im2)
        for wx in (cx - 28, cx + 28): dd.ellipse([wx - 14, cy - 26, wx + 14, cy + 2], fill=(255, 222, 120))
        return im2
    return im

LAND_DAY, LAND_NIGHT = make_land(False), make_land(True)
STARS = [(random.uniform(30, 1050), random.uniform(520, 900), random.uniform(5, 11), random.uniform(0, 6)) for _ in range(34)]

@lru_cache(None)
def moon(smile_k):
    p = P(220, 220)
    p.circ(110, 110, 92, (255, 246, 205), (235, 210, 150), 4)
    p.circ(70, 80, 12, (245, 232, 185)); p.circ(150, 150, 9, (245, 232, 185))
    p.arc(66, 90, 98, 116, 200, 340, (150, 120, 110), 5); p.arc(122, 90, 154, 116, 200, 340, (150, 120, 110), 5)
    p.ell(52, 122, 80, 136, (255, 190, 190)); p.ell(140, 122, 168, 136, (255, 190, 190))
    if smile_k: p.arc(88, 118, 132, 152, 20, 160, (150, 120, 110), 5)
    else: p.line([(98, 136), (122, 136)], (150, 120, 110), 4)
    return p.done()

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)

def star4(d, x, y, r, col):
    d.polygon([(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28), (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)], fill=col)

L = [ln[2] for ln in LINES]
HX, HB = 300, 1545
OX, OB = 800, 1345
MOON_X, MOON_Y0, MOON_Y1 = 760, 1090, 660
NIGHT0, NIGHT1 = L[0] + 0.8, L[0] + 4.2
FLY0 = L[3] + 0.8
NFF = 14
FF = [(random.uniform(150, 880), random.uniform(760, 1380), random.uniform(0.5, 1.1), random.uniform(0, 6)) for _ in range(NFF)]
HEART_C = (520, 880)
def heart_pt(k):
    a = k / NFF * 2 * math.pi
    return HEART_C[0] + 15 * 16 * math.sin(a) ** 3, HEART_C[1] - 15 * (13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))

def ff_pos(k, t):
    bx, by, sp, off = FF[k]
    x = bx + math.sin(t * sp + off) * 60; y = by + math.cos(t * sp * 0.8 + off * 1.3) * 40
    if t > L[5]:
        hx, hy = heart_pt(k); q = ease((t - L[5]) / 1.8)
        x, y = lerp(x, hx + math.sin(t * 2 + k) * 6, q), lerp(y, hy + math.cos(t * 2 + k) * 6, q)
    return x, y

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

HIDE = (420, 1150)
def mochi_state(t, ph, lt):
    """returns x, bottom, expr, wing, behind_hana"""
    free = (600 + math.sin(t * 1.2) * 70, 1180 - abs(math.sin(t * 2)) * 18)
    if ph <= 0:
        return free[0], free[1], "happy", math.sin(t * 5) * 0.5, False
    if ph == 1:
        q = ease(lt / 0.8)
        x = lerp(free[0], HIDE[0], q) + (math.sin(t * 40) * 6 if lt > 0.8 else 0)
        return x, lerp(free[1], HIDE[1], q), "sad", -0.6, True
    if ph == 2:
        sh = math.sin(t * 40) * 6 * max(0, 1 - lt / 2.5)
        return HIDE[0] + sh, HIDE[1], "sad" if lt < 3.2 else "happy", -0.4 + 0.3 * math.sin(t * 2), True
    if ph == 3:
        q = ease((lt - 1.4) / 1.2)
        return lerp(HIDE[0], 600, q), lerp(HIDE[1], 1200, q), "happy" if lt < 2.6 else "joy", math.sin(t * 6) * 0.6, q < 0.5
    if ph == 4:
        q = ease(lt / 1.4); a = t * 1.4
        tx, ty = 540 + math.cos(a) * 170, 1020 + math.sin(a * 2) * 50
        return lerp(600, tx, q), lerp(1200, ty, q), "joy", math.sin(t * 10), False
    # ph 5, 6, outro: Mochi sits in the middle of the firefly heart, happy bounce
    st = L[5]; q = ease((t - st) / 1.4); a = t * 1.4
    fx, fy = 540 + math.cos(a) * 170, 1020 + math.sin(a * 2) * 50
    return lerp(fx, HEART_C[0], q), lerp(fy, HEART_C[1] + 120, q) - abs(math.sin(t * 3)) * 18, "joy", math.sin(t * 9), False

PREVIEW = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x]
FRAMES = [int(x * FPS) for x in PREVIEW] if PREVIEW else range(NFR)
proc = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in FRAMES:
    t = fi / FPS
    i, lt = line_at(t)
    ph = 7 if t >= T_OUTRO else (-1 if i is None else i)
    n = ease((t - NIGHT0) / (NIGHT1 - NIGHT0))
    im = Image.blend(SKY_DUSK, SKY_NIGHT, n) if 0 < n < 1 else (SKY_NIGHT.copy() if n >= 1 else SKY_DUSK.copy())
    d = ImageDraw.Draw(im)
    # setting sun (before night) sinks behind the hills
    if n < 1:
        sy = lerp(760, 1090, ease((t - 0.5) / (NIGHT1 - 0.5)))
        put_glow(im, 300, sy, 210, (255, 225, 170), 0.7 * (1 - n))
        d = ImageDraw.Draw(im); d.ellipse([300 - 80, sy - 80, 300 + 80, sy + 80], fill=(255, 205, 140))
    # twinkling stars
    if n > 0:
        for sx, sy, r, off in STARS:
            tw = 0.55 + 0.45 * math.sin(t * 2.5 + off)
            star4(d, sx, sy, r * tw, (255, 248, 210, int(230 * n * tw)))
    # moon rises during Mochi's line 5
    if t > L[4] - 0.2:
        q = ease((t - (L[4] - 0.2)) / 2.2)
        my = lerp(MOON_Y0, MOON_Y1, q)
        put_glow(im, MOON_X, my, 210, (255, 245, 200), 0.55 * q)
        paste_c(im, moon(t > L[4] + 2.3), MOON_X, my)
    im.alpha_composite(LAND_NIGHT if n >= 1 else (LAND_DAY if n <= 0 else Image.blend(LAND_DAY, LAND_NIGHT, n)))
    d = ImageDraw.Draw(im)

    # ---- Owlbert on the mushroom ----
    om, ob = talking("Professor Owlbert", t)
    owing = 0.0
    if ph == 3: owing = (math.sin(t * 5) + 1) / 2 * 0.7
    if ph >= 5: owing = (math.sin(t * 4) + 1) / 2 * 0.4
    shadow(im, OX, OB - 4, 0.8)
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob)

    # ---- Mochi + Hana ----
    hm, hb = talking("Hana", t)
    mm, mb = talking("Mochi", t)
    mx, mbot, mexpr, mwing, behind = mochi_state(t, ph, lt)
    msc = 0.8
    if ph == 2 and 0.8 < lt < 4.8:       # deep breath: puff up, then out
        msc = 0.8 + 0.06 * math.sin((lt - 0.8) / 4.0 * 2 * math.pi - math.pi / 2) + 0.06
    msp = mochi(mm, round(mwing * 4) / 4, mexpr, blinking(t, 2.3) and mexpr != "joy")
    def draw_mochi():
        paste(im, msp, mx, mbot - mb, msc, msc)
    if behind: draw_mochi()
    harms = ph in (5,) or ph >= 7 or (ph == 6 and lt < 1.0)
    hop = abs(math.sin(t * 6)) * 14 if harms else 0
    if ph == 2: hop = abs(math.sin(t * 3)) * 4
    shadow(im, HX, HB - 4, 0.75)
    paste(im, hana(hm, harms, blinking(t, 0.0)), HX, HB - hb - hop, 0.9, 0.9)
    if not behind: draw_mochi()
    d = ImageDraw.Draw(im)
    # scared wobble lines next to Mochi
    if ph == 1 and lt > 0.8:
        for k in range(3):
            y = mbot - 210 + k * 30
            d.arc([mx + 105, y, mx + 135, y + 26], 280, 80, fill=(200, 210, 255), width=5)
    # breathing ring (Hana + Mochi breathe together)
    if ph == 2 and 0.8 < lt < 4.8:
        q = (lt - 0.8) / 4.0
        r = 120 + 90 * math.sin(q * math.pi)
        cx_, cy_ = 400, 1300
        d.ellipse([cx_ - r * 1.5, cy_ - r, cx_ + r * 1.5, cy_ + r], outline=(255, 235, 170, 200), width=8)
        f = font(72); lab = "breathe in..." if q < 0.5 else "and out..."
        w_ = d.textlength(lab, font=f)
        d.text((540 - w_ / 2 + 3, 653), lab, font=f, fill=(40, 40, 90))
        d.text((540 - w_ / 2, 650), lab, font=f, fill=(255, 240, 190))
    # fireflies
    if t > FLY0:
        for k in range(NFF):
            a0 = FLY0 + k * 0.22
            if t < a0: continue
            vis = ease((t - a0) / 0.5)
            x, y = ff_pos(k, t)
            tw = 0.7 + 0.3 * math.sin(t * 6 + k)
            put_glow(im, x, y, 64, (255, 240, 130), 0.85 * vis * tw)
            d = ImageDraw.Draw(im)
            d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(255, 250, 200, int(255 * vis)))
    if ph >= 6:
        for k in range(5):
            q = ((t - L[6]) * 0.4 + k / 5) % 1
            heart(d, 450 + k * 50 + math.sin(t * 2 + k) * 20, 1330 - q * 260, 18 + 5 * (k % 2), (255, 150, 190, int(230 * (1 - q))))

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "Mochi and the Dark", 88, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (130, 180, 240), "You can be brave too!", 92, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original slow lullaby in G major (4/4), music box + soft pad ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "pluck": w = w + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt)
    if shape == "box": w = w + 0.35 * np.sin(2 * np.pi * freq * 3.01 * tt) * np.exp(-6 * tt) + 0.15 * np.sin(2 * np.pi * freq * 6.2 * tt) * np.exp(-10 * tt)
    if shape == "bell": w = w + 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 4.02 * tt)
    if shape == "pad": w = w + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt); env = np.minimum(1, tt * 1.5) * np.minimum(1, (dur - tt) * 1.5)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at, buf=None):
    buf = audio if buf is None else buf
    i0 = int(at * SR)
    if i0 >= N: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
mel = [67, 71, 74, 71,  72, 76, 74, None,  71, 69, 67, 69,  71, None, None, None,
       72, 71, 69, 67,  69, 71, 74, None,  72, 71, 69, 71,  67, None, None, None]
chords = [(55, 59, 62), (48, 52, 55), (52, 55, 59), (55, 59, 62), (48, 52, 55), (50, 54, 57), (45, 48, 52), (55, 59, 62)]
q4 = 0.52; music = np.zeros(N); k = 0
while k * q4 < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 1.4, 0.05, "box", 3.0), k * q4, music)
    bar = k // 4; ch = chords[bar % len(chords)]
    if k % 4 == 0:
        for n_ in ch: add(tone(f(n_), q4 * 4, 0.018, "pad"), k * q4, music)
        add(tone(f(ch[0] - 12), 1.0, 0.03, "pluck", 4), k * q4, music)
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
for j, m in enumerate([79, 76, 72, 67]): add(tone(f(m), 1.0, 0.07, "bell", 3), 0.1 + j * 0.18)          # title
for j, m in enumerate([74, 71, 67, 62]): add(tone(f(m), 1.2, 0.05, "bell", 2.5), NIGHT0 + j * 0.6)      # sun sets
for j in range(5): add(tone(f(64 + (j % 2)), 0.15, 0.03, "sine", 15), L[1] + 1.0 + j * 0.12)           # wobble
br = np.random.default_rng(3).standard_normal(int(4.0 * SR)); br = np.convolve(br, np.ones(60) / 60, mode="same")
env = np.sin(np.linspace(0, np.pi, len(br))) ** 2; add(br * env * 0.04, L[2] + 0.8)                     # soft breath
for k_ in range(NFF): add(tone(f([84, 86, 88, 91][k_ % 4]), 0.5, 0.035, "bell", 6), FLY0 + k_ * 0.22)  # fireflies
for j, m in enumerate([67, 71, 74, 79, 83]): add(tone(f(m), 1.4, 0.06, "bell", 2.5), L[4] - 0.1 + j * 0.3)  # moon
for j, m in enumerate([79, 83, 86, 91]): add(tone(f(m), 1.0, 0.06, "bell", 3), L[5] + 0.2 + j * 0.16)
for j, m in enumerate([72, 76, 79, 84, 88]): add(tone(f(m), 1.4, 0.07, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
