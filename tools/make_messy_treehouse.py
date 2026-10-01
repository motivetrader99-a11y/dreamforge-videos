"""Petal Valley (Anime Adventures): The messy treehouse — lesson: tidying up.
Original characters, art and music. Renders kids/messy_treehouse_tidy_up.mp4 (captions + music, no voice).
Character designs match make_waiting_turn_on_swing.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/messy_treehouse_tidy_up.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(5150)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "Hana and Mochi played all morning in their cozy treehouse."),
    ("Mochi", "Oh no! Toys everywhere! Where is my teddy?"),
    ("Hana", "It's so messy! I can't find anything!"),
    ("Professor Owlbert", "Let's tidy up together. Every toy has a home!"),
    ("Hana", "Blocks and ball go in the box. Books go on the shelf!"),
    ("Mochi", "Look! I found my teddy! Tidying is fun!"),
    ("Narrator", "When we tidy up, we can find our things. Let's tidy up!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.4, 4.6
LINES, t = [], INTRO
for spk, txt in SCRIPT:
    words = len(txt.split())
    talk = words * 0.34 + 0.4
    dur = max(5.2, talk + 1.8)
    if "shelf" in txt: dur = talk + 3.2
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

# ================= cozy treehouse interior (new for this episode) =================
def fx_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def star4(d, x, y, r, col):
    d.polygon([(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y), (x + r * 0.28, y + r * 0.28),
               (x, y + r), (x - r * 0.28, y + r * 0.28), (x - r, y), (x - r * 0.28, y - r * 0.28)], fill=col)

FLOOR_Y = 1220
WIN_X, WIN_Y, WIN_R = 700, 800, 150
SHELF_Y = 930
BOX_X0, BOX_X1, BOX_TOP, BOX_BOT = 420, 660, 1225, 1360

def make_room():
    base = vgrad(W, H, [(0, (255, 232, 206)), (0.6, (248, 214, 186)), (0.635, (230, 190, 155)), (1, (240, 205, 170))]).convert("RGBA")
    t = P(W, H)
    # vertical wall planks
    for x in range(60, W, 130):
        t.line([(x, 0), (x, FLOOR_Y)], (238, 200, 170), 4)
        for y in (300 + (x % 3) * 160, 820 + (x % 2) * 180):
            t.circ(x + 30, y, 5, (228, 188, 158))
    # floor planks
    t.rrect(-10, FLOOR_Y - 14, W + 10, FLOOR_Y + 10, 4, (205, 160, 125), LINE, 3)
    for k, y in enumerate(range(FLOOR_Y + 70, H, 85)):
        t.line([(0, y), (W, y)], (225, 185, 150), 4)
        for x in range(80 + (k % 2) * 140, W, 280): t.line([(x, y - 85), (x, y)], (225, 185, 150), 3)
    # round window with sky + leaves
    t.circ(WIN_X, WIN_Y, WIN_R + 22, (200, 150, 115), LINE, 4)
    im = t.done(); base.alpha_composite(im)
    sky = vgrad(2 * WIN_R, 2 * WIN_R, [(0, (175, 220, 250)), (1, (225, 242, 255))]).convert("RGBA")
    m = Image.new("L", sky.size, 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * WIN_R - 1, 2 * WIN_R - 1], fill=255)
    sd = ImageDraw.Draw(sky)
    for x, y, r in ((40, 60, 55), (90, 25, 45), (260, 50, 60), (230, 0, 50)):
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(170, 220, 160))
    for x, y, r in ((150, 210, 30), (190, 200, 24), (115, 205, 22)):
        sd.ellipse([x - r, y - r * 0.7, x + r, y + r * 0.7], fill=(255, 255, 255))
    base.paste(sky, (WIN_X - WIN_R, WIN_Y - WIN_R), m)
    t = P(W, H)
    t.line([(WIN_X, WIN_Y - WIN_R), (WIN_X, WIN_Y + WIN_R)], (200, 150, 115), 12)
    t.line([(WIN_X - WIN_R, WIN_Y), (WIN_X + WIN_R, WIN_Y)], (200, 150, 115), 12)
    t.circ(WIN_X, WIN_Y, WIN_R + 2, None, (200, 150, 115), 10)
    t.rrect(WIN_X - 175, WIN_Y + WIN_R - 4, WIN_X + 175, WIN_Y + WIN_R + 28, 10, (215, 168, 130), LINE, 4)
    # shelf on left wall + brackets + little plant
    t.rrect(60, SHELF_Y, 430, SHELF_Y + 26, 8, (215, 168, 130), LINE, 4)
    for x in (110, 380): t.poly([(x - 10, SHELF_Y + 26), (x + 10, SHELF_Y + 26), (x, SHELF_Y + 80)], (200, 150, 115), LINE, 3)
    t.poly([(345, SHELF_Y), (415, SHELF_Y), (405, SHELF_Y - 60), (355, SHELF_Y - 60)], (255, 175, 160), LINE, 3)
    for a in (-0.6, 0, 0.6):
        t.ell(380 + math.sin(a) * 40 - 18, SHELF_Y - 120 + abs(a) * 30, 380 + math.sin(a) * 40 + 18, SHELF_Y - 60, (140, 205, 140), LINE, 3)
    # framed drawing on wall (a sun) between shelf and window
    t.rrect(200, 640, 400, 800, 12, (255, 250, 240), (200, 150, 115), 8)
    t.circ(300, 720, 36, (255, 215, 110))
    for k in range(8):
        a = k * math.pi / 4; t.line([(300 + math.cos(a) * 48, 720 + math.sin(a) * 48), (300 + math.cos(a) * 62, 720 + math.sin(a) * 62)], (255, 200, 90), 6)
    # round rug
    t.ell(150, 1340, 990, 1600, (255, 205, 220), LINE, 3)
    t.ell(220, 1370, 920, 1570, (255, 225, 235))
    t.ell(330, 1410, 810, 1530, (250, 210, 225))
    base.alpha_composite(t.done())
    return base
ROOM = make_room()

@lru_cache(None)
def box_back():
    p = P(W, 260); y0 = BOX_TOP - 160
    p.poly([(BOX_X0 + 10, 160 - 10), (BOX_X1 - 10, 160 - 10), (BOX_X1 - 30, 40), (BOX_X0 + 30, 40)], (160, 225, 205), LINE, 4)  # open lid
    p.rrect(BOX_X0 + 60, 70, BOX_X1 - 60, 110, 12, (200, 240, 225))
    p.rrect(BOX_X0, 140, BOX_X1, 180, 10, (110, 150, 140))   # dark inside
    return p.done()
@lru_cache(None)
def box_front():
    p = P(260, 150)
    p.rrect(4, 4, 256, 146, 18, (175, 232, 212), LINE, 5)
    p.rrect(4, 4, 256, 26, 10, (150, 215, 195), LINE, 4)
    cx, cy, r = 130, 82, 38
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    p.poly(pts, (255, 220, 120), LINE, 3)
    return p.done()

@lru_cache(None)
def block(col, letter):
    p = P(76, 76)
    p.rrect(3, 3, 73, 73, 12, col, LINE, 4)
    p.rrect(12, 12, 64, 64, 8, tuple(min(255, c + 35) for c in col))
    im = p.done(); d = ImageDraw.Draw(im); f = font(40); w_ = d.textlength(letter, font=f)
    d.text((38 - w_ / 2, 8), letter, font=f, fill=WHITE, stroke_width=3, stroke_fill=LINE)
    return im
@lru_cache(None)
def ball():
    p = P(96, 96)
    p.circ(48, 48, 44, (255, 245, 250), LINE, 4)
    p.chord(6, 6, 90, 90, 200, 340, (255, 160, 190)); p.chord(6, 6, 90, 90, 20, 160, (170, 200, 255))
    p.circ(48, 48, 44, None, LINE, 4); p.circ(34, 30, 9, WHITE)
    return p.done()
@lru_cache(None)
def book(col):
    p = P(160, 44)
    p.rrect(3, 3, 157, 41, 8, col, LINE, 4)
    p.rrect(140, 8, 154, 36, 4, (255, 250, 240))
    p.line([(20, 22), (110, 22)], tuple(max(0, c - 40) for c in col), 4)
    return p.done()
@lru_cache(None)
def teddy():
    p = P(130, 140)
    TB, TL = (245, 195, 150), (255, 230, 205)
    for sgn in (-1, 1):
        p.circ(65 + sgn * 34, 26, 18, TB, LINE, 3); p.circ(65 + sgn * 34, 26, 9, (255, 190, 200))
        p.circ(65 + sgn * 42, 98, 18, TB, LINE, 3)            # arms
        p.ell(65 + sgn * 26 - 20, 112, 65 + sgn * 26 + 20, 138, TB, LINE, 3)  # feet
    p.ell(30, 76, 100, 134, TB, LINE, 3); p.ell(46, 92, 84, 128, TL)
    p.circ(65, 52, 38, TB, LINE, 3)
    p.ell(48, 56, 82, 80, TL)
    p.circ(52, 46, 5, (60, 40, 75)); p.circ(78, 46, 5, (60, 40, 75))
    p.circ(65, 60, 5, (120, 70, 80)); p.arc(58, 60, 72, 72, 20, 160, (120, 70, 80), 3)
    for bx in (42, 88): p.ell(bx - 8, 56, bx + 8, 64, (255, 170, 190))
    p.rrect(44, 84, 86, 94, 5, (170, 205, 255))   # little blue ribbon
    return p.done()

BOOK_COLS = [(255, 170, 160), (170, 210, 250), (200, 185, 245)]
# each toy: kind, sprite-key, messy pos (cx, cy, rot), tidy pos (cx, cy, rot, scale), dest
TOYS = [
    ("block", ((255, 150, 150), "A"), (440, 1520, 15), (470, 1212, 0, 0.8), "box"),
    ("block", ((255, 205, 110), "B"), (690, 1540, -12), (535, 1206, 8, 0.8), "box"),
    ("block", ((150, 200, 245), "C"), (875, 1500, 20), (600, 1212, -6, 0.8), "box"),
    ("ball", None, (800, 1420, 0), (560, 1180, 0, 0.75), "box"),
    ("book", BOOK_COLS[0], (565, 1505, 6), (120, SHELF_Y - 80, 90, 1.0), "shelf"),
    ("book", BOOK_COLS[1], (555, 1468, -4), (170, SHELF_Y - 80, 90, 1.0), "shelf"),
    ("book", BOOK_COLS[2], (570, 1431, 3), (220, SHELF_Y - 80, 90, 1.0), "shelf"),
]
def toy_sprite(kind, key):
    if kind == "block": return block(*key)
    if kind == "ball": return ball()
    return book(key)
@lru_cache(None)
def rot_sprite(kind, key, ang, sc):
    sp = toy_sprite(kind, key)
    if sc != 1: sp = sp.resize((max(2, int(sp.width * sc)), max(2, int(sp.height * sc))), Image.LANCZOS)
    return sp.rotate(ang, resample=Image.BICUBIC, expand=True) if ang else sp

L = [ln[2] for ln in LINES]
TIDY_T0 = L[4] + 0.6; TIDY_STEP = 0.56; FLY = 0.8
TEDDY_T0 = L[5] + 0.2
HX, HB, HS = 205, 1560, 0.8
MX, MB, MS = 805, 1300, 0.72
OX, OB, OS = WIN_X, WIN_Y + WIN_R - 2, 0.62

def toy_state(k, t):
    kind, key, (mx_, my_, mr), (tx_, ty_, tr, ts), dest = TOYS[k]
    st = TIDY_T0 + k * TIDY_STEP
    q = 0 if t < st else min(1, (t - st) / FLY)
    e = ease(q)
    x = lerp(mx_, tx_, e); y = lerp(my_, ty_, e) - math.sin(q * math.pi) * (260 if dest == "box" else 340)
    r = lerp(mr, tr, e) + (math.sin(q * math.pi) * 180 if kind == "block" else 0)
    s = lerp(1.0, ts, e)
    return x, y, round(r / 3) * 3, round(s * 20) / 20, q

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

def string_lights(d, t):
    pts = []
    for k in range(41):
        x = -20 + k * 28; sag = 70 * (1 - ((x - 540) / 560) ** 2)
        pts.append((x, 545 + sag))
    d.line(pts, fill=(150, 120, 110), width=4)
    cols = [(255, 190, 200), (255, 230, 150), (180, 225, 255), (200, 240, 190), (220, 195, 255)]
    for k in range(2, 40, 3):
        x, y = pts[k]; c = cols[(k // 3) % 5]
        tw = 0.6 + 0.4 * math.sin(t * 2.2 + k)
        d.ellipse([x - 20, y - 6, x + 20, y + 34], fill=c + (int(90 * tw),))
        d.ellipse([x - 10, y + 2, x + 10, y + 28], fill=c + (255,), outline=LINE + (255,), width=2)

PREVIEW = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x]
FRAMES = [int(x * FPS) for x in PREVIEW] if PREVIEW else range(NFR)
proc = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in FRAMES:
    t = fi / FPS
    i, lt = line_at(t)
    ph = 7 if t >= T_OUTRO else (-1 if i is None else i)
    im = ROOM.copy()
    put_glow(im, WIN_X, WIN_Y, 260, (255, 250, 225), 0.35)
    lay = fx_layer(); string_lights(ImageDraw.Draw(lay), t); im.alpha_composite(lay)

    # ---- Owlbert on the window sill ----
    om, ob = talking("Professor Owlbert", t)
    owing = (math.sin(t * 5) + 1) / 2 * 0.5 if ph == 3 else ((math.sin(t * 4) + 1) / 2 * 0.35 if ph >= 6 else 0.0)
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob, OS, OS)

    # ---- toy box (back + lid) ----
    im.alpha_composite(box_back(), (0, BOX_TOP - 160))

    # ---- teddy (hidden behind books, then hops to Mochi) ----
    teddy_on_mochi = t >= TEDDY_T0 + 1.0
    if t < TEDDY_T0:
        tdx, tdy, tsc = 600, 1470, 0.8
        if ph == 1 or ph == 2: tdy -= abs(math.sin(t * 3)) * 6     # a wiggle hint
        paste_c(im, teddy().resize((104, 112), Image.LANCZOS), tdx, tdy)
    elif not teddy_on_mochi:
        q = ease((t - TEDDY_T0) / 1.0)
        tx_ = lerp(600, MX - 20, q); ty_ = lerp(1470, MB - 70, q) - math.sin(q * math.pi) * 220
        paste_c(im, teddy().resize((104, 112), Image.LANCZOS), tx_, ty_)

    # ---- toys (box-bound toys sit in the box once landed: drawn before box front) ----
    box_now, top_now = [], []
    for k in range(len(TOYS)):
        x, y, r, s, q = toy_state(k, t)
        if TOYS[k][4] == "box" and q >= 0.55: box_now.append((k, x, y, r, s))
        elif TOYS[k][4] == "shelf" and q >= 1: box_now.append((k, x, y, r, s))
        else: top_now.append((k, x, y, r, s))
    # draw books still on the pile first in stack order (bottom book first)
    for k, x, y, r, s in box_now:
        paste_c(im, rot_sprite(TOYS[k][0], TOYS[k][1], r, s), x, y)
    paste(im, box_front(), (BOX_X0 + BOX_X1) / 2, BOX_BOT + 4)
    for k, x, y, r, s in top_now:
        if TOYS[k][4] == "box": continue
        paste_c(im, rot_sprite(TOYS[k][0], TOYS[k][1], r, s), x, y)
    for k, x, y, r, s in top_now:
        if TOYS[k][4] != "box": continue
        paste_c(im, rot_sprite(TOYS[k][0], TOYS[k][1], r, s), x, y)

    # ---- Hana ----
    hm, hb = talking("Hana", t)
    hsad = ph == 2 and lt > 0.2
    toss = ph == 4 and lt > 0.5 and int((lt - 0.5) / TIDY_STEP * 2) % 2 == 0 and lt < 4.6
    harms = toss or (ph >= 6 and int(t * 2) % 2 == 0) or (ph == 5 and lt > 1.2)
    hop = abs(math.sin(t * 6)) * 12 if ph >= 6 else 0
    shadow(im, HX, HB - 4, 0.7)
    paste(im, hana(hm, harms, blinking(t, 0.0), hsad), HX, HB - hb - hop, HS, HS)

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    if ph in (1, 2): mexpr = "sad"
    elif ph >= 5 and not mm: mexpr = "joy"
    else: mexpr = "happy"
    look = math.sin(t * 2.4) * 22 if ph == 1 else 0
    floaty = math.sin(t * 2.0) * 10
    mwing = math.sin(t * (9 if ph >= 5 else 5)) * 0.6
    shadow(im, MX + look, 1395, 0.7)
    paste(im, mochi(mm, round(mwing * 4) / 4, mexpr, blinking(t, 2.3) and mexpr != "joy"), MX + look, MB - mb + floaty, MS, MS)
    if teddy_on_mochi:
        paste_c(im, teddy().resize((96, 104), Image.LANCZOS), MX - 20 + look, MB - 62 - mb + floaty)

    # ---- fx ----
    lay = fx_layer(); dl = ImageDraw.Draw(lay)
    if ph in (1, 2):
        for k, (qx, qy) in enumerate(((MX - 120, 1010), (MX + 90, 980), (HX + 150, 1010))):
            if k == 2 and ph != 2: continue
            bob = math.sin(t * 3 + k) * 10
            f = font(80); dl.text((qx, qy + bob), "?", font=f, fill=(150, 130, 220, 230), stroke_width=5, stroke_fill=(255, 255, 255, 230))
    if ph == 3 and lt > 1.0:     # gentle "home" hints: glowing arrow dots to box and shelf
        a_ = int(200 * ease((lt - 1.0) / 0.5))
        for k in range(5):
            q = ((t * 0.8 + k / 5) % 1)
            dl.ellipse([620 - q * 60 - 8, 1450 - q * 200 - 8, 620 - q * 60 + 8, 1450 - q * 200 + 8], fill=(255, 220, 120, a_))
            dl.ellipse([450 - q * 250 - 8, 1400 - q * 520 - 8, 450 - q * 250 + 8, 1400 - q * 520 + 8], fill=(255, 220, 120, a_))
    for k in range(len(TOYS)):           # landing sparkle
        st = TIDY_T0 + k * TIDY_STEP + FLY
        if 0 <= t - st < 0.5:
            q = (t - st) / 0.5; _, _, (tx_, ty_, _, _), _ = TOYS[k][2], TOYS[k][2], TOYS[k][3], 0
            for j in range(4):
                a = j * math.pi / 2 + 0.6
                star4(dl, tx_ + math.cos(a) * 60 * q, ty_ + math.sin(a) * 60 * q, 16 * (1 - q) + 4, (255, 230, 120, int(255 * (1 - q))))
    if ph >= 5 and t > TEDDY_T0 + 1.0:
        for k in range(10):
            sx_ = [130, 260, 400, 520, 640, 760, 860, 330, 590, 840][k]
            sy_ = [1080, 860, 1150, 1100, 1060, 1000, 1180, 700, 640, 1350][k]
            tw = (math.sin(t * 3 + k * 1.7) + 1) / 2
            star4(dl, sx_, sy_, 10 + 16 * tw, (255, 240, 170, int(120 + 135 * tw)))
    im.alpha_composite(lay)

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "The Messy Treehouse", 86, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (180, 150, 230), "Tidy up after you play!", 80, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original bouncy tidy-up tune in G major (4/4), marimba + soft bass ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "marimba": w = w + 0.25 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-14 * tt)
    if shape == "pluck": w = w + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt)
    if shape == "bell": w = w + 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 4.02 * tt)
    if shape == "pad": w = w + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt); env = np.minimum(1, tt * 1.2) * np.minimum(1, (dur - tt) * 1.2)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at, buf=None):
    buf = audio if buf is None else buf
    i0 = int(at * SR)
    if i0 >= N or i0 < 0: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
mel = [67, 71, 74, 71,  72, 76, 74, None,  71, 74, 79, 76,  74, None, 72, 71,
       69, 72, 76, 72,  71, 74, 72, None,  69, 71, 72, 74,  67, None, None, None]
chords = [(55, 59, 62), (48, 52, 55), (55, 59, 62), (50, 54, 57), (57, 60, 64), (55, 59, 62), (50, 54, 57), (55, 59, 62)]
beat = 0.36; music = np.zeros(N); k = 0
while k * beat < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 0.7, 0.045, "marimba", 6), k * beat, music)
    ch = chords[(k // 4) % len(chords)]
    if k % 4 == 0:
        for n_ in ch: add(tone(f(n_), beat * 4, 0.011, "pad"), k * beat, music)
    if k % 2 == 0: add(tone(f(ch[0] - 12), 0.5, 0.045, "pluck", 5), k * beat, music)
    else: add(tone(f(ch[2]), 0.2, 0.012, "pluck", 12), k * beat, music)
    k += 1
duck = np.ones(N)
for spk, txt, st, dur, talk in LINES:
    a, b_ = int((st + 0.2) * SR), int((st + 0.4 + talk) * SR); duck[a:b_] = 0.6
duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
audio += music * duck
base = {"Hana": 620, "Mochi": 820, "Professor Owlbert": 330}
rnd = random.Random(9)
for spk, txt, st, dur, talk in LINES:
    if spk not in base: continue
    tt = st + 0.3
    while tt < st + 0.3 + talk:
        add(tone(base[spk] * rnd.choice([1, 1.12, 1.25, 0.9]), 0.09, 0.03, "sine", 25), tt); tt += 0.286
for j, m in enumerate([67, 71, 74, 79]): add(tone(f(m), 1.0, 0.07, "bell", 3), 0.1 + j * 0.18)          # title
for k in range(len(TOYS)):                                                                                 # toy lands
    add(tone(f([79, 81, 83, 86, 88, 91, 93][k]), 0.5, 0.06, "bell", 6), TIDY_T0 + k * TIDY_STEP + FLY)
for j, m in enumerate([83, 86, 91]): add(tone(f(m), 0.7, 0.05, "bell", 4), TEDDY_T0 + 1.0 + j * 0.13)    # teddy found
for j, m in enumerate([67, 71, 74, 79, 83]): add(tone(f(m), 1.4, 0.07, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
