"""Petal Valley (Anime Adventures): The lost baby star — lesson: helping others.
Original characters, art and music. Renders kids/lost_baby_star.mp4 (no voice, captions + music)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/lost_baby_star.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(71)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "One quiet evening, something tiny and shiny fell into Petal Valley."),
    ("Hana", "Look! A little baby star! Why are you crying, little star?"),
    ("Mochi", "I think she is lost! Her star family is way up in the sky."),
    ("Professor Owlbert", "Let's help her get home. Mochi, you can fly up high!"),
    ("Hana", "And I will hold my lantern, so we can see the way."),
    ("Mochi", "Up, up, up we go! Look, little star, there is your family!"),
    ("Narrator", "The baby star was home and happy. When someone needs help, we can help too!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.4, 4.4
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


# ---------- baby star (original) ----------
def star_pts(cx, cy, R, r, rot=-90):
    pts = []
    for k in range(10):
        a = math.radians(rot + k * 36); rr = R if k % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts

@lru_cache(None)
def star_sprite(size, mood, blink, col=(255, 228, 120)):
    """mood: sad / happy / joy. size = outer radius."""
    R = size; p = P(int(R * 2.4), int(R * 2.4)); c = R * 1.2
    edge = tuple(max(0, v - 60) for v in col)
    p.poly(star_pts(c, c + R * 0.06, R, R * 0.52), col, edge, max(3, R / 18))
    p.poly(star_pts(c - R * 0.12, c - R * 0.1, R * 0.45, R * 0.24), tuple(min(255, v + 25) for v in col))
    ew, eh = R * 0.28, R * 0.36; ey = c + R * 0.05
    if mood == "joy":
        eye(p, c - R * 0.22, ey, ew, eh, (230, 150, 60), happy=True); eye(p, c + R * 0.22, ey, ew, eh, (230, 150, 60), happy=True)
    else:
        eye(p, c - R * 0.22, ey, ew, eh, (230, 150, 60), blink); eye(p, c + R * 0.22, ey, ew, eh, (230, 150, 60), blink)
    for sgn in (-1, 1): p.ell(c + sgn * R * 0.42 - R * 0.1, ey + R * 0.18, c + sgn * R * 0.42 + R * 0.1, ey + R * 0.27, (255, 165, 150))
    if mood == "sad":
        p.arc(c - R * 0.12, ey + R * 0.26, c + R * 0.12, ey + R * 0.44, 200, 340, (150, 90, 70), max(2, R / 22))
        for sgn in (-1, 1): p.ell(c + sgn * R * 0.3 - R * 0.05, ey + R * 0.2, c + sgn * R * 0.3 + R * 0.05, ey + R * 0.36, (150, 210, 255))
    else:
        p.arc(c - R * 0.13, ey + R * 0.12, c + R * 0.13, ey + R * 0.36, 20, 160, (150, 90, 70), max(2, R / 22))
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

@lru_cache(None)
def lantern():
    p = P(90, 150)
    p.line([(45, 4), (45, 30)], (120, 95, 140), 5)
    p.rrect(20, 26, 70, 40, 6, (190, 150, 220), LINE, 3)
    p.rrect(14, 38, 76, 120, 22, (255, 225, 150), LINE, 4)
    p.ell(28, 55, 62, 110, (255, 245, 205))
    p.rrect(20, 116, 70, 130, 6, (190, 150, 220), LINE, 3)
    return p.done()

# ---------- night background ----------
def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, 3))
    for c in range(3): arr[:, c] = np.interp(ys, [s for s, _ in stops], [col[c] for _, col in stops])
    return Image.fromarray(np.repeat(arr.astype(np.uint8)[:, None, :], w, axis=1))

def make_bg():
    bg = vgrad(W, H, [(0, (90, 80, 160)), (0.35, (140, 120, 200)), (0.6, (205, 170, 215)), (1, (205, 170, 215))]).convert("RGBA")
    t = P(W, H)
    # crescent moon (top-left, below caption area)
    t.circ(150, 760, 66, (255, 246, 210)); t.circ(185, 740, 58, (132, 115, 195))
    t.circ(130, 780, 7, (240, 228, 190))
    bg.alpha_composite(t.done())
    d = ImageDraw.Draw(bg)
    # distant hills
    d.ellipse([-400, 1130, 650, 1620], fill=(150, 150, 205)); d.ellipse([400, 1090, 1500, 1620], fill=(135, 140, 200))
    # little glowing cottage windows on hills
    for x, y in ((180, 1175), (880, 1150)):
        d.polygon([(x - 34, y), (x, y - 30), (x + 34, y)], fill=(170, 120, 170))
        d.rectangle([x - 26, y, x + 26, y + 38], fill=(215, 190, 225)); d.rectangle([x - 9, y + 10, x + 9, y + 26], fill=(255, 230, 150))
    # meadow
    d.ellipse([-600, 1270, 1700, 2300], fill=(135, 185, 175)); d.rectangle([0, 1500, W, H], fill=(135, 185, 175))
    d.ellipse([-300, 1430, 1400, 2600], fill=(125, 175, 168))
    rnd = random.Random(12)
    for _ in range(110):
        x, y = rnd.randint(10, W - 10), rnd.randint(1340, 1900)
        c = rnd.choice([(235, 225, 255), (255, 205, 230), (200, 225, 255), (250, 240, 200)])
        r = 4 + (y - 1340) / 100
        for k in range(4):
            a = k * math.pi / 2 + 0.4
            d.ellipse([x + math.cos(a) * r - r * 0.6, y + math.sin(a) * r - r * 0.6, x + math.cos(a) * r + r * 0.6, y + math.sin(a) * r + r * 0.6], fill=c)
        d.ellipse([x - r * 0.4, y - r * 0.4, x + r * 0.4, y + r * 0.4], fill=(255, 220, 140))
    # mossy rock for Owlbert
    t = P(W, H)
    t.poly([(672, 1490), (690, 1395), (740, 1345), (820, 1332), (890, 1348), (925, 1400), (935, 1490)], (165, 160, 195), LINE, 4)
    t.poly([(700, 1400), (745, 1352), (820, 1340), (885, 1356), (915, 1398), (860, 1385), (800, 1392), (745, 1388)], (160, 210, 175))
    t.ell(700, 1470, 930, 1500, (150, 145, 185))
    t.circ(760, 1440, 12, (190, 185, 215)); t.circ(880, 1445, 9, (190, 185, 215))
    bg.alpha_composite(t.done())
    return bg

BG = make_bg()
SKY_STARS = [(random.uniform(40, 900), random.uniform(560, 1080), random.uniform(2, 5), random.uniform(0, 6)) for _ in range(55)]
FIREFLIES = [(random.uniform(40, 900), random.uniform(1150, 1500), random.uniform(0, 6), random.uniform(0.5, 1.2)) for _ in range(14)]

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

HX, HB = 225, 1492
MX0, MB0 = 585, 1500
OX, OB = 812, 1352
SX0, SY0 = 410, 1415           # baby star resting spot
FAM = [(320, 820, 78), (770, 805, 86)]   # star family (x, y, radius)
HOME = (545, 900)

L = [ln[2] for ln in LINES]

def mochi_state(t):
    i, lt = line_at(t)
    x, b = MX0, MB0; wing = math.sin(t * 5) * 0.4; expr = "happy"
    if t >= T_OUTRO: i, lt = 7, t - T_OUTRO
    if i is None or i <= 1:
        b -= abs(math.sin(t * 3)) * 10
        if i == 1: expr = "wow"
    elif i in (2, 3, 4):
        b -= abs(math.sin(t * 4)) * 12; wing = math.sin(t * 7) * 0.6
        if i == 3 and lt > 3.0: wing = math.sin(t * 12); b -= 20
    elif i == 5:
        wing = math.sin(t * 16)
        k1 = ease(lt / 1.3)            # hop over to the star
        k2 = ease((lt - 1.3) / 3.2)    # fly up
        x = lerp(MX0, SX0 + 20, k1) + lerp(0, HOME[0] - SX0 - 20, k2)
        b = lerp(MB0, SY0 + 60, k1) - 20 * math.sin(k1 * math.pi) + lerp(0, 1110 - SY0 - 60, k2) + math.sin(t * 3) * 8 * k2
        expr = "joy" if lt > 4.5 else "happy"
    else:  # narrator end + outro: drift down a bit, float
        tt = t - L[6]; k = ease(tt / 2.0)
        x = HOME[0] + 20 * math.sin(t * 1.5); b = lerp(1110, 1270, k) + math.sin(t * 3) * 10
        wing = math.sin(t * 10); expr = "joy"
    return x, b, wing, expr

def star_state(t):
    """returns x, y, size, mood, glow_strength"""
    i, lt = line_at(t)
    if t < INTRO: return None
    if i == 0:
        if lt < 0.6: return None
        k = min(1, (lt - 0.6) / 2.2)
        x = lerp(760, SX0, ease(k)); y = lerp(760, SY0, k * k)
        if k >= 1:
            q = lt - 2.8; y -= abs(math.sin(q * 6)) * 30 * math.exp(-q * 3)
        return x, y, 60, "sad", 0.8
    if i in (1, 2):
        return SX0, SY0 + math.sin(t * 2) * 3, 60, "sad", 0.6 + 0.1 * math.sin(t * 4)
    if i in (3, 4):
        return SX0, SY0 - abs(math.sin(t * 3)) * 10, 60, "happy", 0.8
    mx, mb, _, _ = mochi_state(t)
    if i == 5:
        if lt < 1.3: return SX0, SY0, 60, "happy", 0.8
        return mx, mb + 10, 60, ("joy" if lt > 4.5 else "happy"), 1.0
    # line 6 + outro: float from under Mochi up to home spot between family
    tt = t - L[6]; k = ease(tt / 2.2)
    sx = lerp(HOME[0] + 20 * math.sin(L[6] * 1.5), HOME[0], k)
    sy = lerp(1150, HOME[1], k) + math.sin(t * 2) * 6
    return sx, sy, 60 + 6 * k, "joy", 1.0

# ---------- render ----------
PREVIEW = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x]
FRAMES = [int(x * FPS) for x in PREVIEW] if PREVIEW else range(NFR)
proc = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

for fi in FRAMES:
    t = fi / FPS
    im = BG.copy()
    i, lt = line_at(t)
    d = ImageDraw.Draw(im)
    # twinkling sky stars
    for x, y, r, ph in SKY_STARS:
        a = 0.5 + 0.5 * math.sin(t * 2.2 + ph)
        rr = r * (0.7 + 0.5 * a)
        d.polygon([(x, y - rr * 2), (x + rr * 0.5, y - rr * 0.5), (x + rr * 2, y), (x + rr * 0.5, y + rr * 0.5),
                   (x, y + rr * 2), (x - rr * 0.5, y + rr * 0.5), (x - rr * 2, y), (x - rr * 0.5, y - rr * 0.5)],
                  fill=(255, 250, 220, int(120 + 135 * a)))
    # star family: dim & sleepy-looking until Mochi flies up, then glowing
    fam_k = 0.35
    if i is not None and i >= 5: fam_k = 0.35 + 0.65 * ease((lt - 2.0) / 2.0) if i == 5 else 1.0
    if t >= T_OUTRO: fam_k = 1.0
    for j, (fx, fy, fr) in enumerate(FAM):
        put_glow(im, fx, fy, int(fr * 2.2), (255, 240, 170), fam_k * 0.8)
        mood = "joy" if fam_k > 0.9 and (i == 6 or t >= T_OUTRO) else "happy"
        sp = star_sprite(fr, mood, blinking(t, 0.7 + j))
        if fam_k < 1:
            a = np.array(sp); a[:, :, 3] = (a[:, :, 3] * (0.35 + 0.65 * fam_k)).astype(np.uint8); sp = Image.fromarray(a)
        paste_c(im, sp, fx, fy + math.sin(t * 2 + j) * 6)
    # fireflies
    d = ImageDraw.Draw(im)
    for x, y, ph, sp in FIREFLIES:
        fx = x + math.sin(t * sp + ph) * 50; fy = y + math.cos(t * sp * 0.8 + ph) * 35
        a = 0.5 + 0.5 * math.sin(t * 3 * sp + ph)
        put_glow(im, fx, fy, 22, (230, 255, 170), round(a * 0.7, 1))
    # Owlbert
    om, ob = talking("Professor Owlbert", t)
    owing = 0.0
    if i == 3 and lt > 3.0: owing = (math.sin(t * 9) + 1) / 2
    if i == 6 or t >= T_OUTRO: owing = (math.sin(t * 6) + 1) / 2 * 0.5
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob)
    # Hana (+ lantern from line 4)
    hm, hb = talking("Hana", t)
    arms = (i == 6) or (t >= T_OUTRO)
    hop = abs(math.sin(t * 6)) * 14 if (i == 6 or t >= T_OUTRO) else 0
    hbot = HB + 8 - hb - hop
    shadow(im, HX, HB - 4, 0.8)
    paste(im, hana(hm, arms, blinking(t, 0.0)), HX, hbot)
    show_lantern = (i is not None and i >= 4 and not (i == 4 and lt < 0.8)) or t >= T_OUTRO
    if show_lantern:
        if arms: lx, ly = HX + 120, hbot - 620 + 330
        else: lx, ly = HX + 88, hbot - 620 + 505
        sw = math.sin(t * 2.5) * 4
        lamp_k = ease((lt - 0.8) / 0.6) if i == 4 else 1
        put_glow(im, lx + sw, ly + 80, 150, (255, 220, 140), round(0.75 * lamp_k, 2))
        paste(im, lantern(), lx + sw, ly + 145)
    # baby star
    st = star_state(t)
    mx, mb, wing, expr = mochi_state(t)
    carrying = i == 5 and lt >= 1.3
    if st and not carrying:
        sx, sy, sr, mood, gs = st
        put_glow(im, sx, sy, int(sr * 2.6), (255, 235, 150), round(gs * 0.9, 1))
        if i == 0 and lt < 2.8:  # falling trail
            dd = ImageDraw.Draw(im)
            for q in range(1, 6):
                k = max(0, (lt - 0.6) / 2.2 - q * 0.04)
                tx = lerp(760, SX0, ease(k)); ty = lerp(760, SY0, k * k)
                dd.ellipse([tx - 12 + q, ty - 12 + q, tx + 12 - q, ty + 12 - q], fill=(255, 245, 190, 200 - q * 35))
        paste_c(im, star_sprite(sr, mood, blinking(t, 2.0) and mood != "joy"), sx, sy)
    # Mochi
    mm, mbb = talking("Mochi", t)
    shadow(im, mx, MB0 - 6, max(0.3, 0.9 - (MB0 - mb) / 900))
    paste(im, mochi(mm, round(wing * 4) / 4, expr, blinking(t, 2.3) and expr != "joy"), mx, mb + 50 - mbb)
    if carrying and st:
        sx, sy, sr, mood, gs = st
        put_glow(im, sx, sy + 20, int(sr * 2.6), (255, 235, 150), 0.9)
        paste_c(im, star_sprite(sr, mood, False), sx, sy + 20 - mbb)
    # sparkles when star is home
    if i == 6 or t >= T_OUTRO:
        dd = ImageDraw.Draw(im)
        for k in range(8):
            ph = (t * 0.8 + k / 8) % 1; ang = k * math.pi / 4 + t * 0.6
            rr = 70 + 110 * ph
            x = HOME[0] + rr * math.cos(ang); y = HOME[1] + rr * math.sin(ang) * 0.7
            r = 16 * (1 - ph) + 4
            dd.polygon([(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3), (x, y + r),
                        (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)], fill=(255, 245, 170, int(255 * (1 - ph))))
    # captions
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "The Lost Baby Star", 80, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (130, 170, 230), "We help each other!", 104, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio (original music-box lullaby in G, 4/4) ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "bell": w = w + 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 4.02 * tt)
    if shape == "pad": w = w + 0.25 * np.sin(2 * np.pi * freq * 1.502 * tt); env = np.minimum(1, tt * 3) * np.minimum(1, (dur - tt) * 3)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at, buf=None):
    buf = audio if buf is None else buf
    i0 = int(at * SR)
    if i0 >= N: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]

f = lambda m: 440 * 2 ** ((m - 69) / 12)
G = {"G3": 55, "C3": 48, "D3": 50, "E3": 52, "B3": 59, "D4": 62, "E4": 64, "G4": 67, "A4": 69, "B4": 71, "C5": 72, "D5": 74, "E5": 76, "G5": 79}
mel = ["B4", "D5", "G4", None, "A4", "B4", "E4", None, "C5", "B4", "A4", "G4", "A4", None, "D4", None,
       "B4", "D5", "E5", "D5", "C5", "E5", "B4", None, "A4", "G4", "A4", "B4", "G4", None, None, None]
chords = [("G3", "D4"), ("E3", "B3"), ("C3", "G3"), ("D3", "A4"), ("G3", "D4"), ("C3", "G3"), ("D3", "A4"), ("G3", "D4")]
beat = 0.5; music = np.zeros(N); k = 0
while k * beat < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(G[m]), 1.2, 0.065, "bell", 3.2), k * beat, music)
    if k % 4 == 0:
        c = chords[(k // 4) % len(chords)]
        add(tone(f(G[c[0]]), beat * 4, 0.05, "pad"), k * beat, music)
    if k % 2 == 1:
        c = chords[(k // 4) % len(chords)]
        add(tone(f(G[c[1]]) * 2, 0.6, 0.025, "bell", 5), k * beat, music)
    k += 1
duck = np.ones(N)
for spk, txt, st, dur, talk in LINES:
    a, b_ = int((st + 0.2) * SR), int((st + 0.4 + talk) * SR); duck[a:b_] = 0.6
duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
audio += music * duck
base = {"Hana": 620, "Mochi": 820, "Professor Owlbert": 330}
rnd = random.Random(4)
for spk, txt, st, dur, talk in LINES:
    if spk not in base: continue
    tt = st + 0.3
    while tt < st + 0.3 + talk:
        add(tone(base[spk] * rnd.choice([1, 1.12, 1.25, 0.9]), 0.09, 0.033, "sine", 25), tt); tt += 0.286
# sfx
add(tone(784, 0.8, 0.13, "bell", 3), 0.1); add(tone(1174.7, 1.0, 0.13, "bell", 3), 0.5)
for j in range(8): add(tone(f(91 - j * 2), 0.5, 0.07, "bell", 6), L[0] + 0.6 + j * 0.25)   # falling glissando
add(tone(f(67), 0.6, 0.12, "bell", 5), L[0] + 2.85)
for j, m in enumerate([67, 71, 74, 79]): add(tone(f(m), 0.9, 0.08, "bell", 4), L[4] + 0.8 + j * 0.1)  # lantern on
for j in range(10): add(tone(f(67 + j * 2 + (j // 3)), 0.8, 0.07, "bell", 4), L[5] + 1.3 + j * 0.32)  # flying up
for j, m in enumerate([79, 83, 86, 91]): add(tone(f(m), 1.2, 0.1, "bell", 3), L[6] + 1.8 + j * 0.15)
for j, m in enumerate([67, 71, 74, 79, 83]): add(tone(f(m), 1.4, 0.1, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
