"""Dreamforge Kids — Red things.
A cozy pastel play room with a polka-dot wall. Twinkle the star finds red things one at a
time: an apple, a strawberry, a ladybug and a fire truck. Each pops onto a glowing round
rug in the middle, its name appears, a red paint splash says "RED!", then it hops up into
the "Red Shelf" at the top. Quiz: a blue ball, a red tomato and a yellow banana — which one
is red? The tomato glows. Outro: all the red things wave from the shelf.
Captions sit in a bottom-middle panel (kept above the Shorts UI). Original art & music
(soft marimba in G major, 3/4 sway)."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/red_things.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (70, 40, 55)
RED = (226, 45, 55)
random.seed(2024)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, OBJ, QUIZ, OUTRO = 5.0, 6.2, 10.0, 7.5
NOBJ = 4
OBJ_T = [INTRO + i * OBJ for i in range(NOBJ)]
T_QUIZ = INTRO + NOBJ * OBJ
T_OUT = T_QUIZ + QUIZ
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

NAMES = ["apple", "strawberry", "ladybug", "fire truck"]
LINES = [
    (0.3, INTRO - 0.1, "Hi! I'm Twinkle! Let's find RED things!"),
    (OBJ_T[0] + 0.2, OBJ_T[0] + OBJ - 0.1, "A red apple. Crunch, crunch!"),
    (OBJ_T[1] + 0.2, OBJ_T[1] + OBJ - 0.1, "A red strawberry. Yummy!"),
    (OBJ_T[2] + 0.2, OBJ_T[2] + OBJ - 0.1, "A red ladybug with black spots!"),
    (OBJ_T[3] + 0.2, OBJ_T[3] + OBJ - 0.1, "A big red fire truck. Nee-naw!"),
    (T_QUIZ + 0.2, T_QUIZ + 5.0, "Which one is red? Can you find it?"),
    (T_QUIZ + 5.1, T_OUT - 0.1, "The tomato! The tomato is red!"),
    (T_OUT + 0.3, TOTAL - 0.4, "Red, red, red! Great looking! Bye-bye!"),
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

def shade(c, k): return tuple(max(0, min(255, int(v + k))) for v in c)

def face(d, cx, cy, r, ink=(50, 30, 40), blush=True):
    e = r * 0.11
    for dx in (-r * 0.3, r * 0.3):
        d.ellipse([cx + dx - e, cy - e * 1.3, cx + dx + e, cy + e * 1.3], fill=ink)
        d.ellipse([cx + dx - e * 0.5, cy - e * 1.0, cx + dx + e * 0.1, cy - e * 0.3], fill=(255, 255, 255))
    d.arc([cx - r * 0.2, cy + r * 0.02, cx + r * 0.2, cy + r * 0.32], 20, 160, fill=ink, width=max(3, int(r * 0.07)))
    if blush:
        for dx in (-r * 0.52, r * 0.52):
            d.ellipse([cx + dx - r * 0.12, cy + r * 0.12, cx + dx + r * 0.12, cy + r * 0.26], fill=(255, 150, 170, 170))

def gloss(im, box, a=120):
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(box, fill=(255, 255, 255, a))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(6)))

# ---------- characters & objects (drawn at size ~ 2r) ----------
def make_twinkle(r, mouth_open):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c = s / 2
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(c, c, r * 1.1), fill=(255, 225, 90, 140))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15))); d = ImageDraw.Draw(im)
    d.polygon(star_poly(c, c + r * 0.05, r), fill=(225, 165, 30))
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

def make_apple(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse([c - r, c - r * 0.85, c + r, c + r * 0.95], fill=(195, 28, 40))
    d.ellipse([c - r * 0.95, c - r * 0.85, c + r * 0.95, c + r * 0.86], fill=RED)
    d.ellipse([c - r * 0.18, c - r * 0.92, c + r * 0.18, c - r * 0.7], fill=(195, 28, 40))
    d.line([c, c - r * 0.78, c + r * 0.08, c - r * 1.15], fill=(110, 70, 40), width=int(r * 0.12))
    d.ellipse([c + r * 0.1, c - r * 1.15, c + r * 0.6, c - r * 0.88], fill=(90, 180, 80))
    gloss(im, [c - r * 0.7, c - r * 0.6, c - r * 0.35, c - r * 0.15])
    d = ImageDraw.Draw(im); face(d, c, c + r * 0.05, r * 0.85)
    return im

def make_strawberry(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    pts = []
    for i in range(60):
        a = i / 60 * 2 * math.pi
        x = math.sin(a); y = -math.cos(a)
        wdt = 0.95 * (1 - 0.55 * max(0, y)) if y > 0 else 0.95
        pts.append((c + x * r * wdt, c + y * r * (1.05 if y > 0 else 0.7)))
    d.polygon(pts, fill=(205, 35, 50))
    d.polygon([(c + (x - c) * 0.94, c + (y - c) * 0.94 - 3) for x, y in pts], fill=(235, 55, 70))
    rnd = random.Random(5)
    for _ in range(26):
        x = rnd.uniform(-0.75, 0.75); y = rnd.uniform(-0.45, 0.85)
        if abs(x) > 0.9 * (1 - 0.55 * max(0, y)) - 0.12: continue
        if abs(x) < 0.45 and -0.15 < y < 0.45: continue  # keep face clear
        px, py = c + x * r, c + y * r
        d.ellipse([px - r * 0.035, py - r * 0.05, px + r * 0.035, py + r * 0.05], fill=(255, 225, 120))
    for k in range(5):
        a = -math.pi / 2 + (k - 2) * 0.5
        d.polygon([(c - r * 0.12, c - r * 0.62), (c + r * 0.12, c - r * 0.62),
                   (c + math.cos(a + math.pi / 2) * r * 0.55, c - r * 0.62 - abs(math.sin(a + math.pi / 2)) * r * 0.05 - r * 0.12 * (k % 2))],
                  fill=(80, 170, 80))
    d.ellipse([c - r * 0.25, c - r * 0.8, c + r * 0.25, c - r * 0.55], fill=(90, 185, 85))
    d.line([c, c - r * 0.75, c, c - r * 1.0], fill=(80, 150, 70), width=int(r * 0.08))
    gloss(im, [c - r * 0.65, c - r * 0.5, c - r * 0.35, c - r * 0.2], 100)
    d = ImageDraw.Draw(im); face(d, c, c + r * 0.12, r * 0.75)
    return im

def make_ladybug(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    for k in range(3):  # little legs
        for sx in (-1, 1):
            y = c + r * (0.05 + k * 0.3)
            d.line([c + sx * r * 0.8, y, c + sx * r * 1.12, y + r * 0.12], fill=(40, 30, 35), width=int(r * 0.07))
    d.ellipse([c - r * 0.95, c - r * 0.6, c + r * 0.95, c + r * 1.0], fill=(190, 25, 40))
    d.ellipse([c - r * 0.9, c - r * 0.58, c + r * 0.9, c + r * 0.94], fill=RED)
    d.line([c, c - r * 0.4, c, c + r * 0.98], fill=(40, 30, 35), width=int(r * 0.07))
    for x, y, rr in [(-0.5, 0.15, 0.17), (0.5, 0.15, 0.17), (-0.35, 0.58, 0.15), (0.35, 0.58, 0.15), (-0.62, 0.45, 0.1), (0.62, 0.45, 0.1)]:
        d.ellipse([c + (x - rr) * r, c + (y - rr) * r, c + (x + rr) * r, c + (y + rr) * r], fill=(40, 30, 35))
    d.ellipse([c - r * 0.55, c - r * 0.95, c + r * 0.55, c - r * 0.1], fill=(45, 35, 45))
    for sx in (-1, 1):  # antennae
        d.line([c + sx * r * 0.2, c - r * 0.85, c + sx * r * 0.45, c - r * 1.2], fill=(40, 30, 35), width=int(r * 0.06))
        d.ellipse([c + sx * r * 0.45 - r * 0.08, c - r * 1.28, c + sx * r * 0.45 + r * 0.08, c - r * 1.12], fill=(40, 30, 35))
    gloss(im, [c + r * 0.15, c - r * 0.35, c + r * 0.55, c - r * 0.05], 110)
    d = ImageDraw.Draw(im)
    fc, fr = c, c - r * 0.55
    for dx in (-0.2, 0.2):
        d.ellipse([fc + (dx - 0.1) * r, fr - 0.13 * r, fc + (dx + 0.1) * r, fr + 0.11 * r], fill=(255, 255, 255))
        d.ellipse([fc + (dx - 0.05) * r, fr - 0.06 * r, fc + (dx + 0.05) * r, fr + 0.08 * r], fill=(40, 30, 35))
    d.arc([fc - r * 0.14, fr + r * 0.02, fc + r * 0.14, fr + r * 0.22], 20, 160, fill=(255, 255, 255), width=max(3, int(r * 0.05)))
    return im

def make_truck(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    L, T, R, B = c - r * 1.15, c - r * 0.35, c + r * 1.15, c + r * 0.55
    d.rounded_rectangle([L, T + r * 0.06, R, B + r * 0.06], radius=r * 0.12, fill=(180, 25, 35))
    d.rounded_rectangle([L, T, R, B], radius=r * 0.12, fill=RED)
    d.rounded_rectangle([c + r * 0.35, c - r * 0.85, R, T + r * 0.1], radius=r * 0.15, fill=RED)  # cab
    d.rounded_rectangle([c + r * 0.5, c - r * 0.72, c + r * 1.02, T - r * 0.02], radius=r * 0.08, fill=(180, 225, 255))
    d.rectangle([L + r * 0.05, c + r * 0.12, R - r * 0.05, c + r * 0.22], fill=(255, 255, 255))
    # ladder
    d.rectangle([L + r * 0.1, T - r * 0.25, c + r * 0.25, T - r * 0.17], fill=(200, 205, 215))
    d.rectangle([L + r * 0.1, T - r * 0.08, c + r * 0.25, T], fill=(200, 205, 215))
    for k in range(8):
        x = L + r * 0.15 + k * r * 0.18
        d.rectangle([x, T - r * 0.25, x + r * 0.05, T], fill=(200, 205, 215))
    d.rounded_rectangle([c + r * 0.6, c - r * 1.0, c + r * 0.85, c - r * 0.85], radius=r * 0.05, fill=(80, 170, 255))
    for wx in (L + r * 0.45, R - r * 0.45):
        d.ellipse([wx - r * 0.3, B - r * 0.25, wx + r * 0.3, B + r * 0.35], fill=(45, 40, 55))
        d.ellipse([wx - r * 0.13, B - r * 0.08, wx + r * 0.13, B + r * 0.18], fill=(200, 205, 215))
    d.ellipse([R - r * 0.12, c + r * 0.3, R + r * 0.04, c + r * 0.45], fill=(255, 230, 120))
    gloss(im, [L + r * 0.1, T + r * 0.05, L + r * 0.8, T + r * 0.15], 90)
    d = ImageDraw.Draw(im); face(d, c - r * 0.3, c - r * 0.1, r * 0.55)
    return im

def make_tomato(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse([c - r, c - r * 0.8, c + r, c + r * 0.9], fill=(195, 30, 40))
    d.ellipse([c - r * 0.95, c - r * 0.8, c + r * 0.95, c + r * 0.82], fill=(235, 60, 50))
    d.polygon(star_poly(c, c - r * 0.75, r * 0.38, inner=0.35), fill=(80, 165, 75))
    d.line([c, c - r * 0.8, c + r * 0.05, c - r * 1.05], fill=(80, 150, 70), width=int(r * 0.09))
    gloss(im, [c - r * 0.7, c - r * 0.5, c - r * 0.35, c - r * 0.15])
    d = ImageDraw.Draw(im); face(d, c, c + r * 0.05, r * 0.85)
    return im

def make_ball(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse([c - r, c - r, c + r, c + r], fill=(50, 110, 220))
    d.ellipse([c - r * 0.95, c - r * 0.97, c + r * 0.95, c + r * 0.9], fill=(70, 140, 245))
    d.arc([c - r * 1.6, c - r * 0.4, c + r * 1.6, c + r * 2.2], 225, 315, fill=(255, 255, 255), width=int(r * 0.14))
    gloss(im, [c - r * 0.65, c - r * 0.7, c - r * 0.25, c - r * 0.35])
    d = ImageDraw.Draw(im); face(d, c, c + r * 0.2, r * 0.75)
    return im

def make_banana(r):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    outer, inner = [], []
    for i in range(41):
        a = math.radians(200 + i * 140 / 40)
        th = math.sin(i / 40 * math.pi)
        outer.append((c + math.cos(a) * r * 1.05, c - r * 0.55 - math.sin(a) * r * 1.05))
        inner.append((c + math.cos(a) * r * (1.05 - 0.55 * th - 0.04), c - r * 0.55 - math.sin(a) * r * (1.05 - 0.55 * th - 0.04)))
    d.polygon(outer + inner[::-1], fill=(255, 215, 60), outline=(215, 160, 30), width=4)
    d.ellipse([outer[0][0] - r * 0.07, outer[0][1] - r * 0.07, outer[0][0] + r * 0.07, outer[0][1] + r * 0.07], fill=(110, 80, 40))
    d.ellipse([outer[-1][0] - r * 0.07, outer[-1][1] - r * 0.12, outer[-1][0] + r * 0.07, outer[-1][1] + r * 0.02], fill=(110, 80, 40))
    face(d, c, c + r * 0.28, r * 0.5)
    return im

R_BIG = 190
OBJS = [make_apple(R_BIG), make_strawberry(R_BIG), make_ladybug(R_BIG), make_truck(R_BIG)]
QUIZ_OBJS = [make_ball(105), make_tomato(105), make_banana(105)]
TW = {m: make_twinkle(100, m) for m in (False, True)}

# ---------- background ----------
def make_bg():
    g = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([255, 236, 232]), np.array([255, 214, 214])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr, W, axis=1).reshape(H, W, 3)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    for row in range(0, 20):
        for col in range(0, 10):
            x = col * 130 + (65 if row % 2 else 0); y = 460 + row * 70
            if y > 1240: continue
            d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=(255, 196, 200))
    # floor
    d.rectangle([0, 1250, W, H], fill=(240, 205, 170))
    for k in range(0, W, 160):
        d.line([k, 1250, k - 120, H], fill=(225, 185, 150), width=4)
    d.rectangle([0, 1240, W, 1256], fill=(205, 150, 130))
    # red shelf at the top
    d.rounded_rectangle([60, 60, 930, 420], radius=40, fill=(255, 250, 245), outline=(240, 170, 170), width=6)
    d.rounded_rectangle([90, 350, 900, 378], radius=12, fill=(200, 140, 110))
    return bg

BG = make_bg()
SHELF_X = [215, 395, 575, 755]; SHELF_Y = 270

def rug(im, cx, cy, t, strength=1.0):
    g = Image.new("RGBA", (700, 360), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    p = 1 + 0.03 * math.sin(t * 3)
    gd.ellipse([350 - 320 * p, 180 - 130 * p, 350 + 320 * p, 180 + 130 * p], fill=(255, 120, 130, int(110 * strength)))
    gd.ellipse([350 - 260 * p, 180 - 100 * p, 350 + 260 * p, 180 + 100 * p], fill=(255, 170, 175, int(160 * strength)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)), (int(cx - 350), int(cy - 180)))

def splash(d, cx, cy, s, a):
    """A soft red paint splash badge that says RED!"""
    if s <= 0.02: return
    rnd = random.Random(9)
    pts = []
    for i in range(24):
        ang = i / 24 * 2 * math.pi
        rr = (95 if i % 2 == 0 else 78) * s
        pts.append((cx + math.cos(ang) * rr * 1.25, cy + math.sin(ang) * rr))
    d.polygon(pts, fill=(226, 45, 55, a))
    for k in range(5):
        ang = rnd.uniform(0, 2 * math.pi); dist = rnd.uniform(120, 150) * s; rr = rnd.uniform(8, 16) * s
        x, y = cx + math.cos(ang) * dist * 1.2, cy + math.sin(ang) * dist * 0.85
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(226, 45, 55, a))
    f = font(64 * s); w = d.textlength("RED!", font=f)
    d.text((cx - w / 2, cy - 44 * s), "RED!", font=f, fill=(255, 255, 255, a))

def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, inner=0.35), fill=(255, 240, 150, a))

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
    top = 1420 - bh / 2
    d.rounded_rectangle([60, top, 930, top + bh], radius=42, fill=(255, 255, 255, 235), outline=RED, width=6)
    for i, ln in enumerate(lines):
        # colour the word RED / red in red
        f = font(sz); total = d.textlength(ln, font=f); x = 495 - total / 2; y = top + 26 + i * lh
        for wi, word in enumerate(ln.split(" ")):
            col = RED if word.strip("!.,?").lower() == "red" else INK
            d.text((x, y), word, font=f, fill=col)
            x += d.textlength(word + " ", font=f)
    if k < 1: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * k)))
    im.alpha_composite(layer)

def draw_twinkle(im, t, x, y, s=1.0):
    tk = talking(t)
    mouth = tk and int(t * 7) % 2 == 0
    bob = math.sin(t * 2.5) * 10 + (abs(math.sin(t * 9)) * -14 if tk else 0)
    paste(im, TW[mouth], x, y + bob, s, math.sin(t * 1.8) * 6)

def shelf(im, n_full, t, wave=False):
    for i in range(n_full):
        rot = math.sin(t * 5 + i) * 10 if wave else math.sin(t * 1.5 + i) * 3
        bob = math.sin(t * 5 + i * 1.3) * 12 if wave else 0
        paste(im, OBJS[i], SHELF_X[i], SHELF_Y + bob, 0.29, rot)

# ---------- frame ----------
def frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    text_c(d, "Red Shelf", 495, 82, 60, RED, stroke=(255, 255, 255), sw=6)
    CX, CY = 495, 830
    if t < INTRO:
        shelf(im, 0, t)
        rug(im, CX, 1160, t)
        s = pop((t - 0.2) / 0.8)
        draw_twinkle(im, t, CX, 760, 1.6 * s)
        if t > 1.2:
            ps = pop((t - 1.2) / 0.6); f = font(150 * ps)
            if ps > 0.05:
                w = d.textlength("RED", font=f)
                d.text((CX - w / 2, 1010 + (1 - ps) * 60), "RED", font=f, fill=RED, stroke_width=10, stroke_fill=(255, 255, 255))
        for k in range(6):
            a = (math.sin(t * 4 + k * 1.7) + 1) / 2
            sparkle(d, 180 + k * 130, 520 + (k % 2) * 60, 14 + 10 * a, int(120 + 120 * a))
        draw_caption(im, t)
    elif t < T_QUIZ:
        i = int((t - INTRO) // OBJ); lt = t - OBJ_T[i]
        shelf(im, i, t)
        rug(im, CX, 1130, t)
        fly = ease((lt - 5.0) / 0.9)
        if fly <= 0:
            s = pop(lt / 0.7); bob = math.sin(t * 3) * 10
            paste(im, OBJS[i], CX, CY + bob, s, math.sin(t * 2) * 3)
        else:
            x = CX + (SHELF_X[i] - CX) * fly; y = CY + (SHELF_Y - CY) * fly - math.sin(fly * math.pi) * 150
            paste(im, OBJS[i], x, y, 1 - 0.71 * fly, fly * 360)
        if 1.0 < lt < 5.0:
            ns = pop((lt - 1.0) / 0.5)
            text_c(d, NAMES[i], CX, 1100 - (1 - ns) * 20, 92 * max(ns, 0.05), RED, stroke=(255, 255, 255), sw=9)
        if 2.0 < lt < 5.0:
            ss = pop((lt - 2.0) / 0.5); a = int(255 * ease((5.0 - lt) / 0.4))
            splash(d, 790, 560, ss * 0.9, a)
        if lt > 5.0 and fly < 1:
            for k in range(5):
                sparkle(d, CX + (SHELF_X[i] - CX) * fly + math.cos(k * 1.3) * 60, CY + (SHELF_Y - CY) * fly + math.sin(k * 1.9) * 60, 14, 220)
        draw_twinkle(im, t, 150, 560, 0.95)
        draw_caption(im, t)
    elif t < T_OUT:
        lt = t - T_QUIZ
        shelf(im, NOBJ, t)
        text_c(d, "Which one is red?", CX, 500, 74, INK, stroke=(255, 255, 255), sw=8)
        xs = [200, 495, 790]
        reveal = lt - 5.0
        for j, sp in enumerate(QUIZ_OBJS):
            s = pop((lt - 0.4 - j * 0.35) / 0.6)
            y = 860 + math.sin(t * 3 + j) * 10
            if reveal > 0 and j == 1:
                g = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
                pr = 130 + 12 * math.sin(t * 6)
                ImageDraw.Draw(g).ellipse([210 - pr, 210 - pr, 210 + pr, 210 + pr], fill=(255, 90, 100, int(170 * ease(reveal / 0.4))))
                im.alpha_composite(g.filter(ImageFilter.GaussianBlur(18)), (xs[j] - 210, int(y) - 210))
                s *= 1 + 0.18 * ease(reveal / 0.5)
            alpha = 1.0 if (reveal <= 0 or j == 1) else 1 - 0.6 * ease(reveal / 0.5)
            paste(im, sp, xs[j], y, s, alpha=alpha)
        d = ImageDraw.Draw(im)
        if 1.8 < lt < 5.0:  # thinking dots
            for k in range(3):
                a = int(255 * ((math.sin(t * 6 - k) + 1) / 2))
                d.ellipse([CX - 60 + k * 50 - 12, 1080 - 12, CX - 60 + k * 50 + 12, 1080 + 12], fill=(226, 45, 55, a))
        if reveal > 0:
            text_c(d, "tomato", xs[1], 1090, 88 * pop(reveal / 0.5) + 1, RED, stroke=(255, 255, 255), sw=9)
            for k in range(6):
                ang = k / 6 * 2 * math.pi + t
                sparkle(d, xs[1] + math.cos(ang) * 175, 860 + math.sin(ang) * 175, 16, 230)
        draw_twinkle(im, t, 150, 1180, 0.8)
        draw_caption(im, t)
    else:
        lt = t - T_OUT
        shelf(im, NOBJ, t, wave=True)
        paste(im, QUIZ_OBJS[1], 760, 1000 + math.sin(t * 5) * 12, 0.8 * pop(lt / 0.6), math.sin(t * 5) * 8)
        draw_twinkle(im, t, 330, 940, 1.3)
        if lt > 0.8:
            ps = pop((lt - 0.8) / 0.6)
            text_c(d, "Red is great!", CX, 590, 104 * max(ps, 0.05), RED, stroke=(255, 255, 255), sw=10)
        if lt > 3.2:
            text_c(d, "Subscribe for more!", CX, 1150, 62, INK, stroke=(255, 255, 255), sw=7)
        for k in range(8):
            a = (math.sin(t * 4 + k * 1.1) + 1) / 2
            sparkle(d, 120 + k * 105, 500 + (k % 3) * 25, 12 + 10 * a, int(120 + 120 * a))
        draw_caption(im, t)
    return im.convert("RGB")

if __name__ == "__main__":
    import sys
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

    # ---------- audio: soft original marimba waltz in G major ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    def mar(freq, dur, vol=0.2, decay=7):
        tt = np.arange(int(dur * SR)) / SR
        w = np.sin(2 * np.pi * freq * tt) + 0.25 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-30 * tt)
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 300)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig)); audio[i:j] += sig[:j - i]
    G = {"G3": 196.0, "B3": 246.94, "D4": 293.66, "E4": 329.63, "G4": 392.0, "A4": 440.0, "B4": 493.88,
         "C5": 523.25, "D5": 587.33, "E5": 659.25, "C4": 261.63, "A3": 220.0, "F#4": 369.99}
    chords = [["G3", "B3", "D4"], ["C4", "E4", "G4"], ["A3", "C4", "E4"], ["D4", "F#4", "A4"]]
    melody = ["B4", "D5", "B4", "A4", "G4", "A4", "C5", "E5", "C5", "B4", "A4", "G4",
              "A4", "C5", "E5", "D5", "C5", "A4", "F#4", "A4", "D5", "B4", "A4", "G4"]
    beat = 0.42; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 3) % 4; ch = chords[bar]
        add(mar(G[ch[k % 3]], 0.6, 0.045, 6), k * beat)
        add(mar(G[melody[k % 24]], 0.8, 0.05, 5), k * beat + 0.01)
        if k % 3 == 0: add(mar(G[ch[0]] / 2, 1.2, 0.07, 2.5), k * beat)
        k += 1
    for i in range(NOBJ):
        add(mar(784, 0.5, 0.16, 8), OBJ_T[i] + 0.05); add(mar(1046.5, 0.6, 0.16, 8), OBJ_T[i] + 0.18)
        add(mar(659.25, 0.4, 0.12, 9), OBJ_T[i] + 2.0)
        for j, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
            add(mar(f, 0.3, 0.1, 10), OBJ_T[i] + 5.0 + j * 0.12)
    for j, f in enumerate([587.33, 783.99, 987.77, 1174.66]):
        add(mar(f, 0.8, 0.14, 4), T_QUIZ + 5.0 + j * 0.13)
    for j, f in enumerate([392, 493.88, 587.33, 783.99, 987.77]):
        add(mar(f, 1.2, 0.14, 3), T_OUT + 0.1 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
