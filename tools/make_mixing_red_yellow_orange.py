"""Dreamforge Kids — Mixing colors: red + yellow = orange.
A cozy paint studio: Twinkle the star shows a red paint can and a yellow paint can. They tip and
pour into a big white mixing bowl, a paintbrush stirs a red/yellow swirl that slowly blends into
orange. Then a big "red + yellow = orange" splat equation, four orange things painted in by the
brush (orange, carrot, pumpkin, goldfish), a quiz (which color do red + yellow make?) and an outro.
Original art & music (soft marimba-style waltz in F major, 3/4, with pour bloops and stir swishes)."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/mixing_red_yellow_orange.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (70, 40, 60)
RED = (235, 60, 65)
YEL = (255, 210, 40)
ORA = (255, 140, 30)
BLU = (70, 140, 235)
PUR = (160, 90, 210)
CX = 465
random.seed(33)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
T_POTS, T_MIX, T_EQ, T_THINGS, T_QUIZ, T_OUT = 5.0, 11.0, 19.0, 25.0, 33.0, 41.0
T_REVEAL = 37.3
TOTAL = 47.5
NFR = int(TOTAL * FPS)
LINES = [
    (0.3, 4.9, "Hi! I'm Twinkle! Let's mix colors today!"),
    (5.2, 10.9, "Here is red paint. And here is yellow paint!"),
    (11.2, 18.9, "Pour them in the bowl, and stir, stir, stir!"),
    (19.1, 24.9, "Wow! Red and yellow make orange!"),
    (25.1, 32.9, "An orange, a carrot, a pumpkin and a fish are orange!"),
    (33.1, 37.2, "Red and yellow make... which color?"),
    (37.3, 40.9, "Orange! You got it!"),
    (41.2, 47.2, "Red plus yellow makes orange! Bye-bye!"),
]
TALK = [(a, a + min(b - a - 0.3, len(txt.split()) * 0.42 + 0.6)) for a, b, txt in LINES]
def talking(t): return any(a <= t < b for a, b in TALK)

# ---------- helpers ----------
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)
def lerp(a, b, m): return tuple(int(a[i] + (b[i] - a[i]) * m) for i in range(3))

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

def text_multi(d, parts, cx, y, sz, sw=8):
    f = font(sz); total = sum(d.textlength(p, font=f) for p, _ in parts)
    x = cx - total / 2
    for p, col in parts:
        d.text((x, y), p, font=f, fill=col, stroke_width=sw, stroke_fill=INK)
        x += d.textlength(p, font=f)

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def gloss(im, box, a=120, blur=6):
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(box, fill=(255, 255, 255, a))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(blur)))

def canvas(r):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); return im, ImageDraw.Draw(im), s / 2

def cute_face(d, cx, cy, r, ink=INK):
    e = r * 0.1
    for dx in (-r * 0.28, r * 0.28):
        d.ellipse([cx + dx - e, cy - e * 1.3, cx + dx + e, cy + e * 1.3], fill=ink)
        d.ellipse([cx + dx - e * 0.5, cy - e * 1.0, cx + dx + e * 0.1, cy - e * 0.3], fill=(255, 255, 255))
    d.arc([cx - r * 0.18, cy + r * 0.02, cx + r * 0.18, cy + r * 0.3], 20, 160, fill=ink, width=max(3, int(r * 0.06)))
    for dx in (-r * 0.48, r * 0.48):
        d.ellipse([cx + dx - r * 0.11, cy + r * 0.12, cx + dx + r * 0.11, cy + r * 0.25], fill=(255, 120, 140, 160))

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
        d.ellipse([c + dx - e, c - e * 1.4, c + dx + e, c + e * 1.2], fill=INK)
        d.ellipse([c + dx - e * 0.5, c - e * 1.1, c + dx + e * 0.1, c - e * 0.4], fill=(255, 255, 255))
    if mouth_open:
        d.ellipse([c - r * 0.13, c + r * 0.12, c + r * 0.13, c + r * 0.36], fill=(150, 50, 60))
        d.ellipse([c - r * 0.07, c + r * 0.25, c + r * 0.07, c + r * 0.34], fill=(255, 130, 140))
    else:
        d.arc([c - r * 0.16, c + r * 0.05, c + r * 0.16, c + r * 0.28], 20, 160, fill=INK, width=max(3, int(r * 0.06)))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([c + dx - r * 0.1, c + r * 0.1, c + dx + r * 0.1, c + r * 0.22], fill=(255, 130, 150, 150))
    # little orange painter's beret
    d.ellipse([c - r * 0.32, c - r * 1.02, c + r * 0.22, c - r * 0.78], fill=(240, 120, 40))
    d.ellipse([c - r * 0.08, c - r * 1.1, c + r * 0.0, c - r * 0.98], fill=(200, 90, 30))
    gloss(im, [c - r * 0.42, c - r * 0.45, c - r * 0.12, c - r * 0.2], 110, 5)
    return im

TW_BIG = [make_twinkle(170, False), make_twinkle(170, True)]
TW_SM = [make_twinkle(88, False), make_twinkle(88, True)]

def draw_twinkle(im, t, x, y, big=False):
    tk = talking(t)
    mouth = tk and (int(t * 7) % 2 == 0)
    bob = -abs(math.sin(t * 8)) * 16 if tk else math.sin(t * 2.2) * 8
    paste(im, (TW_BIG if big else TW_SM)[1 if mouth else 0], x, y + bob, 1.0, math.sin(t * 1.7) * 5)

# ---------- paint cans ----------
def make_can(col, wid=200, hei=210):
    im = Image.new("RGBA", (wid + 60, hei + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, x1, top, bot = 30, 30 + wid, 60, 60 + hei
    d.rounded_rectangle([x0, top, x1, bot], radius=26, fill=(225, 228, 235))
    d.rectangle([x0, top + 50, x1, bot - 50], fill=col)
    d.ellipse([x0, bot - 26, x1, bot + 26], fill=(200, 203, 212))
    d.rectangle([x0, top + 50, x1, bot - 50], fill=col)
    # label splash
    d.ellipse([x0 + wid * 0.32, top + 70, x0 + wid * 0.68, bot - 70], fill=(255, 255, 255, 230))
    d.ellipse([x0 + wid * 0.38, top + 80, x0 + wid * 0.62, bot - 80], fill=col)
    # rim + paint top
    d.ellipse([x0 - 4, top - 30, x1 + 4, top + 30], fill=(190, 194, 205))
    d.ellipse([x0 + 10, top - 22, x1 - 10, top + 22], fill=col)
    # drip
    dx = x0 + wid * 0.2
    d.rounded_rectangle([dx, top, dx + 24, top + 90], radius=12, fill=col)
    d.ellipse([dx - 4, top + 72, dx + 28, top + 104], fill=col)
    gloss(im, [x0 + 14, top + 10, x0 + 50, bot - 20], 100, 5)
    return im

CAN_R, CAN_Y = make_can(RED), make_can(YEL)

# ---------- splat blob ----------
def make_splat(r, col, face=False, seed=0):
    rnd = random.Random(seed)
    im, d, c = canvas(r)
    pts = []
    for i in range(48):
        a = i / 48 * 2 * math.pi
        rr = r * (1 + 0.08 * math.sin(a * 5 + seed) + 0.05 * math.sin(a * 3 + seed * 2))
        pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
    shade = tuple(max(0, v - 45) for v in col)
    d.polygon([(x, y + r * 0.05) for x, y in pts], fill=shade)
    d.polygon(pts, fill=col)
    for k in range(5):
        a = rnd.uniform(0, 2 * math.pi); rr = r * rnd.uniform(1.15, 1.35); s = r * rnd.uniform(0.07, 0.14)
        d.ellipse([c + rr * math.cos(a) - s, c + rr * math.sin(a) - s, c + rr * math.cos(a) + s, c + rr * math.sin(a) + s], fill=col)
    gloss(im, [c - r * 0.6, c - r * 0.65, c - r * 0.1, c - r * 0.35], 120, 6)
    if face: cute_face(d, c, c + r * 0.05, r * 0.8)
    return im

SPL_R = make_splat(110, RED, True, 1)
SPL_Y = make_splat(110, YEL, True, 2)
SPL_O = make_splat(135, ORA, True, 3)
Q_SPL = [make_splat(115, BLU, False, 4), make_splat(115, PUR, False, 5), make_splat(115, ORA, False, 6)]
Q_COL = [BLU, PUR, ORA]
Q_NAME = ["blue", "purple", "orange"]

# ---------- orange things ----------
def make_orange(r):
    im, d, c = canvas(r)
    d.ellipse([c - r * 0.85, c - r * 0.75, c + r * 0.85, c + r * 0.9], fill=(225, 115, 20))
    d.ellipse([c - r * 0.85, c - r * 0.8, c + r * 0.85, c + r * 0.85], fill=ORA)
    rnd = random.Random(9)
    for _ in range(26):
        x, y = c + rnd.uniform(-0.6, 0.6) * r, c + rnd.uniform(-0.55, 0.65) * r
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(235, 120, 25))
    d.rounded_rectangle([c - r * 0.05, c - r * 0.98, c + r * 0.05, c - r * 0.72], radius=4, fill=(110, 80, 40))
    d.ellipse([c + r * 0.0, c - r * 1.05, c + r * 0.5, c - r * 0.8], fill=(90, 170, 70))
    gloss(im, [c - r * 0.6, c - r * 0.55, c - r * 0.2, c - r * 0.25], 130, 6)
    cute_face(d, c, c + r * 0.1, r * 0.7)
    return im

def make_carrot(r):
    im, d, c = canvas(r)
    for k, a in enumerate((-25, 0, 25)):
        ang = math.radians(a - 90)
        x, y = c + math.cos(ang) * r * 0.55, c - r * 0.55 + math.sin(ang) * r * 0.55
        d.polygon([(c - r * 0.1, c - r * 0.55), (c + r * 0.1, c - r * 0.55), (x + r * 0.1, y), (x - r * 0.1, y)], fill=(80, 165, 70))
        d.ellipse([x - r * 0.14, y - r * 0.14, x + r * 0.14, y + r * 0.14], fill=(95, 185, 80))
    d.polygon([(c - r * 0.42, c - r * 0.55), (c + r * 0.42, c - r * 0.55), (c + r * 0.05, c + r * 1.0), (c - r * 0.05, c + r * 1.0)], fill=ORA)
    d.ellipse([c - r * 0.42, c - r * 0.7, c + r * 0.42, c - r * 0.4], fill=ORA)
    for yy in (0.05, 0.35, 0.62):
        d.line([c - r * 0.25 * (1 - yy), c + r * yy, c - r * 0.05, c + r * yy], fill=(215, 105, 20), width=5)
    gloss(im, [c - r * 0.32, c - r * 0.6, c - r * 0.1, c - r * 0.1], 110, 5)
    cute_face(d, c, c - r * 0.3, r * 0.45)
    return im

def make_pumpkin(r):
    im, d, c = canvas(r)
    for dx, wv, col in ((-0.45, 0.55, (230, 115, 20)), (0.45, 0.55, (230, 115, 20)), (-0.2, 0.5, ORA), (0.2, 0.5, ORA), (0, 0.45, (255, 155, 45))):
        d.ellipse([c + (dx - wv) * r, c - r * 0.6, c + (dx + wv) * r, c + r * 0.8], fill=col)
    d.rounded_rectangle([c - r * 0.08, c - r * 0.9, c + r * 0.1, c - r * 0.55], radius=6, fill=(100, 140, 60))
    d.arc([c + r * 0.05, c - r * 0.95, c + r * 0.45, c - r * 0.6], 180, 330, fill=(90, 160, 70), width=6)
    gloss(im, [c - r * 0.55, c - r * 0.4, c - r * 0.25, c - r * 0.1], 110, 6)
    cute_face(d, c, c + r * 0.12, r * 0.7)
    return im

def make_fish(r):
    im, d, c = canvas(r)
    d.polygon([(c + r * 0.45, c), (c + r * 1.0, c - r * 0.45), (c + r * 0.85, c), (c + r * 1.0, c + r * 0.45)], fill=(240, 115, 25))
    d.polygon([(c - r * 0.1, c - r * 0.5), (c + r * 0.3, c - r * 0.8), (c + r * 0.35, c - r * 0.4)], fill=(240, 115, 25))
    d.ellipse([c - r * 0.85, c - r * 0.55, c + r * 0.6, c + r * 0.55], fill=ORA)
    d.ellipse([c - r * 0.1, c - r * 0.3, c + r * 0.4, c + r * 0.3], fill=(255, 175, 80))
    ex, ey = c - r * 0.45, c - r * 0.12
    d.ellipse([ex - r * 0.17, ey - r * 0.17, ex + r * 0.17, ey + r * 0.17], fill=(255, 255, 255))
    d.ellipse([ex - r * 0.1, ey - r * 0.1, ex + r * 0.1, ey + r * 0.12], fill=INK)
    d.ellipse([ex - r * 0.06, ey - r * 0.08, ex, ey - r * 0.02], fill=(255, 255, 255))
    d.arc([c - r * 0.78, c + r * 0.0, c - r * 0.5, c + r * 0.22], 300, 60, fill=INK, width=5)
    d.ellipse([c - r * 0.42, c + r * 0.12, c - r * 0.22, c + r * 0.24], fill=(255, 120, 140, 160))
    for k in range(3):
        bx, by = c - r * 1.0, c - r * (0.6 + k * 0.28)
        s = r * (0.06 + k * 0.03)
        d.ellipse([bx - s, by - s, bx + s, by + s], outline=(120, 190, 240), width=4)
    gloss(im, [c - r * 0.6, c - r * 0.45, c - r * 0.2, c - r * 0.25], 110, 5)
    return im

THINGS = [make_orange(120), make_carrot(120), make_pumpkin(120), make_fish(120)]
THING_NAMES = ["orange", "carrot", "pumpkin", "fish"]
THING_POS = [(CX - 200, 500), (CX + 200, 500), (CX - 200, 860), (CX + 200, 860)]
THING_SM = [s.resize((s.width * 5 // 9, s.height * 5 // 9), Image.BILINEAR) for s in THINGS]

# ---------- background: cozy paint studio ----------
def background():
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([255, 247, 235]), np.array([255, 228, 208])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1).reshape(H, W, 3)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    for x in range(0, W, 90):
        d.rectangle([x, 0, x + 40, 1240], fill=(255, 238, 222, 255))
    # faint paint dabs on the wall
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    rnd = random.Random(5)
    for _ in range(26):
        x, y = rnd.randint(0, W), rnd.randint(40, 1180)
        r = rnd.randint(14, 34); col = rnd.choice([RED, YEL, ORA, (255, 170, 190), (170, 210, 255)])
        ld.ellipse([x - r, y - r, x + r, y + r], fill=col + (55,))
    bg.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))
    d = ImageDraw.Draw(bg)
    # wooden table
    d.rectangle([0, 1250, W, H], fill=(205, 150, 105))
    d.rectangle([0, 1240, W, 1262], fill=(175, 120, 80))
    for y in range(1300, H, 70):
        d.line([0, y, W, y + 10], fill=(190, 136, 95), width=4)
    return bg

BG = background()

# ---------- captions ----------
def wrap(d, txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if d.textlength(tst, font=f) <= maxw: cur = tst
        else: lines.append(cur); cur = w_
    if cur: lines.append(cur)
    return lines

def draw_caption(im, t):
    cur = None
    for a, b, txt in LINES:
        if a <= t < b: cur = (a, b, txt)
    if not cur: return
    a, b, txt = cur
    al = min(1, (t - a) / 0.25, (b - t) / 0.25)
    if al <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    sz = 64; lines = wrap(d, txt, sz, 780)
    if len(lines) > 2: sz = 56; lines = wrap(d, txt, sz, 800)
    lh = sz * 1.25; hgt = lh * len(lines) + 50
    y0 = 1450 - hgt / 2
    d.rounded_rectangle([40, y0, 890, y0 + hgt], radius=36, fill=(85, 50, 90, 225), outline=(255, 190, 110, 255), width=5)
    for i, ln in enumerate(lines):
        text_c(d, ln, CX, y0 + 22 + i * lh, sz, (255, 255, 255), stroke=(60, 30, 60), sw=4)
    if al < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
    im.alpha_composite(lay)

# ---------- mixing bowl ----------
BOWL_X, RIM_Y, BW, BH = CX, 900, 470, 130
cw, ch = 420, 104
uu, vv = np.meshgrid(np.linspace(-1, 1, cw), np.linspace(-1, 1, ch))
RR = np.sqrt(uu ** 2 + vv ** 2); TH = np.arctan2(vv, uu)
INSIDE = (RR <= 1.0)

def mix_image(t):
    fill = 0.25 + 0.75 * ease((t - 11.6) / 1.6)
    th = 1.6 - 1.6 * ease((t - 13.0) / 1.5)
    s = ease((t - 14.6) / 3.4)
    phase = max(0.0, t - 14.6) * 2.5
    th2 = TH + s * 9 * (1 - RR) + phase * (s > 0)
    u2, v2 = RR * np.cos(th2), RR * np.sin(th2)
    f = u2 + 0.3 * np.sin(3 * v2 + 1)
    yl = np.clip((f - th) * 5 + 0.5, 0, 1)[..., None]
    base = np.array(RED) * (1 - yl) + np.array(YEL) * yl
    m = ease((t - 15.8) / 2.6)
    col = base * (1 - m) + np.array(ORA) * m
    rgba = np.zeros((ch, cw, 4), np.uint8)
    rgba[..., :3] = col.astype(np.uint8)
    mask = RR <= fill
    rgba[..., 3] = np.where(mask, 255, 0)
    img = Image.fromarray(rgba, "RGBA")
    hl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([cw * 0.2, ch * 0.12, cw * 0.45, ch * 0.32], fill=(255, 255, 255, 90))
    img.alpha_composite(hl)
    return img

def draw_bowl(im, t, sc=1.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    bw, bh = BW * sc, BH * sc
    x0, x1 = BOWL_X - bw / 2, BOWL_X + bw / 2
    d.ellipse([x0 + 30, RIM_Y + bh * 1.95, x1 - 30, RIM_Y + bh * 2.35], fill=(150, 100, 70, 120))
    d.chord([x0, RIM_Y - bw * 0.55, x1, RIM_Y + bw * 0.55], 0, 180, fill=(250, 250, 255))
    d.chord([x0 + 6, RIM_Y - bw * 0.55 + 6, x1 - 6, RIM_Y + bw * 0.55 - 6], 0, 180, fill=(255, 255, 255))
    d.ellipse([x0, RIM_Y - bh / 2, x1, RIM_Y + bh / 2], fill=(235, 236, 245))
    d.ellipse([x0 + 16, RIM_Y - bh / 2 + 10, x1 - 16, RIM_Y + bh / 2 - 10], fill=(210, 212, 225))
    # stripe decoration
    d.arc([x0 + 10, RIM_Y - bw * 0.35, x1 - 10, RIM_Y + bw * 0.35], 20, 160, fill=(150, 200, 240), width=10)
    im.alpha_composite(lay)
    if t > 11.55 and sc >= 0.99:
        mi = mix_image(t)
        im.alpha_composite(mi, (int(BOWL_X - cw / 2), int(RIM_Y - ch / 2)))
    lay2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay2).ellipse([x0 + 30, RIM_Y + bw * 0.12, x0 + 110, RIM_Y + bw * 0.32], fill=(255, 255, 255, 140))
    im.alpha_composite(lay2.filter(ImageFilter.GaussianBlur(6)))

def draw_brush(d, tipx, tipy, ang, paint):
    hx, hy = tipx + math.cos(ang) * 330, tipy + math.sin(ang) * 330
    fx, fy = tipx + math.cos(ang) * 70, tipy + math.sin(ang) * 70
    d.line([fx, fy, hx, hy], fill=(150, 95, 60), width=22)
    d.ellipse([hx - 11, hy - 11, hx + 11, hy + 11], fill=(150, 95, 60))
    mx, my = tipx + math.cos(ang) * 95, tipy + math.sin(ang) * 95
    d.line([fx, fy, mx, my], fill=(200, 200, 210), width=28)
    px, py = -math.sin(ang), math.cos(ang)
    d.polygon([(fx + px * 18, fy + py * 18), (fx - px * 18, fy - py * 18), (tipx - px * 5, tipy - py * 5), (tipx + px * 5, tipy + py * 5)], fill=paint)

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

def sparkles(d, cx, cy, t, rad=220, n=8, col=(255, 230, 120)):
    for k in range(n):
        a = k / n * 2 * math.pi + t * 0.8
        r = rad + 20 * math.sin(t * 3 + k)
        s = 10 + 8 * (math.sin(t * 5 + k * 1.7) + 1) / 2
        d.polygon(star_poly(cx + r * math.cos(a), cy + r * math.sin(a), s), fill=col)

for fi in range(NFR):
    t = fi / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    if t < T_POTS:
        draw_twinkle(im, t, CX, 560, big=True) if t > 0 else None
        s = pop(t / 0.9)
        if s < 1: pass
        d = ImageDraw.Draw(im)
        if t > 0.9: text_c(d, "Mixing Colors!", CX, 860, 112, (255, 150, 40), sw=10)
        if t > 1.7:
            text_multi(d, [("Red", RED), (" + ", (255, 255, 255)), ("Yellow", YEL), (" = ?", (255, 255, 255))], CX, 1030, 80, sw=7)
        # little paint dots bouncing
        for k, col in enumerate([RED, YEL, ORA]):
            x = CX - 160 + k * 160; y = 1200 + math.sin(t * 4 + k) * 10
            if t > 2.2 + k * 0.3:
                d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col, outline=INK, width=4)
    elif t < T_MIX:
        lt = t - T_POTS
        sr, sy = pop((lt - 0.2) / 0.7), pop((lt - 2.6) / 0.7)
        paste(im, CAN_R, CX - 200, 680 + math.sin(t * 2) * 6, sr)
        paste(im, CAN_Y, CX + 200, 680 + math.sin(t * 2 + 1) * 6, sy)
        d = ImageDraw.Draw(im)
        if lt > 0.8: text_c(d, "red", CX - 200, 860, 96, RED, sw=8)
        if lt > 3.2: text_c(d, "yellow", CX + 200, 860, 96, YEL, sw=8)
        draw_twinkle(im, t, 835, 1175)
    elif t < T_EQ:
        lt = t - T_MIX
        draw_bowl(im, t)
        d = ImageDraw.Draw(im)
        # cans lift and tip
        for k, (sp, col, side) in enumerate([(CAN_R, RED, -1), (CAN_Y, YEL, 1)]):
            p0 = 0.0 + k * 1.3   # start of tilt
            mv = ease((lt - p0) / 0.6) * (1 - ease((lt - p0 - 2.3) / 0.6))
            x = CX + side * (200 - 40 * mv); y = 680 - 250 * ease((lt - p0) / 0.6) + 0 * mv
            if lt > p0 + 2.6: y = 430 - 0 * mv
            ang = -side * 70 * mv
            if lt < 6.0:
                paste(im, sp, x, y, 0.85, ang, alpha=1 - ease((lt - 4.6) / 0.6))
            # paint stream drops
            if p0 + 0.5 < lt < p0 + 2.3:
                d = ImageDraw.Draw(im)
                sx, sy = x - side * 90, y + 20
                for j in range(9):
                    ph = ((lt * 2.2) + j / 9) % 1.0
                    px = sx + (BOWL_X - side * 40 - sx) * ph
                    py = sy + (RIM_Y - 10 - sy) * ph * ph
                    rr = 22 - 6 * ph
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=col)
        d = ImageDraw.Draw(im)
        # brush stirs
        if lt > 3.3:
            ba = ease((lt - 3.3) / 0.5) * (1 - ease((lt - 7.3) / 0.5))
            a = (lt - 3.6) * 4.2
            tipx = BOWL_X + 120 * math.cos(a); tipy = RIM_Y + 26 * math.sin(a)
            tipy -= (1 - ba) * 400
            m = ease((t - 15.8) / 2.6)
            if ba > 0.02:
                draw_brush(d, tipx, tipy, math.radians(-70), lerp((240, 110, 50), ORA, m))
        if lt > 4.6:
            text_c(d, "stir, stir, stir!", CX, 330, 84, (255, 150, 40), sw=8) if lt < 7.0 else None
        if lt > 7.0:
            text_c(d, "orange!", CX, 330, 110, ORA, sw=9)
            sparkles(d, BOWL_X, RIM_Y, t, 260, 8, (255, 200, 90))
        draw_twinkle(im, t, 835, 1175)
    elif t < T_THINGS:
        lt = t - T_EQ
        for sp, x, at, name, col in [(SPL_R, CX - 290, 0.2, "red", RED), (SPL_Y, CX - 10, 1.0, "yellow", YEL), (SPL_O, CX + 285, 2.0, "orange", ORA)]:
            s = pop((lt - at) / 0.7)
            bob = math.sin(t * 3 + x) * 8
            paste(im, sp, x, 640 + bob, s * (0.75 if sp is not SPL_O else 0.82))
            d = ImageDraw.Draw(im)
            if lt > at + 0.4: text_c(d, name, x, 790, 62, col, sw=6)
        d = ImageDraw.Draw(im)
        if lt > 0.7: text_c(d, "+", CX - 150, 570, 110, (255, 255, 255), sw=8)
        if lt > 1.6: text_c(d, "=", CX + 135, 570, 110, (255, 255, 255), sw=8)
        if lt > 2.6:
            s = pop((lt - 2.6) / 0.6)
            text_c(d, "ORANGE!", CX, 880 + (1 - s) * 40, int(130 * max(0.3, s)), ORA, sw=10)
            sparkles(d, CX + 285, 640, t, 140, 7)
        draw_twinkle(im, t, 835, 1175)
    elif t < T_QUIZ:
        lt = t - T_THINGS
        # mini equation at top
        for k, col in enumerate([RED, YEL, ORA]):
            x = CX - 170 + k * 170
            d.ellipse([x - 38, 165 - 38, x + 38, 165 + 38], fill=col, outline=INK, width=5)
        text_c(d, "+", CX - 85, 118, 70, (255, 255, 255), sw=6)
        text_c(d, "=", CX + 85, 118, 70, (255, 255, 255), sw=6)
        for i, (sp, (x, y)) in enumerate(zip(THINGS, THING_POS)):
            at = 0.3 + i * 1.8
            if lt < at: continue
            rv = ease((lt - at) / 0.9)
            bob = math.sin(t * 2.5 + i) * 7
            if rv < 1:
                msk = Image.new("L", sp.size, 0)
                rr = rv * sp.width * 0.75
                ImageDraw.Draw(msk).ellipse([sp.width / 2 - rr, sp.height / 2 - rr, sp.width / 2 + rr, sp.height / 2 + rr], fill=255)
                sp2 = sp.copy(); sp2.putalpha(Image.fromarray(np.minimum(np.array(sp.getchannel("A")), np.array(msk))))
                paste(im, sp2, x, y + bob)
                d = ImageDraw.Draw(im)
                a = lt * 14
                draw_brush(d, x + 70 * math.cos(a), y + 50 * math.sin(a * 0.7), math.radians(-60), ORA)
            else:
                paste(im, sp, x, y + bob)
            d = ImageDraw.Draw(im)
            if lt > at + 0.7: text_c(d, THING_NAMES[i], x, y + 150, 66, ORA, sw=6)
        draw_twinkle(im, t, 835, 1175)
    elif t < T_OUT:
        lt = t - T_QUIZ
        text_multi(d, [("Red", RED), (" + ", (255, 255, 255)), ("Yellow", YEL), (" = ?", (255, 255, 255))], CX, 230, 92, sw=8)
        rev = ease((t - T_REVEAL) / 0.6)
        for k, sp in enumerate(Q_SPL):
            x = CX - 280 + k * 280
            s = pop((lt - 0.3 - k * 0.4) / 0.7)
            bob = math.sin(t * 3 + k * 2) * 10
            if k == 2: s *= 1 + 0.25 * rev; al = 1.0
            else: al = 1 - 0.65 * rev
            paste(im, sp, x, 680 + bob, s * 0.85, alpha=al)
            d = ImageDraw.Draw(im)
            if lt > 0.8 + k * 0.4:
                text_c(d, Q_NAME[k], x, 840, 58, Q_COL[k] if (k == 2 or rev < 0.5) else (200, 185, 190), sw=5)
        d = ImageDraw.Draw(im)
        if t < T_REVEAL:
            q = 1 + 0.08 * math.sin(t * 6)
            text_c(d, "?", CX, 950, int(130 * q), (255, 255, 255), sw=9)
        else:
            x = CX + 280
            d.ellipse([x + 50, 560, x + 130, 640], fill=(110, 200, 110), outline=(255, 255, 255), width=6)
            d.line([x + 70, 600, x + 87, 618, x + 113, 580], fill=(255, 255, 255), width=10)
            sparkles(d, x, 680, t, 170, 8)
            text_c(d, "Orange!", CX, 940, int(110 * max(0.4, pop((t - T_REVEAL) / 0.6))), ORA, sw=10)
        draw_twinkle(im, t, 835, 1175)
    else:
        lt = t - T_OUT
        draw_twinkle(im, t, CX, 560, big=True)
        for i, sp in enumerate(THING_SM):
            a = i / 4 * 2 * math.pi + t * 0.6
            x, y = CX + 300 * math.cos(a), 560 + 210 * math.sin(a)
            paste(im, sp, x, y, pop((lt - i * 0.25) / 0.6))
        d = ImageDraw.Draw(im)
        if lt > 0.8:
            text_multi(d, [("Red", RED), (" + ", (255, 255, 255)), ("Yellow", YEL), (" = ", (255, 255, 255)), ("Orange", ORA)], CX, 880, 78, sw=7)
        if lt > 2.2: text_c(d, "Great mixing!", CX, 1010, 90, (255, 255, 255), sw=8)
        if lt > 3.2: text_c(d, "Subscribe for more!", CX, 1130, 58, (255, 200, 120), sw=6)
    draw_caption(im, t)
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, kind="marimba", decay=6):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if kind == "marimba": w += 0.35 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-25 * tt)
    if kind == "bell": w += 0.4 * np.sin(2 * np.pi * freq * 2 * tt) + 0.15 * np.sin(2 * np.pi * freq * 3 * tt)
    env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]

# original waltz in F major (3/4)
F = {"F": 349.23, "G": 392.0, "A": 440.0, "Bb": 466.16, "C": 523.25, "D": 587.33, "E": 659.25, "F2": 698.46}
mel = ["A", "C", "F2", "E", "D", "C", "Bb", "D", "G", "A", "G", "F",
       "A", "C", "D", "F2", "E", "D", "C", "Bb", "A", "G", "A", "F"]
bassn = [174.61, 116.54, 130.81, 174.61, 174.61, 116.54, 130.81, 174.61]
chords = [(349.23, 440.0), (466.16, 587.33), (392.0, 523.25), (349.23, 440.0)] * 2
beat = 0.42; k = 0
while k * beat < TOTAL - 1.2:
    bar = k // 3; pos = k % 3
    add(tone(F[mel[k % 24]], 0.8, 0.045, "marimba", 5), k * beat)
    if pos == 0: add(tone(bassn[bar % 8], 1.2, 0.06, "sine", 2), k * beat)
    else:
        for f in chords[bar % 8]: add(tone(f, 0.4, 0.015, "marimba", 8), k * beat)
    k += 1

def bloop(at, f0=600, f1=250, dur=0.18, vol=0.12):
    tt = np.arange(int(dur * SR)) / SR
    fr = np.linspace(f0, f1, len(tt)); ph = 2 * np.pi * np.cumsum(fr) / SR
    add(vol * np.sin(ph) * np.exp(-12 * tt), at)
def swish(at, dur=0.5, vol=0.06):
    n = int(dur * SR); nz = np.random.RandomState(int(at * 10)).randn(n)
    nz = np.convolve(nz, np.ones(40) / 40, mode="same")
    env = np.sin(np.linspace(0, np.pi, n))
    add(vol * nz * env * 4, at)

add(tone(698, 0.6, 0.14, "bell"), 0.9); add(tone(880, 0.8, 0.14, "bell"), 1.7)
add(tone(523, 0.4, 0.14, "bell"), T_POTS + 0.2); add(tone(659, 0.4, 0.14, "bell"), T_POTS + 2.6)
for k2 in range(2):
    p0 = T_MIX + k2 * 1.3
    for j in range(7): bloop(p0 + 0.55 + j * 0.24, 700 - j * 20, 260)
for j in range(8): swish(T_MIX + 3.6 + j * 0.5)
for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]): add(tone(f, 1.0, 0.13, "bell", 3), T_MIX + 7.0 + i * 0.12)
for i, at in enumerate([0.2, 1.0, 2.0]): add(tone([523, 659, 784][i], 0.5, 0.14, "bell"), T_EQ + at)
for i in range(4): add(tone([659, 698, 784, 880][i], 0.5, 0.13, "bell"), T_THINGS + 0.3 + i * 1.8)
for i, f in enumerate([698.46, 880, 1046.5, 1396.9]): add(tone(f, 1.1, 0.14, "bell", 3), T_REVEAL + i * 0.12)
for i, f in enumerate([523.25, 659.25, 783.99, 1046.5, 1318.5]): add(tone(f, 1.2, 0.12, "bell", 3), T_OUT + 0.2 + i * 0.15)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
print("done", round(TOTAL, 1))
