"""Dreamforge Kids - Mixing colors: blue + yellow = green.
Twinkle narrates beside a sunny pond. Two friendly color drops (blue + yellow)
slide together, their overlap turns green, then they squish into one green drop.
Then green things pop up (frog, leaf, turtle) and an equation recap.
"""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/mixing_blue_yellow_green.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
CX = 470                      # content centre (keeps clear of right-side Shorts UI)
BLUE, YEL, GRN = (60, 140, 245), (255, 215, 40), (70, 190, 80)
INK = (35, 50, 70)
random.seed(11)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
LINES = [
    (0.8, 5.6, "Hi friends! I'm Twinkle. Let's mix colors!"),
    (6.3, 12.2, "Here is blue. And here is yellow."),
    (13.0, 17.2, "Let's push them together... squish!"),
    (17.6, 21.4, "Look! Blue and yellow make green!"),
    (22.2, 30.8, "Green like a frog, a leaf, and a turtle!"),
    (32.0, 38.6, "Blue plus yellow makes green. You did it!"),
]
TOTAL = 44.0
NFR = int(TOTAL * FPS)
S_DROPS, S_MIX, S_THINGS, S_RECAP, S_OUT = 6.0, 13.0, 21.6, 31.4, 39.0

def talking(t):
    for a, b, txt in LINES:
        end = a + min(b - a - 0.2, len(txt.split()) * 0.42 + 0.7)
        if a <= t < end: return True
    return False

def pop(x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)

def dark(c, k=45): return tuple(max(0, v - k) for v in c[:3])

def text_c(d, txt, x, y, sz, fill, stroke=INK, sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((x - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def text_multi(d, parts, x, y, sz, sw=8):
    f = font(sz); tw = sum(d.textlength(p, font=f) for p, _ in parts); xx = x - tw / 2
    for p, c in parts:
        d.text((xx, y), p, font=f, fill=c, stroke_width=sw, stroke_fill=INK); xx += d.textlength(p, font=f)

def paste(canvas, sp, cx, cy, sx, sy=None, rot=0):
    sy = sx if sy is None else sy
    if sx <= 0.02 or sy <= 0.02: return
    w, h = max(2, int(sp.width * sx)), max(2, int(sp.height * sy))
    s = sp.resize((w, h), Image.BILINEAR)
    if rot: s = s.rotate(rot, resample=Image.BILINEAR, expand=True)
    canvas.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))

def eyes(d, cx, cy, r, look=0.0, blink=False):
    """big shiny cartoon eyes"""
    for dx in (-r * 0.32, r * 0.32):
        ex = cx + dx
        if blink:
            d.arc([ex - r * 0.13, cy - r * 0.08, ex + r * 0.13, cy + r * 0.1], 200, 340, fill=INK, width=max(3, int(r * 0.05)))
            continue
        d.ellipse([ex - r * 0.14, cy - r * 0.19, ex + r * 0.14, cy + r * 0.19], fill=INK)
        d.ellipse([ex - r * 0.08 + look, cy - r * 0.15, ex + r * 0.02 + look, cy - r * 0.05], fill=(255, 255, 255))
        d.ellipse([ex + r * 0.03 + look, cy + r * 0.05, ex + r * 0.08 + look, cy + r * 0.1], fill=(255, 255, 255))

def mouth(d, cx, cy, r, open_):
    if open_:
        d.ellipse([cx - r * 0.13, cy - r * 0.04, cx + r * 0.13, cy + r * 0.2], fill=(120, 40, 60))
        d.ellipse([cx - r * 0.07, cy + r * 0.08, cx + r * 0.07, cy + r * 0.18], fill=(255, 130, 150))
    else:
        d.arc([cx - r * 0.16, cy - r * 0.08, cx + r * 0.16, cy + r * 0.14], 20, 160, fill=INK, width=max(3, int(r * 0.05)))

def cheeks(d, cx, cy, r):
    for dx in (-r * 0.5, r * 0.5):
        d.ellipse([cx + dx - r * 0.1, cy - r * 0.04, cx + dx + r * 0.1, cy + r * 0.08], fill=(255, 130, 160))

# ---------- Twinkle ----------
def star_poly(cx, cy, r, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(-math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def make_twinkle(r, open_):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(s / 2, s / 2, r * 1.08), fill=(255, 240, 150, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(s / 2, s / 2 + r * 0.05, r), fill=(235, 170, 30))
    d.polygon(star_poly(s / 2, s / 2, r), fill=(255, 210, 60))
    cy = s / 2 + r * 0.06
    eyes(d, s / 2, cy - r * 0.05, r * 0.85)
    cheeks(d, s / 2, cy + r * 0.12, r * 0.8)
    mouth(d, s / 2, cy + r * 0.14, r * 0.9, open_)
    return im

TW = {o: make_twinkle(150, o) for o in (False, True)}
TW_SMALL = {o: make_twinkle(80, o) for o in (False, True)}

# ---------- colour drops ----------
def drop_mask(r):
    """teardrop shape mask (point up)"""
    s = int(r * 2.6); m = Image.new("L", (s, s), 0); d = ImageDraw.Draw(m)
    cx, cy = s / 2, s / 2 + r * 0.25
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    d.polygon([(cx - r * 0.86, cy - r * 0.5), (cx, cy - r * 1.75), (cx + r * 0.86, cy - r * 0.5)], fill=255)
    return m

DR = 165
DMASK = drop_mask(DR)

def drop_sprite(color, mask=DMASK):
    s = mask.width; im = Image.new("RGBA", (s, s), color + (0,))
    im.putalpha(mask)
    shade = Image.new("RGBA", (s, s), dark(color, 40) + (255,))
    sm = mask.filter(ImageFilter.GaussianBlur(18)).point(lambda v: 255 - v)
    sm = Image.composite(sm, Image.new("L", (s, s), 0), mask).point(lambda v: int(v * 0.6))
    im.alpha_composite(Image.composite(shade, Image.new("RGBA", (s, s), (0, 0, 0, 0)), sm))
    hl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([s * 0.27, s * 0.4, s * 0.4, s * 0.56], fill=(255, 255, 255, 150))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(5)))
    return im

def face_on(canvas, cx, cy, r, open_=False, blink=False, look=0):
    d = ImageDraw.Draw(canvas)
    eyes(d, cx, cy, r, look, blink); cheeks(d, cx, cy + r * 0.2, r); mouth(d, cx, cy + r * 0.24, r, open_)

SP_B, SP_Y, SP_G = drop_sprite(BLUE), drop_sprite(YEL), drop_sprite(GRN)
DOFF = DR * 0.25   # sprite centre -> body centre offset

# ---------- green things ----------
def make_frog(r=120):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    g, gd = (90, 200, 90), (50, 150, 60)
    for dx in (-1, 1):
        d.ellipse([c + dx * r * 0.75 - r * 0.45, c + r * 0.55, c + dx * r * 0.75 + r * 0.45, c + r * 0.95], fill=gd)
    d.ellipse([c - r, c - r * 0.55, c + r, c + r * 0.85], fill=g)
    d.ellipse([c - r * 0.6, c + r * 0.05, c + r * 0.6, c + r * 0.75], fill=(190, 240, 150))
    for dx in (-1, 1):
        ex = c + dx * r * 0.45
        d.ellipse([ex - r * 0.38, c - r * 0.95, ex + r * 0.38, c - r * 0.2], fill=g)
        d.ellipse([ex - r * 0.26, c - r * 0.82, ex + r * 0.26, c - r * 0.32], fill=(255, 255, 255))
        d.ellipse([ex - r * 0.15, c - r * 0.72, ex + r * 0.15, c - r * 0.38], fill=INK)
        d.ellipse([ex - r * 0.1, c - r * 0.68, ex - r * 0.02, c - r * 0.58], fill=(255, 255, 255))
    d.arc([c - r * 0.45, c - r * 0.3, c + r * 0.45, c + r * 0.15], 15, 165, fill=INK, width=8)
    for dx in (-1, 1):
        d.ellipse([c + dx * r * 0.7 - 16, c - r * 0.05, c + dx * r * 0.7 + 16, c + r * 0.08], fill=(255, 140, 160))
    return im

def make_leaf(r=130):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    pts = []
    for i in range(61):
        a = i / 60 * math.pi
        pts.append((c + math.cos(a) * r * 1.0 * -1 + 0, c - math.sin(a) * r * 0.55))
    top = [(c - r + 2 * r * i / 40, c - math.sin(math.pi * i / 40) * r * 0.62) for i in range(41)]
    bot = [(c + r - 2 * r * i / 40, c + math.sin(math.pi * i / 40) * r * 0.62) for i in range(41)]
    leaf = Image.new("RGBA", (s, s), (0, 0, 0, 0)); ld = ImageDraw.Draw(leaf)
    ld.polygon(top + bot, fill=(80, 185, 70)); ld.polygon(top + [(c + r, c), (c - r, c)], fill=(105, 205, 85))
    ld.line([(c - r - 40, c + 10), (c + r * 0.9, c)], fill=(45, 120, 50), width=10)
    for k in range(-3, 4):
        x = c + k * r * 0.24
        ld.line([(x, c), (x + r * 0.2, c - r * 0.36)], fill=(55, 140, 55), width=6)
        ld.line([(x, c), (x + r * 0.2, c + r * 0.36)], fill=(55, 140, 55), width=6)
    return leaf.rotate(25, resample=Image.BICUBIC)

def make_turtle(r=125):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    skin, shell, sd = (150, 215, 110), (60, 165, 70), (40, 125, 55)
    for dx in (-0.6, 0.45):
        d.rounded_rectangle([c + dx * r - 22, c + r * 0.1, c + dx * r + 30, c + r * 0.6], 18, fill=skin)
    d.ellipse([c + r * 0.7, c - r * 0.35, c + r * 1.25, c + r * 0.25], fill=skin)
    d.ellipse([c + r * 0.95, c - r * 0.2, c + r * 1.07, c - r * 0.05], fill=INK)
    d.ellipse([c + r * 0.98, c - r * 0.18, c + r * 1.02, c - r * 0.12], fill=(255, 255, 255))
    d.arc([c + r * 0.88, c - r * 0.1, c + r * 1.16, c + r * 0.12], 20, 150, fill=INK, width=6)
    d.polygon([(c - r * 0.95, c + r * 0.25), (c - r * 1.25, c + r * 0.35), (c - r * 0.9, c + r * 0.4)], fill=skin)
    d.pieslice([c - r, c - r * 0.75, c + r * 0.85, c + r * 0.85], 180, 360, fill=shell)
    d.rectangle([c - r, c + r * 0.02, c + r * 0.85, c + r * 0.2], fill=sd)
    for hx, hy in [(-0.5, -0.25), (0.05, -0.45), (0.45, -0.2), (-0.1, -0.05)]:
        d.regular_polygon((c + hx * r, c + hy * r, r * 0.17), 6, fill=sd)
    return im

THINGS = [("frog", make_frog()), ("leaf", make_leaf()), ("turtle", make_turtle())]
THING_X = [CX - 300, CX, CX + 300]

# ---------- background: sunny pond meadow ----------
def background():
    g = np.linspace(0, 1, H)[:, None]
    top, bot = np.array([150, 215, 255]), np.array([225, 245, 255])
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun)
    sd.ellipse([780, 70, 1020, 310], fill=(255, 240, 160, 160)); sun = sun.filter(ImageFilter.GaussianBlur(30))
    bg.alpha_composite(sun); d = ImageDraw.Draw(bg); d.ellipse([830, 120, 970, 260], fill=(255, 230, 110))
    d.ellipse([-300, 1420, 700, 1900], fill=(150, 215, 120))
    d.ellipse([350, 1460, 1400, 1950], fill=(130, 200, 105))
    d.rectangle([0, 1640, W, H], fill=(120, 190, 95))
    d.ellipse([170, 1700, 900, 1860], fill=(110, 185, 225)); d.ellipse([230, 1720, 840, 1840], fill=(140, 205, 240))
    for _ in range(60):
        x, y = random.randint(0, W), random.randint(1600, H)
        d.polygon([(x, y), (x + 6, y - 30), (x + 12, y)], fill=(95, 170, 80))
    for _ in range(14):
        x, y = random.randint(20, W - 20), random.randint(1560, 1680); col = random.choice([(255, 255, 255), (255, 200, 220), (255, 230, 120)])
        for a in range(5):
            d.ellipse([x + 10 * math.cos(a * 1.256) - 7, y + 10 * math.sin(a * 1.256) - 7, x + 10 * math.cos(a * 1.256) + 7, y + 10 * math.sin(a * 1.256) + 7], fill=col)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 190, 60))
    return bg

BG = background()

def cloud(d, x, y, s):
    for dx, dy, r in [(0, 0, 50), (55, -20, 60), (115, 0, 48), (55, 15, 50)]:
        d.ellipse([x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s], fill=(255, 255, 255, 230))

# ---------- captions ----------
CAP_Y = 1330
def caption(canvas, t):
    for a, b, txt in LINES:
        if a <= t < b:
            al = min(1, (t - a) / 0.25, (b - t) / 0.25)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
            f = font(60); words = txt.split(); lines, cur = [], ""
            for w_ in words:
                tst = (cur + " " + w_).strip()
                if d.textlength(tst, font=f) > 800: lines.append(cur); cur = w_
                else: cur = tst
            lines.append(cur)
            hh = 80 * len(lines) + 40
            d.rounded_rectangle([CX - 440, CAP_Y, CX + 440, CAP_Y + hh], 40, fill=(255, 255, 255, 215), outline=(120, 170, 220), width=6)
            for i, ln in enumerate(lines):
                text_c(d, ln, CX, CAP_Y + 18 + i * 80, 60, (40, 70, 140), stroke=(255, 255, 255), sw=3)
            if al < 1: lay.putalpha(lay.getchannel("A").point(lambda v: int(v * al)))
            canvas.alpha_composite(lay)
            return

# ---------- mixing composite ----------
BAND_Y0, BAND_H = 520, 760
def mix_frame(canvas, xb, xy, yc, merge_s):
    """draw blue and yellow drops at xb, xy; overlap rendered green"""
    band = Image.new("RGBA", (W, BAND_H), (0, 0, 0, 0))
    mb = Image.new("L", (W, BAND_H), 0); my = Image.new("L", (W, BAND_H), 0)
    s = DMASK.width
    mb.paste(DMASK, (int(xb - s / 2), int(yc - BAND_Y0 - s / 2))); my.paste(DMASK, (int(xy - s / 2), int(yc - BAND_Y0 - s / 2)))
    b = np.asarray(mb, dtype=np.float32) / 255; y = np.asarray(my, dtype=np.float32) / 255
    ov = np.minimum(b, y); ob = b - ov; oy = y - ov
    rgb = np.zeros((BAND_H, W, 3), np.float32)
    for m, c in ((ob, BLUE), (oy, YEL), (ov, GRN)):
        rgb += m[..., None] * np.array(c, np.float32)
    a = np.clip(ob + oy + ov, 0, 1)
    rgb = np.where(a[..., None] > 0, rgb / np.maximum(a[..., None], 1e-6), 0)
    arr = np.dstack([rgb, a * 255]).astype(np.uint8)
    band = Image.fromarray(arr, "RGBA")
    canvas.alpha_composite(band, (0, BAND_Y0))
    d = ImageDraw.Draw(canvas)
    for x in (xb, xy):  # outlines + highlights
        d.ellipse([x - DR * 0.55, yc + DOFF - DR * 0.75, x - DR * 0.3, yc + DOFF - DR * 0.45], fill=(255, 255, 255, 150))

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    for k, (x0, y0, s, v) in enumerate([(-200, 380, 1.0, 18), (300, 230, 0.8, 12), (700, 450, 0.9, 15)]):
        cloud(d, (x0 + t * v) % (W + 400) - 200, y0, s)
    tk = talking(t); mo = tk and int(t * 8) % 2 == 0
    bounce = abs(math.sin(t * 8)) * 14 if tk else math.sin(t * 2.5) * 6
    blink = (t % 3.7) < 0.12

    if t < S_DROPS:
        paste(im, TW[mo], CX, 860 - bounce, pop(t / 0.8), rot=math.sin(t * 2) * 5)
        if t > 1.0: text_c(d, "Mixing Colors!", CX, 340, 108, (60, 170, 70), sw=10)
        if t > 1.8: text_multi(d, [("Blue", BLUE), (" + ", (255, 255, 255)), ("Yellow", YEL), (" = ?", (255, 255, 255))], CX, 1130, 84)
    else:
        if t < S_OUT:  # small Twinkle narrator, top-left
            paste(im, TW_SMALL[mo], 120, 200 - bounce * 0.6, pop((t - S_DROPS) / 0.6))
        if S_DROPS <= t < S_THINGS:
            yc = 900
            if t < S_MIX:
                lt = t - S_DROPS
                xb = -200 + (CX - 230 + 200) * ease(lt / 1.2)
                xy = CX + 230
                hop_b = abs(math.sin(lt * 4)) * 25 if lt > 1.2 else 0
                if lt > 2.4:
                    ys = pop((lt - 2.4) / 0.7)
                    paste(im, SP_Y, xy, yc - abs(math.sin(lt * 4 + 1)) * 25, ys)
                    if ys > 0.5: face_on(im, xy, yc + DOFF - 10, 110, blink=blink)
                paste(im, SP_B, xb, yc - hop_b, 1.0)
                face_on(im, xb, yc + DOFF - 10 - hop_b, 110, blink=blink)
                d = ImageDraw.Draw(im)
                if lt > 0.8: text_c(d, "blue", CX - 230, 590, 96, BLUE, sw=9)
                if lt > 3.0: text_c(d, "yellow", CX + 230, 590, 96, YEL, sw=9)
            else:
                lt = t - S_MIX
                p = ease(lt / 3.6)
                gap = 230 * (1 - p)
                if lt < 4.2:
                    mix_frame(im, CX - gap, CX + gap, yc, p)
                    face_on(im, CX - gap - 20 * (1 - p), yc + DOFF - 10, 100, open_=False)
                    if gap > 60: face_on(im, CX + gap + 20, yc + DOFF - 10, 100)
                    d = ImageDraw.Draw(im)
                    text_c(d, "squish!" if lt > 2.2 else "push, push...", CX, 560, 92, (60, 170, 70) if lt > 2.2 else (255, 255, 255), sw=9)
                else:
                    wl = lt - 4.2
                    wob = math.sin(wl * 14) * 0.12 * math.exp(-wl * 2.2)
                    paste(im, SP_G, CX, yc + 20, 1.08 + wob, 1.08 - wob)
                    face_on(im, CX, yc + DOFF + 8, 118, open_=True, blink=blink)
                    d = ImageDraw.Draw(im)
                    s = pop(wl / 0.6)
                    text_c(d, "GREEN!", CX, 540 + (1 - s) * 40, 140 * max(0.3, s), GRN, sw=11)
                    for k in range(10):  # sparkles
                        a = k * 0.628 + wl; rr = 260 + 30 * math.sin(wl * 3 + k)
                        if wl < 3.0:
                            sx, sy = CX + rr * math.cos(a), yc + 30 + rr * math.sin(a)
                            d.polygon(star_poly(sx, sy, 18), fill=(255, 245, 160))
        elif S_THINGS <= t < S_RECAP:
            lt = t - S_THINGS
            text_c(d, "Green things!", CX, 420, 100, GRN, sw=10)
            for i, ((name, sp), x) in enumerate(zip(THINGS, THING_X)):
                at = 0.8 + i * 1.8
                if lt >= at:
                    hop = abs(math.sin((lt - at) * 3 + i)) * 18
                    paste(im, sp, x, 880 - hop, pop((lt - at) / 0.6) * 0.82)
                    if lt - at > 0.4: text_c(d, name, x, 1110, 70, (255, 255, 255), stroke=(40, 120, 50), sw=8)
        elif S_RECAP <= t < S_OUT:
            lt = t - S_RECAP
            for i, (sp, x, col) in enumerate([(SP_B, CX - 320, BLUE), (SP_Y, CX, YEL), (SP_G, CX + 320, GRN)]):
                at = 0.3 + i * 1.3
                if lt >= at:
                    s = pop((lt - at) / 0.6) * 0.62
                    paste(im, sp, x, 880 - (abs(math.sin(lt * 4)) * 15 if i == 2 else 0), s)
                    if s > 0.4: face_on(im, x, 880 + DOFF * 0.62 - 6, 66, blink=blink)
            d = ImageDraw.Draw(im)
            if lt > 1.0: text_c(d, "+", CX - 160, 820, 110, (255, 255, 255), sw=8)
            if lt > 2.3: text_c(d, "=", CX + 160, 820, 110, (255, 255, 255), sw=8)
            if lt > 3.0: text_multi(d, [("Blue", BLUE), (" + ", (255, 255, 255)), ("Yellow", YEL), (" = ", (255, 255, 255)), ("Green", GRN)], CX, 1130, 72, sw=7)
            text_c(d, "Let's say it!", CX, 420, 96, (255, 255, 255), stroke=(60, 120, 200), sw=9)
        else:
            lt = t - S_OUT
            paste(im, TW[mo], CX, 820 - math.sin(t * 3) * 14, pop(lt / 0.8), rot=math.sin(t * 4) * 8)
            paste(im, SP_G, CX + 270, 960, 0.5); face_on(im, CX + 270, 960 + DOFF * 0.5 - 4, 55, open_=True)
            d = ImageDraw.Draw(im)
            if lt > 0.6: text_c(d, "Great mixing!", CX, 380, 110, (60, 170, 70), sw=10)
            if lt > 1.6: text_c(d, "Subscribe for more!", CX, 1150, 66, (255, 255, 255), stroke=(60, 120, 200), sw=7)
    caption(im, t)
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle marimba waltz in F ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, kind="marimba", decay=7):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if kind == "marimba": w += 0.25 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-tt * 30)
    if kind == "bell": w += 0.4 * np.sin(2 * np.pi * freq * 2.01 * tt)
    env = np.exp(-decay * tt) * np.minimum(1, tt * 300)
    return vol * w * env
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]
F = {"F": 349.23, "G": 392.0, "A": 440.0, "Bb": 466.16, "C": 523.25, "D": 587.33, "C5": 1046.5, "F5": 698.46}
melody = ["F", "A", "C", "A", "G", "Bb", "D", "Bb", "A", "C", "F5", "C", "G", "A", "F", None]
bassn = [174.61, 233.08, 174.61, 130.81]
beat = 0.42; k = 0
while k * beat < TOTAL - 1.5:
    n = melody[k % 16]
    if n: add(tone(F[n], 0.8, 0.045), k * beat)
    if k % 3 == 0: add(tone(bassn[(k // 12) % 4], 1.2, 0.06, "sine", 2.5), k * beat)
    k += 1
add(tone(698, 0.6, 0.12, "bell", 5), 0.2); add(tone(880, 0.8, 0.12, "bell", 5), 1.0)
add(tone(523, 0.4, 0.15), S_DROPS + 0.3); add(tone(659, 0.4, 0.15), S_DROPS + 2.5)
# squish: soft downward glide
tt = np.arange(int(0.6 * SR)) / SR; fr = 500 - 300 * tt / 0.6
add(0.15 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt * 4), S_MIX + 3.6)
for i, f in enumerate([698.46, 880, 1046.5, 1396.9]): add(tone(f, 1.0, 0.13, "bell", 4), S_MIX + 4.2 + i * 0.12)
for i in range(3): add(tone([587.33, 659.25, 783.99][i], 0.5, 0.15), S_THINGS + 0.8 + i * 1.8)
for i in range(3): add(tone([523.25, 659.25, 783.99][i], 0.5, 0.15), S_RECAP + 0.3 + i * 1.3)
for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]): add(tone(f, 1.2, 0.13, "bell", 3), S_OUT + 0.2 + i * 0.15)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
print("done", TOTAL)
