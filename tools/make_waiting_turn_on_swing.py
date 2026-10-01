"""Petal Valley (Anime Adventures): Waiting for your turn on the swing — lesson: patience.
Original characters, art and music. Renders kids/waiting_turn_on_swing.mp4 (captions + music, no voice).
Character designs match make_new_friend_looks_different.py (Hana, Mochi, Professor Owlbert)."""
import math, random, subprocess, wave, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/waiting_turn_on_swing.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (75, 55, 95)
LINE = (120, 95, 140)
random.seed(8484)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

SCRIPT = [
    ("Narrator", "Hana and Mochi ran to the big tree swing in Petal Valley."),
    ("Mochi", "Wheee! Up, up, up! I love the swing!"),
    ("Hana", "I want a turn now! Hurry, Mochi!"),
    ("Professor Owlbert", "Waiting can be fun, Hana. Let's count to ten together!"),
    ("Hana", "One, two, three, four, five... six, seven, eight, nine, ten!"),
    ("Mochi", "Your turn, Hana! Thank you for waiting!"),
    ("Narrator", "Be patient and take turns. Waiting makes everyone happy!"),
]
SPK_COL = {"Narrator": (150, 130, 220), "Mochi": (90, 170, 240), "Hana": (240, 120, 170),
           "Professor Owlbert": (190, 140, 90)}
INTRO, OUTRO = 3.4, 4.6
LINES, t = [], INTRO
for spk, txt in SCRIPT:
    words = len(txt.split())
    talk = words * 0.34 + 0.4
    dur = max(5.2, talk + 1.8)
    if spk == "Hana" and "ten!" in txt: dur = talk + 2.6
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

# ================= morning playground under the peach-leaf swing tree (new for this episode) =================
def fx_layer(): return Image.new("RGBA", (W, H), (0, 0, 0, 0))
def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.97, y - r * 0.15), (x + r * 0.97, y - r * 0.15), (x, y + r * 1.05)], fill=col)

SKY = vgrad(W, H, [(0, (200, 236, 245)), (0.3, (225, 240, 236)), (0.5, (255, 236, 220)), (0.62, (215, 238, 200)), (1, (175, 220, 170))]).convert("RGBA")
PIVX, PIVY, ROPE = 600, 770, 545
BRANCH_Y = 770
DY = 100

def make_land():
    t = P(W, H)
    # far hills with mushroom cottages
    t.poly([(-60, 1060), (180, 990), (420, 1040), (690, 975), (900, 1030), (1140, 990), (1140, 1200), (-60, 1200)], (200, 228, 215))
    for hx, hy, cap in ((300, 1030, (255, 170, 160)), (760, 1015, (190, 175, 240))):
        t.rrect(hx - 26, hy - 10, hx + 26, hy + 32, 8, (255, 245, 230), LINE, 3)
        t.chord(hx - 52, hy - 52, hx + 52, hy + 22, 180, 360, cap)
        t.arc(hx - 52, hy - 52, hx + 52, hy + 22, 180, 360, LINE, 3)
        for dx in (-24, 6, 28): t.circ(hx + dx, hy - 26 + abs(dx) * 0.2, 7, (255, 255, 255))
        t.rrect(hx - 8, hy + 6, hx + 8, hy + 32, 6, (190, 145, 125))
    # meadow
    t.poly([(-60, 1110), (1140, 1100), (1140, H + 10), (-60, H + 10)], (185, 228, 170))
    # sandy patch under the swing
    t.ell(330, 1330, 880, 1440, (245, 225, 185))
    t.ell(350, 1340, 860, 1430, (252, 236, 200))
    # wooden fence on the right
    for x in (870, 940, 1010, 1080):
        t.rrect(x - 14, 1150, x + 14, 1300, 6, (235, 205, 165), LINE, 3)
        t.poly([(x - 14, 1152), (x, 1132), (x + 14, 1152)], (235, 205, 165), LINE, 3)
    t.rrect(850, 1185, 1100, 1203, 4, (225, 190, 150), LINE, 3)
    t.rrect(850, 1245, 1100, 1263, 4, (225, 190, 150), LINE, 3)
    # big tree: trunk on the left, long branch for swing + Owlbert
    t.poly([(20, 1360), (60, 760 + DY), (170, 760 + DY), (210, 1360)], (180, 135, 115), LINE, 4)
    t.arc(70, 950, 130, 1030, 200, 340, (150, 110, 95), 4)
    t.poly([(140, 690 + DY), (900, BRANCH_Y - 18), (912, BRANCH_Y + 18), (150, 760 + DY)], (180, 135, 115), LINE, 4)
    t.circ(905, BRANCH_Y, 20, (180, 135, 115), LINE, 4)
    # peach leaf canopy (top-left), sits under caption zone edge
    for x, y, r in ((40, 590, 140), (180, 560, 120), (-30, 720, 110), (290, 610, 90), (120, 700, 100)):
        t.circ(x, y + DY, r + 4, (240, 165, 140)); t.circ(x, y + DY, r, (255, 200, 175))
    for x, y in ((30, 560), (170, 520), (270, 600), (100, 680), (-10, 680), (200, 640)):
        t.circ(x, y + DY, 16, (255, 228, 205))
    # tulips along the bottom-left meadow
    rnd = random.Random(31)
    for k in range(9):
        x = 40 + k * 95 + rnd.randint(-15, 15); y = 1500 + rnd.randint(-20, 30)
        if 330 < x < 880 and y < 1450: continue
        col = rnd.choice([(255, 170, 190), (255, 210, 120), (200, 180, 250)])
        t.line([(x, y), (x, y + 60)], (110, 180, 110), 6)
        t.ell(x - 20, y + 20, x - 2, y + 50, (140, 205, 140))
        t.poly([(x - 18, y - 10), (x - 18, y - 36), (x - 8, y - 22), (x, y - 40), (x + 8, y - 22), (x + 18, y - 36), (x + 18, y - 10), (x, y + 4)], col, LINE, 2)
    im = t.done()
    d = ImageDraw.Draw(im)
    for _ in range(60):
        x, y = rnd.randint(10, W - 10), rnd.randint(1140, 1900)
        if 320 < x < 890 and 1320 < y < 1450: continue
        c = rnd.choice([(150, 205, 140), (205, 238, 185)])
        d.line([(x - 6, y), (x - 9, y - 12)], fill=c, width=4); d.line([(x, y), (x, y - 15)], fill=c, width=4); d.line([(x + 6, y), (x + 9, y - 12)], fill=c, width=4)
    return im
LAND = make_land()

@lru_cache(None)
def seat():
    p = P(250, 60)
    p.rrect(5, 8, 245, 46, 14, (255, 190, 150), LINE, 4)
    p.rrect(18, 14, 232, 22, 4, (255, 220, 195))
    for x in (60, 125, 190):
        for a in range(5):
            aa = a * 1.2566
            p.circ(x + math.cos(aa) * 7, 32 + math.sin(aa) * 7, 5, (255, 255, 255))
        p.circ(x, 32, 4, (255, 210, 100))
    return p.done()

def swing_pos(theta):
    sx = PIVX + math.sin(theta) * ROPE; sy = PIVY + math.cos(theta) * ROPE
    return sx, sy

def draw_ropes(d, theta):
    sx, sy = swing_pos(theta)
    ca, sa = math.cos(theta), math.sin(theta)
    for off in (-95, 95):
        tx, ty = PIVX + off * ca, PIVY - off * sa * 0.0
        bx, by = sx + off * ca, sy - off * sa
        d.line([(PIVX + off * 0.6, PIVY), (bx, by)], fill=(150, 115, 90), width=8)
        d.line([(PIVX + off * 0.6, PIVY), (bx, by)], fill=(225, 190, 150), width=4)
    for off in (-57, 57):
        d.ellipse([PIVX + off - 14, PIVY - 14, PIVX + off + 14, PIVY + 14], outline=(150, 115, 90), width=6)

def paste_seat(im, theta):
    sx, sy = swing_pos(theta)
    sp = seat().rotate(math.degrees(theta), resample=Image.BICUBIC, expand=True)
    paste_c(im, sp, sx, sy + 8)

def flower_counter(d, x, y, n, col, q):
    r = 46 * q
    if r < 2: return
    for a in range(6):
        aa = a * math.pi / 3
        d.ellipse([x + math.cos(aa) * r * 0.55 - r * 0.5, y + math.sin(aa) * r * 0.55 - r * 0.5,
                   x + math.cos(aa) * r * 0.55 + r * 0.5, y + math.sin(aa) * r * 0.55 + r * 0.5], fill=col)
    d.ellipse([x - r * 0.62, y - r * 0.62, x + r * 0.62, y + r * 0.62], fill=(255, 255, 255))
    f = font(int(52 * q)); s = str(n); w_ = d.textlength(s, font=f)
    d.text((x - w_ / 2, y - 37 * q), s, font=f, fill=INK)

BUTTERFLIES = [(random.uniform(0, 6), random.uniform(0.5, 0.9), c) for c in ((255, 180, 210), (180, 200, 255), (255, 220, 130))]
def butterfly(d, x, y, flap, col):
    w_ = 22 * (0.4 + 0.6 * abs(math.sin(flap)))
    d.ellipse([x - w_ - 4, y - 20, x - 2, y + 2], fill=col); d.ellipse([x + 2, y - 20, x + w_ + 4, y + 2], fill=col)
    d.ellipse([x - w_ * 0.8, y - 2, x - 2, y + 14], fill=col); d.ellipse([x + 2, y - 2, x + w_ * 0.8, y + 14], fill=col)
    d.rounded_rectangle([x - 3, y - 16, x + 3, y + 14], radius=3, fill=LINE)

def talking(spk, t):
    i, lt = line_at(t)
    if i is None or LINES[i][0] != spk: return False, 0
    talk = LINES[i][4]
    if 0.3 < lt < 0.3 + talk:
        return (int((lt - 0.3) * 7) % 2 == 0), abs(math.sin((lt - 0.3) * 9)) * 14
    return False, 0

L = [ln[2] for ln in LINES]
OX, OB, OS = 800, BRANCH_Y - 2, 0.72
HX0, HB, HS = 195, 1555, 0.82
SWAP = L[5]                    # Mochi hops off, Hana climbs on
COUNT_T0 = L[4] + 0.3          # counting flowers appear one by one
COUNT_STEP = (LINES[4][4]) / 10
FLOWER_COLS = [(255, 175, 200), (255, 205, 120), (170, 220, 170), (170, 205, 250), (210, 185, 250)]

def swing_theta(t):
    if t < L[0] + 1.0: amp = 0.05 + 0.25 * ease((t - 0.5) / 2.5)
    elif t < SWAP: amp = 0.32
    elif t < SWAP + 1.6: amp = 0.32 * (1 - ease((t - SWAP) / 1.4))
    elif t < SWAP + 2.6: amp = 0.0
    else: amp = 0.30 * ease((t - SWAP - 2.6) / 1.5)
    return math.sin(t * 2.3) * amp

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
    put_glow(im, 760, 860, 200, (255, 245, 215), 0.6)
    d = ImageDraw.Draw(im)
    for cx0, cy0, s, sp in ((300, 820, 0.9, 9), (820, 900, 0.7, 6)):
        x = (cx0 + t * sp) % (W + 300) - 150
        for dx, dy, r in ((0, 0, 50), (-55, 12, 36), (55, 12, 38), (25, -25, 34)):
            d.ellipse([x + dx * s - r * s, cy0 + dy * s - r * s, x + dx * s + r * s, cy0 + dy * s + r * s], fill=(255, 252, 250))
    im.alpha_composite(LAND)
    d = ImageDraw.Draw(im)

    # ---- Owlbert on the branch ----
    om, ob = talking("Professor Owlbert", t)
    owing = (math.sin(t * 5) + 1) / 2 * 0.5 if ph == 3 else ((math.sin(t * 4) + 1) / 2 * 0.35 if ph >= 6 else 0.0)
    paste(im, owl(om, round(owing * 4) / 4, blinking(t, 1.1)), OX, OB - ob, OS, OS)

    # ---- swing ----
    theta = swing_theta(t)
    sx, sy = swing_pos(theta)
    shadow(im, sx, 1395, 0.9)
    d = ImageDraw.Draw(im)
    draw_ropes(d, theta)

    # ---- Mochi ----
    mm, mb = talking("Mochi", t)
    mwing = math.sin(t * 6) * 0.5
    if t < SWAP:
        mx, mbot = sx, sy + 14
        mexpr = "joy" if (ph in (1,) and not mm and lt > 0.3) else "happy"
        if ph == 2 and lt > 1.5: mexpr = "happy"
    else:
        q = ease((t - SWAP) / 1.4)
        if t - SWAP < 1.4: mx0, mb0 = sx, sy + 14
        else: mx0, mb0 = PIVX, PIVY + ROPE + 14
        tx, tb = 800, 1140
        mx = lerp(mx0, tx, q); mbot = lerp(mb0, tb, q) - math.sin(q * math.pi) * 160 - abs(math.sin(t * 2.5)) * 10
        mexpr = "happy" if mm else "joy"
        mwing = math.sin(t * 9) * 0.8
    paste(im, mochi(mm, round(mwing * 4) / 4, mexpr, blinking(t, 2.3) and mexpr != "joy"), mx, mbot - mb, 0.72, 0.72)
    d = ImageDraw.Draw(im)

    # ---- Hana ----
    hm, hb = talking("Hana", t)
    hsad = ph == 2 and lt > 0.2
    on_swing = t >= SWAP + 1.9
    if not on_swing:
        if t >= SWAP + 0.4:
            q = ease((t - SWAP - 0.4) / 1.5)
            hx = lerp(HX0, PIVX, q); hbot = lerp(HB, PIVY + ROPE + 90, q) - math.sin(q * math.pi) * 60
        else:
            hx, hbot = HX0, HB
        stomp = abs(math.sin(lt * 10)) * 12 if (ph == 2 and lt < 2.2) else 0
        hop = abs(math.sin(t * 6)) * 12 if (ph == 4 and lt > LINES[4][4] + 0.3) else 0
        harms = (ph == 4 and lt > LINES[4][4] + 0.3) or (ph == 2 and int(lt * 4) % 2 == 0 and lt < 2.2)
        shadow(im, hx, hbot - 4, 0.7)
        paste(im, hana(hm, harms, blinking(t, 0.0), hsad), hx, hbot - hb - stomp - hop, HS, HS)
        paste_seat(im, theta)
    else:
        harms = ph >= 6 and int(t * 2) % 2 == 0
        paste(im, hana(hm, harms, blinking(t, 0.0), False), sx, sy + 90 - hb, 0.72, 0.72)
        paste_seat(im, theta)
    if t < SWAP and False: pass
    d = ImageDraw.Draw(im)

    # Hana's impatient "!" and then the gentle counting card
    if ph == 2 and 0.3 < lt < 3.0:
        q = ease((lt - 0.3) / 0.3)
        f = font(int(140 * q) + 4); w_ = d.textlength("!", font=f)
        d.text((HX0 + 150 - w_ / 2, HB - 700), "!", font=f, fill=(240, 120, 170), stroke_width=6, stroke_fill=(255, 255, 255))
    if (ph == 3 and lt > 1.2) or ph == 4 or (ph == 5 and lt < 0.6):
        q = ease((lt - 1.2) / 0.5) if ph == 3 else (1 - ease(lt / 0.6) if ph == 5 else 1)
        lay = fx_layer(); dl = ImageDraw.Draw(lay)
        x0, y0, x1, y1 = 270, 800, 910, 1090
        dl.rounded_rectangle([x0, y0, x1, y1], radius=36, fill=(255, 255, 255, 225), outline=(190, 140, 90), width=6)
        for n in range(1, 11):
            row, col = divmod(n - 1, 5)
            fx = 340 + col * 125; fy = 880 + row * 128
            if ph == 4:
                at = COUNT_T0 + (n - 1) * COUNT_STEP
                qq = 0 if t < at else min(1.0, 0.2 + (t - at) / 0.25)
                if qq < 1 and t >= at: qq = 1 + math.sin(qq * math.pi) * 0.15
            elif ph == 5: qq = 1
            else: qq = 0
            if qq <= 0:
                dl.ellipse([fx - 16, fy - 16, fx + 16, fy + 16], fill=(235, 225, 240))
            else:
                flower_counter(dl, fx, fy, n, FLOWER_COLS[(n - 1) % 5], qq)
        if q < 1:
            a_ = np.array(lay); a_[:, :, 3] = (a_[:, :, 3] * q).astype(np.uint8); lay = Image.fromarray(a_)
        im.alpha_composite(lay); d = ImageDraw.Draw(im)

    # butterflies always; hearts + sparkles at the happy end
    lay = fx_layer(); dl = ImageDraw.Draw(lay)
    for off, sp, col in BUTTERFLIES:
        bx_ = 120 + ((t * 40 * sp + off * 120) % 760)
        by_ = 1180 + math.sin(t * sp * 2 + off) * 80
        butterfly(dl, bx_, by_, t * 14 + off, col + (230,))
    if ph >= 5 and t > SWAP + 2.0:
        for k in range(6):
            q = ((t - SWAP) * 0.35 + k / 6) % 1
            heart(dl, 220 + k * 115 + math.sin(t * 2 + k) * 18, 1150 - q * 240, 18 + 5 * (k % 2), (255, 150, 190, int(230 * (1 - q))))
    im.alpha_composite(lay)

    # ---- captions ----
    if t < INTRO:
        bubble(im, "Petal Valley", (240, 150, 190), "Waiting for a Turn", 88, ease(t / 0.5), sub="An Anime Adventure")
    elif t >= T_OUTRO:
        lt2 = t - T_OUTRO
        bubble(im, None, (180, 150, 230), "Take turns and be patient!", 80, ease(lt2 / 0.5),
               sub="Subscribe to Dreamforge Kids for more!" if lt2 > 1.2 else None)
    else:
        spk, txt, st_, dur, talk = LINES[i]
        bubble(im, spk, SPK_COL[spk], txt, 64, ease(lt / 0.35))
    frame = im.convert("RGB")
    if PREVIEW: frame.save(f"{os.environ.get('PREVDIR', '/tmp')}/prev_{fi/FPS:05.1f}.png"); continue
    proc.stdin.write(frame.tobytes())
if PREVIEW: sys.exit(0)
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle swing waltz in F major (3/4), kalimba + music box + soft pad ----------
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
    if i0 >= N or i0 < 0: return
    j = min(N, i0 + len(sig)); buf[i0:j] += sig[:j - i0]
f = lambda m: 440 * 2 ** ((m - 69) / 12)
# waltz: 3 beats per bar, melody per beat (None = rest), 8 bars, original
mel = [72, 77, 81,  79, None, 77,  76, 77, 79,  72, None, None,
       74, 77, 81,  82, 81, 79,   77, 76, 74,  77, None, None]
chords = [(53, 57, 60), (48, 52, 55), (48, 52, 55), (53, 57, 60), (50, 53, 57), (46, 50, 53), (48, 52, 55), (53, 57, 60)]
beat = 0.42; music = np.zeros(N); k = 0
while k * beat < TOTAL - 1:
    m = mel[k % len(mel)]
    if m: add(tone(f(m), 1.1, 0.042, "box", 3.2), k * beat, music)
    bar = k // 3; ch = chords[bar % len(chords)]
    if k % 3 == 0:
        for n_ in ch: add(tone(f(n_), beat * 3, 0.013, "pad"), k * beat, music)
        add(tone(f(ch[0] - 12), 1.0, 0.04, "pluck", 3), k * beat, music)
    else:
        add(tone(f(ch[1] + 12), 0.3, 0.014, "pluck", 9), k * beat, music)
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
# sfx
for j, m in enumerate([72, 77, 81, 84]): add(tone(f(m), 1.0, 0.07, "bell", 3), 0.1 + j * 0.18)          # title
for n in range(10): add(tone(f(72 + [0, 2, 4, 5, 7, 9, 11, 12, 14, 16][n]), 0.5, 0.06, "bell", 6), COUNT_T0 + n * COUNT_STEP)  # counting
for j, m in enumerate([84, 88, 91]): add(tone(f(m), 0.7, 0.05, "bell", 4), SWAP + 1.9 + j * 0.13)      # Hana on the swing
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
