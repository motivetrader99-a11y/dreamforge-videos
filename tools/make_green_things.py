"""Dreamforge Kids — Green things.
A soft morning pond: Twinkle the star hops across lily pads. At every pad a green thing pops up
out of the water with a gentle splash — a frog, a leaf, peas in a pod and a turtle — its name
appears in a leafy label, then it floats up to hang on a curly vine ("My green things") at the top.
Quiz: three bubbles (pink cupcake, green broccoli, brown acorn) — which one is green?
Outro: all the green things bob around Twinkle. Captions sit in a panel above the Shorts UI.
Original art & music (plucked kalimba-style lullaby in D major, 4/4, with water plops)."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/green_things.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (45, 60, 55)
GRN = (110, 200, 90)
GRN_D = (60, 150, 70)
GRN_L = (190, 240, 160)
GRN_TXT = (40, 150, 60)
CX = 470
random.seed(21)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, SEG, QUIZ, OUTRO = 5.0, 6.2, 9.0, 6.5
NOBJ = 4
SEG_T = [INTRO + i * SEG for i in range(NOBJ)]
T_QUIZ = INTRO + NOBJ * SEG
T_OUT = T_QUIZ + QUIZ
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)
HOP, RISE, FLY = 1.0, 1.15, 4.9

NAMES = ["frog", "leaf", "peas", "turtle"]
LINES = [
    (0.3, INTRO - 0.1, "Hi! I'm Twinkle! Let's find green things at the pond!"),
    (SEG_T[0] + 0.2, SEG_T[0] + SEG - 0.1, "A little frog is green. Ribbit, ribbit!"),
    (SEG_T[1] + 0.2, SEG_T[1] + SEG - 0.1, "A leaf is green, just like the grass!"),
    (SEG_T[2] + 0.2, SEG_T[2] + SEG - 0.1, "Peas in a pod are green. Yum!"),
    (SEG_T[3] + 0.2, SEG_T[3] + SEG - 0.1, "A slow turtle has a green shell!"),
    (T_QUIZ + 0.2, T_QUIZ + 4.8, "Which one is green? Can you find it?"),
    (T_QUIZ + 4.9, T_OUT - 0.1, "The broccoli! Broccoli is green!"),
    (T_OUT + 0.3, TOTAL - 0.4, "Green is all around us! Bye-bye!"),
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

def text_c(d, txt, cx, y, sz, fill, stroke=INK, sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def gloss(im, box, a=120, blur=6):
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(box, fill=(255, 255, 255, a))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(blur)))

def face(d, cx, cy, r, ink=(45, 50, 45), eye=0.11):
    e = r * eye
    for dx in (-r * 0.3, r * 0.3):
        d.ellipse([cx + dx - e, cy - e * 1.3, cx + dx + e, cy + e * 1.3], fill=ink)
        d.ellipse([cx + dx - e * 0.5, cy - e * 1.0, cx + dx + e * 0.1, cy - e * 0.3], fill=(255, 255, 255))
    d.arc([cx - r * 0.2, cy + r * 0.02, cx + r * 0.2, cy + r * 0.32], 20, 160, fill=ink, width=max(3, int(r * 0.07)))
    for dx in (-r * 0.52, r * 0.52):
        d.ellipse([cx + dx - r * 0.12, cy + r * 0.12, cx + dx + r * 0.12, cy + r * 0.26], fill=(255, 140, 150, 170))

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

# ---------- green things ----------
def make_frog(r):
    im, d, c = canvas(r)
    # back legs
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.55 - r * 0.38, c + r * 0.25, c + sx * r * 0.55 + r * 0.38, c + r * 0.75], fill=GRN_D)
    d.ellipse([c - r * 0.85, c - r * 0.35, c + r * 0.85, c + r * 0.7], fill=GRN)
    d.ellipse([c - r * 0.5, c + r * 0.05, c + r * 0.5, c + r * 0.66], fill=GRN_L)
    # eye bumps
    for sx in (-1, 1):
        ex = c + sx * r * 0.42; ey = c - r * 0.42
        d.ellipse([ex - r * 0.3, ey - r * 0.3, ex + r * 0.3, ey + r * 0.3], fill=GRN)
        d.ellipse([ex - r * 0.2, ey - r * 0.22, ex + r * 0.2, ey + r * 0.2], fill=(255, 255, 255))
        d.ellipse([ex - r * 0.12, ey - r * 0.13, ex + r * 0.12, ey + r * 0.15], fill=(40, 45, 40))
        d.ellipse([ex - r * 0.07, ey - r * 0.1, ex, ey - r * 0.03], fill=(255, 255, 255))
    d.arc([c - r * 0.45, c - r * 0.25, c + r * 0.45, c + r * 0.2], 25, 155, fill=(40, 70, 45), width=max(3, int(r * 0.06)))
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.58 - r * 0.12, c - r * 0.05, c + sx * r * 0.58 + r * 0.12, c + r * 0.07], fill=(255, 140, 150, 170))
    # front feet
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.3 - r * 0.16, c + r * 0.58, c + sx * r * 0.3 + r * 0.16, c + r * 0.76], fill=GRN_D)
    gloss(im, [c - r * 0.6, c - r * 0.25, c - r * 0.2, c - r * 0.05], 110, 6)
    return im

def make_leaf(r):
    im, d, c = canvas(r)
    pts = []
    for i in range(41):
        a = i / 40 * math.pi
        pts.append((c + math.sin(a) * r * 0.7 * (1 - 0.15 * math.cos(a)), c - r * 0.95 * math.cos(a)))
    pts += [(2 * c - x, y) for x, y in reversed(pts)]
    d.polygon(pts, fill=(95, 185, 80))
    d.polygon([(x * 0.92 + c * 0.08, y * 0.92 + c * 0.08) for x, y in pts], fill=(125, 210, 95))
    d.line([(c, c - r * 0.85), (c, c + r * 1.2)], fill=(70, 140, 60), width=max(4, int(r * 0.06)))
    for k in range(4):
        y = c - r * 0.5 + k * r * 0.3
        for sx in (-1, 1):
            d.line([(c, y + r * 0.1), (c + sx * r * 0.42, y - r * 0.12)], fill=(80, 155, 65), width=max(3, int(r * 0.04)))
    face(d, c, c + r * 0.05, r * 0.6)
    # dew drop
    d.ellipse([c + r * 0.2, c - r * 0.6, c + r * 0.36, c - r * 0.42], fill=(210, 245, 255))
    d.ellipse([c + r * 0.24, c - r * 0.57, c + r * 0.29, c - r * 0.52], fill=(255, 255, 255))
    return im

def make_peas(r):
    im, d, c = canvas(r)
    d.rounded_rectangle([c - r * 1.05, c - r * 0.42, c + r * 1.05, c + r * 0.42], radius=r * 0.42, fill=(95, 170, 70))
    d.rounded_rectangle([c - r * 0.95, c - r * 0.32, c + r * 0.95, c + r * 0.32], radius=r * 0.32, fill=(205, 240, 170))
    d.polygon([(c + r * 1.0, c - r * 0.1), (c + r * 1.25, c - r * 0.35), (c + r * 1.18, c - r * 0.02)], fill=(80, 150, 60))
    for k in range(4):
        px = c - r * 0.66 + k * r * 0.44
        d.ellipse([px - r * 0.21, c - r * 0.21, px + r * 0.21, c + r * 0.21], fill=(120, 205, 80))
        d.ellipse([px - r * 0.12, c - r * 0.15, px - r * 0.03, c - r * 0.06], fill=(220, 255, 200))
        e = r * 0.03
        for dx in (-r * 0.07, r * 0.07):
            d.ellipse([px + dx - e, c - e * 1.3, px + dx + e, c + e * 1.3], fill=(40, 60, 40))
        d.arc([px - r * 0.06, c, px + r * 0.06, c + r * 0.09], 20, 160, fill=(40, 60, 40), width=3)
    return im

def make_turtle(r):
    im, d, c = canvas(r)
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.55 - r * 0.2, c + r * 0.25, c + sx * r * 0.55 + r * 0.2, c + r * 0.62], fill=(170, 220, 130))
    d.ellipse([c + r * 0.62, c - r * 0.25, c + r * 1.18, c + r * 0.3], fill=(170, 220, 130))  # head
    hx, hy = c + r * 0.92, c + r * 0.0
    for dx in (-r * 0.1, r * 0.1):
        d.ellipse([hx + dx - r * 0.05, hy - r * 0.09, hx + dx + r * 0.05, hy + r * 0.05], fill=(40, 50, 40))
        d.ellipse([hx + dx - r * 0.03, hy - r * 0.07, hx + dx, hy - r * 0.03], fill=(255, 255, 255))
    d.arc([hx - r * 0.1, hy, hx + r * 0.1, hy + r * 0.14], 20, 160, fill=(40, 50, 40), width=3)
    d.ellipse([hx + r * 0.08, hy + r * 0.03, hx + r * 0.2, hy + r * 0.11], fill=(255, 140, 150, 170))
    d.chord([c - r * 0.85, c - r * 0.75, c + r * 0.75, c + r * 0.85], 180, 360, fill=(70, 150, 70))
    d.rectangle([c - r * 0.88, c + r * 0.02, c + r * 0.78, c + r * 0.2], fill=(55, 125, 60))
    # shell pattern
    for k, (px, py, pr) in enumerate([(c - r * 0.05, c - r * 0.38, 0.22), (c - r * 0.48, c - r * 0.18, 0.17),
                                      (c + r * 0.38, c - r * 0.18, 0.17)]):
        pts = [(px + math.cos(a * math.pi / 3) * r * pr, py + math.sin(a * math.pi / 3) * r * pr) for a in range(6)]
        d.polygon(pts, fill=(130, 200, 100))
    gloss(im, [c - r * 0.55, c - r * 0.65, c - r * 0.1, c - r * 0.45], 120, 6)
    return im

def make_cupcake(r):
    im, d, c = canvas(r)
    d.polygon([(c - r * 0.6, c), (c + r * 0.6, c), (c + r * 0.45, c + r * 0.75), (c - r * 0.45, c + r * 0.75)], fill=(240, 200, 150))
    for k in range(5):
        x = c - r * 0.48 + k * r * 0.24
        d.line([(x, c + r * 0.05), (x + r * 0.03, c + r * 0.7)], fill=(215, 170, 120), width=4)
    for (x, y, rr) in [(c - r * 0.4, c - r * 0.1, 0.32), (c + r * 0.4, c - r * 0.1, 0.32), (c, c - r * 0.25, 0.42), (c, c - r * 0.6, 0.26)]:
        d.ellipse([x - r * rr, y - r * rr, x + r * rr, y + r * rr], fill=(255, 170, 200))
    d.ellipse([c - r * 0.12, c - r * 0.95, c + r * 0.12, c - r * 0.7], fill=(230, 60, 80))
    return im

def make_broccoli(r):
    im, d, c = canvas(r)
    d.polygon([(c - r * 0.25, c + r * 0.05), (c + r * 0.25, c + r * 0.05), (c + r * 0.2, c + r * 0.85), (c - r * 0.2, c + r * 0.85)], fill=(170, 220, 130))
    for (x, y, rr) in [(c - r * 0.5, c - r * 0.1, 0.36), (c + r * 0.5, c - r * 0.1, 0.36), (c - r * 0.25, c - r * 0.45, 0.4),
                       (c + r * 0.25, c - r * 0.45, 0.4), (c, c - r * 0.1, 0.38)]:
        d.ellipse([x - r * rr, y - r * rr, x + r * rr, y + r * rr], fill=(70, 160, 70))
        d.ellipse([x - r * rr * 0.6, y - r * rr * 0.7, x + r * rr * 0.2, y], fill=(105, 190, 90))
    face(d, c, c - r * 0.18, r * 0.55, ink=(30, 50, 30))
    return im

def make_acorn(r):
    im, d, c = canvas(r)
    d.ellipse([c - r * 0.5, c - r * 0.25, c + r * 0.5, c + r * 0.85], fill=(200, 140, 80))
    d.chord([c - r * 0.62, c - r * 0.6, c + r * 0.62, c + r * 0.2], 180, 360, fill=(140, 95, 55))
    d.rectangle([c - r * 0.62, c - r * 0.2, c + r * 0.62, c - r * 0.05], fill=(140, 95, 55))
    d.rectangle([c - r * 0.06, c - r * 0.85, c + r * 0.06, c - r * 0.55], fill=(110, 75, 45))
    gloss(im, [c - r * 0.35, c + r * 0.05, c - r * 0.1, c + r * 0.4], 110, 5)
    return im

TW = [make_twinkle(78, m) for m in (False, True)]
TW_BIG = [make_twinkle(165, m) for m in (False, True)]
ITEMS = [make_frog(160), make_leaf(160), make_peas(150), make_turtle(160)]
QUIZ_IT = [make_cupcake(110), make_broccoli(110), make_acorn(110)]
SLOT_SCALE = 0.36

# ---------- scene ----------
POND_TOP = 1060
PADS = [(150, 1240), (360, 1150), (580, 1245), (800, 1150)]

def background():
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([255, 228, 205]), np.array([215, 245, 225])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1).reshape(H, W, 3)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # soft sun glow
    gl = Image.new("RGBA", (W, H), (255, 245, 210, 0))
    ImageDraw.Draw(gl).ellipse([700, 470, 980, 750], fill=(255, 245, 210, 200))
    bg.alpha_composite(gl.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(bg)
    # hills
    d.ellipse([-400, 860, 700, 1400], fill=(175, 225, 170))
    d.ellipse([350, 900, 1500, 1450], fill=(155, 210, 160))
    d.rectangle([0, 1040, W, H], fill=(140, 200, 150))
    # pond
    d.ellipse([-120, POND_TOP, W + 120, 1420], fill=(150, 210, 230))
    d.ellipse([-60, POND_TOP + 25, W + 60, 1390], fill=(175, 225, 240))
    for k in range(9):
        x = random.randint(60, 950); y = random.randint(POND_TOP + 60, 1350)
        d.arc([x - 50, y - 8, x + 50, y + 8], 200, 340, fill=(220, 245, 255), width=3)
    # reeds / cattails at the left edge
    for k in range(6):
        x = 20 + k * 22
        d.line([(x, 1100), (x + 8, 880 + k * 12)], fill=(90, 150, 80), width=6)
        if k % 2 == 0:
            d.rounded_rectangle([x + 2, 880 + k * 12, x + 18, 950 + k * 12], radius=8, fill=(150, 105, 70))
    # little flowers
    for k in range(10):
        x = random.randint(160, 920); y = random.randint(1000, 1050)
        col = random.choice([(255, 200, 220), (255, 255, 255), (255, 235, 150)])
        for a in range(5):
            px = x + math.cos(a * 1.256) * 9; py = y + math.sin(a * 1.256) * 9
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=col)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 200, 80))
    # vine at top
    pts = [(x, 150 + math.sin(x / 110) * 22) for x in range(0, 960, 6)]
    d.line(pts, fill=(90, 160, 80), width=12, joint="curve")
    for k in range(14):
        x = 30 + k * 66; y = 150 + math.sin(x / 110) * 22
        sx = 1 if k % 2 else -1
        d.ellipse([x - 18, y + sx * 6 - 12, x + 18, y + sx * 6 + 12 + 8 * sx], fill=(120, 195, 95))
    return bg

BG = background()
SLOTS = [(170 + i * 205, 330) for i in range(NOBJ)]

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
    sz = 64; lines = wrap(d, txt, sz, 780)
    if len(lines) > 2: sz = 56; lines = wrap(d, txt, sz, 800)
    lh = sz * 1.22; bh = lh * len(lines) + 52
    top = 1550 - bh
    d.rounded_rectangle([45, top, 925, top + bh], radius=44, fill=(250, 255, 245, 240), outline=GRN_D, width=7)
    for i, ln in enumerate(lines):
        f = font(sz); total = d.textlength(ln, font=f); x = 485 - total / 2; y = top + 22 + i * lh
        for word in ln.split(" "):
            col = GRN_TXT if "green" in word.lower() else INK
            d.text((x, y), word, font=f, fill=col)
            x += d.textlength(word + " ", font=f)
    if k < 1: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * k)))
    im.alpha_composite(layer)

def draw_pads(d, t, glow_i=-1):
    for i, (x, y) in enumerate(PADS):
        bob = math.sin(t * 1.5 + i) * 3
        d.ellipse([x - 95, y - 30 + bob, x + 95, y + 34 + bob], fill=(95, 170, 85))
        d.ellipse([x - 88, y - 34 + bob, x + 88, y + 26 + bob], fill=(130, 205, 105) if i != glow_i else (165, 230, 130))
        d.polygon([(x, y - 4 + bob), (x + 70, y - 30 + bob), (x + 85, y - 6 + bob)], fill=(95, 170, 85))

def twinkle_pos(t):
    """Twinkle hops from pad to pad; returns (x, y)."""
    if t < INTRO: return None
    if t >= T_OUT: return None
    if t >= T_QUIZ: i0 = i1 = NOBJ - 1; k = 1
    else:
        i = int((t - INTRO) // SEG); lt = t - SEG_T[i]
        i1 = i; i0 = max(0, i - 1); k = ease(lt / HOP) if i > 0 else 1
        if i == 0 and lt < HOP:  # drop in from the stage
            k2 = ease(lt / HOP)
            x = 480 + (PADS[0][0] - 480) * k2; y = 760 + (PADS[0][1] - 80 - 760) * k2
            return x, y - math.sin(math.pi * k2) * 120
    x0, y0 = PADS[i0]; x1, y1 = PADS[i1]
    x = x0 + (x1 - x0) * k; y = (y0 + (y1 - y0) * k) - 80 - math.sin(math.pi * k) * 160
    return x, y

def draw_twinkle(im, t, x, y, big=False):
    tk = talking(t)
    mouth = tk and int(t * 7) % 2 == 0
    bob = math.sin(t * 2.5) * 8 + (-abs(math.sin(t * 9)) * 12 if tk else 0)
    paste(im, (TW_BIG if big else TW)[mouth], x, y + bob, 1.0, math.sin(t * 1.8) * 6)

def ripple(d, x, y, k):
    for j in range(3):
        kk = k - j * 0.18
        if 0 < kk < 1:
            rw = 40 + kk * 170; a = int(220 * (1 - kk))
            d.ellipse([x - rw, y - rw * 0.25, x + rw, y + rw * 0.25], outline=(255, 255, 255, a), width=5)

def droplets(d, x, y, k):
    if not (0 < k < 1): return
    for j in range(7):
        a = -math.pi / 2 + (j - 3) * 0.35
        dx = math.cos(a) * 160 * k; dy = math.sin(a) * 260 * k + 330 * k * k
        r = 12 * (1 - k) + 4
        d.ellipse([x + dx - r, y + dy - r, x + dx + r, y + dy + r], fill=(200, 240, 255, int(255 * (1 - k))))

def leaf_label(d, txt, cx, y, k):
    if k <= 0: return
    f = font(int(96 * min(1.1, k))); w = d.textlength(txt, font=f)
    hgt = 96 * min(1.1, k)
    d.rounded_rectangle([cx - w / 2 - 50, y - 12, cx + w / 2 + 50, y + hgt * 1.25], radius=60, fill=(235, 255, 225, 235), outline=GRN_D, width=6)
    d.text((cx - w / 2, y - 4), txt, font=f, fill=GRN_TXT)

def draw_slots(im, d, t, filled):
    for i, (x, y) in enumerate(SLOTS):
        d.line([(x, 160 + math.sin(x / 110) * 22), (x, y - 80)], fill=(90, 160, 80), width=5)
        d.ellipse([x - 80, y - 80, x + 80, y + 80], fill=(255, 255, 255, 170), outline=(150, 210, 130), width=6)
        if i < filled:
            paste(im, ITEMS[i], x, y + math.sin(t * 3 + i) * 4, SLOT_SCALE, math.sin(t * 2 + i) * 4)
            d = ImageDraw.Draw(im)
    return d

STAGE = (480, 640)

# ---------- frame ----------
def frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    if t < INTRO:
        draw_pads(d, t)
        paste(im, TW_BIG[talking(t) and int(t * 7) % 2 == 0], STAGE[0], 700 + math.sin(t * 2.5) * 10, pop(t / 0.9), math.sin(t * 2) * 6)
        d = ImageDraw.Draw(im)
        if t > 0.8:
            s = pop((t - 0.8) / 0.6)
            text_c(d, "Green", 480, 300 - 30 * (1 - s), 150 * max(0.3, s), GRN, stroke=(255, 255, 255), sw=12)
            if t > 1.3: text_c(d, "Things!", 480, 470, 110, GRN_D, stroke=(255, 255, 255), sw=10)
        draw_caption(im, t)
        return im.convert("RGB")

    if t >= T_OUT:
        lt = t - T_OUT
        draw_pads(d, t)
        for i in range(NOBJ):
            a = -math.pi / 2 + (i - 1.5) * 0.85 + math.sin(t) * 0.05
            x = 480 + math.cos(a) * 330; y = 830 + math.sin(a) * 330 * 0.9 + math.sin(t * 3 + i) * 12
            paste(im, ITEMS[i], x, y + 120, 0.55 * pop((lt - i * 0.15) / 0.6))
        draw_twinkle(im, t, 480, 900, big=True); d = ImageDraw.Draw(im)
        text_c(d, "Great job!", 480, 230, 120 * max(0.3, pop(lt / 0.6)), GRN, stroke=(255, 255, 255), sw=12)
        if lt > 2.0: text_c(d, "Subscribe for more!", 480, 1240, 58, (255, 255, 255), stroke=GRN_D, sw=7)
        for k in range(10):
            a = t * 1.2 + k * 0.63; x = 480 + math.cos(a) * 420; y = 800 + math.sin(a * 1.3) * 300
            d.polygon(star_poly(x, y, 14 + 6 * math.sin(t * 4 + k), inner=0.4), fill=(255, 235, 120, 220))
        draw_caption(im, t)
        return im.convert("RGB")

    if t >= T_QUIZ:
        lt = t - T_QUIZ
        draw_pads(d, t)
        d = draw_slots(im, d, t, NOBJ)
        ans = lt > 4.9
        text_c(d, "Which one is green?", 480, 480, 76, GRN_D, stroke=(255, 255, 255), sw=9)
        for i, (x, sp) in enumerate(zip([190, 480, 770], QUIZ_IT)):
            y = 760 + math.sin(t * 2 + i * 2) * 14
            s = pop((lt - 0.3 - i * 0.25) / 0.6)
            alpha = 1.0
            if ans and i != 1: alpha = max(0.3, 1 - (lt - 4.9) / 0.6)
            sc = s
            if ans and i == 1: sc = 1 + 0.12 * abs(math.sin((lt - 4.9) * 5)) * max(0, 1 - (lt - 4.9) / 2.5)
            if s > 0:
                bub = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
                rr = 128 * sc
                bd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 255, 255, int(150 * alpha)),
                           outline=(GRN_D + (int(255 * alpha),)) if ans and i == 1 else (255, 255, 255, int(230 * alpha)), width=10 if ans and i == 1 else 6)
                im.alpha_composite(bub)
                paste(im, sp, x, y, 0.75 * sc, 0, alpha)
        d = ImageDraw.Draw(im)
        if ans:
            k = pop((lt - 4.9) / 0.5)
            text_c(d, "Broccoli!", 480, 920, 88 * max(0.3, k), GRN, stroke=(255, 255, 255), sw=10)
            for j in range(8):
                a = j * math.pi / 4 + lt; rr = 150 + 40 * math.sin(lt * 4)
                d.polygon(star_poly(480 + math.cos(a) * rr, 760 + math.sin(a) * rr, 16, inner=0.4), fill=(255, 230, 110, 230))
        x, y = twinkle_pos(t); draw_twinkle(im, t, x, y)
        draw_caption(im, t)
        return im.convert("RGB")

    # ---- object segments ----
    i = int((t - INTRO) // SEG); lt = t - SEG_T[i]
    draw_pads(d, t, glow_i=i if lt > HOP * 0.9 else -1)
    d = draw_slots(im, d, t, i)
    px, py = PADS[i]
    sx, sy = STAGE
    # splash where the thing pops out
    ripple(d, px, py, (lt - HOP) / 1.4)
    droplets(d, px, py - 20, (lt - HOP) / 0.9)
    if lt >= HOP:
        if lt < FLY:
            k = ease((lt - HOP) / (RISE * 0.8))
            x = px + (sx - px) * k; y = py + (sy - py) * k - math.sin(math.pi * k) * 60
            s = 0.25 + 0.75 * pop((lt - HOP) / RISE)
            paste(im, ITEMS[i], x, y + math.sin(t * 3) * 10 * k, s, math.sin(t * 2.2) * 5 * k)
        else:
            k = ease((lt - FLY) / 1.0)
            x = sx + (SLOTS[i][0] - sx) * k; y = sy + (SLOTS[i][1] - sy) * k - math.sin(math.pi * k) * 80
            paste(im, ITEMS[i], x, y, 1.0 + (SLOT_SCALE - 1.0) * k)
            if k >= 1:
                pass
        d = ImageDraw.Draw(im)
        if HOP + 0.9 < lt < FLY + 0.2:
            kk = pop((lt - HOP - 0.9) / 0.5) * (1 - ease((lt - FLY) / 0.2))
            leaf_label(d, NAMES[i], sx, 855, kk)
        if HOP + 1.0 < lt < FLY:
            for j in range(6):
                a = j * math.pi / 3 + lt * 1.5; rr = 230
                d.polygon(star_poly(sx + math.cos(a) * rr, sy + math.sin(a) * rr * 0.85, 13 + 5 * math.sin(lt * 5 + j), inner=0.4), fill=(255, 240, 140, 210))
    tp = twinkle_pos(t)
    draw_twinkle(im, t, *tp)
    draw_caption(im, t)
    return im.convert("RGB")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for ts in sys.argv[2:]:
            frame(float(ts)).save(f"_prev_{ts}.png")
        sys.exit()
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(frame(fi / FPS).tobytes())
    proc.stdin.close(); proc.wait()

    # ---------- audio: plucked kalimba-style lullaby in D major (original) ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    def pluck(freq, dur, vol=0.2, decay=5):
        tt = np.arange(int(dur * SR)) / SR
        w = np.sin(2 * np.pi * freq * tt) + 0.25 * np.sin(2 * np.pi * freq * 3.0 * tt) * np.exp(-10 * tt) \
            + 0.12 * np.sin(2 * np.pi * freq * 5.4 * tt) * np.exp(-20 * tt)
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 400)
    def pad(freqs, dur, vol=0.02):
        tt = np.arange(int(dur * SR)) / SR
        w = sum(np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2 * tt) for f in freqs)
        return vol * w * np.sin(np.pi * tt / dur)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig)); audio[i:j] += sig[:j - i]
    Fq = {"D3": 146.83, "A2": 110.0, "B2": 123.47, "G2": 98.0, "F#3": 185.0, "A3": 220.0, "D4": 293.66, "E4": 329.63,
          "F#4": 369.99, "G4": 392.0, "A4": 440.0, "B4": 493.88, "C#5": 554.37, "D5": 587.33, "E5": 659.25, "F#5": 739.99}
    prog = [("D3", ["D4", "F#4", "A4"]), ("B2", ["D4", "F#4", "B4"]), ("G2", ["D4", "G4", "B4"]), ("A2", ["C#5", "E4", "A4"])]
    melody = ["F#5", "E5", "D5", None, "A4", "B4", "D5", None, "B4", "A4", "F#4", "A4", "E5", None, "C#5", None,
              "D5", "F#5", "E5", "D5", "B4", None, "D5", "B4", "G4", "B4", "D5", "E5", "E5", None, None, None]
    beat = 60 / 100; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 4) % 4; root, ch = prog[bar]
        if k % 4 == 0:
            add(pluck(Fq[root], 2.0, 0.07, 1.8), k * beat)
            add(pad([Fq[n] for n in ch], beat * 4, 0.008), k * beat)
        add(pluck(Fq[ch[k % 3]], 0.6, 0.025, 6), k * beat + beat / 2)
        m = melody[k % 32]
        if m: add(pluck(Fq[m], 1.0, 0.045, 3.5), k * beat)
        k += 1
    def plop(at, vol=0.12, f0=900, f1=250):
        n = int(0.18 * SR); tt = np.arange(n) / SR
        f = f0 + (f1 - f0) * (tt / tt[-1]); ph = 2 * np.pi * np.cumsum(f) / SR
        add(vol * np.sin(ph) * np.exp(-18 * tt), at)
    def boing(at, vol=0.08):
        n = int(0.3 * SR); tt = np.arange(n) / SR
        f = 300 + 500 * (tt / tt[-1]); ph = 2 * np.pi * np.cumsum(f) / SR
        add(vol * np.sin(ph) * np.sin(np.pi * tt / tt[-1]), at)
    for i in range(NOBJ):
        if i > 0: boing(SEG_T[i] + 0.05)
        plop(SEG_T[i] + HOP * 0.95, 0.07, 500, 200)
        plop(SEG_T[i] + HOP + 0.05)
        for j, f in enumerate([587.33, 739.99, 880.0, 1174.66]):
            add(pluck(f, 0.6, 0.08, 6), SEG_T[i] + HOP + 0.9 + j * 0.09)
        add(pluck(1479.98, 0.5, 0.05, 7), SEG_T[i] + FLY + 0.9)
    for j, f in enumerate([587.33, 739.99, 880.0, 1174.66]):
        add(pluck(f, 0.9, 0.1, 4), T_QUIZ + 4.9 + j * 0.13)
    for j, f in enumerate([293.66, 369.99, 440.0, 587.33, 739.99]):
        add(pluck(f, 1.3, 0.1, 3), T_OUT + 0.1 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
