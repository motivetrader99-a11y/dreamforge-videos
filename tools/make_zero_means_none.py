"""Dreamforge Kids — Zero means none.
Round 1: a lily pond at soft sunrise; three frogs sit on lily pads and hop away one by one
into the far water (little splash rings). A floating number bubble counts 3, 2, 1, 0.
Round 2: a flower meadow; two butterflies flutter off their flowers, 2, 1, 0.
Each time the empty pads / flowers get dotted "nothing here" rings and the bubble says
"none!". Outro: a big empty circle is traced — zero looks like an empty circle — and the
frogs and butterflies come back to wave bye. Captions sit in a panel at the TOP of the
frame with Twinkle the star narrating. Original art & music (soft kalimba waltz, F major)."""
import math, random, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/zero_means_none.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (60, 50, 90)
random.seed(1010)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, R1LEN, R2LEN, OUTRO = 5.0, 13.0, 11.0, 8.0
R1 = INTRO
R2 = R1 + R1LEN
T_OUT = R2 + R2LEN
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

FROG_IN, FROG_GAP = 0.3, 0.3
HOP_T = [3.6, 5.6, 7.6]; HOP_D = 1.0          # frog hop start (round-local)
FLY_T = [3.8, 5.0]; FLY_D = 1.8               # butterfly departures (round-local)

LINES = [
    (0.3, INTRO - 0.2, "Hi! I'm Twinkle! Let's learn about zero!"),
    (R1 + 0.2, R1 + 3.4, "Three frogs on the lily pads."),
    (R1 + 3.5, R1 + 8.6, "Hop! Hop! Hop! Away they go!"),
    (R1 + 8.8, R1 + R1LEN - 0.15, "Zero frogs! Zero means none!"),
    (R2 + 0.2, R2 + 3.6, "Two butterflies on the flowers."),
    (R2 + 3.7, R2 + 6.7, "Flutter, flutter... they fly away!"),
    (R2 + 6.9, R2 + R2LEN - 0.15, "Zero butterflies! None left!"),
    (T_OUT + 0.3, TOTAL - 0.5, "Zero looks like an empty circle. Bye-bye!"),
]
TALK = [(a, a + min(b - a - 0.2, len(txt.split()) * 0.42 + 0.6)) for a, b, txt in LINES]
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
        sp = sp.copy(); a = sp.getchannel("A").point(lambda v: int(v * alpha)); sp.putalpha(a)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def text_c(d, txt, cx, y, sz, fill, stroke=INK, sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def vgrad(w, h, top, bot):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = np.zeros((h, w, 4), np.uint8)
    arr[..., :3] = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    arr[..., 3] = 255
    return Image.fromarray(arr, "RGBA")

# ---------- characters ----------
def make_twinkle(r, mouth_open):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c = s / 2
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(c, c, r * 1.08), fill=(255, 225, 90, 130))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15))); d = ImageDraw.Draw(im)
    d.polygon(star_poly(c, c + r * 0.05, r), fill=(225, 165, 30))
    d.polygon(star_poly(c, c, r), fill=(255, 210, 60))
    e = r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([c + dx - e, c - e * 1.4, c + dx + e, c + e * 1.2], fill=(70, 40, 60))
        d.ellipse([c + dx - e * 0.5, c - e * 1.1, c + dx + e * 0.1, c - e * 0.4], fill=(255, 255, 255))
    if mouth_open:
        d.ellipse([c - r * 0.13, c + r * 0.12, c + r * 0.13, c + r * 0.34], fill=(150, 50, 60))
        d.ellipse([c - r * 0.07, c + r * 0.24, c + r * 0.07, c + r * 0.33], fill=(255, 130, 140))
    else:
        d.arc([c - r * 0.16, c + r * 0.05, c + r * 0.16, c + r * 0.28], 20, 160, fill=(70, 40, 60), width=max(3, int(r * 0.06)))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([c + dx - r * 0.1, c + r * 0.1, c + dx + r * 0.1, c + r * 0.22], fill=(255, 130, 150, 150))
    return im

def make_frog(r, body, belly):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    dark = tuple(max(0, v - 45) for v in body)
    # back feet
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.95 - r * 0.35, c + r * 0.55, c + sx * r * 0.95 + r * 0.35, c + r * 0.85], fill=dark)
    d.ellipse([c - r, c - r * 0.55, c + r, c + r * 0.8], fill=body)
    d.ellipse([c - r * 0.6, c - r * 0.05, c + r * 0.6, c + r * 0.78], fill=belly)
    # eyes on top
    for sx in (-1, 1):
        ex = c + sx * r * 0.48; ey = c - r * 0.62
        d.ellipse([ex - r * 0.38, ey - r * 0.38, ex + r * 0.38, ey + r * 0.38], fill=body)
        d.ellipse([ex - r * 0.27, ey - r * 0.27, ex + r * 0.27, ey + r * 0.27], fill=(255, 255, 255))
        d.ellipse([ex - r * 0.17, ey - r * 0.2, ex + r * 0.15, ey + r * 0.2], fill=(45, 40, 60))
        d.ellipse([ex - r * 0.1, ey - r * 0.15, ex, ey - r * 0.04], fill=(255, 255, 255))
    d.arc([c - r * 0.42, c - r * 0.35, c + r * 0.42, c + r * 0.12], 25, 155, fill=(60, 70, 50), width=max(3, int(r * 0.08)))
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.62 - r * 0.14, c - r * 0.18, c + sx * r * 0.62 + r * 0.14, c - r * 0.02], fill=(255, 150, 160, 190))
    # front feet
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.35 - r * 0.2, c + r * 0.66, c + sx * r * 0.35 + r * 0.2, c + r * 0.86], fill=dark)
    return im

def make_butterfly(r, wing, spot, flap):
    """flap in 0..1 : 1 = wings fully open."""
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c = s / 2
    wl = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(wl)
    for sx in (-1, 1):
        d.ellipse([c + sx * r * 0.05 - (r * 0.95 if sx < 0 else 0), c - r * 0.85, c + sx * r * 0.05 + (r * 0.95 if sx > 0 else 0), c + r * 0.15], fill=wing)
        d.ellipse([c + sx * r * 0.08 - (r * 0.7 if sx < 0 else 0), c - r * 0.05, c + sx * r * 0.08 + (r * 0.7 if sx > 0 else 0), c + r * 0.72], fill=wing)
        d.ellipse([c + sx * r * 0.52 - r * 0.18, c - r * 0.55, c + sx * r * 0.52 + r * 0.18, c - r * 0.2], fill=spot)
        d.ellipse([c + sx * r * 0.42 - r * 0.12, c + r * 0.2, c + sx * r * 0.42 + r * 0.12, c + r * 0.44], fill=(255, 255, 255, 200))
    sc = 0.25 + 0.75 * flap
    ww = max(2, int(s * sc))
    wl = wl.resize((ww, s), Image.BILINEAR)
    im.alpha_composite(wl, (int(c - ww / 2), 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([c - r * 0.12, c - r * 0.45, c + r * 0.12, c + r * 0.6], radius=int(r * 0.12), fill=(110, 80, 120))
    d.ellipse([c - r * 0.22, c - r * 0.78, c + r * 0.22, c - r * 0.36], fill=(130, 95, 140))
    for sx in (-1, 1):
        d.line([c + sx * r * 0.08, c - r * 0.72, c + sx * r * 0.3, c - r * 1.1], fill=(110, 80, 120), width=max(2, int(r * 0.05)))
        d.ellipse([c + sx * r * 0.3 - r * 0.07, c - r * 1.17, c + sx * r * 0.3 + r * 0.07, c - r * 1.03], fill=(110, 80, 120))
        d.ellipse([c + sx * r * 0.09 - r * 0.045, c - r * 0.62, c + sx * r * 0.09 + r * 0.045, c - r * 0.53], fill=(255, 255, 255))
    d.arc([c - r * 0.08, c - r * 0.58, c + r * 0.08, c - r * 0.45], 20, 160, fill=(255, 255, 255), width=max(2, int(r * 0.03)))
    return im

# ---------- props ----------
def make_pad(r, lotus=False):
    s = int(r * 2.4); im = Image.new("RGBA", (s, int(s * 0.62)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c, cy = s / 2, s * 0.31
    d.ellipse([c - r, cy - r * 0.4 + 8, c + r, cy + r * 0.4 + 8], fill=(70, 140, 110, 130))
    d.ellipse([c - r, cy - r * 0.4, c + r, cy + r * 0.4], fill=(120, 195, 120))
    d.pieslice([c - r, cy - r * 0.4, c + r, cy + r * 0.4], 60, 95, fill=(0, 0, 0, 0))
    for a in range(0, 360, 45):
        if 55 < a < 100: continue
        d.line([c, cy, c + math.cos(math.radians(a)) * r * 0.85, cy + math.sin(math.radians(a)) * r * 0.34], fill=(150, 215, 140), width=3)
    if lotus:
        lx, ly = c - r * 0.55, cy - r * 0.05
        for k, (dx, h) in enumerate([(-18, 28), (18, 28), (0, 38)]):
            d.ellipse([lx + dx - 13, ly - h, lx + dx + 13, ly + 6], fill=(255, 180, 205) if k < 2 else (255, 205, 220))
    # paste-safe: recompose with transparent notch
    return im

def make_flower(petal, center, h):
    s = 260; im = Image.new("RGBA", (s, h + 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2; fy = 120
    d.line([c, fy, c + 8, fy + h], fill=(95, 165, 95), width=14)
    d.ellipse([c + 8, fy + h * 0.45, c + 80, fy + h * 0.45 + 34], fill=(120, 190, 110))
    d.ellipse([c - 70, fy + h * 0.65, c + 2, fy + h * 0.65 + 34], fill=(120, 190, 110))
    for k in range(6):
        a = k * math.pi / 3
        x, y = c + math.cos(a) * 58, fy + math.sin(a) * 58
        d.ellipse([x - 44, y - 44, x + 44, y + 44], fill=petal)
    d.ellipse([c - 44, fy - 44, c + 44, fy + 44], fill=center)
    d.ellipse([c - 22, fy - 28, c - 4, fy - 10], fill=(255, 255, 255, 150))
    return im, fy

def cloud(d, x, y, sc, col=(255, 255, 255)):
    for dx, dy, rr in [(-60, 10, 42), (-10, -12, 58), (50, 8, 44), (0, 22, 40)]:
        d.ellipse([x + (dx - rr) * sc, y + (dy - rr) * sc, x + (dx + rr) * sc, y + (dy + rr) * sc], fill=col)

def caption_panel(d):
    d.rounded_rectangle([40, 84, 930, 340], radius=46, fill=(255, 252, 246), outline=(175, 160, 220), width=8)

def pond_bg():
    bg = vgrad(W, H, (255, 214, 196), (205, 225, 255)); d = ImageDraw.Draw(bg)
    d.ellipse([620, 470, 800, 650], fill=(255, 238, 170))
    cloud(d, 720, 760, 0.9); cloud(d, 560, 460, 0.6, (255, 246, 240))
    d.ellipse([-200, 830, 620, 1120], fill=(165, 210, 160)); d.ellipse([380, 850, 1300, 1140], fill=(150, 200, 150))
    d.rectangle([0, 960, W, H], fill=(140, 195, 135))
    pond = vgrad(1000, 560, (140, 200, 235), (95, 165, 215))
    m = Image.new("L", (1000, 560), 0); ImageDraw.Draw(m).ellipse([0, 0, 999, 559], fill=255)
    bg.paste(pond, (40, 990), m); d = ImageDraw.Draw(bg)
    d.ellipse([40, 990, 1039, 1549], outline=(120, 175, 120), width=10)
    for (x, y, w) in [(200, 1330, 120), (620, 1400, 150), (420, 1060, 90), (760, 1100, 80)]:
        d.arc([x - w, y - 10, x + w, y + 10], 200, 340, fill=(190, 225, 245), width=4)
    # reeds / cattails on the edges
    for x0, sgn in [(60, 1), (990, -1)]:
        for k in range(4):
            x = x0 + sgn * k * 26; top = 900 + (k % 2) * 50
            d.line([x, 1150, x + sgn * 10, top], fill=(95, 150, 90), width=8)
            if k % 2 == 0:
                d.rounded_rectangle([x + sgn * 10 - 11, top - 5, x + sgn * 10 + 11, top + 70], radius=10, fill=(160, 110, 80))
    for _ in range(40):
        x, y = random.randint(0, W), random.randint(1560, H)
        d.line([x, y, x - 6, y - 22], fill=(120, 180, 115), width=4)
    caption_panel(d)
    return bg

def meadow_bg():
    bg = vgrad(W, H, (190, 225, 255), (235, 245, 255)); d = ImageDraw.Draw(bg)
    cloud(d, 700, 520, 1.0); cloud(d, 520, 800, 0.7); cloud(d, 860, 700, 0.55)
    d.ellipse([-300, 880, 700, 1300], fill=(180, 225, 150)); d.ellipse([300, 860, 1400, 1300], fill=(165, 215, 140))
    d.rectangle([0, 1080, W, H], fill=(150, 205, 125))
    # little wooden fence
    for x in range(20, W, 110):
        d.rounded_rectangle([x, 990, x + 26, 1110], radius=8, fill=(225, 190, 150))
    d.rectangle([0, 1020, W, 1036], fill=(215, 175, 135)); d.rectangle([0, 1066, W, 1082], fill=(215, 175, 135))
    for _ in range(90):
        x, y = random.randint(0, W), random.randint(1120, H)
        col = random.choice([(255, 255, 255), (255, 235, 130), (255, 200, 220)])
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col)
    for _ in range(50):
        x, y = random.randint(0, W), random.randint(1120, H)
        d.line([x, y, x + 5, y - 20], fill=(125, 185, 110), width=4)
    caption_panel(d)
    return bg

def outro_bg():
    bg = vgrad(W, H, (240, 225, 255), (255, 235, 225)); d = ImageDraw.Draw(bg)
    for _ in range(26):
        x, y = random.randint(40, 900), random.randint(380, 1550)
        d.polygon(star_poly(x, y, random.randint(8, 16), 0, 0.4), fill=(255, 255, 255, 200))
    d.ellipse([-100, 1480, 700, 1800], fill=(185, 225, 165)); d.ellipse([400, 1460, 1250, 1800], fill=(170, 215, 150))
    d.rectangle([0, 1640, W, H], fill=(170, 215, 150))
    caption_panel(d)
    return bg

BG_POND, BG_MEADOW, BG_OUT = pond_bg(), meadow_bg(), outro_bg()
TWK = [make_twinkle(80, False), make_twinkle(80, True)]
TWK_BIG = [make_twinkle(170, False), make_twinkle(170, True)]
FROGS = [make_frog(84, (125, 205, 110), (215, 240, 170)), make_frog(84, (110, 195, 160), (210, 245, 215)),
         make_frog(84, (165, 210, 95), (240, 245, 180))]
PAD, PAD_L = make_pad(140), make_pad(140, lotus=True)
PADS = [(210, 1215), (470, 1300), (730, 1210)]
BFLY_COL = [((200, 170, 255), (255, 200, 120)), ((255, 175, 150), (150, 205, 255))]
BF_FRAMES = [[make_butterfly(92, w, s, f / 5) for f in range(6)] for (w, s) in BFLY_COL]
FLOWERS = []
for (pc, cc, hh, x) in [((255, 170, 200), (255, 220, 110), 330, 270), ((255, 225, 120), (255, 160, 90), 380, 650)]:
    im, fy = make_flower(pc, cc, hh); FLOWERS.append((im, x, 1500 - hh, fy))

def bfly(k, t, scale=1.0):
    f = (math.sin(t * 16 + k * 2) + 1) / 2
    return BF_FRAMES[k][int(round(f * 5))]

# ---------- number bubble ----------
BUB_X, BUB_Y, BUB_R = 290, 610, 160
def draw_bubble(im, n, label, t, since_change, zero_since=None):
    d = ImageDraw.Draw(im)
    s = 1 + 0.18 * max(0, 1 - since_change / 0.35) * math.sin(min(1, since_change / 0.35) * math.pi)
    r = BUB_R * s
    if zero_since is not None:
        gl = Image.new("RGBA", (500, 500), (0, 0, 0, 0))
        pr = 1 + 0.06 * math.sin(t * 5)
        ImageDraw.Draw(gl).ellipse([250 - 200 * pr, 250 - 200 * pr, 250 + 200 * pr, 250 + 200 * pr], fill=(255, 240, 150, 150))
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(22)), (BUB_X - 250, BUB_Y - 250)); d = ImageDraw.Draw(im)
    d.ellipse([BUB_X - r, BUB_Y - r + 10, BUB_X + r, BUB_Y + r + 10], fill=(200, 185, 235))
    d.ellipse([BUB_X - r, BUB_Y - r, BUB_X + r, BUB_Y + r], fill=(255, 255, 255), outline=(175, 160, 220), width=10)
    d.ellipse([BUB_X - r * 0.62, BUB_Y - r * 0.8, BUB_X - r * 0.3, BUB_Y - r * 0.55], fill=(235, 230, 255))
    col = (240, 110, 130) if n == 0 else (110, 90, 200)
    f = font(210 * s); txt = str(n); w = d.textlength(txt, font=f)
    d.text((BUB_X - w / 2, BUB_Y - 150 * s), txt, font=f, fill=col)
    # label ribbon
    lab = "none!" if zero_since is not None else label
    lf = font(62); lw = d.textlength(lab, font=lf)
    d.rounded_rectangle([BUB_X - lw / 2 - 30, BUB_Y + BUB_R + 26, BUB_X + lw / 2 + 30, BUB_Y + BUB_R + 116], radius=40,
                        fill=(255, 225, 110) if zero_since is not None else (255, 250, 240), outline=(175, 160, 220), width=6)
    d.text((BUB_X - lw / 2, BUB_Y + BUB_R + 28), lab, font=lf, fill=INK)

def dotted_ring(d, x, y, rx, ry, a, t):
    n = 20
    for k in range(n):
        ang = k * 2 * math.pi / n + t * 0.8
        px, py = x + math.cos(ang) * rx, y + math.sin(ang) * ry
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(255, 255, 255, int(230 * a)))

def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, 0, 0.35), fill=(255, 250, 200, int(255 * a)))

# ---------- scenes ----------
FROG_LAND = [(330, 1045), (560, 1030), (800, 1060)]
def draw_round1(im, lt, t):
    for k, (px, py) in enumerate(PADS):
        paste(im, PAD_L if k == 1 else PAD, px, py + math.sin(t * 1.5 + k) * 3)
    d = ImageDraw.Draw(im)
    splashes = []
    count = 3
    for k in range(3):
        px, py = PADS[k]; hs = HOP_T[2 - k]  # right-most frog hops first
        st = FROG_IN + k * FROG_GAP
        if lt < st: continue
        if lt >= hs + HOP_D:
            count -= 1; splashes.append((FROG_LAND[k], lt - hs - HOP_D)); continue
        if lt >= hs:
            u = (lt - hs) / HOP_D
            lx, ly = FROG_LAND[k]
            x = px + (lx - px) * u; y = (py - 72) + (ly - (py - 55)) * u - math.sin(u * math.pi) * 330
            sc = 1 - 0.45 * u; al = 1 if u < 0.85 else (1 - u) / 0.15
            paste(im, FROGS[k], x, y, sc, -15 * math.sin(u * math.pi) * (1 if lx > px else -1), al)
            continue
        y = py - 72
        if hs - 0.5 <= lt < hs:  # crouch before hopping
            y += 8
        y += math.sin(t * 3 + k) * 3
        paste(im, FROGS[k], px, y, pop((lt - st) / 0.45))
    d = ImageDraw.Draw(im)
    for (sx, sy), age in splashes:
        if age < 1.6:
            for j in range(3):
                rr = (age - j * 0.2) * 110
                if rr > 0:
                    a = max(0, 1 - age / 1.6)
                    d.ellipse([sx - rr, sy - rr * 0.3, sx + rr, sy + rr * 0.3], outline=(255, 255, 255, int(220 * a)), width=5)
            if age < 0.5:
                for j in range(5):
                    ang = math.pi + j * math.pi / 4
                    rr = 30 + age * 120
                    dx, dy = sx + math.cos(ang) * rr, sy - math.sin(j * math.pi / 4) * rr * 0.9 + age * age * 300
                    d.ellipse([dx - 7, dy - 9, dx + 7, dy + 9], fill=(225, 245, 255))
    zero_at = HOP_T[0] + HOP_D  # last departure (frog 0) lands
    last_change = max([0] + [h + HOP_D for h in HOP_T if lt >= h + HOP_D])
    zs = lt - zero_at if count == 0 else None
    if zs is not None:
        a = min(1, zs / 0.4)
        for px, py in PADS:
            dotted_ring(d, px, py, 150, 62, a, t)
    if lt > 0.2:
        draw_bubble(im, count, "frogs", t, lt - last_change if last_change else lt - 0.2, zs)
        if zs is not None:
            d = ImageDraw.Draw(im)
            for k in range(8):
                ang = k * math.pi / 4 + t
                rr = 190 + min(zs, 1) * 40
                if math.sin(ang) < 0.55: sparkle(d, BUB_X + math.cos(ang) * rr, BUB_Y + math.sin(ang) * rr, 14, 0.9)

def draw_round2(im, lt, t):
    for k, (fim, x, top, fy) in enumerate(FLOWERS):
        sw = math.sin(t * 1.4 + k) * 2
        paste(im, fim, x, top + fim.height / 2 - fy + 0, 1.0, sw)
    d = ImageDraw.Draw(im)
    count = 2
    for k in range(2):
        fim, x, top, fy = FLOWERS[k]
        hx, hy = x, top - 60
        st = 0.3 + k * 0.35; ft = FLY_T[k]
        if lt < st: continue
        if lt >= ft + FLY_D: count -= 1; continue
        if lt >= ft:
            u = (lt - ft) / FLY_D
            tx, ty = (x - 520, 820) if k == 0 else (x + 520, 700)
            bx = hx + (tx - hx) * ease(u) + math.sin(u * 12) * 40
            by = hy + (ty - hy) * u - math.sin(u * math.pi) * 60
            al = 1 if u < 0.7 else (1 - u) / 0.3
            paste(im, bfly(k, t * 1.6), bx, by, 1 - 0.3 * u, math.sin(u * 10) * 12, al)
            continue
        f = 0.78 + 0.22 * math.sin(t * 5 + k) if ft - lt > 0.8 else (math.sin(t * 16) + 1) / 2
        paste(im, BF_FRAMES[k][int(round(f * 5))], hx, hy + math.sin(t * 2 + k) * 4, pop((lt - st) / 0.5))
    d = ImageDraw.Draw(im)
    zero_at = FLY_T[1] + FLY_D
    last_change = max([0] + [h + FLY_D for h in FLY_T if lt >= h + FLY_D])
    zs = lt - zero_at if count == 0 else None
    if zs is not None:
        a = min(1, zs / 0.4)
        for fim, x, top, fy in FLOWERS:
            dotted_ring(d, x, top - 30, 110, 105, a, t)
    if lt > 0.2:
        draw_bubble(im, count, "butterflies", t, lt - last_change if last_change else lt - 0.2, zs)
        if zs is not None:
            d = ImageDraw.Draw(im)
            for k in range(8):
                ang = k * math.pi / 4 - t
                if math.sin(ang) < 0.55: sparkle(d, BUB_X + math.cos(ang) * 210, BUB_Y + math.sin(ang) * 210, 14, 0.9)

CIRC_X, CIRC_Y, CIRC_R = 470, 900, 280
def draw_outro(im, lt, t):
    d = ImageDraw.Draw(im)
    prog = ease((lt - 0.4) / 1.8)
    if prog > 0:
        # soft shadow ring then rainbow-ish traced stroke
        cols = [(255, 150, 170), (255, 190, 120), (255, 225, 110), (150, 215, 140), (140, 190, 255), (190, 160, 255)]
        steps = int(180 * prog)
        for i in range(steps):
            a0 = -90 + i * 2
            col = cols[int(i / 180 * len(cols)) % len(cols)]
            d.arc([CIRC_X - CIRC_R, CIRC_Y - CIRC_R * 1.25, CIRC_X + CIRC_R, CIRC_Y + CIRC_R * 1.25], a0, a0 + 2.6, fill=col, width=46)
        if prog < 1:
            ang = math.radians(-90 + 360 * prog)
            px, py = CIRC_X + math.cos(ang) * CIRC_R, CIRC_Y + math.sin(ang) * CIRC_R * 1.25
            sparkle(d, px, py, 30, 1)
    if lt > 2.3:
        a = min(1, (lt - 2.3) / 0.4)
        f = font(50); txt = "nothing inside!"; w = d.textlength(txt, font=f)
        d.text((CIRC_X - w / 2, CIRC_Y - 40), txt, font=f, fill=(150, 130, 200, int(255 * a)))
        s = pop((lt - 2.3) / 0.5)
        if s > 0.05:
            text_c(d, "0 = none", CIRC_X, 1215 + (1 - s) * 40, 110 * s, (255, 235, 120), stroke=(120, 90, 180), sw=8)
    # friends come back to wave bye
    if lt > 3.4:
        for k, (x, y) in enumerate([(150, 1470), (470, 1490), (790, 1470)]):
            s = pop((lt - 3.4 - k * 0.25) / 0.5)
            paste(im, FROGS[k], x, y - abs(math.sin(t * 4 + k)) * 40, s)
        for k, (x, y) in enumerate([(160, 580), (790, 600)]):
            s = pop((lt - 4.2 - k * 0.3) / 0.5)
            paste(im, bfly(k, t), x + math.sin(t * 2 + k) * 20, y + math.cos(t * 2.5 + k) * 20, s)
        d = ImageDraw.Draw(im)
        if lt > 4.0:
            for k in range(10):
                ang = k * math.pi / 5 + t * 0.7
                sparkle(d, CIRC_X + math.cos(ang) * 330, CIRC_Y + math.sin(ang) * 380, 12 + 5 * math.sin(t * 5 + k), 0.9)

def wrap(d, txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw: cur = trial
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def draw_caption(im, d, t, show_twinkle=True):
    for a, b, txt in LINES:
        if a <= t < b:
            al = min(1, (t - a) / 0.25, (b - t) / 0.25)
            sz = 62; lines = wrap(d, txt, sz, 610)
            while len(lines) > 3: sz -= 4; lines = wrap(d, txt, sz, 610)
            lh = sz * 1.2; y0 = 212 - lh * len(lines) / 2 - 8
            for k, ln in enumerate(lines):
                f = font(sz); w = d.textlength(ln, font=f)
                d.text((375 - w / 2, y0 + k * lh), ln, font=f, fill=INK + (int(255 * al),))
            break
    if show_twinkle:
        tk = talking(t); mo = tk and int(t * 8) % 2 == 0
        bob = math.sin(t * 3) * 6 + (abs(math.sin(t * 11)) * -10 if tk else 0)
        paste(im, TWK[mo], 812, 212 + bob, 1.0, math.sin(t * 2) * 5)

def frame(t):
    if t < INTRO:
        im = BG_POND.copy(); d = ImageDraw.Draw(im)
        for k, (px, py) in enumerate(PADS):
            paste(im, PAD_L if k == 1 else PAD, px, py, pop((t - 1.2 - k * 0.2) / 0.5))
        mo = talking(t) and int(t * 8) % 2 == 0
        paste(im, TWK_BIG[mo], 470, 830 + math.sin(t * 3) * 14 - (abs(math.sin(t * 10)) * 12 if talking(t) else 0),
              pop(t / 0.8), math.sin(t * 2) * 6)
        d = ImageDraw.Draw(im)
        if t > 0.9:
            s = pop((t - 0.9) / 0.5)
            text_c(d, "ZERO", 470, 370 + (1 - s) * 30, 150 * max(s, 0.05), (255, 245, 250), stroke=(240, 110, 130), sw=10)
        draw_caption(im, d, t, show_twinkle=False)
    elif t < R2:
        im = BG_POND.copy(); draw_round1(im, t - R1, t)
        draw_caption(im, ImageDraw.Draw(im), t)
    elif t < T_OUT:
        im = BG_MEADOW.copy(); draw_round2(im, t - R2, t)
        draw_caption(im, ImageDraw.Draw(im), t)
    else:
        im = BG_OUT.copy(); draw_outro(im, t - T_OUT, t)
        draw_caption(im, ImageDraw.Draw(im), t)
    # soft crossfade between scenes
    for edge, col in [(R2, (235, 240, 255, 255)), (T_OUT, (245, 235, 255, 255))]:
        if abs(t - edge) < 0.25:
            k = abs(t - edge) / 0.25
            im = Image.blend(Image.new("RGBA", (W, H), col), im, k)
    if t < 0.4 or t > TOTAL - 0.6:
        k = min(t / 0.4, (TOTAL - t) / 0.6)
        im = Image.blend(Image.new("RGBA", (W, H), (255, 225, 215, 255)), im, max(0, min(1, k)))
    return im

if __name__ == "__main__":
    only = [float(x) for x in sys.argv[1:]]
    if only:
        for tt in only: frame(tt).convert("RGB").save(f"_preview_{tt:.1f}.png")
        sys.exit(0)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(frame(fi / FPS).convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()

    # ---------- audio: original soft kalimba waltz in F major (3/4) ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    def kal(freq, dur, vol=0.2, decay=6):
        tt = np.arange(int(dur * SR)) / SR
        w = np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 3.01 * tt) * np.exp(-12 * tt) \
            + 0.15 * np.sin(2 * np.pi * freq * 5.4 * tt) * np.exp(-25 * tt)
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 500)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N: audio[i:j] += sig[:j - i]
    NT = {"F2": 87.31, "C3": 130.81, "D3": 146.83, "Bb2": 116.54, "F3": 174.61, "A3": 220.0, "C4": 261.63,
          "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0, "Bb4": 466.16, "C5": 523.25}
    bass = ["F2", "D3", "Bb2", "C3"]
    chord = [["A3", "C4"], ["F3", "A3"], ["D4", "F4"], ["E4", "G4"]]
    mel = ["C5", "A4", "F4", "G4", "A4", None, "Bb4", "A4", "G4", "F4", None, None,
           "A4", "C5", "A4", "G4", "F4", "G4", "E4", "F4", "G4", "F4", None, None]
    beat = 0.45; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 3) % 4
        if k % 3 == 0: add(kal(NT[bass[bar]] * 2, 1.4, 0.08, 2.5), k * beat)
        else:
            for n in chord[bar]: add(kal(NT[n], 0.5, 0.025, 7), k * beat)
        m = mel[k % 24]
        if m: add(kal(NT[m], 0.9, 0.04, 4), k * beat)
        k += 1
    # sound effects
    for k in range(3): add(kal(784, 0.2, 0.06, 14), R1 + FROG_IN + k * FROG_GAP)
    for k, h in enumerate(HOP_T):
        tt = np.arange(int(0.3 * SR)) / SR; fr = 300 + 600 * tt / 0.3   # soft "boing"
        add(0.07 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-6 * tt), R1 + h)
        nz = np.random.RandomState(k).randn(int(0.5 * SR)); tt = np.arange(len(nz)) / SR
        nz = np.convolve(nz, np.ones(30) / 30, "same")                      # gentle "plip" splash
        add(0.12 * nz * np.exp(-9 * tt), R1 + h + HOP_D); add(kal(1046.5, 0.3, 0.05, 12), R1 + h + HOP_D)
    for j, f_ in enumerate([698.46, 880, 1046.5, 1396.9]): add(kal(f_, 1.0, 0.1, 3), R1 + HOP_T[0] + HOP_D + 0.1 + j * 0.12)
    for k, ft in enumerate(FLY_T):
        for j in range(6): add(kal(1396.9 * (1 + j * 0.12), 0.25, 0.035, 10), R2 + ft + j * 0.09)  # flutter chime
    for j, f_ in enumerate([698.46, 880, 1046.5, 1396.9]): add(kal(f_, 1.0, 0.1, 3), R2 + FLY_T[1] + FLY_D + 0.1 + j * 0.12)
    for j in range(9): add(kal(523.25 * 2 ** (j / 12 * 1.5), 0.3, 0.04, 8), T_OUT + 0.4 + j * 0.2)  # circle tracing
    for j, f_ in enumerate([523.25, 659.25, 783.99, 1046.5]): add(kal(f_, 1.3, 0.1, 2.5), T_OUT + 2.3 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
