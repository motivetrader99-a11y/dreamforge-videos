"""Dreamforge Kids — Yellow things.
The Yellow Train chugs across a lavender evening-pastel meadow. Each pastel wagon carries a
surprise: Twinkle the star calls it out and a yellow thing rises from the wagon — the sun, a
banana, a duckling and a lemon — then flies up into a "Yellow collection" row at the top.
Quiz: three floating bubbles (purple grapes, yellow corn, red strawberry) — which one is yellow?
Outro: the train parades with all the yellow things aboard. Original art & music (gentle 3/4
waltz in G major with soft train chuffs)."""
import math, random, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/yellow_things.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (60, 45, 85)
YEL = (255, 212, 40)
YEL_D = (225, 165, 10)
YEL_L = (255, 238, 140)
GOLD_TXT = (200, 135, 0)
CX = 465  # visual centre (keeps right 150px clear)
random.seed(11)

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
MOVE, RISE, FLY = 1.1, 1.3, 5.0  # seconds into a segment

NAMES = ["sun", "banana", "duck", "lemon"]
LINES = [
    (0.3, INTRO - 0.1, "Hi! I'm Twinkle! All aboard the Yellow Train!"),
    (SEG_T[0] + 0.2, SEG_T[0] + SEG - 0.1, "The sun is yellow and warm!"),
    (SEG_T[1] + 0.2, SEG_T[1] + SEG - 0.1, "A yellow banana. Yummy!"),
    (SEG_T[2] + 0.2, SEG_T[2] + SEG - 0.1, "A little yellow duck says quack, quack!"),
    (SEG_T[3] + 0.2, SEG_T[3] + SEG - 0.1, "A lemon is yellow and sour!"),
    (T_QUIZ + 0.2, T_QUIZ + 4.8, "Which one is yellow? Can you find it?"),
    (T_QUIZ + 4.9, T_OUT - 0.1, "The corn! The corn is yellow!"),
    (T_OUT + 0.3, TOTAL - 0.4, "Yellow is so sunny! Bye-bye!"),
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

def face(d, cx, cy, r, ink=(70, 45, 50)):
    e = r * 0.11
    for dx in (-r * 0.3, r * 0.3):
        d.ellipse([cx + dx - e, cy - e * 1.3, cx + dx + e, cy + e * 1.3], fill=ink)
        d.ellipse([cx + dx - e * 0.5, cy - e * 1.0, cx + dx + e * 0.1, cy - e * 0.3], fill=(255, 255, 255))
    d.arc([cx - r * 0.2, cy + r * 0.02, cx + r * 0.2, cy + r * 0.32], 20, 160, fill=ink, width=max(3, int(r * 0.07)))
    for dx in (-r * 0.52, r * 0.52):
        d.ellipse([cx + dx - r * 0.12, cy + r * 0.12, cx + dx + r * 0.12, cy + r * 0.26], fill=(255, 140, 150, 170))

def canvas(r):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); return im, ImageDraw.Draw(im), s / 2

# ---------- Twinkle (narrator) ----------
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

# ---------- yellow things ----------
def make_sun(r):
    im, d, c = canvas(r)
    for i in range(12):
        a = i * math.pi / 6
        p1 = (c + math.cos(a - 0.13) * r * 0.78, c + math.sin(a - 0.13) * r * 0.78)
        p2 = (c + math.cos(a + 0.13) * r * 0.78, c + math.sin(a + 0.13) * r * 0.78)
        p3 = (c + math.cos(a) * r * 1.2, c + math.sin(a) * r * 1.2)
        d.polygon([p1, p3, p2], fill=YEL_D if i % 2 else YEL)
    d.ellipse([c - r * 0.8, c - r * 0.8, c + r * 0.8, c + r * 0.8], fill=YEL_D)
    d.ellipse([c - r * 0.76, c - r * 0.8, c + r * 0.76, c + r * 0.72], fill=YEL)
    gloss(im, [c - r * 0.55, c - r * 0.62, c - r * 0.1, c - r * 0.35], 130, r * 0.05)
    face(ImageDraw.Draw(im), c, c + r * 0.05, r * 0.6)
    return im

def make_banana(r):
    im, d, c = canvas(r)
    outer = [(c + math.cos(a) * r * 1.0, c - r * 0.55 + math.sin(a) * r * 1.0) for a in np.linspace(0.35, math.pi - 0.35, 30)]
    inner = [(c + math.cos(a) * r * 0.95, c - r * 0.85 + math.sin(a) * r * 0.75) for a in np.linspace(math.pi - 0.42, 0.42, 30)]
    d.polygon([(x, y + r * 0.04) for x, y in outer] + [(x, y + r * 0.04) for x, y in inner], fill=YEL_D)
    d.polygon(outer + inner, fill=YEL)
    hl = [(c + math.cos(a) * r * 0.88, c - r * 0.62 + math.sin(a) * r * 0.82) for a in np.linspace(0.9, math.pi - 0.9, 16)]
    d.line(hl, fill=YEL_L, width=max(4, int(r * 0.07)))
    # tips
    x0, y0 = outer[0]; x1, y1 = outer[-1]
    d.ellipse([x0 - r * 0.07, y0 - r * 0.12, x0 + r * 0.07, y0 + r * 0.02], fill=(120, 85, 40))
    d.rounded_rectangle([x1 - r * 0.05, y1 - r * 0.2, x1 + r * 0.09, y1 + r * 0.02], radius=6, fill=(140, 120, 50))
    face(ImageDraw.Draw(im), c, c + r * 0.12, r * 0.45)
    return im

def make_duck(r):
    im, d, c = canvas(r)
    # body
    d.ellipse([c - r * 0.95, c - r * 0.05, c + r * 0.75, c + r * 0.9], fill=YEL_D)
    d.ellipse([c - r * 0.95, c - r * 0.1, c + r * 0.72, c + r * 0.84], fill=YEL)
    d.polygon([(c - r * 0.8, c + r * 0.15), (c - r * 1.15, c - r * 0.15), (c - r * 0.95, c + r * 0.4)], fill=YEL)
    # wing
    d.chord([c - r * 0.6, c + r * 0.1, c + r * 0.25, c + r * 0.7], 0, 180, fill=YEL_D)
    # head
    hx, hy = c + r * 0.3, c - r * 0.35
    d.ellipse([hx - r * 0.5, hy - r * 0.5, hx + r * 0.5, hy + r * 0.5], fill=YEL)
    gloss(im, [hx - r * 0.35, hy - r * 0.42, hx - r * 0.05, hy - r * 0.22], 130, r * 0.04); d = ImageDraw.Draw(im)
    # beak
    d.ellipse([hx + r * 0.3, hy + r * 0.0, hx + r * 0.78, hy + r * 0.22], fill=(255, 140, 40))
    d.ellipse([hx + r * 0.3, hy + r * 0.12, hx + r * 0.7, hy + r * 0.3], fill=(235, 115, 30))
    # eye + blush
    e = r * 0.07
    d.ellipse([hx + r * 0.08 - e, hy - r * 0.15 - e * 1.3, hx + r * 0.08 + e, hy - r * 0.15 + e * 1.3], fill=(60, 40, 50))
    d.ellipse([hx + r * 0.05, hy - r * 0.22, hx + r * 0.1, hy - r * 0.16], fill=(255, 255, 255))
    d.ellipse([hx - r * 0.2, hy + r * 0.05, hx + r * 0.02, hy + r * 0.18], fill=(255, 140, 150, 170))
    # hair tuft
    d.arc([hx - r * 0.1, hy - r * 0.75, hx + r * 0.15, hy - r * 0.42], 180, 360, fill=YEL_D, width=max(3, int(r * 0.06)))
    return im

def make_lemon(r):
    im, d, c = canvas(r)
    pts = []
    for a in np.linspace(0, 2 * math.pi, 60, endpoint=False):
        rx = r * 0.95 * (1 + 0.18 * abs(math.cos(a)) ** 8)
        pts.append((c + math.cos(a) * rx, c + math.sin(a) * r * 0.68))
    d.polygon([(x, y + r * 0.04) for x, y in pts], fill=YEL_D)
    d.polygon(pts, fill=(255, 225, 50))
    gloss(im, [c - r * 0.6, c - r * 0.5, c - r * 0.05, c - r * 0.25], 140, r * 0.05); d = ImageDraw.Draw(im)
    # leaf
    d.polygon([(c + r * 0.55, c - r * 0.55), (c + r * 0.85, c - r * 0.95), (c + r * 1.05, c - r * 0.7)], fill=(110, 190, 90))
    for k in range(14):
        x = c + random.uniform(-0.7, 0.7) * r; y = c + random.uniform(-0.45, 0.45) * r
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(245, 200, 30))
    face(d, c, c + r * 0.0, r * 0.5)
    return im

# quiz items
def make_grapes(r):
    im, d, c = canvas(r)
    d.line([(c, c - r * 0.75), (c + r * 0.1, c - r * 0.95)], fill=(110, 80, 50), width=max(4, int(r * 0.07)))
    d.ellipse([c + r * 0.05, c - r * 1.0, c + r * 0.45, c - r * 0.75], fill=(110, 190, 90))
    rows = [(-0.45, 3), (-0.05, 3), (0.32, 2), (0.65, 1)]
    for ry, n in rows:
        for k in range(n):
            x = c + (k - (n - 1) / 2) * r * 0.42; y = c + ry * r
            d.ellipse([x - r * 0.23, y - r * 0.23, x + r * 0.23, y + r * 0.23], fill=(120, 70, 170))
            d.ellipse([x - r * 0.13, y - r * 0.15, x - r * 0.02, y - r * 0.05], fill=(190, 160, 230))
    return im

def make_corn(r):
    im, d, c = canvas(r)
    d.ellipse([c - r * 0.42, c - r * 0.95, c + r * 0.42, c + r * 0.8], fill=YEL_D)
    d.ellipse([c - r * 0.4, c - r * 0.95, c + r * 0.38, c + r * 0.75], fill=YEL)
    for yy in np.arange(-0.8, 0.7, 0.16):
        half = math.sqrt(max(0, 1 - ((yy + 0.08) / 0.86) ** 2)) * 0.36
        for xx in np.arange(-half + 0.06, half, 0.13):
            x, y = c + xx * r, c + yy * r
            d.ellipse([x - r * 0.055, y - r * 0.06, x + r * 0.055, y + r * 0.06], fill=(255, 228, 90))
    d.polygon([(c - r * 0.2, c + r * 1.0), (c - r * 0.75, c - r * 0.3), (c - r * 0.3, c + r * 0.3)], fill=(110, 190, 90))
    d.polygon([(c + r * 0.2, c + r * 1.0), (c + r * 0.75, c - r * 0.3), (c + r * 0.3, c + r * 0.3)], fill=(90, 170, 80))
    return im

def make_strawberry(r):
    im, d, c = canvas(r)
    d.polygon([(c - r * 0.7, c - r * 0.35), (c + r * 0.7, c - r * 0.35), (c + r * 0.45, c + r * 0.45), (c, c + r * 0.85),
               (c - r * 0.45, c + r * 0.45)], fill=(230, 60, 80))
    d.ellipse([c - r * 0.72, c - r * 0.6, c + r * 0.72, c + r * 0.25], fill=(230, 60, 80))
    for k in range(12):
        x = c + random.uniform(-0.45, 0.45) * r; y = c + random.uniform(-0.35, 0.45) * r
        d.ellipse([x - 4, y - 6, x + 4, y + 6], fill=(255, 220, 140))
    for k in range(5):
        a = math.pi + k * math.pi / 4
        d.polygon([(c, c - r * 0.55), (c + math.cos(a - 0.3) * r * 0.25, c - r * 0.55 + math.sin(a - 0.3) * r * 0.1),
                   (c + math.cos(a) * r * 0.5, c - r * 0.55 + math.sin(a) * r * 0.35 - r * 0.05)], fill=(90, 170, 80))
    return im

R_ITEM = 165
ITEMS = [make_sun(R_ITEM), make_banana(int(R_ITEM * 1.3)), make_duck(R_ITEM), make_lemon(R_ITEM)]
QUIZ_ITEMS = [make_grapes(120), make_corn(120), make_strawberry(120)]
TW = [make_twinkle(105, False), make_twinkle(105, True)]
TW_BIG = [make_twinkle(190, False), make_twinkle(190, True)]

# ---------- scene ----------
def background():
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([200, 185, 240]), np.array([255, 220, 235])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    for cx, cy, s in [(330, 830, 0.8), (820, 470, 0.8), (760, 960, 0.6)]:
        for dx, dy, rr in [(-60, 10, 50), (0, -15, 65), (65, 8, 48)]:
            d.ellipse([cx + dx * s - rr * s, cy + dy * s - rr * s, cx + dx * s + rr * s, cy + dy * s + rr * s], fill=(255, 255, 255, 200))
    d.ellipse([-400, 1080, 700, 1500], fill=(170, 220, 190))
    d.ellipse([380, 1050, 1500, 1520], fill=(150, 210, 180))
    d.rectangle([0, 1260, W, H], fill=(140, 200, 170))
    for x in range(0, W, 46):
        d.ellipse([x + 10, 1250, x + 28, 1268], fill=(255, 255, 255) if (x // 46) % 2 else (255, 190, 210))
    # rails
    d.rectangle([0, 1238, W, 1248], fill=(150, 120, 110))
    for x in range(-20, W, 56):
        d.rectangle([x, 1246, x + 30, 1258], fill=(170, 135, 110))
    return bg
BG = background()

WAGON_COL = [(255, 170, 190), (150, 220, 200), (150, 195, 250), (200, 170, 240)]
WG = 250  # wagon spacing

def draw_wagon(d, x, col, t, open_k=0.0):
    y0, y1 = 1080, 1215
    d.rounded_rectangle([x - 110, y0, x + 110, y1], radius=22, fill=col, outline=INK, width=5)
    d.rounded_rectangle([x - 90, y0 + 22, x + 90, y1 - 25], radius=14, fill=tuple(min(255, c + 30) for c in col))
    for wx in (x - 62, x + 62):
        d.ellipse([wx - 30, 1190, wx + 30, 1250], fill=INK)
        d.ellipse([wx - 14, 1206, wx + 14, 1234], fill=(230, 220, 240))
    d.rectangle([x + 110, 1185, x + 140, 1197], fill=INK)
    if open_k > 0:  # lid flips open
        a = open_k * 1.6
        d.line([(x - 110, y0), (x - 110 + math.cos(a) * 220, y0 - math.sin(a) * 220 * 0.6)], fill=INK, width=10)

def draw_loco(d, x, t):
    y1 = 1215
    d.rounded_rectangle([x - 150, 1060, x + 60, y1], radius=26, fill=(255, 140, 120), outline=INK, width=5)
    d.rounded_rectangle([x - 150, 960, x - 40, 1080], radius=18, fill=(255, 140, 120), outline=INK, width=5)
    d.rounded_rectangle([x - 130, 980, x - 60, 1040], radius=10, fill=(230, 245, 255))
    d.rounded_rectangle([x + 60, 1100, x + 130, y1], radius=20, fill=(255, 175, 150), outline=INK, width=5)
    d.rectangle([x - 10, 1000, x + 30, 1060], fill=(255, 175, 150), outline=INK, width=5)
    d.ellipse([x + 105, 1130, x + 135, 1160], fill=(255, 245, 190))
    for wx, rr in ((x - 100, 42), (x + 20, 42), (x + 100, 28)):
        d.ellipse([wx - rr, 1250 - 2 * rr + 10, wx + rr, 1250 + 10 - 0], fill=INK)
        d.ellipse([wx - rr * 0.45, 1250 - rr + 10 - rr * 0.45, wx + rr * 0.45, 1250 - rr + 10 + rr * 0.45], fill=(230, 220, 240))

def train_offset(t):
    """x of wagon 0 centre."""
    if t < INTRO:
        return -700 + (CX + 700) * ease((t - 0.2) / 2.8)
    if t < T_QUIZ:
        i = min(NOBJ - 1, int((t - INTRO) // SEG)); lt = t - SEG_T[i]
        if i == 0: return CX
        return CX + WG * (i - 1) + WG * ease(lt / MOVE)
    return CX + WG * 3

def draw_train(im, t, cargo):
    """cargo[j] = True if wagon j still shows its item peeking out."""
    d = ImageDraw.Draw(im)
    x0 = train_offset(t)
    moving = (t < 3.0) or (INTRO <= t < T_QUIZ and SEG_T[min(NOBJ - 1, int((t - INTRO) // SEG))] + MOVE > t and t > SEG_T[1])
    jig = math.sin(t * 18) * 3 if moving else 0
    for j in range(NOBJ):
        x = x0 - j * WG
        if -150 < x < W + 150:
            if cargo[j]:
                paste(im, ITEMS[j], x, 1075 + jig, 0.32); d = ImageDraw.Draw(im)
            draw_wagon(d, x, WAGON_COL[j], t)
    lx = x0 + 250
    if lx < W + 200:
        draw_loco(d, lx, t)
        # puffs
        for k in range(3):
            ph = (t * 0.8 + k / 3) % 1
            a = int(200 * (1 - ph))
            rr = 18 + ph * 40
            px, py = lx + 10 - ph * 80, 980 - ph * 220
            FX.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(255, 255, 255, a))
    return d

# ---------- captions (speech panel with tail toward Twinkle) ----------
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
    sz = 66; lines = wrap(d, txt, sz, 780)
    if len(lines) > 2: sz = 58; lines = wrap(d, txt, sz, 800)
    lh = sz * 1.22; bh = lh * len(lines) + 56
    top = 1335
    d.rounded_rectangle([45, top, 925, top + bh], radius=40, fill=(255, 252, 235, 240), outline=YEL_D, width=7)
    for i, ln in enumerate(lines):
        f = font(sz); total = d.textlength(ln, font=f); x = 485 - total / 2; y = top + 24 + i * lh
        for word in ln.split(" "):
            col = GOLD_TXT if "yellow" in word.lower() else INK
            d.text((x, y), word, font=f, fill=col)
            x += d.textlength(word + " ", font=f)
    if k < 1: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * k)))
    im.alpha_composite(layer)

def draw_twinkle(im, t, x, y, big=False):
    tk = talking(t)
    mouth = tk and int(t * 7) % 2 == 0
    bob = math.sin(t * 2.5) * 10 + (-abs(math.sin(t * 9)) * 14 if tk else 0)
    paste(im, (TW_BIG if big else TW)[mouth], x, y + bob, 1.0, math.sin(t * 1.8) * 6)

def sparkle(x, y, r, a, col=(255, 240, 150)):
    FX.polygon(star_poly(x, y, r, inner=0.35), fill=col + (int(max(0, min(255, a))),))

SLOTS = [(165 + i * 200, 300) for i in range(NOBJ)]
TW_HOME = (160, 560)
ITEM_POS = (560, 700)

def draw_slots(im, d, t, filled):
    for i, (x, y) in enumerate(SLOTS):
        d.ellipse([x - 78, y - 78, x + 78, y + 78], fill=(255, 255, 255, 160), outline=(255, 255, 255), width=5)
        if i < filled:
            paste(im, ITEMS[i], x, y + math.sin(t * 3 + i) * 4, 0.36); d = ImageDraw.Draw(im)
    return d

# ---------- frame ----------
def frame(t):
    global FX
    im = BG.copy()
    fxl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); FX = ImageDraw.Draw(fxl)
    d = ImageDraw.Draw(im)
    if t < INTRO:
        draw_train(im, t, [True] * NOBJ); d = ImageDraw.Draw(im)
        s = pop((t - 0.2) / 0.8)
        if s > 0:
            f = font(112 * s); txt = "Yellow Things"; w = d.textlength(txt, font=f)
            d.text((CX - w / 2, 150 + (1 - s) * 60), txt, font=f, fill=YEL, stroke_width=12, stroke_fill=INK)
        if t > 1.3:
            text_c(d, "Ride the Yellow Train!", CX, 340, 58, (255, 255, 255), sw=7)
        draw_twinkle(im, t, CX, 700 + (1 - ease(t / 1.2)) * -500)
    elif t < T_QUIZ:
        i = min(NOBJ - 1, int((t - INTRO) // SEG)); lt = t - SEG_T[i]
        filled = i + (1 if lt > FLY + 0.9 else 0)
        text_c(d, "Find YELLOW things!", CX, 110, 68, YEL, sw=9)
        d = draw_slots(im, d, t, filled)
        draw_train(im, t, [j > i or (j == i and lt < RISE) for j in range(NOBJ)]); d = ImageDraw.Draw(im)
        draw_twinkle(im, t, TW_HOME[0], TW_HOME[1])
        # rising item
        if lt >= RISE:
            rk = ease((lt - RISE) / 0.9)
            if lt < FLY:
                x = CX + (ITEM_POS[0] - CX) * rk; y = 1075 + (ITEM_POS[1] - 1075) * rk
                s = 0.32 + (1.0 - 0.32) * rk
                bob = math.sin(t * 3) * 10 * rk
                paste(im, ITEMS[i], x, y + bob, s, math.sin(t * 2) * 4 * rk)
                # glow ring
                if rk > 0.5:
                    rr = R_ITEM * 1.35 + math.sin(lt * 4) * 8
                    FX.ellipse([x - rr, y - rr, x + rr, y + rr], outline=YEL_L + (200,), width=8)
            else:
                fk = ease((lt - FLY) / 0.9)
                sx, sy = SLOTS[i]
                x = ITEM_POS[0] + (sx - ITEM_POS[0]) * fk
                y = ITEM_POS[1] + (sy - ITEM_POS[1]) * fk - math.sin(fk * math.pi) * 120
                if fk < 1: paste(im, ITEMS[i], x, y, 1.0 - 0.64 * fk)
                for j in range(5):
                    sparkle(x - (sx - ITEM_POS[0]) * 0.05 * j, y + 30 * j, 18 - 3 * j, 255 - 45 * j)
            d = ImageDraw.Draw(im)
            rl = lt - RISE - 0.6
            if 0 < rl < 1.6:
                for j in range(8):
                    a = j * math.pi / 4 + rl
                    rr = R_ITEM * (1.0 + rl * 0.5)
                    sparkle(ITEM_POS[0] + math.cos(a) * rr, ITEM_POS[1] + math.sin(a) * rr, 20, 255 * (1 - rl / 1.6),
                            (255, 255, 255) if j % 2 else (255, 225, 80))
            if rl > 0.2 and lt < FLY:
                s = pop((rl - 0.2) / 0.5)
                text_c(d, NAMES[i], ITEM_POS[0], 895, 84 * max(s, 0.05), YEL, sw=10)
        else:
            # wagon pulses: "what's inside?"
            if lt > MOVE - 0.2 or i == 0:
                text_c(d, "?", CX, 900 + math.sin(lt * 8) * 8, 110, (255, 255, 255), sw=10)
    elif t < T_OUT:
        lt = t - T_QUIZ
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 235, 150))); d = ImageDraw.Draw(im)
        text_c(d, "Which one is yellow?", CX, 140, 72, YEL, sw=9)
        draw_twinkle(im, t, 165, 420)
        reveal = lt - 4.9
        pos = [(230, 800), (470, 1040), (715, 760)]
        for j, (x, y) in enumerate(pos):
            ap = pop((lt - 0.3 - j * 0.35) / 0.6)
            if ap <= 0: continue
            fy = y + math.sin(t * 2 + j * 2) * 14
            lift = -abs(math.sin(reveal * 4)) * 35 if (reveal > 0 and j == 1) else 0
            if reveal > 0 and j == 1:
                g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(g).ellipse([x - 175, fy + lift - 175, x + 175, fy + lift + 175], fill=(255, 220, 60, 210))
                im.alpha_composite(g.filter(ImageFilter.GaussianBlur(22)))
            bub = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
            rr = 140 * ap
            bd.ellipse([x - rr, fy + lift - rr, x + rr, fy + lift + rr], fill=(255, 255, 255, 215),
                       outline=(YEL_D if (reveal > 0 and j == 1) else (210, 200, 235)) + (255,), width=8)
            bd.ellipse([x - rr * 0.6, fy + lift - rr * 0.75, x - rr * 0.25, fy + lift - rr * 0.5], fill=(255, 255, 255, 255))
            im.alpha_composite(bub)
            paste(im, QUIZ_ITEMS[j], x, fy + lift, 0.72 * ap, math.sin(t * 2 + j) * 5)
            if reveal > 0 and j != 1:
                dim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(dim).ellipse([x - rr, fy - rr, x + rr, fy + rr], fill=(255, 255, 255, 140))
                im.alpha_composite(dim)
        d = ImageDraw.Draw(im)
        if reveal > 0.3:
            text_c(d, "corn", 470, 1185, 84 * max(pop((reveal - 0.3) / 0.5), 0.05), YEL, sw=10)
            for j in range(10):
                a = j * math.pi / 5 + reveal * 1.5
                sparkle(470 + math.cos(a) * 200, 1040 + math.sin(a) * 200, 20, 255 * max(0, 1 - reveal / 3.5))
    else:
        lt = t - T_OUT
        draw_train(im, T_OUT - 0.01, [False] * NOBJ)
        d = ImageDraw.Draw(im)
        # parade: all yellow things ride on top of wagons, train view fixed
        x0 = CX - 0  # re-centre: show wagons 0..3 nicely
        ring = [(185, 780), (745, 780), (185, 1010), (745, 1010)]
        for i in range(NOBJ):
            s = pop((lt - 0.2 - i * 0.2) / 0.5)
            paste(im, ITEMS[i], ring[i][0], ring[i][1] + math.sin(t * 5 + i) * 12, 0.62 * s, math.sin(t * 4 + i) * 10)
        draw_twinkle(im, t, CX, 880, big=True)
        d = ImageDraw.Draw(im)
        ps = pop((lt - 0.3) / 0.6)
        if ps > 0.1: text_c(d, "Yellow is sunny!", CX, 230, 104 * ps, YEL, sw=11)
        if lt > 2.2:
            text_c(d, "Subscribe for more!", CX, 430, 60, (255, 255, 255), sw=7)
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

    # ---------- audio: gentle original 3/4 waltz in G major + soft chuffs ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    def bell(freq, dur, vol=0.2, decay=4):
        tt = np.arange(int(dur * SR)) / SR
        w = np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 2.01 * tt) * np.exp(-6 * tt)
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 300)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig)); audio[i:j] += sig[:j - i]
    Fq = {"G3": 196.0, "B3": 246.94, "D4": 293.66, "C4": 261.63, "E4": 329.63, "A3": 220.0, "F#4": 369.99,
          "G4": 392.0, "A4": 440.0, "B4": 493.88, "C5": 523.25, "D5": 587.33, "E5": 659.25, "D3": 146.83, "C3": 130.81, "E3": 164.81}
    chords = [("G3", "B3", "D4"), ("C3", "E4", "G4"), ("E3", "G4", "B4"), ("D3", "F#4", "A4")]
    melody = ["B4", "D5", "B4", "A4", "G4", None, "C5", "E5", "C5", "B4", "A4", None,
              "B4", "G4", "E4", "G4", "A4", "B4", "A4", "F#4", "D4", "A4", None, None]
    beat = 60 / 120; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 3) % 4; ch = chords[bar]
        if k % 3 == 0: add(bell(Fq[ch[0]], 1.4, 0.06, 2.5), k * beat)
        else: add(bell(Fq[ch[1]], 0.5, 0.025, 6) + 0, k * beat); add(bell(Fq[ch[2]], 0.5, 0.025, 6), k * beat)
        m = melody[(k // 1) % 24] if k % 1 == 0 else None
        if m: add(bell(Fq[m], 0.9, 0.04, 3.5), k * beat + 0.01)
        k += 1
    # soft chuffs while the train moves
    rng = np.random.default_rng(3)
    def chuff(at, vol=0.03):
        n = int(0.12 * SR); tt = np.arange(n) / SR
        nz = np.convolve(rng.standard_normal(n), np.ones(12) / 12, mode="same")
        add(vol * nz * np.exp(-30 * tt), at)
    for tt in np.arange(0.2, 3.0, 0.25): chuff(tt)
    for i in range(1, NOBJ):
        for tt in np.arange(0, MOVE, 0.22): chuff(SEG_T[i] + tt)
    def whistle(at):
        tt = np.arange(int(0.6 * SR)) / SR
        w = (np.sin(2 * np.pi * 880 * tt) + 0.6 * np.sin(2 * np.pi * 1108.7 * tt)) * np.sin(np.pi * tt / 0.6)
        add(0.04 * w, at)
    whistle(0.4)
    for i in range(NOBJ):
        for j, f in enumerate([587.33, 783.99, 987.77, 1174.66]):
            add(bell(f, 0.6, 0.09, 6), SEG_T[i] + RISE + j * 0.09)
        add(bell(1567.98, 0.5, 0.05, 7), SEG_T[i] + FLY + 0.8)
    for j, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
        add(bell(f, 0.8, 0.11, 4), T_QUIZ + 4.9 + j * 0.13)
    for j, f in enumerate([392, 493.88, 587.33, 783.99, 987.77]):
        add(bell(f, 1.2, 0.1, 3), T_OUT + 0.1 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
