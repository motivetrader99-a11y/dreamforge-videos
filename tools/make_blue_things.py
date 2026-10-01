"""Dreamforge Kids — Blue things.
A sunny pastel garden where four things start out grey: a kite in the sky, a little bird on a
tree branch, a basket of berries and a pair of rain boots. Twinkle the star sends a trail of
sparkles to each one and a blue paint bloom spreads across it — the thing turns BLUE and its
name appears. Quiz on three picture cards (green leaf, blue butterfly, orange carrot): which
one is blue? The butterfly flutters. Outro: the blue things gather round Twinkle.
Captions sit in a panel above the Shorts UI. Original art & music (soft plucked lullaby in F
major, 4/4, with a warm pad)."""
import math, random, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/blue_things.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (55, 45, 80)
BLUE = (40, 110, 230)
BLUE_D = (25, 75, 175)
BLUE_L = (120, 175, 255)
random.seed(77)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, SEG, QUIZ, OUTRO = 5.0, 6.0, 9.5, 6.5
NOBJ = 4
SEG_T = [INTRO + i * SEG for i in range(NOBJ)]
T_QUIZ = INTRO + NOBJ * SEG
T_OUT = T_QUIZ + QUIZ
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)
REVEAL_AT = 1.3   # seconds into a segment when the paint bloom starts

NAMES = ["kite", "bluebird", "blueberries", "boots"]
LINES = [
    (0.3, INTRO - 0.1, "Hi! I'm Twinkle! Let's find BLUE things!"),
    (SEG_T[0] + 0.2, SEG_T[0] + SEG - 0.1, "Look up! A blue kite in the sky!"),
    (SEG_T[1] + 0.2, SEG_T[1] + SEG - 0.1, "A little bluebird says tweet, tweet!"),
    (SEG_T[2] + 0.2, SEG_T[2] + SEG - 0.1, "Blueberries! Small, round and blue!"),
    (SEG_T[3] + 0.2, SEG_T[3] + SEG - 0.1, "Blue boots for splashy puddles!"),
    (T_QUIZ + 0.2, T_QUIZ + 5.0, "Which one is blue? Can you find it?"),
    (T_QUIZ + 5.1, T_OUT - 0.1, "The butterfly! The butterfly is blue!"),
    (T_OUT + 0.3, TOTAL - 0.4, "Blue, blue, blue! You did it! Bye-bye!"),
]
TALK = [(a, a + min(b - a - 0.3, len(txt.split()) * 0.42 + 0.6)) for a, b, txt in LINES]
def talking(t): return any(a <= t < b for a, b in TALK)

# ---------- helpers ----------
def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def paste(canvas, sp, cx, cy, s=1.0, rot=0, alpha=1.0):
    if s <= 0.02 or alpha <= 0.01: return
    if s != 1.0:
        sp = sp.resize((max(2, int(sp.width * s)), max(2, int(sp.height * s))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        sp = sp.copy(); sp.putalpha(sp.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def text_c(d, txt, cx, y, sz, fill, stroke=(255, 255, 255), sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def gloss(im, box, a=120, blur=6):
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(box, fill=(255, 255, 255, a))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(blur)))

def face(d, cx, cy, r, ink=(45, 35, 60)):
    e = r * 0.11
    for dx in (-r * 0.3, r * 0.3):
        d.ellipse([cx + dx - e, cy - e * 1.3, cx + dx + e, cy + e * 1.3], fill=ink)
        d.ellipse([cx + dx - e * 0.5, cy - e * 1.0, cx + dx + e * 0.1, cy - e * 0.3], fill=(255, 255, 255))
    d.arc([cx - r * 0.2, cy + r * 0.02, cx + r * 0.2, cy + r * 0.32], 20, 160, fill=ink, width=max(3, int(r * 0.07)))
    for dx in (-r * 0.52, r * 0.52):
        d.ellipse([cx + dx - r * 0.12, cy + r * 0.12, cx + dx + r * 0.12, cy + r * 0.26], fill=(255, 150, 175, 170))

def canvas(r):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); return im, ImageDraw.Draw(im), s / 2

# ---------- Twinkle ----------
def make_twinkle(r, mouth_open):
    im, d, c = canvas(r)
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(c, c, r * 1.12), fill=(255, 225, 90, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.16))); d = ImageDraw.Draw(im)
    d.polygon(star_poly(c, c + r * 0.05, r), fill=(228, 165, 30))
    d.polygon(star_poly(c, c, r), fill=(255, 210, 60))
    e = r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([c + dx - e, c - e * 1.4, c + dx + e, c + e * 1.2], fill=(70, 40, 60))
        d.ellipse([c + dx - e * 0.5, c - e * 1.1, c + dx + e * 0.1, c - e * 0.4], fill=(255, 255, 255))
    if mouth_open:
        d.ellipse([c - r * 0.13, c + r * 0.12, c + r * 0.13, c + r * 0.36], fill=(150, 50, 60))
        d.ellipse([c - r * 0.07, c + r * 0.25, c + r * 0.07, c + r * 0.34], fill=(255, 130, 140))
    else:
        d.arc([c - r * 0.16, c + r * 0.05, c + r * 0.16, c + r * 0.28], 20, 160, fill=(70, 40, 60), width=max(3, int(r * 0.06)))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([c + dx - r * 0.1, c + r * 0.1, c + dx + r * 0.1, c + r * 0.22], fill=(255, 130, 150, 150))
    return im

# ---------- blue things ----------
def make_kite(r):
    im, d, c = canvas(r)
    top, left, right, bot = (c, c - r * 0.95), (c - r * 0.7, c - r * 0.1), (c + r * 0.7, c - r * 0.1), (c, c + r * 0.85)
    # tail
    pts = [(c + math.sin(i * 0.9) * r * 0.18, c + r * 0.85 + i * r * 0.11) for i in range(12)]
    d.line(pts, fill=(90, 90, 120), width=max(3, int(r * 0.04)))
    for i in (3, 6, 9):
        x, y = pts[i]
        d.polygon([(x, y), (x - r * 0.14, y - r * 0.08), (x - r * 0.14, y + r * 0.08)], fill=BLUE_L)
        d.polygon([(x, y), (x + r * 0.14, y - r * 0.08), (x + r * 0.14, y + r * 0.08)], fill=BLUE_L)
    d.polygon([top, right, bot, left], fill=BLUE_D)
    d.polygon([top, (right[0] - r * 0.05, right[1]), (c, bot[1] - r * 0.06), (left[0] + r * 0.05, left[1])], fill=BLUE)
    d.polygon([top, right, (c, c - r * 0.1)], fill=BLUE_L)
    d.polygon([left, bot, (c, c - r * 0.1)], fill=BLUE_L)
    d.line([top, bot], fill=(250, 250, 255), width=max(3, int(r * 0.035)))
    d.line([left, right], fill=(250, 250, 255), width=max(3, int(r * 0.035)))
    face(d, c, c + r * 0.12, r * 0.42)
    return im

def make_bird(r):
    im, d, c = canvas(r)
    # tail
    d.polygon([(c - r * 0.7, c + r * 0.1), (c - r * 1.15, c - r * 0.25), (c - r * 1.05, c + r * 0.35)], fill=BLUE_D)
    d.ellipse([c - r * 0.85, c - r * 0.75, c + r * 0.75, c + r * 0.8], fill=BLUE)
    d.ellipse([c - r * 0.35, c - r * 0.05, c + r * 0.6, c + r * 0.75], fill=(235, 242, 255))
    # wing
    d.chord([c - r * 0.65, c - r * 0.2, c + r * 0.15, c + r * 0.55], 180, 360, fill=BLUE_D)
    d.ellipse([c - r * 0.65, c + r * 0.0, c + r * 0.15, c + r * 0.4], fill=BLUE_D)
    # head tuft
    d.polygon([(c - r * 0.05, c - r * 0.7), (c + r * 0.1, c - r * 1.0), (c + r * 0.2, c - r * 0.68)], fill=BLUE_D)
    # beak
    d.polygon([(c + r * 0.7, c - r * 0.18), (c + r * 1.05, c - r * 0.05), (c + r * 0.7, c + r * 0.08)], fill=(255, 170, 60))
    # eye
    e = r * 0.12
    d.ellipse([c + r * 0.3 - e, c - r * 0.35 - e * 1.2, c + r * 0.3 + e, c - r * 0.35 + e * 1.2], fill=(40, 30, 55))
    d.ellipse([c + r * 0.27 - e * 0.4, c - r * 0.45, c + r * 0.27 + e * 0.2, c - r * 0.38], fill=(255, 255, 255))
    d.ellipse([c + r * 0.38, c - r * 0.12, c + r * 0.58, c + r * 0.0], fill=(255, 150, 175, 170))
    # feet
    for dx in (-r * 0.1, r * 0.2):
        d.line([c + dx, c + r * 0.78, c + dx, c + r * 0.95], fill=(255, 160, 60), width=max(3, int(r * 0.06)))
    gloss(im, [c - r * 0.6, c - r * 0.6, c - r * 0.2, c - r * 0.35], 110)
    return im

def make_berries(r):
    im, d, c = canvas(r)
    # berries heap (drawn first, basket rim in front)
    spots = [(-0.45, -0.15), (-0.1, -0.3), (0.3, -0.2), (0.6, 0.0), (-0.65, 0.05), (0.1, 0.0), (-0.3, 0.05), (0.45, -0.45), (-0.2, -0.55)]
    br = r * 0.25
    for dx, dy in spots:
        x, y = c + dx * r, c + dy * r
        d.ellipse([x - br, y - br, x + br, y + br], fill=BLUE_D)
        d.ellipse([x - br * 0.92, y - br * 0.98, x + br * 0.88, y + br * 0.8], fill=(70, 95, 210))
        d.polygon(star_poly(x, y - br * 0.55, br * 0.28, inner=0.45), fill=(35, 45, 120))
        d.ellipse([x - br * 0.6, y - br * 0.6, x - br * 0.25, y - br * 0.3], fill=(170, 195, 255))
    # basket
    d.pieslice([c - r * 0.95, c - r * 0.65, c + r * 0.95, c + r * 1.05], 0, 180, fill=(205, 150, 95))
    for i in range(5):
        y = c + r * 0.25 + i * r * 0.15
        d.line([c - r * 0.9 + i * r * 0.05, y, c + r * 0.9 - i * r * 0.05, y], fill=(170, 115, 65), width=max(2, int(r * 0.03)))
    d.rounded_rectangle([c - r * 1.0, c + r * 0.1, c + r * 1.0, c + r * 0.27], radius=int(r * 0.08), fill=(225, 170, 110))
    face(d, c, c + r * 0.45, r * 0.4, ink=(90, 55, 35))
    return im

def make_boots(r):
    im, d, c = canvas(r)
    def boot(x0, flip):
        sx = -1 if flip else 1
        d.rounded_rectangle([x0 - r * 0.28, c - r * 0.85, x0 + r * 0.28, c + r * 0.55], radius=int(r * 0.12), fill=BLUE)
        foot = [x0 - r * 0.28 * sx, c + r * 0.25, x0 + r * 0.7 * sx, c + r * 0.8]
        fx = sorted([foot[0], foot[2]])
        d.rounded_rectangle([fx[0], foot[1], fx[1], foot[3]], radius=int(r * 0.22), fill=BLUE)
        d.rounded_rectangle([fx[0] - r * 0.02, c + r * 0.68, fx[1] + r * 0.02, c + r * 0.86], radius=int(r * 0.08), fill=BLUE_D)
        d.rounded_rectangle([x0 - r * 0.33, c - r * 0.92, x0 + r * 0.33, c - r * 0.72], radius=int(r * 0.08), fill=BLUE_L)
        # little white dots
        for k in range(3):
            d.ellipse([x0 - r * 0.08, c - r * 0.5 + k * r * 0.3, x0 + r * 0.04, c - r * 0.38 + k * r * 0.3], fill=(240, 246, 255))
    boot(c - r * 0.55, True)
    boot(c + r * 0.45, False)
    gloss(im, [c - r * 0.75, c - r * 0.7, c - r * 0.6, c - r * 0.1], 120, 4)
    gloss(im, [c + r * 0.25, c - r * 0.7, c + r * 0.4, c - r * 0.1], 120, 4)
    d = ImageDraw.Draw(im); face(d, c + r * 0.45, c - r * 0.25, r * 0.32)
    return im

def make_leaf(r):
    im, d, c = canvas(r)
    d.ellipse([c - r * 0.55, c - r * 0.95, c + r * 0.55, c + r * 0.85], fill=(70, 175, 85))
    d.line([c, c - r * 0.8, c, c + r * 1.15], fill=(40, 120, 55), width=max(3, int(r * 0.06)))
    for k in range(3):
        y = c - r * 0.4 + k * r * 0.35
        d.line([c, y + r * 0.15, c - r * 0.35, y - r * 0.1], fill=(40, 120, 55), width=max(2, int(r * 0.04)))
        d.line([c, y + r * 0.15, c + r * 0.35, y - r * 0.1], fill=(40, 120, 55), width=max(2, int(r * 0.04)))
    return im

def make_butterfly(r, flap=1.0):
    im, d, c = canvas(r)
    wx = r * 0.85 * flap
    for sx in (-1, 1):
        d.ellipse(sorted_box(c, c + sx * wx, c - r * 0.85, c - r * 0.05), fill=BLUE)
        d.ellipse(sorted_box(c, c + sx * wx * 0.75, c - r * 0.1, c + r * 0.7), fill=BLUE_D)
        d.ellipse(sorted_box(c + sx * wx * 0.3, c + sx * wx * 0.7, c - r * 0.6, c - r * 0.3), fill=BLUE_L)
    d.rounded_rectangle([c - r * 0.1, c - r * 0.6, c + r * 0.1, c + r * 0.65], radius=int(r * 0.1), fill=(70, 55, 90))
    d.line([c - r * 0.04, c - r * 0.58, c - r * 0.25, c - r * 0.95], fill=(70, 55, 90), width=max(2, int(r * 0.04)))
    d.line([c + r * 0.04, c - r * 0.58, c + r * 0.25, c - r * 0.95], fill=(70, 55, 90), width=max(2, int(r * 0.04)))
    return im

def sorted_box(c, xa, ya, yb):
    return [min(c, xa), ya, max(c, xa), yb]

def make_carrot(r):
    im, d, c = canvas(r)
    for a in (-25, 0, 25):
        x = c + math.sin(math.radians(a)) * r * 0.5
        d.ellipse([x - r * 0.12, c - r * 1.05, x + r * 0.12, c - r * 0.45], fill=(80, 170, 80))
    d.polygon([(c - r * 0.38, c - r * 0.55), (c + r * 0.38, c - r * 0.55), (c, c + r * 1.0)], fill=(255, 140, 45))
    d.ellipse([c - r * 0.38, c - r * 0.7, c + r * 0.38, c - r * 0.4], fill=(255, 140, 45))
    for k in range(3):
        y = c - r * 0.25 + k * r * 0.3
        d.line([c - r * 0.2 + k * r * 0.05, y, c - r * 0.05, y], fill=(215, 105, 30), width=max(2, int(r * 0.04)))
    return im

def greyed(sp):
    a = sp.getchannel("A")
    g = sp.convert("L").point(lambda v: int(150 + v * 0.35))
    out = Image.merge("RGBA", (g, g, g, a))
    # soft dashed-looking outline effect: slightly darker edge
    return out

# ---------- scene ----------
# item positions (kept left of x=930 and above y=1300)
POS = [(700, 470), (300, 640), (300, 1130), (690, 1150)]
SIZE = [130, 95, 125, 120]
CX = 465   # content centre (shifted left of the Shorts side buttons)
TW_HOME = (480, 880)

def background():
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([255, 236, 214]), np.array([255, 214, 226])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.ascontiguousarray(np.repeat(arr[:, None, :], W, axis=1))).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # sun
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sun).ellipse([60, 190, 250, 380], fill=(255, 220, 120, 200))
    bg.alpha_composite(sun.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(bg)
    d.ellipse([90, 220, 220, 350], fill=(255, 228, 140))
    # clouds (cream, not blue)
    for cx, cy, s in [(420, 330, 1.0), (870, 760, 0.8), (560, 620, 0.6)]:
        for dx, dy, rr in [(-60, 10, 50), (0, -15, 65), (60, 10, 50), (0, 20, 50)]:
            d.ellipse([cx + (dx - rr) * s, cy + (dy - rr) * s, cx + (dx + rr) * s, cy + (dy + rr) * s], fill=(255, 250, 244))
    # far hills
    d.ellipse([-300, 880, 700, 1300], fill=(190, 225, 170))
    d.ellipse([400, 900, 1500, 1350], fill=(170, 215, 160))
    # grass
    d.rectangle([0, 1020, W, H], fill=(150, 205, 130))
    d.ellipse([-200, 990, 1300, 1120], fill=(150, 205, 130))
    # path
    d.polygon([(420, 1020), (560, 1020), (820, H), (180, H)], fill=(240, 220, 180))
    # tree (left) with a branch for the bird
    d.rounded_rectangle([90, 520, 170, 1060], radius=20, fill=(160, 110, 75))
    d.line([(150, 720), (240, 700), (390, 700)], fill=(160, 110, 75), width=26)
    for cx, cy, rr in [(130, 470, 150), (40, 560, 110), (230, 540, 110), (130, 600, 120)]:
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(105, 175, 100))
    for cx, cy in [(80, 430), (200, 470), (120, 560)]:
        d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=(255, 150, 160))
    # flowers
    rnd = random.Random(5)
    for _ in range(40):
        x, y = rnd.randint(20, 1060), rnd.randint(1050, 1900)
        if 300 < x < 700 and y > 1040: continue
        col = rnd.choice([(255, 170, 190), (255, 225, 120), (255, 255, 255)])
        for a in range(5):
            px, py = x + math.cos(a * 1.256) * 9, y + math.sin(a * 1.256) * 9
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 200, 80))
    # kite string from grass to kite
    return bg

BG = background()
TW = [make_twinkle(110, False), make_twinkle(110, True)]
TW_BIG = [make_twinkle(170, False), make_twinkle(170, True)]
OBJ = [make_kite(SIZE[0]), make_bird(SIZE[1]), make_berries(SIZE[2]), make_boots(SIZE[3])]
GREY = [greyed(o) for o in OBJ]
QUIZ_OBJ = [make_leaf(120), None, make_carrot(120)]
def quiz_bg():
    q = Image.new("RGBA", (W, H), (255, 246, 236, 255)); qd = ImageDraw.Draw(q)
    for yy in range(0, H, 120):
        for xx in range(0, W, 120):
            o = 60 if (yy // 120) % 2 else 0
            qd.ellipse([xx + o - 10, yy - 10, xx + o + 10, yy + 10], fill=(225, 235, 255))
    return q
QBG = quiz_bg()

def bloom(i, k):
    """Colour version revealed by a growing soft circle (paint bloom)."""
    if k <= 0: return GREY[i]
    if k >= 1: return OBJ[i]
    sp = OBJ[i]; s = sp.width
    m = Image.new("L", (s, s), 0)
    rr = k * s * 0.75
    ImageDraw.Draw(m).ellipse([s / 2 - rr, s / 2 - rr, s / 2 + rr, s / 2 + rr], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(10))
    col = sp.copy(); col.putalpha(Image.composite(sp.getchannel("A"), Image.new("L", (s, s), 0), m))
    out = GREY[i].copy(); out.alpha_composite(col)
    return out

def sparkle(d, x, y, r, a, col=(255, 240, 150)):
    FX.polygon(star_poly(x, y, r, inner=0.35), fill=col + (int(a),))

# ---------- caption ----------
def wrap(d, txt, sz, maxw):
    words, lines, cur = txt.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font(sz)) <= maxw: cur = test
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def draw_caption(im, t):
    for a, b, txt in LINES:
        if a <= t < b: break
    else: return
    k = ease((t - a) / 0.25) * ease((b - t) / 0.25)
    if k <= 0: return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    sz = 66; lines = wrap(d, txt, sz, 760)
    if len(lines) > 2: sz = 58; lines = wrap(d, txt, sz, 780)
    lh = sz * 1.22; bh = lh * len(lines) + 60
    top = 1440 - bh / 2
    d.rounded_rectangle([50, top, 920, top + bh], radius=42, fill=(255, 255, 255, 238), outline=BLUE, width=6)
    for i, ln in enumerate(lines):
        f = font(sz); total = d.textlength(ln, font=f); x = 485 - total / 2; y = top + 26 + i * lh
        for word in ln.split(" "):
            col = BLUE if "blue" in word.lower() else INK
            d.text((x, y), word, font=f, fill=col)
            x += d.textlength(word + " ", font=f)
    if k < 1: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * k)))
    im.alpha_composite(layer)

def draw_twinkle(im, t, x, y, big=False):
    tk = talking(t)
    mouth = tk and int(t * 7) % 2 == 0
    bob = math.sin(t * 2.5) * 10 + (-abs(math.sin(t * 9)) * 14 if tk else 0)
    paste(im, (TW_BIG if big else TW)[mouth], x, y + bob, 1.0, math.sin(t * 1.8) * 6)

def header(d, t):
    text_c(d, "Find BLUE things!", CX, 120, 74, BLUE, sw=9)

def draw_items(im, d, t, cur):
    """cur = index of the item being revealed now (or None); items before it are already blue."""
    # kite string
    kx, ky = POS[0]
    d.line([(kx, ky + 30), (kx - 120, ky + 300), (kx - 180, 1000)], fill=(140, 130, 150), width=3)
    for i in range(NOBJ):
        x, y = POS[i]
        if cur is None: k = 1.0
        elif i < cur: k = 1.0
        elif i > cur: k = 0.0
        else: k = ease((t - SEG_T[i] - REVEAL_AT) / 0.9)
        sp = bloom(i, k)
        sway = math.sin(t * 1.6 + i) * (6 if i == 0 else 2)
        bob = 0
        if i == cur and k > 0:
            lt = t - SEG_T[i] - REVEAL_AT
            bob = -abs(math.sin(lt * 5)) * 22 * max(0, 1 - lt / 3)
        if i == 1: bob += 0  # bird sits on its branch
        paste(im, sp, x, y + bob, 1.0, sway)
        if i == cur and k <= 0:
            # pulsing "?" hint ring
            lt = t - SEG_T[i]
            rr = SIZE[i] * 1.25 + math.sin(lt * 6) * 8
            FX.ellipse([x - rr, y - rr, x + rr, y + rr], outline=(255, 255, 255, 230), width=7)

# ---------- frame ----------
def frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    global FX
    fxl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); FX = ImageDraw.Draw(fxl)
    if t < INTRO:
        draw_items(im, d, t, 0)  # all grey
        d = ImageDraw.Draw(im)
        s = pop((t - 0.2) / 0.8)
        if s > 0:
            f = font(130 * s); txt = "Blue Things"; w = d.textlength(txt, font=f)
            d.text((CX - w / 2, 120 + (1 - s) * 60), txt, font=f, fill=BLUE, stroke_width=12, stroke_fill=(255, 255, 255))
        if t > 1.4:
            text_c(d, "with Twinkle!", CX, 300, 60, INK, sw=7)
        x = TW_HOME[0] + (1 - ease(t / 1.2)) * -500
        draw_twinkle(im, t, x, TW_HOME[1])
    elif t < T_QUIZ:
        i = min(NOBJ - 1, int((t - INTRO) // SEG)); lt = t - SEG_T[i]
        draw_items(im, d, t, i)
        d = ImageDraw.Draw(im)
        header(d, t)
        # Twinkle leans toward the item
        tx = TW_HOME[0] + (POS[i][0] - TW_HOME[0]) * 0.12
        draw_twinkle(im, t, tx, TW_HOME[1])
        d = ImageDraw.Draw(im)
        # sparkle trail from Twinkle to item
        if 0.5 < lt < REVEAL_AT + 0.4:
            p = ease((lt - 0.5) / (REVEAL_AT - 0.5))
            x0, y0 = tx, TW_HOME[1] - 40; x1, y1 = POS[i]
            for j in range(8):
                q = p - j * 0.06
                if q <= 0 or q > 1: continue
                mx = x0 + (x1 - x0) * q; my = y0 + (y1 - y0) * q - math.sin(q * math.pi) * 160
                sparkle(d, mx, my, 22 - j * 2, 255 - j * 28, BLUE_L if j % 2 else (255, 240, 150))
        # sparkles after reveal
        rl = lt - REVEAL_AT
        if 0 < rl < 1.6:
            x, y = POS[i]
            for j in range(8):
                a = j * math.pi / 4 + rl
                rr = SIZE[i] * (0.9 + rl * 0.6)
                sparkle(d, x + math.cos(a) * rr, y + math.sin(a) * rr, 18, 255 * (1 - rl / 1.6), (255, 240, 150) if j % 2 else BLUE_L)
        # name label
        if rl > 0.6:
            s = pop((rl - 0.6) / 0.5)
            x, y = POS[i]
            ly = y + SIZE[i] * 1.15 if i != 0 else y + SIZE[i] * 1.25
            if i in (1, 2, 3): ly = y - SIZE[i] * 1.75
            text_c(d, NAMES[i], max(170, min(760, x)), ly, 70 * max(s, 0.05), BLUE, sw=9)
    elif t < T_OUT:
        lt = t - T_QUIZ
        im.alpha_composite(QBG); d = ImageDraw.Draw(im)
        text_c(d, "Which one is blue?", CX, 200, 76, INK, sw=9)
        draw_twinkle(im, t, CX, 470); d = ImageDraw.Draw(im)
        xs = [195, 465, 735]; reveal = lt - 5.0
        for j in range(3):
            x, y = xs[j], 830
            lift = 0
            if reveal > 0 and j == 1: lift = -abs(math.sin(reveal * 4)) * 30
            box = [x - 120, y - 170 + lift, x + 120, y + 170 + lift]
            if reveal > 0 and j == 1:
                g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(g).rounded_rectangle([box[0] - 25, box[1] - 25, box[2] + 25, box[3] + 25], radius=50, fill=BLUE_L + (200,))
                im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18))); d = ImageDraw.Draw(im)
            d.rounded_rectangle(box, radius=36, fill=(255, 255, 255), outline=BLUE if (reveal > 0 and j == 1) else (220, 210, 220), width=8)
            appear = pop((lt - 0.4 - j * 0.35) / 0.5)
            if j == 1:
                flap = 0.55 + 0.45 * abs(math.cos(t * (9 if reveal > 0 else 3)))
                sp = make_butterfly(105, flap)
            else:
                sp = QUIZ_OBJ[j]
            paste(im, sp, x, y + lift, 0.75 * appear, math.sin(t * 2 + j) * 4)
            d = ImageDraw.Draw(im)
            if reveal > 0 and j != 1:
                dim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(dim).rounded_rectangle(box, radius=36, fill=(255, 255, 255, 140))
                im.alpha_composite(dim); d = ImageDraw.Draw(im)
        if reveal > 0.3:
            text_c(d, "butterfly", xs[1], 1040, 80 * max(pop((reveal - 0.3) / 0.5), 0.05), BLUE, sw=9)
    else:
        lt = t - T_OUT
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 248, 240, 170)))
        d = ImageDraw.Draw(im)
        ring = [(230, 730), (700, 730), (230, 1110), (700, 1110)]
        for i in range(NOBJ):
            s = pop((lt - 0.2 - i * 0.2) / 0.5)
            paste(im, OBJ[i], ring[i][0], ring[i][1] + math.sin(t * 5 + i) * 12, 0.75 * s, math.sin(t * 4 + i) * 10)
        draw_twinkle(im, t, CX, 920, big=True)
        d = ImageDraw.Draw(im)
        ps = pop((lt - 0.3) / 0.6)
        text_c(d, "Blue is cool!", CX, 250, 110 * max(ps, 0.05), BLUE, sw=11)
        if lt > 2.2:
            text_c(d, "Subscribe for more!", CX, 470, 60, INK, sw=7)
    im.alpha_composite(fxl)
    draw_caption(im, t)
    return im.convert("RGB")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "frames":
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f"_frame_{tt}.png")
        raise SystemExit
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(frame(fi / FPS).tobytes())
    proc.stdin.close(); proc.wait()

    # ---------- audio: soft original plucked lullaby in F major ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    def pluck(freq, dur, vol=0.2, decay=5):
        tt = np.arange(int(dur * SR)) / SR
        w = (np.sin(2 * np.pi * freq * tt) + 0.5 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-8 * tt)
             + 0.25 * np.sin(2 * np.pi * freq * 3 * tt) * np.exp(-14 * tt))
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 400)
    def pad(freqs, dur, vol=0.03):
        tt = np.arange(int(dur * SR)) / SR
        w = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 1.003 * tt) for f in freqs)
        env = np.minimum(1, tt / 0.6) * np.minimum(1, (dur - tt) / 0.6)
        return vol * w * env
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig)); audio[i:j] += sig[:j - i]
    F = {"F3": 174.61, "A3": 220.0, "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0,
         "A4": 440.0, "Bb3": 233.08, "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "D3": 146.83, "G3": 196.0}
    chords = [["F3", "A3", "C4"], ["D3", "F3", "A3"], ["Bb3", "D4", "F4"], ["C4", "E4", "G4"]]
    melody = ["A4", None, "C5", "A4", "G4", None, "F4", None,
              "F4", None, "A4", "G4", "F4", None, "D4", None,
              "D4", None, "F4", "Bb4", "A4", None, "G4", None,
              "E4", None, "G4", "C5", "A4", None, None, None]
    e8 = 60 / 92 / 2; k = 0
    while k * e8 < TOTAL - 1:
        bar = (k // 8) % 4; ch = chords[bar]
        add(pluck(F[ch[[0, 1, 2, 1][k % 4]]], 0.7, 0.04, 5), k * e8)
        m = melody[k % 32]
        if m: add(pluck(F[m], 1.0, 0.045, 3.5), k * e8 + 0.005)
        if k % 8 == 0: add(pad([F[n] / 2 for n in ch], 8 * e8 + 0.3, 0.012), k * e8)
        k += 1
    def gliss(f0, f1, dur, vol=0.08):
        tt = np.arange(int(dur * SR)) / SR
        f = f0 * (f1 / f0) ** (tt / dur)
        ph = 2 * np.pi * np.cumsum(f) / SR
        return vol * np.sin(ph) * np.sin(np.pi * tt / dur)
    for i in range(NOBJ):
        add(gliss(600, 1500, 0.7, 0.06), SEG_T[i] + 0.5)
        for j, f in enumerate([698.46, 880, 1046.5, 1396.9]):
            add(pluck(f, 0.5, 0.11, 7), SEG_T[i] + REVEAL_AT + j * 0.09)
    for j, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
        add(pluck(f, 0.8, 0.13, 4), T_QUIZ + 5.0 + j * 0.13)
    for j, f in enumerate([349.23, 440, 523.25, 698.46, 880]):
        add(pluck(f, 1.2, 0.12, 3), T_OUT + 0.1 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
