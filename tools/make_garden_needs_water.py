"""Petal Valley (Anime Adventures): The garden needs water — lesson: caring for plants.
Original characters, art and music. Renders kids/garden_needs_water.mp4 (captions + music, no voice).
Character designs match make_mochi_afraid_of_the_dark.py / make_hana_says_sorry.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/garden_needs_water.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(5151)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "It was a sunny morning in the Petal Valley garden."),
    ("Hana", "Oh no! Our flowers look droopy and sad."),
    ("Mochi", "Maybe they are thirsty, just like me!"),
    ("Professor Owlbert", "Plants need water and sunshine to grow."),
    ("Hana", "Let's give them a drink with my watering can!"),
    ("Mochi", "Look! The flowers are standing up and smiling!"),
    ("Narrator", "When we care for plants, they grow happy and strong."),
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





# ================= sunny flower garden scene (new for this episode) =================
def fx_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def mix(a, b, k): return tuple(int(lerp(a[i], b[i], k)) for i in range(3))

SKY = vgrad(W, H, [(0, (165, 215, 255)), (0.30, (200, 232, 255)), (0.52, (240, 248, 235)), (1, (240, 248, 235))]).convert("RGBA")
BED_Y0, BED_Y1 = 1430, 1530
FX = [430, 530, 630, 730, 838]
FBASE = 1478
FCOL = [(255, 150, 190), (255, 212, 80), (190, 160, 240), (255, 160, 125), (130, 195, 250)]
DRY = (196, 176, 150)

def make_land():
    t = P(W, H)
    t.poly([(-60, 1000), (160, 920), (380, 980), (600, 900), (820, 970), (1140, 910), (1140, 1150), (-60, 1150)], (200, 230, 200))
    t.poly([(-60, 1060), (260, 1000), (560, 1050), (860, 990), (1140, 1040), (1140, 1200), (-60, 1200)], (176, 220, 172))
    # little pastel greenhouse far left
    t.rrect(40, 935, 190, 1040, 14, (230, 248, 250), LINE, 4)
    t.poly([(30, 945), (115, 880), (200, 945)], (255, 200, 215), LINE, 4)
    for x in (80, 150): t.line([(x, 960), (x, 1030)], (190, 220, 235), 4)
    # picket fence
    t.rrect(-20, 1118, 1100, 1136, 6, (255, 250, 240), LINE, 3)
    t.rrect(-20, 1160, 1100, 1178, 6, (255, 250, 240), LINE, 3)
    for x in range(10, 1080, 70):
        top = 1080 if x != 780 else 1100
        if x == 780:
            t.rrect(x - 22, 1100, x + 22, 1215, 8, (255, 238, 220), LINE, 4)   # Owlbert's post
        else:
            t.poly([(x - 18, top + 22), (x, top), (x + 18, top + 22), (x + 18, 1205), (x - 18, 1205)], (255, 250, 240), LINE, 3)
    # lawn
    t.poly([(-60, 1195), (1140, 1185), (1140, H + 10), (-60, H + 10)], (172, 220, 160))
    # stepping stones
    for x, y, r in ((120, 1660, 46), (260, 1740, 40), (420, 1800, 44)):
        t.ell(x - r * 1.3, y - r * 0.6, x + r * 1.3, y + r * 0.6, (232, 225, 215), LINE, 3)
    # flower bed (dry soil) with a rounded wooden edge
    t.rrect(360, BED_Y0 - 10, 905, BED_Y1 + 18, 44, (215, 170, 130), LINE, 4)
    t.rrect(375, BED_Y0, 890, BED_Y1, 38, DRY)
    im = t.done()
    d = ImageDraw.Draw(im)
    for k in range(9):                                     # dry cracks
        x = 400 + k * 56; y = 1455 + (k % 3) * 18
        d.line([(x, y), (x + 14, y + 10), (x + 8, y + 22)], fill=(170, 150, 125), width=3)
    rnd = random.Random(11)
    for _ in range(70):                                    # tiny grass tufts / clover
        x, y = rnd.randint(10, W - 10), rnd.randint(1220, 1900)
        if 350 < x < 915 and 1415 < y < 1555: continue
        c = rnd.choice([(150, 205, 140), (190, 235, 170), (255, 255, 255)])
        if c == (255, 255, 255):
            for a in range(5):
                aa = a * 1.2566; d.ellipse([x + math.cos(aa) * 6 - 4, y + math.sin(aa) * 6 - 4, x + math.cos(aa) * 6 + 4, y + math.sin(aa) * 6 + 4], fill=c)
            d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 215, 110))
        else:
            d.line([(x - 6, y), (x - 9, y - 12)], fill=c, width=4); d.line([(x, y), (x, y - 15)], fill=c, width=4); d.line([(x + 6, y), (x + 9, y - 12)], fill=c, width=4)
    return im
LAND = make_land()

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)
@lru_cache(None)
def wet_spot(aq):
    sp = Image.new("RGBA", (150, 70), (0, 0, 0, 0))
    ImageDraw.Draw(sp).ellipse([0, 0, 149, 69], fill=(130, 95, 75, int(aq * 22)))
    return sp.filter(ImageFilter.GaussianBlur(4))

@lru_cache(None)
def flower(k, dq):
    """dq: 0 (upright, happy, big) .. 16 (droopy, sad, faded)."""
    dr = dq / 16
    p = P(420, 380); bx, by = 280, 368
    Ls = 175 + 30 * (1 - dr)
    R = 40 + 12 * (1 - dr)
    col = mix(FCOL[k], DRY, 0.5 * dr)
    leaf = mix((120, 200, 120), (180, 185, 130), dr)
    stem_d = mix((90, 160, 90), (150, 150, 105), dr)
    hx, hy = bx - 0.62 * Ls * dr, by - Ls * (1 - 0.42 * dr)
    cx_, cy_ = bx + 10 * dr, by - Ls * 0.85
    pts = [((1 - u) ** 2 * bx + 2 * (1 - u) * u * cx_ + u * u * hx, (1 - u) ** 2 * by + 2 * (1 - u) * u * cy_ + u * u * hy) for u in np.linspace(0, 1, 16)]
    p.line(pts, stem_d, 14); p.line(pts, mix(leaf, (255, 255, 255), 0.05), 9)
    # two leaves (droop down when dry)
    for sgn, frac in ((1, 0.28), (-1, 0.5)):
        lx, ly = pts[int(frac * 15)]
        tipx, tipy = lx + sgn * 62, ly - 34 + 60 * dr
        midx, midy = lx + sgn * 30, ly - 30 + 30 * dr
        p.poly([(lx, ly), (midx, midy - 10), (tipx, tipy), (midx + sgn * 6, midy + 18)], leaf, stem_d, 3)
    # petals (sag downward when dry)
    n = 8
    for j in range(n):
        a = j * 2 * math.pi / n + 0.2
        pr = R * (0.62 - 0.08 * dr)
        px, py = hx + math.cos(a) * R * 0.95, hy + math.sin(a) * R * 0.95 + 12 * dr * (1 + math.sin(a))
        p.circ(px, py, pr + 3, mix(col, (90, 70, 90), 0.35));
    for j in range(n):
        a = j * 2 * math.pi / n + 0.2
        pr = R * (0.62 - 0.08 * dr)
        px, py = hx + math.cos(a) * R * 0.95, hy + math.sin(a) * R * 0.95 + 12 * dr * (1 + math.sin(a))
        p.circ(px, py, pr, col)
        p.circ(px - pr * 0.25, py - pr * 0.25, pr * 0.3, mix(col, (255, 255, 255), 0.45))
    # face disc
    cr = R * 0.62
    fy = hy + 8 * dr
    p.circ(hx, fy, cr + 3, (200, 150, 70)); p.circ(hx, fy, cr, mix((255, 222, 120), DRY, 0.3 * dr))
    ex = cr * 0.42
    if dr > 0.5:
        for sgn in (-1, 1):
            p.arc(hx + sgn * ex - 9, fy - 2, hx + sgn * ex + 9, fy + 14, 200, 340, (110, 75, 70), 4)
        p.arc(hx - 10, fy + cr * 0.45, hx + 10, fy + cr * 0.45 + 16, 200, 340, (150, 80, 80), 4)
    else:
        for sgn in (-1, 1):
            eye(p, hx + sgn * ex, fy - 3, 15, 20, (90, 60, 50))
        p.chord(hx - 13, fy + 2, hx + 13, fy + 22, 0, 180, (190, 80, 100))
        for sgn in (-1, 1): p.ell(hx + sgn * cr * 0.72 - 7, fy + 6, hx + sgn * cr * 0.72 + 7, fy + 14, (255, 160, 170))
    return p.done()

@lru_cache(None)
def sun_face(smile):
    p = P(200, 200)
    p.circ(100, 100, 74, (255, 214, 95), (240, 170, 70), 5)
    p.circ(100, 100, 60, (255, 228, 125))
    for sgn in (-1, 1):
        p.arc(100 + sgn * 26 - 12, 82, 100 + sgn * 26 + 12, 104, 200, 340, (170, 110, 70), 5)
        p.ell(100 + sgn * 42 - 12, 108, 100 + sgn * 42 + 12, 120, (255, 170, 140))
    if smile: p.chord(84, 104, 116, 136, 0, 180, (200, 100, 90))
    else: p.arc(86, 104, 114, 128, 20, 160, (170, 110, 70), 5)
    return p.done()

@lru_cache(None)
def can_sprite(tq):
    """watering can, pivot (handle) at sprite centre (180,180); tq = tilt in degrees (forward)."""
    p = P(360, 360)
    C = (150, 220, 205); CD = (90, 160, 150)
    p.arc(150, 120, 220, 200, 90, 290, CD, 12)                     # handle loop around pivot
    p.rrect(190, 150, 290, 250, 22, C, LINE, 4)                      # body
    p.rrect(190, 150, 290, 170, 10, (180, 235, 222))
    p.circ(240, 205, 18, (255, 200, 215)); p.circ(240, 205, 7, (255, 240, 120))   # flower sticker
    p.poly([(282, 200), (342, 150), (350, 162), (288, 222)], C, LINE, 4)          # spout
    p.ell(335, 136, 360, 172, CD, LINE, 3)                                        # rose
    return p.done().rotate(-tq, resample=Image.BICUBIC, center=(180, 180))

def spout_tip(px, py, tq):
    vx, vy = 168, -26                                                 # rose centre relative to pivot
    a = math.radians(tq)
    return px + vx * math.cos(a) - vy * math.sin(a), py + vx * math.sin(a) + vy * math.cos(a)

def butterfly(d, x, y, s, flap, col):
    w = 0.35 + 0.65 * abs(math.sin(flap))
    for sgn in (-1, 1):
        d.ellipse([x + sgn * 2 - (sgn < 0) * 30 * s * w, y - 26 * s, x + sgn * 2 + (sgn > 0) * 30 * s * w, y + 2 * s], fill=col)
        d.ellipse([x + sgn * 2 - (sgn < 0) * 22 * s * w, y - 2 * s, x + sgn * 2 + (sgn > 0) * 22 * s * w, y + 18 * s], fill=mix(col, (255, 255, 255), 0.35))
    d.rounded_rectangle([x - 4 * s, y - 20 * s, x + 4 * s, y + 18 * s], radius=4 * s, fill=(110, 80, 110))

def drop_icon(d, x, y, r, col=(110, 185, 245)):
    d.ellipse([x - r, y - r * 0.4, x + r, y + r * 1.6], fill=col)
    d.polygon([(x - r * 0.92, y + r * 0.3), (x, y - r * 1.5), (x + r * 0.92, y + r * 0.3)], fill=col)
    d.ellipse([x - r * 0.5, y + r * 0.2, x - r * 0.1, y + r * 0.7], fill=(235, 248, 255))

def sun_icon(d, x, y, r):
    for j in range(8):
        a = j * math.pi / 4
        d.line([(x + math.cos(a) * r * 1.2, y + math.sin(a) * r * 1.2), (x + math.cos(a) * r * 1.6, y + math.sin(a) * r * 1.6)], fill=(255, 190, 70), width=8)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 214, 95))

def sprout_icon(d, x, y, r):
    d.rounded_rectangle([x - r * 0.9, y + r * 0.55, x + r * 0.9, y + r * 1.25], radius=12, fill=(215, 160, 120))
    d.line([(x, y + r * 0.6), (x, y - r * 0.5)], fill=(90, 160, 90), width=9)
    d.ellipse([x - r * 1.0, y - r * 0.9, x, y - r * 0.2], fill=(130, 205, 120))
    d.ellipse([x, y - r * 1.2, x + r * 1.0, y - r * 0.5], fill=(130, 205, 120))

L = [ln[2] for ln in LINES]
HX, HB, HS = 205, 1560, 0.85
OX, OB = 780, 1108
POUR0, POUR1 = L[4] + 0.9, L[4] + 3.0
RAIN0, RAIN1 = L[4] + 1.9, L[4] + 4.6
WET = [POUR0 + 0.5, POUR0 + 1.3, RAIN0 + 0.5, RAIN0 + 1.0, RAIN0 + 1.5]

def h01(n): return (math.sin(n * 12.9898) * 43758.5453) % 1.0

def droop(k, t):
    base = 0.82 + 0.18 * ease((t - L[1]) / 1.5)
    return base * (1 - ease((t - WET[k] - 0.4) / 1.6))

def wetness(k, t): return ease((t - WET[k] + 0.3) / 1.0)

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

def mochi_state(t, ph, lt):
    idle = (590 + math.sin(t * 1.1) * 60, 1150 - abs(math.sin(t * 2)) * 16)
    if ph <= 1: return idle[0], idle[1], ("sad" if ph == 1 else "happy"), math.sin(t * 5) * 0.5
    if ph in (2, 3): return idle[0], idle[1], "happy", math.sin(t * 5) * 0.5
    if ph == 4:
        q = ease((lt - 1.0) / 1.0)
        drift = 90 * ease((t - RAIN0) / (RAIN1 - RAIN0))          # glides along the bed while raining
        return lerp(idle[0], 640 + drift, q), lerp(idle[1], 840, q) + math.sin(t * 3) * 6, "happy" if lt < 2 else "joy", math.sin(t * 7) * 0.6
    st = L[5]; q = ease((t - st) / 1.2); a = (t - st) * 1.5
    tx, ty = 520 + math.sin(a) * 120, 900 + math.sin(a * 2) * 30
    return lerp(730, tx, q), lerp(840, ty, q) - abs(math.sin(t * 3)) * 14, "joy", math.sin(t * 9)

CLOUDS = [(150, 560, 1.0, 14), (620, 520, 0.8, 9), (980, 600, 1.1, 11)]
BFLY = [((255, 170, 210), 0.0), ((255, 220, 110), 1.7), ((170, 200, 255), 3.1)]

PREVIEW = [float(x) for x in os.environ.get("PREVIEW", "").split(",") if x]
FRAMES = [int(x * FPS) for x in PREVIEW] if PREVIEW else range(NFR)
proc = None if PREVIEW else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in FRAMES:
    t = fi / FPS
    i, lt = line_at(t)
    ph = 7 if t >= T_OUTRO else (-1 if i is None else i)
    im = SKY.copy(); d = ImageDraw.Draw(im)
    # drifting clouds
    for cx0, cy0, s, sp in CLOUDS:
        x = (cx0 + t * sp) % (W + 300) - 150
        for dx, dy, r in ((0, 0, 50), (-55, 12, 36), (55, 12, 38), (25, -25, 34)):
            d.ellipse([x + dx * s - r * s, cy0 + dy * s - r * s, x + dx * s + r * s, cy0 + dy * s + r * s], fill=(255, 255, 255))
    # smiling sun with slowly turning rays
    SX, SY = 165, 690
    put_glow(im, SX, SY, 190, (255, 240, 170), 0.6)
    d = ImageDraw.Draw(im)
    for j in range(10):
        a = j * math.pi / 5 + t * 0.25
        r0, r1 = 88, 116 + 8 * math.sin(t * 3 + j)
        d.line([(SX + math.cos(a) * r0, SY + math.sin(a) * r0), (SX + math.cos(a) * r1, SY + math.sin(a) * r1)], fill=(255, 200, 80), width=10)
    paste_c(im, sun_face(ph not in (1, 2)), SX, SY)
    im.alpha_composite(LAND)
    # soil darkens where water soaks in
    for k in range(5):
        w_ = wetness(k, t)
        if w_ > 0.02: im.alpha_composite(wet_spot(int(w_ * 10)), (FX[k] - 75, FBASE - 32))
    # flowers
    for k in range(5):
        dr = droop(k, t)
        sway = math.sin(t * 1.6 + k) * (3 if dr < 0.3 else 1)
        sp_ = flower(k, int(round(dr * 16)))
        im.alpha_composite(sp_, (int(FX[k] - 280 + sway), int(FBASE - 368)))
    d = ImageDraw.Draw(im)
    # sparkles when a flower perks up
    for k in range(5):
        q = (t - WET[k] - 1.2) / 1.2
        if 0 < q < 1:
            for j in range(5):
                a = j * 1.2566 + k
                rr = 60 + 90 * q
                star_x, star_y = FX[k] - 10 + math.cos(a) * rr, FBASE - 220 + math.sin(a) * rr * 0.7
                rs = 16 * (1 - q) + 4
                d.polygon([(star_x, star_y - rs), (star_x + rs * .3, star_y - rs * .3), (star_x + rs, star_y), (star_x + rs * .3, star_y + rs * .3),
                           (star_x, star_y + rs), (star_x - rs * .3, star_y + rs * .3), (star_x - rs, star_y), (star_x - rs * .3, star_y - rs * .3)], fill=(255, 245, 160))

    # ---- Owlbert on the fence post ----
    om, ob = talking("Professor Owlbert", t)
    owing = (math.sin(t * 5) + 1) / 2 * 0.6 if ph == 3 else ((math.sin(t * 4) + 1) / 2 * 0.35 if ph >= 6 else 0.0)
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob, 0.82, 0.82)

    # ---- Hana with her watering can ----
    hm, hb = talking("Hana", t)
    harms = ph >= 6
    hop = abs(math.sin(t * 6)) * 14 if harms else 0
    hsad = ph in (1, 2) and not hm
    shadow(im, HX, HB - 4, 0.7)
    paste(im, hana(hm, harms, blinking(t, 0.0), hsad), HX, HB - hb - hop, HS, HS)
    hand = (HX + 88 * HS, HB - hb - hop - 115 * HS)
    tilt = 0.0
    if POUR0 - 0.4 < t < POUR1 + 0.4:
        tilt = 38 * ease((t - (POUR0 - 0.4)) / 0.4) * (1 - ease((t - POUR1) / 0.4))
    if harms:
        cpx, cpy = 330, 1530; tilt = 0.0                # can rests on the grass while she cheers
    else:
        cpx, cpy = hand[0] - 4, hand[1] - 6
    shadow(im, cpx + 60, 1566, 0.35) if harms else None
    im.alpha_composite(can_sprite(int(round(tilt))), (int(cpx - 180), int(cpy - 180)))
    d = ImageDraw.Draw(im)
    # water stream from the can
    if POUR0 < t < POUR1 + 0.6:
        s = POUR0
        while s < min(t, POUR1):
            a = t - s
            n_ = int(s * 100)
            tq = 38 * ease((s - (POUR0 - 0.4)) / 0.4)
            sx, sy = spout_tip(cpx, cpy, tq)
            vx = 70 + 220 * h01(n_) ; vy = -180 - 120 * h01(n_ + 7)
            x, y = sx + vx * a, sy + vy * a + 700 * a * a
            if y < FBASE - 5:
                d.ellipse([x - 7, y - 9, x + 7, y + 9], fill=(120, 190, 250)); d.ellipse([x - 3, y - 5, x + 1, y - 1], fill=(225, 245, 255))
            s += 0.035

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    mx, mbot, mexpr, mwing = mochi_state(t, ph, lt)
    MS = 0.68
    # gentle rain from Mochi's cloud tummy
    if RAIN0 < t < RAIN1 + 0.8:
        s = RAIN0
        while s < min(t, RAIN1):
            a = t - s; n_ = int(s * 100)
            x0 = mx - 95 + 190 * h01(n_ + 3)
            y = mbot - 40 + 650 * a
            if y < FBASE - 5:
                d.line([(x0, y), (x0 - 4, y + 22)], fill=(120, 190, 250), width=7)
            s += 0.03
        if t < RAIN1:
            put_glow(im, mx, mbot - 60, 120, (190, 225, 255), 0.5)
    msp = mochi(mm, round(mwing * 4) / 4, mexpr, blinking(t, 2.3) and mexpr != "joy")
    paste(im, msp, mx, mbot - mb, MS, MS)
    d = ImageDraw.Draw(im)
    # Mochi's thought bubble: thirsty -> water drop
    if ph == 2 and lt > 0.6:
        q = ease((lt - 0.6) / 0.4)
        bx_, by_ = mx - 175, mbot - 300
        for rr, ox, oy in ((10, 95, 120), (16, 60, 80)):
            d.ellipse([bx_ + ox - rr * q, by_ + oy - rr * q, bx_ + ox + rr * q, by_ + oy + rr * q], fill=(255, 255, 255), outline=(150, 190, 230), width=3)
        R_ = 62 * q
        d.ellipse([bx_ - R_, by_ - R_, bx_ + R_, by_ + R_], fill=(255, 255, 255), outline=(150, 190, 230), width=4)
        if q > 0.5: drop_icon(d, bx_, by_ - 10, 26 * q)

    # Owlbert's picture card: water + sun = grow
    if ph == 3 or (ph == 4 and lt < 0.5):
        q = ease(lt / 0.5) if ph == 3 else 1 - ease(lt / 0.5)
        lay = fx_layer(); dl = ImageDraw.Draw(lay)
        x0, y0, x1, y1 = 300, 590, 900, 830
        dl.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=(255, 255, 255, 235), outline=(190, 140, 90), width=6)
        cy = 685
        drop_icon(dl, 390, cy - 10, 38)
        sun_icon(dl, 600, cy, 36)
        sprout_icon(dl, 810, cy - 6, 44)
        for xx, sym in ((495, "+"), (705, "=")):
            w_ = dl.textlength(sym, font=font(80)); dl.text((xx - w_ / 2, cy - 62), sym, font=font(80), fill=INK)
        for xx, lab in ((390, "water"), (600, "sun"), (810, "grow")):
            w_ = dl.textlength(lab, font=font(46)); dl.text((xx - w_ / 2, 752), lab, font=font(46), fill=(150, 110, 80))
        if q < 1:
            a_ = np.array(lay); a_[:, :, 3] = (a_[:, :, 3] * q).astype(np.uint8); lay = Image.fromarray(a_)
        im.alpha_composite(lay); d = ImageDraw.Draw(im)

    # butterflies return to the happy garden
    if t > L[5] + 0.5:
        for k, (col, off) in enumerate(BFLY):
            q = ease((t - L[5] - 0.5 - k * 0.4) / 2.0)
            tx = 450 + k * 170 + math.sin(t * 0.9 + off) * 90
            ty = 1150 + math.sin(t * 1.3 + off) * 60 - k * 30
            x = lerp(-80 if k % 2 == 0 else W + 80, tx, q); y = lerp(900, ty, q)
            butterfly(d, x, y, 1.2, t * 9 + off, col)
    if ph >= 6:
        lay = fx_layer(); dl = ImageDraw.Draw(lay)
        for k in range(5):
            q = ((t - L[6]) * 0.4 + k / 5) % 1
            heart(dl, 230 + k * 120 + math.sin(t * 2 + k) * 20, 1050 - q * 200, 18 + 5 * (k % 2), (255, 150, 190, int(230 * (1 - q))))
        im.alpha_composite(lay)

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "The Thirsty Garden", 88, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (120, 200, 140), "Give your plants some love!", 86, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original bright waltz in F major (3/4), marimba + soft pad ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "marimba": w = w + 0.25 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-14 * tt)
    if shape == "pluck": w = w + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt)
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
mel = [72, 69, 70,  72, 77, 76,  74, 72, 70,  69, None, None,
       70, 74, 72,  70, 69, 67,  69, 72, 65,  67, None, None,
       72, 69, 70,  72, 77, 79,  77, 76, 74,  72, None, 70,
       69, 67, 69,  70, 72, 74,  72, 67, 69,  65, None, None]
chords = [(53, 57, 60), (53, 57, 60), (46, 50, 53), (53, 57, 60), (46, 50, 53), (48, 52, 55), (53, 57, 60), (48, 52, 55),
          (53, 57, 60), (50, 53, 57), (46, 50, 53), (53, 57, 60), (46, 50, 53), (48, 52, 55), (48, 52, 55), (53, 57, 60)]
q3 = 0.40; music = np.zeros(N); k = 0
while k * q3 < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 0.9, 0.05, "marimba", 4.5), k * q3, music)
    bar = k // 3; ch = chords[bar % len(chords)]
    if k % 3 == 0:
        for n_ in ch: add(tone(f(n_), q3 * 3, 0.016, "pad"), k * q3, music)
        add(tone(f(ch[0] - 12), 0.7, 0.035, "pluck", 4), k * q3, music)
    else:
        add(tone(f(ch[1]), 0.3, 0.012, "pluck", 9), k * q3, music)
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
for j, m in enumerate([72, 77, 81, 84]): add(tone(f(m), 1.0, 0.07, "bell", 3), 0.1 + j * 0.18)          # title
for j, m in enumerate([69, 67, 65]): add(tone(f(m), 0.6, 0.04, "sine", 4), L[1] + 0.6 + j * 0.3)      # droopy
rng = np.random.default_rng(9)
def splash(dur, vol, smooth):
    nz = rng.standard_normal(int(dur * SR)); nz = np.convolve(nz, np.ones(smooth) / smooth, mode="same")
    return nz * np.sin(np.linspace(0, np.pi, len(nz))) ** 1.5 * vol
add(splash(POUR1 - POUR0, 0.06, 6), POUR0)                                                              # pouring water
add(splash(RAIN1 - RAIN0, 0.04, 3), RAIN0)                                                              # soft rain
for j in range(24): add(tone(f(84 + rnd.choice([0, 3, 5, 7])), 0.12, 0.025, "sine", 30), POUR0 + 0.4 + j * 0.15)   # drips
for k_ in range(5):
    for j, m in enumerate([72, 76, 79]): add(tone(f(m + k_ * 2), 0.8, 0.045, "bell", 4), WET[k_] + 0.8 + j * 0.12)  # perk up
for j, m in enumerate([84, 88, 91, 96]): add(tone(f(m), 0.9, 0.05, "bell", 3.5), L[5] + 0.6 + j * 0.14)
for j, m in enumerate([72, 77, 81, 84, 89]): add(tone(f(m), 1.4, 0.07, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
