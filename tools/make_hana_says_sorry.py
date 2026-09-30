"""Petal Valley (Anime Adventures): Hana says sorry — lesson: apologising.
Original characters, art and music. Renders kids/hana_says_sorry.mp4 (captions + music, no voice).
Character designs match make_sharing_last_dumpling.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/hana_says_sorry.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(314)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "One sunny morning, Mochi built a tall pebble tower by the pond."),
    ("Hana", "Look, a butterfly! Wait for me, little butterfly!"),
    ("Mochi", "Oh no! My tower fell down. I feel so sad."),
    ("Professor Owlbert", "Hana, when we hurt a friend by mistake, we say sorry."),
    ("Hana", "I'm sorry, Mochi. I did not look. Can I help you fix it?"),
    ("Mochi", "Yes! Thank you, Hana. Let's build it together!"),
    ("Narrator", "Saying sorry helps friends feel better again!"),
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

# ================= pond scene (new for this episode) =================
PEB_COL = [(255, 190, 200), (255, 220, 150), (190, 230, 190), (180, 215, 250), (215, 195, 250), (255, 235, 235)]
PEB_SZ = [(150, 74), (132, 66), (116, 60), (100, 54), (84, 48), (68, 42)]

@lru_cache(None)
def pebble(k, face):
    w, h = PEB_SZ[k]; col = PEB_COL[k]
    p = P(w + 16, h + 16)
    p.ell(8, 8, 8 + w, 8 + h, col, LINE, 4)
    dk = tuple(max(0, c - 25) for c in col)
    p.chord(12, 8 + h * 0.35, 4 + w, 4 + h, 10, 170, dk)
    p.ell(8 + w * 0.18, 8 + h * 0.14, 8 + w * 0.42, 8 + h * 0.34, (255, 255, 255))
    if face:
        cx, cy = 8 + w / 2, 8 + h * 0.55
        for sgn in (-1, 1): p.circ(cx + sgn * w * 0.14, cy - 2, 4, (90, 65, 90))
        p.arc(cx - 8, cy - 4, cx + 8, cy + 8, 20, 160, (90, 65, 90), 3)
    return p.done()

@lru_cache(None)
def pebble_rot(k, ang):
    return pebble(k, False).rotate(ang, resample=Image.BICUBIC, expand=True)

@lru_cache(None)
def flower_top():
    p = P(90, 120)
    p.line([(45, 115), (45, 55)], (110, 180, 120), 7)
    p.ell(46, 78, 80, 96, (150, 210, 150))
    for k in range(6):
        a = k * math.pi / 3
        p.circ(45 + 20 * math.cos(a), 40 + 20 * math.sin(a), 15, (255, 170, 205), LINE, 2)
    p.circ(45, 40, 13, (255, 215, 110), LINE, 2)
    return p.done()

def make_bg():
    bg = vgrad(W, H, [(0, (200, 235, 225)), (0.35, (225, 240, 235)), (0.55, (255, 232, 215)), (1, (255, 232, 215))]).convert("RGBA")
    t = P(W, H)
    # distant lavender mountains + morning sun
    t.circ(260, 760, 80, (255, 240, 185))
    t.poly([(-50, 1110), (170, 830), (330, 960), (520, 800), (760, 1000), (920, 860), (1130, 1110)], (215, 205, 240))
    t.poly([(420, 860), (520, 800), (600, 865), (560, 850), (520, 880), (470, 850)], (255, 255, 255))
    t.poly([(-50, 1150), (240, 960), (520, 1080), (820, 950), (1130, 1150)], (195, 225, 205))
    bg.alpha_composite(t.done())
    d = ImageDraw.Draw(bg)
    # grass field
    d.rectangle([0, 1130, W, H], fill=(180, 225, 180))
    # pond (mid-ground) with shine + lily pads
    d.ellipse([-120, 1170, 700, 1350], fill=(150, 205, 235))
    d.ellipse([-80, 1185, 660, 1335], fill=(170, 218, 242))
    for x0, y0, x1 in ((60, 1230, 220), (330, 1280, 470), (150, 1305, 250)):
        d.rounded_rectangle([x0, y0, x1, y0 + 8], radius=4, fill=(230, 245, 255))
    for cx, cy, r in ((470, 1215, 38), (560, 1255, 30), (90, 1270, 34)):
        d.ellipse([cx - r, cy - r * 0.45, cx + r, cy + r * 0.45], fill=(125, 190, 140))
        d.polygon([(cx, cy), (cx + r, cy - r * 0.2), (cx + r, cy + r * 0.2)], fill=(170, 218, 242))
    d.ellipse([452, 1196, 476, 1214], fill=(255, 190, 215)); d.ellipse([458, 1200, 470, 1210], fill=(255, 235, 150))
    # reeds
    for x in (640, 668, 700, 20, 44):
        d.line([(x, 1340), (x - 6, 1210)], fill=(120, 180, 120), width=7)
        d.rounded_rectangle([x - 16, 1205, x + 2, 1250], radius=9, fill=(190, 140, 110))
    # foreground meadow
    d.ellipse([-400, 1330, 1500, 2400], fill=(165, 215, 170))
    rnd = random.Random(7)
    for _ in range(70):
        x, y = rnd.randint(10, W - 10), rnd.randint(1380, 1900)
        r = 3 + (y - 1380) / 120
        c = rnd.choice([(255, 255, 255), (255, 215, 230), (230, 215, 255), (255, 240, 180)])
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + math.cos(a) * r - r * .55, y + math.sin(a) * r - r * .55, x + math.cos(a) * r + r * .55, y + math.sin(a) * r + r * .55], fill=c)
        d.ellipse([x - r * .4, y - r * .4, x + r * .4, y + r * .4], fill=(255, 205, 110))
    # tree on the right with a branch for Owlbert
    t = P(W, H)
    t.poly([(880, 1420), (905, 1150), (890, 1000), (960, 1000), (950, 1150), (975, 1420)], (190, 145, 120), LINE, 4)
    t.poly([(900, 1135), (700, 1110), (690, 1128), (900, 1165)], (190, 145, 120), LINE, 4)
    for cx, cy, r in ((930, 900, 130), (1040, 960, 110), (820, 960, 90), (990, 820, 100)):
        t.circ(cx, cy, r + 5, (130, 190, 150))
    for cx, cy, r in ((930, 900, 130), (1040, 960, 110), (820, 960, 90), (990, 820, 100)):
        t.circ(cx, cy, r, (170, 220, 180))
    for cx, cy in ((880, 860), (990, 930), (830, 990), (1010, 800)):
        t.circ(cx, cy, 12, (255, 200, 220))
    bg.alpha_composite(t.done())
    return bg

BG = make_bg()
SPARK = [(random.uniform(40, 900), random.uniform(560, 1150), random.uniform(0, 6)) for _ in range(14)]

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)

def star4(d, x, y, r, col):
    d.polygon([(x, y - r), (x + r * .28, y - r * .28), (x + r, y), (x + r * .28, y + r * .28), (x, y + r), (x - r * .28, y + r * .28), (x - r, y), (x - r * .28, y - r * .28)], fill=col)

def butterfly(d, bx, by, t):
    fl = abs(math.sin(t * 12)) * 0.8 + 0.2
    for sgn in (-1, 1):
        d.ellipse([bx + sgn * 4 - (sgn < 0) * 30 * fl, by - 26, bx + sgn * 4 + (sgn > 0) * 30 * fl, by + 4], fill=(255, 200, 120))
        d.ellipse([bx + sgn * 4 - (sgn < 0) * 20 * fl, by, bx + sgn * 4 + (sgn > 0) * 20 * fl, by + 20], fill=(255, 170, 200))
    d.line([(bx, by - 20), (bx, by + 16)], fill=LINE, width=4)

def blinking(t, off): return ((t + off) % 3.9) < 0.13

HX0, HB = 290, 1500       # Hana resting spot
MX, MB0 = 800, 1470       # Mochi
OX, OB = 790, 1122        # Owlbert on branch
TX, TB = 545, 1500        # tower centre / base
L = [ln[2] for ln in LINES]
CRASH = L[1] + LINES[1][3] - 1.5
# tower stack positions (centre y of each pebble)
STACK, y = [], TB
for k in range(6):
    h = PEB_SZ[k][1]; STACK.append((TX + (k % 2) * 6 - 3, y - h / 2 + 4)); y -= h - 8
rs = random.Random(9)
SCATTER = [(x, TB - 14 + rs.uniform(-12, 18), rs.uniform(-40, 40)) for x in (520, 650, 580, 615, 490, 555)]
REBUILD0 = L[5] + 1.2    # pebbles return one by one

def pebble_state(k, t):
    """returns (x, y, angle) for pebble k at time t"""
    sx, sy = STACK[k]; fx, fy, fa = SCATTER[k]
    if t < CRASH: return sx, sy, 0
    rb = REBUILD0 + k * 0.5
    if t < rb:
        q = ease((t - CRASH - k * 0.05) / 1.0)
        x = lerp(sx, fx, q); y = lerp(sy, fy, q) - math.sin(q * math.pi) * 60 * (k / 5)
        return x, y, fa * q
    q = ease((t - rb) / 0.6)
    x = lerp(fx, sx, q); y = lerp(fy, sy, q) - math.sin(q * math.pi) * 90
    return x, y, fa * (1 - q)

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
    # twinkly morning sparkles
    for x, y, off in SPARK:
        a = (math.sin(t * 2 + off) + 1) / 2
        star4(d, x, y, 6 + 6 * a, (255, 255, 255, int(90 + 140 * a)))

    # ---- Owlbert on the branch ----
    om, ob = talking("Professor Owlbert", t)
    owing = 0.0
    if ph == 3: owing = (math.sin(t * 6) + 1) / 2 * 0.6
    if ph >= 6: owing = (math.sin(t * 5) + 1) / 2 * 0.5
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob)

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    wing = math.sin(t * 5) * 0.4; expr = "happy"
    mbot = MB0 - abs(math.sin(t * 3)) * 8
    if t > CRASH + 0.4 and (ph in (1, 2, 3) or (ph == 4 and lt < 3.4)): expr = "sad"; wing = -0.5
    if ph == 4 and lt >= 3.4: expr = "happy"
    if ph == 5: expr = "joy"; wing = math.sin(t * 10) * 0.8; mbot -= abs(math.sin(t * 5)) * 16
    if ph >= 6: expr = "joy"; wing = math.sin(t * 9); mbot = MB0 - 30 - abs(math.sin(t * 4)) * 22
    shadow(im, MX, MB0 - 6, 0.8)
    paste(im, mochi(mm, round(wing * 4) / 4, expr, blinking(t, 2.3) and expr != "joy"), MX, mbot + 50 - mb)

    # ---- pebble tower ----
    shadow(im, TX, TB - 4, 0.75)
    tower_done = t >= REBUILD0 + 5 * 0.5 + 0.6
    for k in range(6):
        x, y, a = pebble_state(k, t)
        sp = pebble(k, k == 5 and not (CRASH <= t < REBUILD0 + 3.1)) if abs(a) < 1 else pebble_rot(k, int(a))
        paste_c(im, sp, x, y)
    if tower_done:
        q = ease((t - (REBUILD0 + 3.1)) / 0.5)
        fl = flower_top()
        if q < 1: fl = fl.resize((max(2, int(fl.width * q)), max(2, int(fl.height * q))))
        top = STACK[5][1] - PEB_SZ[5][1] / 2 + 8
        paste(im, fl, STACK[5][0], top)
        for k in range(5):
            a = t * 1.5 + k * 1.256
            star4(d, TX + 130 * math.cos(a), 1320 + 90 * math.sin(a), 12, (255, 230, 130, 220))
    # crash puff
    if CRASH <= t < CRASH + 1.0:
        q = (t - CRASH) / 1.0
        for k in range(7):
            a = k * 2 * math.pi / 7
            r = 40 + 110 * q
            d.ellipse([TX + r * math.cos(a) - 22, 1380 + r * 0.6 * math.sin(a) - 22, TX + r * math.cos(a) + 22, 1380 + r * 0.6 * math.sin(a) + 22],
                      fill=(255, 255, 255, int(200 * (1 - q))))

    # ---- butterfly ----
    if ph in (-1, 0):
        butterfly(d, 180 + math.sin(t * 0.8) * 90, 1080 + math.sin(t * 1.7) * 40, t)
    elif ph == 1:
        bx = lerp(180, 1000, ease(lt / (LINES[1][3] - 0.6))); by = 1080 + math.sin(t * 2.2) * 70
        if bx < 980: butterfly(d, bx, by, t)

    # ---- Hana ----
    hm, hb = talking("Hana", t)
    sad = False; arms = False; hop = 0
    if ph <= 0: hx = -260
    elif ph == 1:
        q = min(1.0, lt / (CRASH - L[1]))
        hx = lerp(-230, 390, q); arms = t < CRASH; hop = abs(math.sin(t * 9)) * 22 if t < CRASH else 0
        if t >= CRASH: sad = True; hx = 390 - ease((t - CRASH) / 0.4) * 20
    elif ph == 2:
        hx = lerp(370, HX0, ease(lt / 1.5)); sad = True
    elif ph == 3:
        hx = HX0; sad = True
    elif ph == 4:
        hx = HX0 + ease(lt / 1.0) * 30; sad = lt < 2.6
    else:
        hx = HX0 + 30; arms = (ph == 5 and lt > 1.0) or ph >= 6
        if ph >= 6: hop = abs(math.sin(t * 6)) * 12
    if hx > -250:
        shadow(im, hx, HB - 4, 0.8)
        paste(im, hana(hm, arms, blinking(t, 0.0) and not sad, sad), hx, HB - hb - hop + (8 if sad and ph == 4 else 0))
    d = ImageDraw.Draw(im)
    # sorry heart floats from Hana to Mochi
    if ph == 4 and 2.4 < lt < 5.2:
        q = ease((lt - 2.4) / 2.0)
        hx2 = lerp(HX0 + 120, MX - 60, q); hy2 = 1150 - math.sin(q * math.pi) * 120
        heart(d, hx2, hy2, 34, (255, 130, 170, 235))
    if ph >= 6:
        for k in range(6):
            q = ((t - L[6]) * 0.35 + k / 6) % 1
            heart(d, 380 + (k % 3) * 150 + math.sin(t * 2 + k) * 25, 1300 - q * 360, 18 + 6 * (k % 2), (255, 130, 170, int(230 * (1 - q))))

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "Hana Says Sorry", 88, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (240, 130, 170), "Say sorry, and help fix it!", 96, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original soft lullaby-march in G major (4/4), music-box + pad ----------
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
# original melody, 8 eighth-notes per bar (None = rest)
mel = [79, None, 76, 78, 79, None, 83, None,  81, 79, 78, None, 76, None, None, None,
       74, None, 76, 78, 79, 81, 83, None,    81, None, 78, None, 79, None, None, None,
       83, None, 81, 79, 76, None, 78, 79,    81, None, 79, 76, 74, None, None, None,
       76, 78, 79, None, 74, None, 71, None,  74, None, 76, 78, 79, None, None, None]
chords = [(55, 59, 62), (48, 52, 55), (50, 54, 57), (55, 59, 62), (52, 55, 59), (48, 52, 55), (50, 54, 57), (55, 59, 62)]
e8 = 0.3; music = np.zeros(N); k = 0
while k * e8 < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 0.9, 0.05, "bell", 4.5), k * e8, music)
    bar = k // 8
    ch = chords[bar % len(chords)]
    if k % 8 == 0:
        for n_ in ch: add(tone(f(n_), e8 * 8, 0.022, "pad"), k * e8, music)
    if k % 2 == 0:
        add(tone(f(ch[(k // 2) % 3] - 12), 0.5, 0.03, "pluck", 6), k * e8, music)
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
add(tone(f(79), 0.8, 0.12, "bell", 3), 0.1); add(tone(f(86), 1.0, 0.12, "bell", 3), 0.5)
for j in range(6): add(tone(f(60 + (5 - j) * 2), 0.25, 0.09, "pluck", 10), CRASH + 0.05 + j * 0.12)   # tumble clacks
for j, m in enumerate([76, 72, 69]): add(tone(f(m), 0.6, 0.06, "bell", 5), L[2] + 0.4 + j * 0.2)         # oh no
for j, m in enumerate([79, 83, 86]): add(tone(f(m), 0.7, 0.07, "bell", 4), L[4] + 2.5 + j * 0.2)         # sorry heart
for k in range(6): add(tone(f(74 + [0, 2, 4, 5, 7, 9][k]), 0.4, 0.08, "pluck", 8), REBUILD0 + k * 0.5 + 0.55)  # stack clinks
for j, m in enumerate([79, 83, 86, 91]): add(tone(f(m), 0.9, 0.08, "bell", 4), REBUILD0 + 3.1 + j * 0.12)
for j, m in enumerate([79, 83, 86, 91, 95]): add(tone(f(m), 1.4, 0.09, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
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
