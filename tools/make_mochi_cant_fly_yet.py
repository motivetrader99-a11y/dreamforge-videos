"""Petal Valley (Anime Adventures): Mochi can't fly yet — lesson: keep trying.
Original characters, art and music. Renders kids/mochi_cant_fly_yet.mp4 (no voice, captions + music)."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/mochi_cant_fly_yet.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(33)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- script / timeline ----------
SCRIPT = [
    ("Narrator", "One sunny morning in Petal Valley, little Mochi wanted to fly."),
    ("Mochi", "Watch me fly! Flap, flap... Oh no! I fell down."),
    ("Hana", "It's okay, Mochi! Everybody falls. Let's try again!"),
    ("Professor Owlbert", "Start with little flaps, then bigger flaps. Like this!"),
    ("Mochi", "Flap, flap, flap... I'm floating! I'm flying!"),
    ("Hana", "Yay! You did it, Mochi! You kept trying!"),
    ("Narrator", "When something is hard, keep trying. You can do it too!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.6, 4.6
LINES, t = [], INTRO
for spk, txt in SCRIPT:
    words = len(txt.split())
    talk = words * 0.36 + 0.4
    dur = max(5.0, talk + 1.6)
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

# ---------- background ----------
def vgrad(w, h, stops):
    ys = np.linspace(0, 1, h)
    arr = np.zeros((h, 3))
    for c in range(3): arr[:, c] = np.interp(ys, [s for s, _ in stops], [col[c] for _, col in stops])
    return Image.fromarray(np.repeat(arr.astype(np.uint8)[:, None, :], w, axis=1))

def make_bg():
    bg = vgrad(W, H, [(0, (255, 214, 228)), (0.4, (225, 222, 255)), (0.66, (215, 240, 255)), (1, (215, 240, 255))]).convert("RGBA")
    cl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(cl)
    for x, y, s in ((140, 640, 1.0), (760, 560, 0.8), (430, 1000, 0.7), (960, 950, 0.6)):
        for dx, dy, r in ((0, 0, 60), (55, -20, 70), (115, 0, 55), (60, 20, 60)):
            d.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=(255, 255, 255, 200))
    bg.alpha_composite(cl.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(bg)
    # distant hills
    d.ellipse([-400, 1120, 700, 1600], fill=(200, 232, 215)); d.ellipse([450, 1080, 1500, 1600], fill=(190, 228, 210))
    # distant round blossom trees
    for x, y, r in ((120, 1150, 55), (330, 1185, 42), (640, 1130, 50), (900, 1160, 45)):
        d.rectangle([x - 6, y, x + 6, y + 70], fill=(200, 170, 160))
        d.ellipse([x - r, y - r, x + r, y + r * 0.8], fill=(255, 205, 225))
    # meadow
    d.ellipse([-600, 1260, 1700, 2300], fill=(190, 236, 185)); d.rectangle([0, 1500, W, H], fill=(190, 236, 185))
    d.ellipse([-300, 1420, 1400, 2600], fill=(178, 228, 175))
    rnd = random.Random(5)
    for _ in range(120):
        x, y = rnd.randint(10, W - 10), rnd.randint(1330, 1900)
        c = rnd.choice([(255, 250, 210), (255, 200, 225), (220, 205, 255), (255, 230, 150)])
        r = 5 + (y - 1330) / 90
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + math.cos(a) * r - r * 0.6, y + math.sin(a) * r - r * 0.6, x + math.cos(a) * r + r * 0.6, y + math.sin(a) * r + r * 0.6], fill=c)
        d.ellipse([x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5], fill=(255, 215, 110))
    # big cherry-blossom tree (right, behind Owlbert)
    t = P(W, H)
    t.poly([(985, 1440), (1060, 1440), (1050, 900), (1000, 900)], (205, 165, 140), LINE, 4)
    t.line([(1010, 1050), (930, 960)], (205, 165, 140), 26)
    for x, y, r in ((1000, 760, 150), (870, 820, 110), (1080, 900, 120), (930, 700, 95), (1070, 640, 110), (820, 920, 70)):
        t.circ(x, y, r + 4, (240, 170, 200));
    for x, y, r in ((1000, 760, 150), (870, 820, 110), (1080, 900, 120), (930, 700, 95), (1070, 640, 110), (820, 920, 70)):
        t.circ(x, y, r, (255, 200, 222))
    for _ in range(40):
        x, y = rnd.randint(760, 1080), rnd.randint(600, 980)
        t.circ(x, y, rnd.randint(6, 12), (255, 235, 242))
    # stump for Owlbert
    t.rrect(700, 1355, 890, 1490, 20, (215, 175, 140), LINE, 4)
    t.ell(700, 1335, 890, 1380, (240, 210, 170), LINE, 4)
    t.ell(750, 1345, 840, 1370, None, (215, 175, 140), 3)
    bg.alpha_composite(t.done())
    return bg

BG = make_bg()

def make_rainbow():
    r = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(r)
    cols = [(255, 170, 185), (255, 205, 160), (255, 240, 165), (190, 240, 180), (170, 215, 255), (205, 185, 255)]
    for i, c in enumerate(cols):
        R = 560 - i * 34
        d.ellipse([540 - R, 1300 - R, 540 + R, 1300 + R], outline=c + (255,), width=36)
    r = r.filter(ImageFilter.GaussianBlur(3))
    a = np.array(r); a[1240:, :, 3] = 0; return a
RAINBOW = make_rainbow()
@lru_cache(None)
def rainbow(level):
    a = RAINBOW.copy(); a[:, :, 3] = (a[:, :, 3].astype(np.float32) * level / 10 * 0.75).astype(np.uint8)
    return Image.fromarray(a)

SHADOW = Image.new("RGBA", (240, 50), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).ellipse([0, 0, 239, 49], fill=(90, 140, 100, 70))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(5))

def paste(canvas, sp, cx, bottom, sx=1.0, sy=1.0):
    if sx != 1 or sy != 1:
        sp = sp.resize((max(2, int(sp.width * sx)), max(2, int(sp.height * sy))), Image.BILINEAR)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(bottom - sp.height)))

def shadow(canvas, cx, y, s):
    sp = SHADOW.resize((max(2, int(240 * s)), max(2, int(50 * s))))
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(y - sp.height / 2)))

def spark(d, x, y, r, a=255):
    pts = []
    for i in range(8):
        ang = i * math.pi / 4; rr = r if i % 2 == 0 else r * 0.3
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    d.polygon(pts, fill=(255, 245, 170, a))

PETALS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(0.5, 1.2), random.uniform(0, 6)) for _ in range(26)]

def wrap(d, txt, sz, maxw):
    f = font(sz); out, cur = [], ""
    for w in txt.split():
        tr = (cur + " " + w).strip()
        if d.textlength(tr, font=f) <= maxw: cur = tr
        else: out.append(cur); cur = w
    out.append(cur); return out

BX0, BX1, BY0 = 60, 920, 200
def bubble(im, name, col, txt, sz, pop=1.0, sub=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    lines = wrap(d, txt, sz, BX1 - BX0 - 90)
    lh = sz * 1.22
    sublines = wrap(d, sub, 50, BX1 - BX0 - 90) if sub else []
    hgt = 70 + len(lines) * lh + len(sublines) * 64 + 40
    d.rounded_rectangle([BX0, BY0, BX1, BY0 + hgt], radius=44, fill=(255, 255, 255, 238), outline=col, width=7)
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

def blinking(t, off):
    return ((t + off) % 3.7) < 0.13

# positions
HX, HB = 250, 1492          # Hana center x, feet
MX0, MB0 = 520, 1498        # Mochi ground position
OX, OB = 795, 1352          # Owlbert on stump

def mochi_state(t):
    """returns x, bottom, sx, sy, wing, expr, dust_t"""
    i, lt = line_at(t)
    wing = math.sin(t * 5) * 0.4; expr = "happy"; x, b = MX0, MB0; sx = sy = 1.0; dust = None
    if t < INTRO or i == 0:
        b -= abs(math.sin(t * 3)) * 12; wing = math.sin(t * 8) * 0.7
    elif i == 1:
        if lt < 0.4: sy, sx = 1 - 0.12 * ease(lt / 0.4), 1 + 0.1 * ease(lt / 0.4)
        elif lt < 1.6: k = (lt - 0.4) / 1.2; b -= 260 * math.sin(k * math.pi / 2) ** 0.8; wing = math.sin(t * 28)
        elif lt < 2.4: k = (lt - 1.6) / 0.8; b -= 260 * (1 - k * k); wing = math.sin(t * 28) * 0.5; expr = "wow"
        else:
            k = lt - 2.4; q = 0.2 * math.exp(-k * 5) * math.cos(k * 18)
            sy, sx = 1 - q, 1 + q; expr = "sad"; wing = -0.8; dust = k
    elif i == 2:
        expr = "sad" if lt < 2.2 else "happy"; wing = -0.8 if lt < 2.2 else math.sin(t * 6) * 0.5
        if lt >= 2.2: b -= abs(math.sin(t * 4)) * 10
    elif i == 3:
        wing = math.sin(t * (6 if lt < 2.5 else 11)) * (0.5 if lt < 2.5 else 0.9)
        b -= abs(math.sin(t * 5)) * (8 if lt < 2.5 else 30)
    elif i == 4:
        wing = math.sin(t * 16); k = ease((lt - 0.3) / 3.4)
        b = MB0 - 520 * k + math.sin(t * 3) * 10 * k; x = MX0 + 40 * k; expr = "wow" if lt < 2.4 else "joy"
    elif i == 5:
        wing = math.sin(t * 14); expr = "joy"
        a = lt * 1.3
        x = 560 + 170 * math.sin(a); b = MB0 - 520 - 80 * math.sin(2 * a) + 40 * (1 - math.cos(a)) * 0
    elif i == 6 or t >= T_OUTRO:
        wing = math.sin(t * 12); expr = "joy"
        tt = t - (LINES[6][2])
        k = ease(tt / 1.5)
        x5 = 560 + 170 * math.sin(LINES[5][3] * 1.3); b5 = MB0 - 520 - 80 * math.sin(2 * LINES[5][3] * 1.3)
        x = x5 + (540 - x5) * k; b = b5 + (MB0 - 470 - b5) * k + math.sin(t * 3) * 14
    return x, b, sx, sy, wing, expr, dust

# ---------- render ----------
import os, sys
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

FRAME_SAVE = {}
for fi in FRAMES:
    t = fi / FPS
    im = BG.copy()
    i, lt = line_at(t)
    # rainbow in last line + outro
    if t >= LINES[6][2]:
        lvl = min(10, int((t - LINES[6][2]) / 1.5 * 10))
        if lvl > 0: im.alpha_composite(rainbow(lvl))
    d = ImageDraw.Draw(im)
    # falling petals (behind characters)
    for k, (px, py, sp, ph) in enumerate(PETALS):
        y = (py + t * 70 * sp) % (H + 60) - 30
        x = (px + math.sin(t * 1.3 + ph) * 40) % W
        r = 9 * sp + 4; a = t * 2 + ph
        d.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55], fill=(255, 190, 215))
    # Owlbert
    om, ob = talking("Professor Owlbert", t)
    owing = 0.0
    if i == 3 and lt > 2.2: owing = (math.sin(t * 11) + 1) / 2
    if i == 5: owing = (math.sin(t * 8) + 1) / 2 * 0.6
    if t >= T_OUTRO: owing = (math.sin(t * 6) + 1) / 2 * 0.5
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob)
    # Hana
    hm, hb = talking("Hana", t)
    arms = (i == 5) or (t >= T_OUTRO) or (i == 2 and lt > 3.2)
    shadow(im, HX, HB - 4, 0.8)
    paste(im, hana(hm, arms, blinking(t, 0.0)), HX, HB + 8 - hb - (abs(math.sin(t * 6)) * 16 if i == 5 else 0))
    # Mochi
    x, b, sx, sy, wing, expr, dust = mochi_state(t)
    mm, mb = talking("Mochi", t)
    hgt = MB0 - b
    shadow(im, x, MB0 - 6, max(0.35, 0.9 - hgt / 900))
    if dust is not None and dust < 1.2:
        dd = ImageDraw.Draw(im)
        for s in (-1, 1):
            for j in range(3):
                r = 14 + dust * 30 - j * 6; a = int(200 * (1 - dust / 1.2))
                dx = x + s * (70 + dust * 120 + j * 30); dy = MB0 - 20 - j * 14 - dust * 20
                dd.ellipse([dx - r, dy - r, dx + r, dy + r], fill=(255, 255, 255, a))
    paste(im, mochi(mm, round(wing * 4) / 4, expr, blinking(t, 2.3) and expr != "joy"), x, b + 50 - mb, sx, sy)
    d = ImageDraw.Draw(im)
    # sparkles when flying
    if (i is not None and i >= 4) or t >= T_OUTRO:
        for k in range(6):
            ph = (t * 1.6 + k / 6) % 1
            ang = k * 1.05 + t
            sx_ = x - 60 * math.cos(ang) * (1 + ph); sy_ = b - 100 + 120 * ph + 30 * math.sin(ang)
            spark(d, sx_, sy_, 18 * (1 - ph) + 4, int(255 * (1 - ph)))
    # captions
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "Mochi Can't Fly Yet", 78, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (130, 200, 150), "Keep trying!", 120, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 66, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"/tmp/prev_{fi/FPS:.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio (original) ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=5.0):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if shape == "bell": w = w + 0.35 * np.sin(2 * np.pi * freq * 2 * tt) + 0.12 * np.sin(2 * np.pi * freq * 3.01 * tt)
    if shape == "pad": w = w + 0.3 * np.sin(2 * np.pi * freq * 2.003 * tt); env = np.minimum(1, tt * 4) * np.minimum(1, (dur - tt) * 3)
    else: env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at):
    i0 = int(at * SR)
    if i0 >= N: return
    j = min(N, i0 + len(sig)); audio[i0:j] += sig[:j - i0]

n = {"F3": 174.61, "Bb2": 116.54, "C3": 130.81, "D3": 146.83, "F4": 349.23, "G4": 392.0, "A4": 440.0, "Bb4": 466.16,
     "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46}
# gentle 3/4 waltz in F — original melody
mel = ["A4", "C5", "F5", "E5", "D5", "C5", "D5", "F5", "D5", "C5", None, "A4",
       "Bb4", "D5", "C5", "A4", "G4", "F4", "G4", "A4", "C5", "F4", None, None]
bass = ["F3", "Bb2", "C3", "F3", "D3", "Bb2", "C3", "F3"]
beat = 0.42; k = 0
music = np.zeros(N); saved = audio; audio = music
while k * beat < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(n[m], 1.0, 0.07, "bell", 3.5), k * beat)
    if k % 3 == 0: add(tone(n[bass[(k // 3) % 8]], beat * 3, 0.06, "pad"), k * beat)
    k += 1
audio = saved
# duck music under dialogue
duck = np.ones(N)
for spk, txt, st, dur, talk in LINES:
    a, b_ = int((st + 0.2) * SR), int((st + 0.4 + talk) * SR); duck[a:b_] = 0.65
duck = np.convolve(duck, np.ones(4410) / 4410, mode="same")
audio += music * duck
# soft talk "blips" per character (no words, just gentle pitch chirps)
base = {"Hana": 620, "Mochi": 820, "Professor Owlbert": 330}
rnd = random.Random(9)
for spk, txt, st, dur, talk in LINES:
    if spk not in base: continue
    tt = st + 0.3
    while tt < st + 0.3 + talk:
        add(tone(base[spk] * rnd.choice([1, 1.12, 1.25, 0.9]), 0.09, 0.035, "sine", 25), tt); tt += 0.143 * 2
# sfx
add(tone(784, 0.8, 0.14, "bell", 3), 0.1); add(tone(1046.5, 1.0, 0.14, "bell", 3), 0.5)
L1 = LINES[1][2]
sw = np.arange(int(1.1 * SR)) / SR; add(0.08 * np.sin(2 * np.pi * (300 * sw + 250 * sw * sw)) * np.minimum(1, (1.1 - sw) * 4), L1 + 0.4)
add(tone(110, 0.5, 0.35, "sine", 9) + tone(165, 0.5, 0.1, "sine", 12), L1 + 2.4)
add(tone(392, 0.5, 0.1, "bell", 5), L1 + 2.7); add(tone(330, 0.7, 0.1, "bell", 4), L1 + 3.0)
L4 = LINES[4][2]
for j, f in enumerate([523.25, 587.33, 659.25, 783.99, 880, 1046.5]):
    add(tone(f, 0.8, 0.1, "bell", 4), L4 + 0.4 + j * 0.5)
L5 = LINES[5][2]
for j, f in enumerate([698.46, 880, 1046.5, 1396.9]): add(tone(f, 1.0, 0.12, "bell", 3), L5 + 0.05 + j * 0.12)
for j, f in enumerate([523.25, 659.25, 783.99, 1046.5, 1318.5]): add(tone(f, 1.4, 0.11, "bell", 2.5), T_OUTRO + 0.1 + j * 0.16)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = audio * fade
pk = np.abs(audio).max(); audio = audio / pk * 0.8 if pk > 0.8 else audio
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((np.clip(audio, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", OUT, round(TOTAL, 1))
