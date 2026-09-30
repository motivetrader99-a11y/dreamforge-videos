"""Dreamforge Kids — More or less? Comparing groups.
Sunny picnic meadow: two picnic mats side by side. Each round, two groups of friendly
objects pop in (apples 4 vs 2, flowers 1 vs 5, cupcakes 3 vs 3). Twinkle matches them
one-to-one with dotted lines; the leftover ones sparkle, and the group is labelled
MORE, LESS or SAME. Twinkle the star narrates. Original art & music."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/more_or_less_comparing_groups.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (70, 45, 90)
random.seed(21)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, RD, OUTRO = 5.0, 12.5, 6.0
R = [INTRO, INTRO + RD, INTRO + 2 * RD]
T_OUT = INTRO + 3 * RD
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

ROUNDS = [  # sprite, left n, right n, ask, answer side
    dict(kind="apple", L=4, Rn=2, head="Which has MORE?", result="MORE", side=0),
    dict(kind="flower", L=1, Rn=5, head="Which has LESS?", result="LESS", side=0),
    dict(kind="cupcake", L=3, Rn=3, head="More or less?", result="SAME", side=-1),
]

LINES = [
    (0.3, INTRO - 0.2, "Hi! I'm Twinkle! Let's learn more and less!"),
    (R[0] + 0.2, R[0] + 5.0, "Two groups of apples! Let's match them."),
    (R[0] + 5.2, R[0] + 12.3, "Four is more than two. This side has MORE!"),
    (R[1] + 0.2, R[1] + 5.0, "Now flowers! Which group has less?"),
    (R[1] + 5.2, R[1] + 12.3, "One is less than five. This side has LESS!"),
    (R[2] + 0.2, R[2] + 5.0, "Yummy cupcakes! Let's match them."),
    (R[2] + 5.2, R[2] + 12.3, "Three and three. They are the SAME!"),
    (T_OUT + 0.3, TOTAL - 0.4, "Great job! More, less, or the same!"),
]
TALK = [(a, a + min(b - a - 0.2, len(txt.split()) * 0.36 + 0.4)) for a, b, txt in LINES]
def talking(t): return any(a <= t < b for a, b in TALK)

# ---------- layout ----------
PX = [(70, 450), (520, 900)]      # panel x ranges (right edge < 930)
PCX = [260, 710]
PY0, PY1 = 540, 1320
def rowy(i): return 720 + i * 112

# ---------- art ----------
def vgrad(w, h, top, bot):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, w, axis=1))

def make_bg():
    im = vgrad(W, H, (255, 222, 205), (205, 240, 225)).convert("RGBA")
    d = ImageDraw.Draw(im)
    # soft sun top-right-ish (behind UI side is fine, decorative)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([760, 60, 1040, 340], fill=(255, 240, 170, 200))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(25)))
    d = ImageDraw.Draw(im)
    d.ellipse([820, 120, 980, 280], fill=(255, 236, 150))
    # hills
    d.ellipse([-500, 1180, 800, 2300], fill=(170, 225, 170))
    d.ellipse([300, 1250, 1600, 2400], fill=(150, 212, 160))
    d.rectangle([0, 1600, W, H], fill=(140, 205, 150))
    # meadow flowers (bottom decor only)
    for _ in range(60):
        x, y = random.randint(0, W), random.randint(1480, H - 20)
        c = random.choice([(255, 255, 255), (255, 200, 220), (255, 240, 150), (210, 190, 255)])
        r = random.randint(5, 10)
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + math.cos(a) * r - r * 0.7, y + math.sin(a) * r - r * 0.7,
                       x + math.cos(a) * r + r * 0.7, y + math.sin(a) * r + r * 0.7], fill=c)
        d.ellipse([x - r * 0.5, y - r * 0.5, x + r * 0.5, y + r * 0.5], fill=(255, 200, 80))
    return im

def cloud(w):
    im = Image.new("RGBA", (w, int(w * 0.55)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    h = im.height
    for cx, cy, r in ((0.3, 0.62, 0.22), (0.5, 0.45, 0.28), (0.72, 0.6, 0.22)):
        d.ellipse([w * (cx - r), h * cy - w * r, w * (cx + r), h * cy + w * r * 0.9], fill=(255, 255, 255, 230))
    d.rounded_rectangle([w * 0.1, h * 0.55, w * 0.9, h * 0.95], int(h * 0.2), fill=(255, 255, 255, 230))
    return im

def face(d, cx, cy, s, eye_dy=0.0):
    e = s * 0.075
    for dx in (-s * 0.14, s * 0.14):
        d.ellipse([cx + dx - e, cy - e * 1.3 + eye_dy, cx + dx + e, cy + e * 1.3 + eye_dy], fill=(55, 35, 65))
        d.ellipse([cx + dx - e * 0.5, cy - e * 0.95 + eye_dy, cx + dx + e * 0.1, cy - e * 0.3 + eye_dy], fill=(255, 255, 255))
    d.arc([cx - s * 0.09, cy + s * 0.02 + eye_dy, cx + s * 0.09, cy + s * 0.16 + eye_dy], 20, 160, fill=(55, 35, 65), width=max(2, int(s * 0.03)))
    for dx in (-s * 0.25, s * 0.25):
        d.ellipse([cx + dx - s * 0.06, cy + s * 0.04 + eye_dy, cx + dx + s * 0.06, cy + s * 0.11 + eye_dy], fill=(255, 120, 150, 150))

def make_apple(s=104):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    d.line([(c, s * 0.2), (c + s * 0.05, s * 0.05)], fill=(120, 80, 50), width=int(s * 0.06))
    d.ellipse([c + s * 0.04, s * 0.04, c + s * 0.3, s * 0.18], fill=(110, 200, 100))
    d.ellipse([s * 0.1, s * 0.18, c + s * 0.06, s * 0.92], fill=(235, 70, 80))
    d.ellipse([c - s * 0.06, s * 0.18, s * 0.9, s * 0.92], fill=(235, 70, 80))
    d.ellipse([s * 0.2, s * 0.26, s * 0.36, s * 0.42], fill=(255, 170, 170))
    face(d, c, s * 0.56, s)
    return im

def make_flower(s=104):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2; cy = s * 0.42
    d.line([(c, cy), (c, s * 0.98)], fill=(80, 170, 90), width=int(s * 0.07))
    d.ellipse([c, s * 0.72, c + s * 0.24, s * 0.84], fill=(100, 190, 100))
    for k in range(6):
        a = k * math.pi / 3
        px, py, r = c + math.cos(a) * s * 0.22, cy + math.sin(a) * s * 0.22, s * 0.15
        d.ellipse([px - r, py - r, px + r, py + r], fill=(250, 150, 200))
    d.ellipse([c - s * 0.2, cy - s * 0.2, c + s * 0.2, cy + s * 0.2], fill=(255, 215, 90))
    face(d, c, cy, s * 0.8)
    return im

def make_cupcake(s=104):
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    d.polygon([(s * 0.18, s * 0.55), (s * 0.82, s * 0.55), (s * 0.72, s * 0.95), (s * 0.28, s * 0.95)], fill=(140, 200, 240))
    for k in range(5):
        x = s * 0.27 + k * s * 0.115
        d.line([(x, s * 0.58), (x + s * 0.02, s * 0.92)], fill=(110, 170, 220), width=3)
    d.ellipse([s * 0.12, s * 0.35, s * 0.88, s * 0.68], fill=(255, 190, 215))
    d.ellipse([s * 0.24, s * 0.22, s * 0.76, s * 0.5], fill=(255, 205, 225))
    d.ellipse([c - s * 0.08, s * 0.06, c + s * 0.08, s * 0.22], fill=(230, 50, 70))
    for x, y, col in ((0.3, 0.45, (120, 200, 255)), (0.62, 0.4, (255, 230, 90)), (0.72, 0.55, (160, 230, 140))):
        d.rounded_rectangle([s * x, s * y, s * x + s * 0.07, s * y + s * 0.03], 2, fill=col)
    face(d, c, s * 0.72, s * 0.85)
    return im

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def make_twinkle(r, mouth_open):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(glow).polygon(star_poly(s / 2, s / 2, r * 1.06), fill=(255, 240, 150, 140))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(s / 2, s / 2 + r * 0.04, r), fill=(225, 165, 30))
    d.polygon(star_poly(s / 2, s / 2, r), fill=(255, 210, 60))
    cx, cy, e = s / 2, s / 2 + r * 0.05, r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([cx + dx - e, cy - e * 1.35, cx + dx + e, cy + e * 1.35], fill=(60, 40, 70))
        d.ellipse([cx + dx - e * 0.45, cy - e * 1.0, cx + dx + e * 0.15, cy - e * 0.3], fill=(255, 255, 255))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([cx + dx - r * 0.09, cy + r * 0.1, cx + dx + r * 0.09, cy + r * 0.22], fill=(255, 120, 150, 150))
    if mouth_open:
        d.ellipse([cx - r * 0.12, cy + r * 0.12, cx + r * 0.12, cy + r * 0.34], fill=(120, 40, 60))
        d.ellipse([cx - r * 0.07, cy + r * 0.24, cx + r * 0.07, cy + r * 0.33], fill=(255, 130, 150))
    else:
        d.arc([cx - r * 0.16, cy + r * 0.04, cx + r * 0.16, cy + r * 0.28], 20, 160, fill=(60, 40, 70), width=max(3, int(r * 0.05)))
    return im

BG = make_bg()
CLOUD = cloud(260)
SPR = {"apple": make_apple(), "flower": make_flower(), "cupcake": make_cupcake()}
TW_SMALL = [make_twinkle(78, False), make_twinkle(78, True)]
TW_BIG = [make_twinkle(165, False), make_twinkle(165, True)]

def paste(canvas, sp, cx, cy, scale=1.0, rot=0.0):
    if scale <= 0.02: return
    if scale != 1.0:
        sp = sp.resize((max(2, int(sp.width * scale)), max(2, int(sp.height * scale))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BILINEAR, expand=True)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def text_c(d, txt, y, sz, fill, cx=W / 2, stroke=INK, sw=8):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def wrap(txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    dd = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if dd.textlength(tst, font=f) <= maxw: cur = tst
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def caption(im, t):
    for a, b, txt in LINES:
        if a <= t < b: break
    else: return
    al = min(1, (t - a) / 0.25, (b - t) / 0.25)
    lines = wrap(txt, 60, 780)
    lh = 78; bh = lh * len(lines) + 40
    y0 = 1555 - bh
    box = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([80, y0, 930, y0 + bh], 40, fill=(255, 255, 255, int(235 * al)), outline=(250, 150, 190, int(255 * al)), width=6)
    for i, ln in enumerate(lines):
        f = font(60); w = bd.textlength(ln, font=f)
        bd.text((505 - w / 2, y0 + 18 + i * lh), ln, font=f, fill=INK + (int(255 * al),))
    im.alpha_composite(box)

MAT = [(255, 250, 235), (240, 248, 255)]
def draw_mat(im, side, glow):
    x0, x1 = PX[side]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    if glow > 0:
        d.rounded_rectangle([x0 - 14, PY0 - 14, x1 + 14, PY1 + 14], 50, fill=(255, 230, 120, int(170 * glow)))
        lay = lay.filter(ImageFilter.GaussianBlur(10)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([x0, PY0, x1, PY1], 40, fill=MAT[side] + (235,), outline=(250, 170, 200) if side == 0 else (150, 190, 240), width=7)
    # gingham stripes
    for k in range(1, 6):
        xx = x0 + k * (x1 - x0) / 6
        d.line([(xx, PY0 + 110), (xx, PY1 - 20)], fill=((250, 200, 215, 60) if side == 0 else (170, 205, 245, 60)), width=14)
    im.alpha_composite(lay)

def ribbon(d, cx, cy, txt, col, sc):
    if sc <= 0: return
    f = font(62 * sc); w = d.textlength(txt, font=f)
    hw, hh = w / 2 + 34 * sc, 46 * sc
    d.polygon([(cx - hw - 30 * sc, cy - hh * 0.6), (cx - hw + 10, cy - hh * 0.6), (cx - hw + 10, cy + hh * 0.9), (cx - hw - 30 * sc, cy + hh * 0.9), (cx - hw - 10 * sc, cy + hh * 0.15)], fill=tuple(max(0, c - 50) for c in col))
    d.polygon([(cx + hw + 30 * sc, cy - hh * 0.6), (cx + hw - 10, cy - hh * 0.6), (cx + hw - 10, cy + hh * 0.9), (cx + hw + 30 * sc, cy + hh * 0.9), (cx + hw + 10 * sc, cy + hh * 0.15)], fill=tuple(max(0, c - 50) for c in col))
    d.rounded_rectangle([cx - hw, cy - hh, cx + hw, cy + hh], int(18 * sc), fill=col, outline=(255, 255, 255), width=5)
    d.text((cx - w / 2, cy - hh * 0.95), txt, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=INK)

def dotted(d, x0, x1, y, p, col):
    xe = x0 + (x1 - x0) * p; x = x0
    while x < xe:
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col); x += 26

def heart(d, cx, cy, r, col):
    d.ellipse([cx - r, cy - r * 0.8, cx, cy + r * 0.2], fill=col)
    d.ellipse([cx, cy - r * 0.8, cx + r, cy + r * 0.2], fill=col)
    d.polygon([(cx - r * 0.95, cy - r * 0.15), (cx + r * 0.95, cy - r * 0.15), (cx, cy + r)], fill=col)

# round-local times
POP0, POPG = 0.4, 0.3
def match_t(k): return 3.2 + 0.7 * k

def draw_round(im, rd, rt, t):
    sp = SPR[rd["kind"]]; n = (rd["L"], rd["Rn"]); m = min(n)
    tmatch_end = match_t(m) + 0.2
    t_res = max(5.6, tmatch_end + 0.6)
    res = pop((rt - t_res) / 0.6)
    glow_side = rd["side"]
    for s in (0, 1):
        g = 0.0
        if res > 0 and (glow_side == s or glow_side == -1): g = min(1, res) * (0.75 + 0.25 * math.sin(t * 5))
        draw_mat(im, s, g)
    d = ImageDraw.Draw(im)
    # counts at mat top
    for s in (0, 1):
        cs = pop((rt - (POP0 + POPG * (n[0] + n[1]) + 0.3)) / 0.5)
        if cs > 0:
            cx, cy, r = PCX[s], PY0 + 62, 46 * cs
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255), outline=INK, width=5)
            f = font(64 * cs); tx = str(n[s]); w = d.textlength(tx, font=f)
            d.text((cx - w / 2, cy - 46 * cs), tx, font=f, fill=INK)
    # matching dotted lines + hearts
    for k in range(m):
        p = ease((rt - match_t(k)) / 0.45)
        if p <= 0: continue
        y = rowy(k)
        dotted(d, PCX[0] + 62, PCX[1] - 62, y, p, (240, 110, 160))
        if p >= 1:
            hs = pop((rt - match_t(k) - 0.45) / 0.4)
            heart(d, (PCX[0] + PCX[1]) / 2, y - 4, 22 * hs, (240, 90, 140))
    # items
    idx = 0
    for s in (0, 1):
        for i in range(n[s]):
            at = POP0 + POPG * idx; idx += 1
            sc = pop((rt - at) / 0.5)
            if sc <= 0: continue
            bob = math.sin(t * 3 + i + s * 2) * 4
            rot = 0.0
            extra = i >= m
            if extra and rt > tmatch_end:
                sc *= 1 + 0.1 * math.sin((rt - tmatch_end) * 8)
                rot = math.sin((rt - tmatch_end) * 6) * 8
                # sparkle ring
                aa = int(200 * min(1, (rt - tmatch_end) / 0.4))
                cx, cy = PCX[s], rowy(i)
                for k in range(6):
                    a = t * 2 + k * math.pi / 3
                    sx, sy = cx + math.cos(a) * 64, cy + math.sin(a) * 58
                    d.polygon(star_poly(sx, sy, 12), fill=(255, 215, 70, aa))
            paste(im, sp, PCX[s], rowy(i) + bob, sc, rot)
    d = ImageDraw.Draw(im)
    if res > 0:
        col = {"MORE": (255, 140, 60), "LESS": (120, 150, 240), "SAME": (120, 200, 120)}[rd["result"]]
        if glow_side == -1:
            ribbon(d, (PCX[0] + PCX[1]) / 2, 1268, "SAME!", col, res)
            es = res
            f = font(120 * es); w = d.textlength("=", font=f)
            d.text(((PCX[0] + PCX[1]) / 2 - w / 2, rowy(1) - 95 * es), "=", font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=INK)
        else:
            ribbon(d, PCX[glow_side], 1268, rd["result"] + "!", col, res)
            other = 1 - glow_side
            word = "less" if rd["result"] == "MORE" else "more"
            if rt > t_res + 1.6:
                text_c(d, f"{n[glow_side]} is {rd['result'].lower()} than {n[other]}", 400, 62, (255, 255, 255), cx=585, sw=7)

# floating clouds
CLOUDS = [(random.uniform(0, 1), random.uniform(360, 470), random.uniform(18, 30), random.uniform(0.5, 0.8)) for _ in range(3)]

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi / FPS
    im = BG.copy()
    for ph, y, sp_, sc in CLOUDS:
        x = -200 + ((ph * 1400 + t * sp_) % 1400)
        paste(im, CLOUD, x, y, sc)
    d = ImageDraw.Draw(im)
    mouth = talking(t) and (int(t * 7) % 2 == 0)

    if t < INTRO:
        bob = math.sin(t * 3) * 14 - (10 if mouth else 0)
        paste(im, TW_BIG[mouth], 480, 560 + bob, pop(t / 0.9), math.sin(t * 2) * 5)
        d = ImageDraw.Draw(im)
        for k, kind in enumerate(("apple", "flower", "cupcake", "apple", "cupcake")):
            a = t * 0.9 + k * 2 * math.pi / 5
            paste(im, SPR[kind], 480 + math.cos(a) * 330, 560 + math.sin(a) * 250, pop((t - 0.6 - k * 0.15) / 0.5) * 0.9)
        d = ImageDraw.Draw(im)
        if t > 1.0: text_c(d, "More or Less?", 900, 118, (255, 150, 190), cx=480, sw=10)
        if t > 1.8: text_c(d, "Comparing groups", 1060, 70, (255, 255, 255), cx=480, sw=7)
    elif t < T_OUT:
        ri = min(2, int((t - INTRO) // RD)); rt = t - R[ri]; rd = ROUNDS[ri]
        # fade in the round
        draw_round(im, rd, rt, t)
        d = ImageDraw.Draw(im)
        bob = math.sin(t * 3) * 8 - (10 if mouth else 0)
        paste(im, TW_SMALL[mouth], 150, 250 + bob, 1.0, math.sin(t * 2) * 4)
        d = ImageDraw.Draw(im)
        hs = pop((rt - 0.1) / 0.6)
        if hs > 0:
            f = font(76 * hs); w = d.textlength(rd["head"], font=f)
            d.text((590 - w / 2, 200 + 38 * (1 - hs)), rd["head"], font=f, fill=(255, 245, 160), stroke_width=9, stroke_fill=INK)
    else:
        lt = t - T_OUT; bob = math.sin(t * 3) * 14 - (10 if mouth else 0)
        paste(im, TW_BIG[mouth], 480, 540 + bob, pop(lt / 0.9), math.sin(t * 4) * 8)
        for k in range(9):
            kind = ("apple", "flower", "cupcake")[k % 3]
            x = -120 + ((lt * 220 + k * 125) % 1180)
            paste(im, SPR[kind], x, 1290 + math.sin(t * 5 + k) * 18 - abs(math.sin(t * 5 + k)) * 20, 0.9)
        d = ImageDraw.Draw(im)
        if lt > 0.7: text_c(d, "Great job!", 860, 116, (255, 150, 190), cx=480, sw=10)
        if lt > 1.5: text_c(d, "More, less, same!", 1010, 66, (255, 255, 255), cx=480, sw=7)
        if lt > 3.0: text_c(d, "Subscribe for more!", 1110, 56, (255, 245, 160), cx=480, sw=6)
    caption(im, t)
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle 4/4 skip in G, xylophone + soft bass ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, kind="xylo", decay=6):
    tt = np.arange(int(dur * SR)) / SR
    if kind == "xylo":
        w = np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(2 * np.pi * freq * 3 * tt) * np.exp(-25 * tt)
    elif kind == "bass":
        w = np.sin(2 * np.pi * freq * tt) + 0.2 * np.sin(2 * np.pi * freq * 2 * tt)
    else:
        w = np.sin(2 * np.pi * freq * tt)
    env = np.exp(-decay * tt) * np.minimum(1, tt * 200)
    return vol * w * env
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]
def slide(at, f0, f1, dur=0.22, vol=0.12):
    tt = np.arange(int(dur * SR)) / SR
    f = f0 + (f1 - f0) * (tt / dur)
    add(vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-8 * tt), at)

NT = {"G": 392.0, "A": 440.0, "B": 493.88, "D": 587.33, "E": 659.25, "G2": 783.99, "rest": 0}
mel = ["G", "B", "D", "B", "E", "D", "B", "rest", "A", "B", "A", "G", "E", "G", "A", "rest",
       "D", "E", "G2", "E", "D", "B", "D", "rest", "E", "D", "B", "A", "G", "A", "G", "rest"]
bass = [98.0, 130.81, 146.83, 98.0]   # G C D G
beat = 0.36; k = 0
while k * beat < TOTAL - 1.0:
    nn = mel[k % len(mel)]
    if nn != "rest": add(tone(NT[nn], 0.6, 0.04, "xylo", 7), k * beat)
    if k % 4 == 0: add(tone(bass[(k // 8) % 4], 1.4, 0.07, "bass", 2.2), k * beat)
    if k % 2 == 1: add(tone(2400, 0.05, 0.008, "sine", 60), k * beat)
    k += 1
for kk, f in enumerate([392, 494, 587, 784]):
    add(tone(f, 0.8, 0.12, "xylo", 5), 0.4 + kk * 0.2)
for ri, rd in enumerate(ROUNDS):
    base = R[ri]; n = rd["L"] + rd["Rn"]; m = min(rd["L"], rd["Rn"])
    for i in range(n): slide(base + POP0 + POPG * i + 0.1, 350, 750, 0.15, 0.1)
    for k2 in range(m): add(tone(880 + k2 * 110, 0.5, 0.1, "xylo", 7), base + match_t(k2) + 0.45)
    t_res = max(5.6, match_t(m) + 0.8)
    if rd["result"] == "MORE": seq = [523.25, 659.25, 783.99, 1046.5]
    elif rd["result"] == "LESS": seq = [1046.5, 783.99, 659.25, 523.25]
    else: seq = [659.25, 659.25, 783.99, 783.99]
    for i, f in enumerate(seq): add(tone(f, 0.9, 0.13, "xylo", 4), base + t_res + i * 0.14)
for i, f in enumerate([587.33, 783.99, 987.77, 1174.66]):
    add(tone(f, 1.2, 0.13, "xylo", 3), T_OUT + 0.1 + i * 0.18)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", round(TOTAL, 1))
