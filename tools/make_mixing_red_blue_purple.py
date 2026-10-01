"""Dreamforge Kids - Mixing colors: red + blue = purple.
Twinkle narrates at a cosy art table at sunset. Two smiling paint buckets
(red + blue) pour into a glass jar, a spoon stirs a swirl until it turns purple,
then a paintbrush paints purple grapes, a plum and a butterfly on an easel,
followed by an equation recap. Original art and music.
"""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/mixing_red_blue_purple.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
CX = 465
RED, BLUE, PUR = np.array([235, 60, 75.]), np.array([55, 110, 235.]), np.array([150, 70, 205.])
REDt, BLUEt, PURt = tuple(int(v) for v in RED), tuple(int(v) for v in BLUE), tuple(int(v) for v in PUR)
INK = (55, 35, 75)
random.seed(23)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

LINES = [
    (0.8, 5.8, "Hi friends! I'm Twinkle. Let's make a new color!"),
    (6.4, 12.4, "Here is red paint. And here is blue paint."),
    (13.0, 20.0, "Pour them in the jar... and stir, stir, stir!"),
    (20.6, 24.8, "Wow! Red and blue make purple!"),
    (25.4, 34.4, "Let's paint purple grapes, a plum, and a butterfly!"),
    (35.0, 40.6, "Red plus blue makes purple. Great job!"),
]
TOTAL = 46.5
NFR = int(TOTAL * FPS)
S_BUCK, S_POUR, S_STIR, S_WOW, S_PAINT, S_RECAP, S_OUT = 6.2, 13.0, 16.4, 20.4, 25.2, 34.8, 41.0
TALK = [(a, a + min(b - a - 0.3, len(txt.split()) * 0.42 + 0.6)) for a, b, txt in LINES]

def talking(t): return any(a <= t < b for a, b in TALK)
def ease(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)
def dark(c, k=50): return tuple(max(0, int(v) - k) for v in c[:3])

def paste(canvas, sp, cx, cy, s=1.0, rot=0.0):
    if s <= 0.02: return
    if s != 1.0: sp = sp.resize((max(2, int(sp.width * s)), max(2, int(sp.height * s))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def text_c(d, txt, x, y, sz, fill, stroke=INK, sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((x - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

# ---------- Twinkle ----------
def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def make_twinkle(r, mouth_open):
    s = int(r * 2.7); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); c = s / 2
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(c, c, r * 1.08), fill=(255, 230, 120, 130))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(c, c + r * 0.05, r), fill=(225, 160, 30))
    d.polygon(star_poly(c, c, r), fill=(255, 210, 60))
    d.ellipse([c - r * 0.42, c - r * 0.55, c - r * 0.12, c - r * 0.32], fill=(255, 250, 210))
    e = r * 0.1; cy = c + r * 0.05
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([c + dx - e, cy - e * 1.35, c + dx + e, cy + e * 1.35], fill=INK)
        d.ellipse([c + dx - e * 0.5, cy - e * 1.05, c + dx + e * 0.15, cy - e * 0.3], fill=(255, 255, 255))
    if mouth_open:
        d.ellipse([c - r * 0.13, cy + r * 0.12, c + r * 0.13, cy + r * 0.34], fill=(150, 50, 70))
        d.ellipse([c - r * 0.07, cy + r * 0.24, c + r * 0.07, cy + r * 0.33], fill=(255, 130, 150))
    else:
        d.arc([c - r * 0.16, cy + r * 0.04, c + r * 0.16, cy + r * 0.28], 20, 160, fill=INK, width=max(3, int(r * 0.05)))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([c + dx - r * 0.1, cy + r * 0.1, c + dx + r * 0.1, cy + r * 0.22], fill=(255, 130, 150, 150))
    return im

TW = {(r, m): make_twinkle(r, m) for r in (95, 190) for m in (False, True)}

def draw_twinkle(im, t, x, y, r):
    tk = talking(t)
    mo = tk and math.sin(t * 2 * math.pi * 4.2) > -0.1
    bob = -abs(math.sin(t * 7.5)) * 14 if tk else math.sin(t * 2.2) * 6
    paste(im, TW[(r, mo)], x, y + bob, 1.0, math.sin(t * 1.7) * 5)

# ---------- background ----------
def background():
    g = np.linspace(0, 1, H)[:, None]
    top, mid = np.array([255, 205, 175.]), np.array([215, 190, 240.])
    arr = top * (1 - g) + mid * g
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # window with sunset and soft clouds (studio wall)
    d.rounded_rectangle([560, 230, 960, 560], radius=40, fill=(255, 235, 200), outline=(200, 150, 120), width=12)
    d.ellipse([700, 380, 830, 510], fill=(255, 190, 120))
    for cx, cy in ((640, 330), (850, 300)):
        for dx, rr in ((-40, 34), (0, 46), (40, 34)): d.ellipse([cx + dx - rr, cy - rr, cx + dx + rr, cy + rr], fill=(255, 250, 245))
    d.line([760, 240, 760, 550], fill=(200, 150, 120), width=10); d.line([570, 395, 950, 395], fill=(200, 150, 120), width=10)
    # bunting
    for i in range(9):
        x = 30 + i * 110; col = [REDt, BLUEt, PURt][i % 3]
        d.polygon([(x, 40), (x + 90, 40), (x + 45, 115)], fill=col + (200,))
    d.line([0, 40, W, 40], fill=(150, 110, 90), width=5)
    # table
    d.rectangle([0, 1250, W, H], fill=(225, 175, 130))
    d.rectangle([0, 1250, W, 1275], fill=(200, 145, 100))
    for y in (1340, 1450, 1580, 1720):
        d.line([0, y, W, y + 8], fill=(210, 160, 115), width=4)
    # paint splats on table edge (decor, low)
    for x, col in ((90, REDt), (980, BLUEt), (850, PURt)):
        d.ellipse([x - 40, 1600, x + 40, 1640], fill=col + (160,))
    return bg

BG = background()

# ---------- sprites ----------
def make_bucket(col):
    w, h = 250, 250; im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc([40, 0, 210, 140], 180, 360, fill=(120, 120, 140), width=10)
    d.polygon([(30, 70), (220, 70), (195, 240), (55, 240)], fill=(235, 238, 245), outline=(150, 150, 170))
    d.polygon([(30, 70), (220, 70), (214, 115), (36, 115)], fill=tuple(col))
    d.ellipse([28, 52, 222, 92], fill=dark(col, 30), outline=(150, 150, 170), width=4)
    d.ellipse([60, 60, 190, 84], fill=tuple(col))
    # drip
    d.ellipse([70, 110, 92, 150], fill=tuple(col))
    # face
    for ex in (100, 150):
        d.ellipse([ex - 11, 150, ex + 11, 178], fill=INK); d.ellipse([ex - 6, 153, ex + 1, 162], fill=(255, 255, 255))
    d.arc([108, 170, 142, 198], 20, 160, fill=INK, width=5)
    for ex in (80, 170): d.ellipse([ex - 13, 178, ex + 13, 190], fill=(255, 150, 160))
    return im

BUCKET_R, BUCKET_B = make_bucket(REDt), make_bucket(BLUEt)

JW, JH = 320, 380                 # jar size
JX, JY = CX - JW // 2, 860        # jar top-left
def jar_mask():
    m = Image.new("L", (JW, JH), 0); d = ImageDraw.Draw(m)
    d.rounded_rectangle([22, 60, JW - 22, JH - 14], radius=60, fill=255)
    return np.array(m) > 0
JMASK = jar_mask()
yy, xx = np.mgrid[0:JH, 0:JW].astype(float)
JCX, JCY = JW / 2, JH * 0.6

def jar_glass():
    im = Image.new("RGBA", (JW, JH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 52, JW - 14, JH - 6], radius=66, outline=(255, 255, 255, 230), width=12)
    d.rounded_rectangle([8, 20, JW - 8, 62], radius=18, fill=(255, 255, 255, 120), outline=(255, 255, 255, 230), width=6)
    d.line([52, 110, 52, 280], fill=(255, 255, 255, 170), width=14)
    return im
GLASS = jar_glass()

def jar_liquid(level, stir, mix):
    """level 0..1, stir angle progress, mix 0..1 -> RGBA image"""
    top = JH - 14 - level * (JH - 90)
    dx, dy = xx - JCX, yy - JCY
    r = np.hypot(dx, dy); th = np.arctan2(dy, dx)
    th2 = th + stir * np.clip(1 - r / 220, 0, 1) * 3.0
    xs = r * np.cos(th2)
    w = 1 / (1 + np.exp(-xs / 14))           # 0 red .. 1 blue
    col = RED[None, None, :] * (1 - w[..., None]) + BLUE[None, None, :] * w[..., None]
    col = col * (1 - mix) + PUR[None, None, :] * mix
    a = (JMASK & (yy >= top)).astype(np.uint8) * 255
    arr = np.dstack([np.clip(col, 0, 255).astype(np.uint8), a])
    im = Image.fromarray(arr, "RGBA")
    if level > 0.02:
        d = ImageDraw.Draw(im); wc = tuple(int(v) for v in (RED * 0.5 + BLUE * 0.5) * (1 - mix) + PUR * mix)
        d.line([40, top + 6, JW - 40, top + 6], fill=tuple(min(255, c + 50) for c in wc) + (200,), width=6)
    return im

def make_spoon():
    im = Image.new("RGBA", (80, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 0, 50, 330], radius=10, fill=(215, 160, 100), outline=(160, 110, 70), width=3)
    d.ellipse([10, 310, 70, 410], fill=(215, 160, 100), outline=(160, 110, 70), width=3)
    return im
SPOON = make_spoon()

# purple things
def make_grapes():
    im = Image.new("RGBA", (230, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([115, 20, 120, 60], fill=(120, 80, 40), width=10)
    d.ellipse([120, 18, 200, 60], fill=(90, 180, 80))
    rows = [(4, 85), (3, 135), (2, 182), (1, 225)]
    for n, y in rows:
        for i in range(n):
            x = 115 + (i - (n - 1) / 2) * 50
            d.ellipse([x - 28, y - 28, x + 28, y + 28], fill=dark(PURt, 20), outline=dark(PURt, 70), width=3)
            d.ellipse([x - 16, y - 18, x - 4, y - 6], fill=(220, 190, 250))
    return im

def make_plum():
    im = Image.new("RGBA", (230, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([30, 60, 200, 240], fill=PURt, outline=dark(PURt, 70), width=5)
    d.arc([95, 70, 140, 230], 270, 90, fill=dark(PURt, 40), width=5)
    d.ellipse([60, 95, 95, 140], fill=(215, 180, 250))
    d.line([115, 62, 108, 28], fill=(120, 80, 40), width=9)
    d.ellipse([112, 18, 180, 50], fill=(90, 180, 80))
    for ex in (90, 140): d.ellipse([ex - 9, 150, ex + 9, 172], fill=INK)
    d.arc([100, 168, 130, 192], 20, 160, fill=INK, width=5)
    return im

def make_butterfly():
    im = Image.new("RGBA", (230, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lc, dc = (175, 110, 230), dark(PURt, 30)
    d.ellipse([10, 40, 112, 150], fill=lc, outline=dc, width=5); d.ellipse([118, 40, 220, 150], fill=lc, outline=dc, width=5)
    d.ellipse([28, 135, 108, 225], fill=PURt, outline=dc, width=5); d.ellipse([122, 135, 202, 225], fill=PURt, outline=dc, width=5)
    for cx, cy in ((60, 95), (170, 95)): d.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], fill=(255, 220, 120))
    d.rounded_rectangle([104, 60, 126, 220], radius=11, fill=INK)
    d.line([110, 64, 85, 18], fill=INK, width=4); d.line([120, 64, 145, 18], fill=INK, width=4)
    d.ellipse([78, 10, 92, 24], fill=INK); d.ellipse([138, 10, 152, 24], fill=INK)
    return im

ITEMS = [(make_grapes(), "grapes"), (make_plum(), "plum"), (make_butterfly(), "butterfly")]

def make_brush():
    im = Image.new("RGBA", (70, 330), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([25, 0, 45, 220], radius=10, fill=(255, 200, 90), outline=(190, 130, 50), width=3)
    d.rectangle([20, 215, 50, 255], fill=(190, 195, 210))
    d.polygon([(18, 255), (52, 255), (44, 320), (35, 330), (26, 320)], fill=PURt)
    return im
BRUSH = make_brush()

def jar_icon(r, col, mixc=None):
    im = Image.new("RGBA", (2 * r + 20, 2 * r + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = r + 10
    d.ellipse([c - r, c - r, c + r, c + r], fill=col, outline=INK, width=7)
    d.ellipse([c - r * 0.55, c - r * 0.6, c - r * 0.15, c - r * 0.3], fill=(255, 255, 255, 140))
    return im

def sparkle(d, x, y, r, a=255):
    d.polygon(star_poly(x, y, r, 0, 0.35), fill=(255, 255, 230, a))

# ---------- captions ----------
def wrap(d, txt, sz, maxw):
    f = font(sz); words = txt.split(); out, cur = [], ""
    for w_ in words:
        tt = (cur + " " + w_).strip()
        if d.textlength(tt, font=f) <= maxw: cur = tt
        else: out.append(cur); cur = w_
    if cur: out.append(cur)
    return out

def caption(im, t):
    d = ImageDraw.Draw(im)
    for a, b, txt in LINES:
        if a <= t < b:
            k = ease((t - a) / 0.25) * ease((b - t) / 0.25)
            sz = 64; lines = wrap(d, txt, sz, 780)
            if len(lines) > 2: sz = 56; lines = wrap(d, txt, sz, 800)
            lh = sz * 1.25; hgt = lh * len(lines) + 46
            y0 = 1335 + (1 - k) * 30
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle([40, y0, 890, y0 + hgt], radius=38, fill=(80, 45, 110, int(225 * k)),
                                 outline=(255, 210, 120, int(255 * k)), width=5)
            for i, ln in enumerate(lines):
                f = font(sz); w = od.textlength(ln, font=f)
                od.text((465 - w / 2, y0 + 20 + i * lh), ln, font=f, fill=(255, 255, 255, int(255 * k)),
                        stroke_width=4, stroke_fill=(50, 25, 70, int(255 * k)))
            im.alpha_composite(ov)
            return

# ---------- scene pieces ----------
def header(d, t, txt, start, col=(255, 255, 255)):
    k = pop((t - start) / 0.5)
    if k > 0: text_c(d, txt, 560, 150, 74 * k + 1, col, sw=8)

def draw_stage(im, t):
    d = ImageDraw.Draw(im)
    # buckets
    if S_BUCK <= t < S_WOW + 0.6:
        for i, (sp, bx, lab, col) in enumerate(((BUCKET_R, 235, "RED", REDt), (BUCKET_B, 695, "BLUE", BLUEt))):
            at = S_BUCK + 0.3 + i * 2.6
            s = pop((t - at) / 0.6)
            if s <= 0: continue
            pk = ease((t - S_POUR) / 0.8) * (1 - ease((t - (S_STIR - 0.4)) / 0.6))
            out = ease((t - S_WOW) / 0.6)
            by = 720 - pk * 110 + math.sin(t * 2.5 + i) * 6 - out * 0
            bxx = bx + (1 if i == 0 else -1) * pk * 25 + (-1 if i == 0 else 1) * out * 420
            rot = (-1 if i == 0 else 1) * pk * 48
            paste(im, sp, bxx, by, s, rot)
            if t < S_POUR + 0.3:
                text_c(d, lab, bx, 860, 70 * min(1, s), col, stroke=(255, 255, 255), sw=8)
            # stream
            if pk > 0.6:
                sx = bxx + (1 if i == 0 else -1) * 110; sy = by - 30
                ex, ey = CX + (-35 if i == 0 else 35), 1000
                pts = [(sx + (ex - sx) * u + (1 if i == 0 else -1) * math.sin(u * math.pi) * 40,
                        sy + (ey - sy) * u * u - math.sin(u * math.pi) * 30) for u in np.linspace(0, 1, 18)]
                d.line(pts, fill=col, width=int(22 * (pk - 0.6) / 0.4) + 2, joint="curve")
    # jar
    if S_BUCK + 5.0 <= t < S_PAINT + 0.5:
        js = pop((t - (S_BUCK + 5.0)) / 0.6)
        out = ease((t - S_PAINT) / 0.5)
        level = 0.82 * ease((t - (S_POUR + 0.7)) / 3.0)
        stir = 8.0 * ease((t - S_STIR) / 3.6) if t >= S_STIR else 0.0
        mix = ease((t - (S_STIR + 1.2)) / 2.6)
        jar = Image.new("RGBA", (JW, JH), (0, 0, 0, 0))
        jar.alpha_composite(jar_liquid(level, stir, mix))
        if S_STIR <= t < S_WOW + 0.3:
            ang = (t - S_STIR) * 6.5
            sx = JW / 2 + math.cos(ang) * 70
            sp = SPOON.rotate(math.sin(ang) * 12, resample=Image.BICUBIC, expand=True)
            im_sp = (sx, sp)   # spoon drawn over jar (sticks out top)
        else:
            im_sp = None
        jar.alpha_composite(GLASS)
        s = js * (1 - out) + 0.001
        jy = JY + JH / 2 + (math.sin(t * 9) * 4 if t > S_STIR and t < S_WOW else 0)
        if t >= S_WOW: s *= 1 + 0.06 * math.sin((t - S_WOW) * 6) * (1 - ease((t - S_WOW) / 3))
        paste(im, jar, CX, jy, s)
        if im_sp and s > 0.5:
            sx, sp = im_sp
            im.alpha_composite(sp, (int(JX + sx - sp.width / 2), int(JY - 150)))
        d = ImageDraw.Draw(im)
        if t >= S_WOW:
            lt = t - S_WOW
            for k in range(10):
                a = k / 10 * 2 * math.pi + lt * 0.8; rr = 230 + 20 * math.sin(lt * 3 + k)
                al = int(255 * (0.5 + 0.5 * math.sin(lt * 5 + k))) * (1 - out)
                sparkle(d, CX + math.cos(a) * rr, JY + JH / 2 + 30 + math.sin(a) * rr * 0.9, 18 + 8 * math.sin(lt * 4 + k), int(al))
            k = pop(lt / 0.6) * (1 - out)
            if k > 0: text_c(d, "PURPLE!", CX, 560, 140 * k + 1, PURt, stroke=(255, 255, 255), sw=12)
    # easel and painting
    if S_PAINT <= t < S_RECAP + 0.5:
        lt = t - S_PAINT; out = ease((t - S_RECAP) / 0.5)
        k = ease(lt / 0.6) * (1 - out)
        if k > 0:
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            yo = (1 - k) * 200
            od.line([200, 1240 + yo, 300, 560 + yo], fill=(170, 110, 70), width=26)
            od.line([730, 1240 + yo, 630, 560 + yo], fill=(170, 110, 70), width=26)
            od.line([465, 1240 + yo, 465, 600 + yo], fill=(150, 95, 60), width=20)
            od.rounded_rectangle([75, 600 + yo, 855, 1150 + yo], radius=24, fill=(255, 253, 248), outline=(170, 110, 70), width=14)
            od.rectangle([60, 1140 + yo, 870, 1170 + yo], fill=(170, 110, 70))
            ov.putalpha(Image.fromarray((np.array(ov.split()[3]) * k).astype(np.uint8)))
            im.alpha_composite(ov)
            brush_at = None
            for i, (sp, name) in enumerate(ITEMS):
                st = 2.2 + i * 2.6
                f = ease((lt - st) / 1.6)
                ix = 210 + i * 255; iy = 830 + yo
                if f > 0 and out < 1:
                    m = Image.new("L", sp.size, 0); md = ImageDraw.Draw(m)
                    edge = f * (sp.height + 40) - 20
                    md.polygon([(0, 0), (sp.width, 0), (sp.width, edge + 15), (0, edge - 15)], fill=255)
                    md.rectangle([0, 0, sp.width, max(0, edge - 15)], fill=255)
                    piece = sp.copy(); a = np.array(piece.split()[3]) * (np.array(m) / 255) * (1 - out)
                    piece.putalpha(Image.fromarray(a.astype(np.uint8)))
                    bounce = math.sin((lt - st - 1.6) * 3) * 6 if f >= 1 else 0
                    paste(im, piece, ix, iy + bounce)
                    if f < 1:
                        brush_at = (ix + math.sin(lt * 16) * 80, iy - sp.height / 2 + edge)
                    if f >= 1:
                        d2 = ImageDraw.Draw(im)
                        text_c(d2, name, ix, iy + 150, 46, PURt, stroke=(255, 255, 255), sw=5)
            if brush_at:
                paste(im, BRUSH, brush_at[0] + 20, brush_at[1] - 150, 1.0, -25)
    # recap
    if S_RECAP <= t < S_OUT + 0.4:
        lt = t - S_RECAP; d = ImageDraw.Draw(im); out = ease((t - S_OUT) / 0.4)
        y = 860
        parts = [(150, REDt, "red", 0.3), (465 + 0 * 0, None, "+", 0.9), (465, BLUEt, "blue", 1.3)]
        s1 = pop((lt - 0.3) / 0.5) * (1 - out); s2 = pop((lt - 1.3) / 0.5) * (1 - out); s3 = pop((lt - 2.6) / 0.6) * (1 - out)
        if s1 > 0:
            paste(im, jar_icon(95, REDt), 150, y, s1); text_c(d, "red", 150, y + 120, 54 * s1 + 1, REDt, stroke=(255, 255, 255), sw=6)
        if s1 > 0.5: text_c(d, "+", 307, y - 60, 100, INK, stroke=(255, 255, 255), sw=6)
        if s2 > 0:
            paste(im, jar_icon(95, BLUEt), 465, y, s2); text_c(d, "blue", 465, y + 120, 54 * s2 + 1, BLUEt, stroke=(255, 255, 255), sw=6)
        if s2 > 0.5: text_c(d, "=", 622, y - 60, 100, INK, stroke=(255, 255, 255), sw=6)
        if s3 > 0:
            paste(im, jar_icon(95, PURt), 780, y, s3 * (1 + 0.05 * math.sin(lt * 5)))
            text_c(d, "purple", 780, y + 120, 54 * s3 + 1, PURt, stroke=(255, 255, 255), sw=6)
            for k_ in range(6):
                a = lt * 1.5 + k_
                sparkle(d, 780 + math.cos(a) * 140, y + math.sin(a) * 140, 14, int(220 * s3))

def draw_frame(t):
    im = BG.copy(); d = ImageDraw.Draw(im)
    # floating dust sparkles
    for k in range(10):
        x = (k * 173 + t * 20) % 900; y = 260 + (k * 271) % 900 + math.sin(t + k) * 20
        a = int(90 + 80 * math.sin(t * 2 + k)); sparkle(d, x, y, 7, a)
    if t < S_BUCK:
        s = pop(t / 0.8); draw_twinkle(im, t, CX, 700, 190) if s >= 1 else paste(im, TW[(190, False)], CX, 700, s)
        d = ImageDraw.Draw(im)
        if t > 1.0:
            k = pop((t - 1.0) / 0.6); text_c(d, "Let's Mix Colors!", CX, 1000, 100 * k + 1, (255, 255, 255), sw=10)
        if t > 2.0:
            k = pop((t - 2.0) / 0.6)
            f = font(84 * k + 1); parts = [("Red", REDt), (" + ", INK), ("Blue", BLUEt), (" = ?", INK)]
            tw = sum(d.textlength(p, font=f) for p, _ in parts); x = CX - tw / 2
            for p, c in parts:
                d.text((x, 1150), p, font=f, fill=c, stroke_width=8, stroke_fill=(255, 255, 255)); x += d.textlength(p, font=f)
    elif t < S_OUT:
        k = ease((t - S_BUCK) / 0.6)
        tx = CX + (165 - CX) * k; ty = 700 + (230 - 700) * k
        if k < 1: paste(im, TW[(190, False)], tx, ty, 1 - 0.5 * k)
        else: draw_twinkle(im, t, 165, 230, 95)
        d = ImageDraw.Draw(im)
        if t < S_POUR: header(d, t, "Two paints!", S_BUCK + 0.4)
        elif t < S_WOW: header(d, t, "Stir, stir, stir!", S_POUR + 0.2)
        elif S_PAINT <= t < S_RECAP: header(d, t, "Purple things!", S_PAINT + 0.3, PURt)
        elif t >= S_RECAP: header(d, t, "Remember!", S_RECAP + 0.2)
        draw_stage(im, t)
    else:
        lt = t - S_OUT
        s = pop(lt / 0.8)
        if s < 1: paste(im, TW[(190, False)], CX, 680, s)
        else: draw_twinkle(im, t, CX, 680, 190)
        d = ImageDraw.Draw(im)
        for k in range(12):
            a = k / 12 * 2 * math.pi + lt; sparkle(d, CX + math.cos(a) * 300, 680 + math.sin(a) * 280, 16, int(200 * min(1, lt)))
        if lt > 0.6: text_c(d, "Great job!", CX, 990, 120 * pop((lt - 0.6) / 0.6) + 1, PURt, stroke=(255, 255, 255), sw=12)
        if lt > 1.6: text_c(d, "Red + Blue = Purple", CX, 1150, 70, (255, 255, 255), sw=8)
        if lt > 2.6: text_c(d, "Subscribe for more!", CX, 1290, 64, (255, 235, 150), sw=7)
    caption(im, t)
    return im

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:   # preview frames
        for tt in sys.argv[1:]:
            draw_frame(float(tt)).convert("RGB").save(f"_prev_{tt}.png")
        sys.exit()
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)
    for fi in range(NFR):
        proc.stdin.write(draw_frame(fi / FPS).convert("RGB").tobytes())
    proc.stdin.close(); proc.wait()

    # ---------- audio (original) ----------
    N = int(TOTAL * SR); audio = np.zeros(N); rng = np.random.default_rng(5)
    def tone(freq, dur, vol=0.2, kind="bell", decay=5):
        tt = np.arange(int(dur * SR)) / SR; w = np.sin(2 * np.pi * freq * tt)
        if kind == "bell": w += 0.35 * np.sin(2 * np.pi * freq * 2.01 * tt) + 0.12 * np.sin(2 * np.pi * freq * 3 * tt)
        if kind == "soft": w += 0.2 * np.sin(2 * np.pi * freq * 2 * tt)
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 150)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N: audio[i:j] += sig[:j - i]
    def swish(dur, vol, f0=1500):
        n = int(dur * SR); x = rng.standard_normal(n); x = np.convolve(x, np.ones(12) / 12, mode="same")
        env = np.sin(np.linspace(0, np.pi, n)) ** 2; return vol * x * env
    # gentle waltz in F major (original)
    F = {"F": 349.23, "G": 392.0, "A": 440.0, "Bb": 466.16, "C": 523.25, "D": 587.33, "E": 659.25, "F2": 698.46}
    mel = ["A", "C", "F2", "E", "D", "C", "Bb", "A", "G", "A", "C", "A", "G", "F", "G", "A",
           "D", "C", "Bb", "D", "C", "A", "G", "F"]
    bass = [174.61, 233.08, 261.63, 174.61, 146.83, 233.08, 196.0, 261.63]
    beat = 0.42; k = 0
    while k * beat < TOTAL - 1.5:
        add(tone(F[mel[k % len(mel)]] * 2, 0.8, 0.035, "bell", 4.5), k * beat)
        if k % 3 == 0: add(tone(bass[(k // 3) % 8], 1.3, 0.06, "soft", 2), k * beat)
        else: add(tone(bass[(k // 3) % 8] * 1.5, 0.4, 0.02, "soft", 6), k * beat)
        k += 1
    # sfx
    add(tone(880, 0.6, 0.12), 0.1); add(tone(1174.7, 0.8, 0.12), 0.35)
    for at in (S_BUCK + 0.3, S_BUCK + 2.9): add(tone(660, 0.5, 0.12), at); add(tone(990, 0.6, 0.1), at + 0.12)
    for i in range(14): add(tone(300 - i * 9, 0.18, 0.08, "soft", 14), S_POUR + 0.8 + i * 0.2)   # glugs
    for i in range(7): add(swish(0.45, 0.05), S_STIR + i * 0.5)
    for i, f in enumerate([698.46, 880, 1046.5, 1396.9]): add(tone(f, 1.0, 0.13), S_WOW + i * 0.13)
    for i in range(3):
        add(swish(1.4, 0.035), S_PAINT + 2.2 + i * 2.6); add(tone(1318.5, 0.7, 0.1), S_PAINT + 3.8 + i * 2.6)
    for i, at in enumerate((0.3, 1.3, 2.6)): add(tone([784, 988, 1318.5][i], 0.8, 0.12), S_RECAP + at)
    for i, f in enumerate([698.46, 880, 1046.5, 1396.9, 1760]): add(tone(f, 1.2, 0.12, "bell", 3), S_OUT + 0.1 + i * 0.15)
    fade = np.ones(N); fl = int(1.6 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    print("done", TOTAL)
