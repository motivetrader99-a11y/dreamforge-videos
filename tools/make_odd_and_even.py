"""Dreamforge Kids — Odd and even numbers.
Scene 1: a cosy laundry room. Four socks pop onto a clothesline, then slide together
into matching pairs — everyone has a partner, so four is EVEN.
Scene 2: five socks hang up; they pair up but one little yellow sock is left over — ODD.
Scene 3: a number chart 1-10 in two columns. Each number shows its dots in pairs.
Even numbers light up teal (all dots paired), then odd numbers light up orange
(one extra dot glows). Outro: two cards recap EVEN = pairs, ODD = one extra.
Captions in a top panel with Twinkle the star narrating on its left.
Original art and music (plucked string tune in G major, 4/4)."""
import math, random, subprocess, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/odd_and_even_numbers.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (55, 50, 85)
TEAL = (40, 175, 170)
ORANGE = (245, 140, 50)
random.seed(2468)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, S1LEN, S2LEN, S3LEN, OUTRO = 5.0, 10.5, 11.0, 15.0, 7.5
S1 = INTRO
S2 = S1 + S1LEN
S3 = S2 + S2LEN
T_OUT = S3 + S3LEN
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

HANG_T, HANG_GAP = 0.6, 0.45     # sock pop-in (scene-local)
PAIR_T, PAIR_D = 3.9, 1.1        # slide into pairs (scene-local)
EVEN_T = [S3 + 0.6 + k * 1.15 for k in range(5)]      # 2,4,6,8,10 light up
ODD_T = [S3 + 7.9 + k * 1.15 for k in range(5)]       # 1,3,5,7,9 light up

LINES = [
    (0.3, INTRO - 0.2, "Hi! I'm Twinkle! Let's learn odd and even!"),
    (S1 + 0.2, S1 + 4.6, "Four socks. Let's make pairs!"),
    (S1 + 4.8, S1 + S1LEN - 0.15, "Everyone has a partner! Four is even!"),
    (S2 + 0.2, S2 + 4.9, "Now five socks. Let's make pairs!"),
    (S2 + 5.1, S2 + S2LEN - 0.15, "One sock is left over. Five is odd!"),
    (S3 + 0.2, S3 + 7.4, "Even numbers: 2, 4, 6, 8, 10!"),
    (S3 + 7.6, S3 + S3LEN - 0.15, "Odd numbers: 1, 3, 5, 7, 9!"),
    (T_OUT + 0.3, TOTAL - 0.5, "Even makes pairs. Odd has one extra. Bye-bye!"),
]
TALK = [(a, a + min(b - a - 0.2, len(txt.split()) * 0.42 + 0.7)) for a, b, txt in LINES]
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

# ---------- Twinkle ----------
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

# ---------- socks ----------
def make_sock(body, accent, pattern, mood="happy"):
    """Sock hanging from its cuff (top). ~150 x 260, anchor = top centre."""
    sw, sh = 190, 280; im = Image.new("RGBA", (sw, sh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dark = tuple(max(0, v - 40) for v in body)
    # leg + foot shape (foot points right)
    leg = [(35, 30), (115, 30), (115, 175)]
    d.rounded_rectangle([35, 30, 115, 200], radius=14, fill=body)
    d.ellipse([35, 150, 180, 250], fill=body)
    d.rectangle([35, 150, 115, 200], fill=body)
    # toe & heel accent
    d.chord([120, 160, 182, 248], -90, 90, fill=accent)
    d.pieslice([30, 190, 90, 252], 90, 180, fill=accent)
    # pattern on leg
    if pattern == "stripes":
        for y in (78, 112, 146):
            d.rectangle([35, y, 115, y + 14], fill=accent)
    elif pattern == "dots":
        for (x, y) in [(55, 75), (95, 95), (60, 125), (100, 140), (75, 160)]:
            d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=accent)
    elif pattern == "hearts":
        for (x, y) in [(60, 85), (95, 125)]:
            d.ellipse([x - 11, y - 8, x + 1, y + 4], fill=accent); d.ellipse([x - 1, y - 8, x + 11, y + 4], fill=accent)
            d.polygon([(x - 11, y - 1), (x + 11, y - 1), (x, y + 13)], fill=accent)
    elif pattern == "zigzag":
        for y in (85, 130):
            pts = [(35 + k * 16, y + (0 if k % 2 == 0 else 14)) for k in range(6)]
            d.line(pts, fill=accent, width=9, joint="curve")
    elif pattern == "stars":
        for (x, y) in [(62, 90), (92, 138)]:
            d.polygon(star_poly(x, y, 16), fill=accent)
    # cuff
    d.rounded_rectangle([28, 18, 122, 50], radius=12, fill=dark)
    for x in range(40, 116, 14): d.line([(x, 22), (x, 46)], fill=body, width=4)
    # face on the foot
    fx, fy = 128, 198
    for dx in (-18, 18):
        d.ellipse([fx + dx - 9, fy - 12, fx + dx + 9, fy + 8], fill=(55, 45, 70))
        d.ellipse([fx + dx - 5, fy - 9, fx + dx, fy - 3], fill=(255, 255, 255))
    if mood == "happy":
        d.arc([fx - 14, fy + 2, fx + 14, fy + 24], 20, 160, fill=(55, 45, 70), width=5)
    else:  # curious little "o"
        d.ellipse([fx - 7, fy + 8, fx + 7, fy + 22], fill=(150, 60, 70))
    for dx in (-30, 30):
        d.ellipse([fx + dx - 9, fy + 5, fx + dx + 9, fy + 15], fill=(255, 140, 160, 160))
    return im

PEG = Image.new("RGBA", (40, 70), (0, 0, 0, 0))
_pd = ImageDraw.Draw(PEG)
_pd.rounded_rectangle([10, 0, 30, 66], radius=8, fill=(205, 160, 110)); _pd.rectangle([18, 4, 22, 62], fill=(170, 125, 80))
_pd.ellipse([14, 28, 26, 40], fill=(150, 150, 165))

SOCKS1 = [((250, 150, 190), (255, 230, 240), "stripes"), ((250, 150, 190), (255, 230, 240), "stripes"),
          ((110, 175, 240), (225, 240, 255), "dots"), ((110, 175, 240), (225, 240, 255), "dots")]
SOCKS2 = [((120, 200, 140), (230, 250, 225), "zigzag"), ((120, 200, 140), (230, 250, 225), "zigzag"),
          ((175, 140, 230), (240, 230, 255), "hearts"), ((175, 140, 230), (240, 230, 255), "hearts"),
          ((255, 200, 70), (255, 245, 200), "stars")]
SP1 = [make_sock(b, a, p) for b, a, p in SOCKS1]
SP2 = [make_sock(b, a, p) for b, a, p in SOCKS2]
LONE_CURIOUS = make_sock(*SOCKS2[4], mood="curious")

def line_y(x):  # clothesline with gentle sag
    u = (x - 480) / 440
    return 640 + 55 * (1 - u * u)

def spread_x(n):
    return [130 + (830 - 130) * k / (n - 1) for k in range(n)]

def sock_scale(n): return 1.0 if n <= 4 else 0.78

def paired_x(n):
    pairs = n // 2; extra = n % 2; sc = sock_scale(n)
    centers = [255, 705] if n == 4 else [175, 455, 750]
    xs = []
    for g in range(pairs):
        xs += [centers[g] - 62 * sc, centers[g] + 62 * sc]
    if extra: xs.append(centers[-1] - 10)
    return xs, centers

# ---------- backgrounds ----------
def room_bg():
    im = vgrad(W, H, (210, 240, 232), (240, 250, 240)); d = ImageDraw.Draw(im)
    for y in range(80, 1460, 120):          # little wallpaper flowers
        for x in range(60 + (y // 120 % 2) * 60, W, 120):
            for a in range(5):
                ang = a * 2 * math.pi / 5
                d.ellipse([x + 9 * math.cos(ang) - 6, y + 9 * math.sin(ang) - 6, x + 9 * math.cos(ang) + 6, y + 9 * math.sin(ang) + 6], fill=(190, 228, 218))
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(250, 235, 200))
    # window with soft sky
    d.rounded_rectangle([600, 380, 900, 560], radius=20, fill=(250, 245, 235))
    d.rounded_rectangle([615, 395, 885, 545], radius=12, fill=(185, 220, 250))
    d.ellipse([800, 410, 860, 470], fill=(255, 235, 150))
    for cx, cy in [(680, 480), (760, 500)]:
        for dx, dy, rr in [(-22, 4, 18), (0, -6, 24), (22, 4, 18)]:
            d.ellipse([cx + dx - rr, cy + dy - rr, cx + dx + rr, cy + dy + rr], fill=(255, 255, 255))
    d.line([(750, 395), (750, 545)], fill=(250, 245, 235), width=10)
    # floor
    d.rectangle([0, 1460, W, H], fill=(225, 190, 150))
    for y in range(1490, H, 60): d.line([(0, y), (W, y)], fill=(205, 168, 128), width=4)
    d.rectangle([0, 1450, W, 1470], fill=(245, 230, 210))
    # laundry basket bottom-left (decor, kept above bottom 350)
    d.rounded_rectangle([60, 1330, 330, 1540], radius=30, fill=(215, 175, 120))
    for x in range(85, 320, 30): d.line([(x, 1345), (x, 1530)], fill=(190, 150, 100), width=6)
    d.rounded_rectangle([50, 1310, 340, 1350], radius=18, fill=(200, 160, 105))
    # poles + line
    for x in (40, 920):
        d.rounded_rectangle([x - 12, 600, x + 12, 1460], radius=10, fill=(180, 140, 100))
        d.ellipse([x - 20, 585, x + 20, 625], fill=(200, 160, 115))
    pts = [(x, line_y(x)) for x in range(40, 921, 10)]
    d.line(pts, fill=(140, 120, 130), width=6)
    return im

def chart_bg():
    im = vgrad(W, H, (232, 228, 255), (255, 240, 235)); d = ImageDraw.Draw(im)
    for k in range(40):
        x = random.randint(20, 1060); y = random.randint(380, 1560); r = random.randint(4, 10)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 120))
    d.rectangle([0, 1600, W, H], fill=(225, 215, 245))
    return im

def outro_bg():
    im = vgrad(W, H, (255, 236, 222), (226, 240, 255)); d = ImageDraw.Draw(im)
    for k in range(30):
        x = random.randint(30, 1050); y = random.randint(380, 1560)
        d.polygon(star_poly(x, y, random.randint(6, 13)), fill=(255, 250, 235))
    return im

BG_ROOM = room_bg()
BG_CHART = chart_bg()
BG_OUT = outro_bg()
TWK = [make_twinkle(80, False), make_twinkle(80, True)]
TWK_BIG = [make_twinkle(170, False), make_twinkle(170, True)]

# ---------- drawing bits ----------
def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, inner=0.35), fill=(255, 245, 170, int(255 * a)))

def badge(im, txt, cx, cy, col, s):
    if s <= 0.02: return
    bw, bh = 470, 150
    b = Image.new("RGBA", (bw + 20, bh + 20), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
    bd.rounded_rectangle([10, 14, bw + 10, bh + 14], radius=60, fill=tuple(max(0, v - 50) for v in col))
    bd.rounded_rectangle([10, 6, bw + 10, bh + 6], radius=60, fill=col)
    f = font(92); w = bd.textlength(txt, font=f)
    bd.text(((bw + 20 - w) / 2, 22), txt, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=tuple(max(0, v - 70) for v in col))
    paste(im, b, cx, cy, s)

def pair_loop(d, x0, x1, y0, y1, col, a):
    d.rounded_rectangle([x0, y0, x1, y1], radius=50, outline=col + (int(255 * a),), width=8)

def heart(d, x, y, r, col):
    d.ellipse([x - r, y - r * 0.8, x, y + r * 0.2], fill=col); d.ellipse([x, y - r * 0.8, x + r, y + r * 0.2], fill=col)
    d.polygon([(x - r * 0.98, y - r * 0.2), (x + r * 0.98, y - r * 0.2), (x, y + r * 0.95)], fill=col)

def draw_socks(im, lt, t, sprites, n, show_lonely):
    d = ImageDraw.Draw(im)
    xs0 = spread_x(n); xs1, centers = paired_x(n)
    k_move = ease((lt - PAIR_T) / PAIR_D)
    for i in range(n):
        s = pop((lt - HANG_T - i * HANG_GAP) / 0.45)
        if s <= 0: continue
        x = xs0[i] + (xs1[i] - xs0[i]) * k_move
        y = line_y(x)
        sway = math.sin(t * 2.2 + i) * 4
        if 0 < lt - PAIR_T < PAIR_D: sway += math.sin((lt - PAIR_T) * 9) * 6
        lonely = show_lonely and i == n - 1 and n % 2 == 1
        sp = sprites[i]
        if lonely and lt > PAIR_T + PAIR_D + 0.3: sp = LONE_CURIOUS
        hop = 0
        if not lonely and lt > PAIR_T + PAIR_D + 0.2:
            hop = -abs(math.sin((lt - PAIR_T) * 4 + (i // 2) * 0.8)) * 12
        if lonely and lt > PAIR_T + PAIR_D + 0.3:
            sway += math.sin(t * 5) * 7
        # sprite anchored at cuff (top): sprite centre is ~140px below the line
        sc = sock_scale(n)
        paste(im, sp, x + 28 * sc, y + 140 * sc * s + hop, s * sc, sway)
        paste(im, PEG, x, y + 10, s * sc)
    d = ImageDraw.Draw(im)
    # pair loops + hearts after pairing
    a = ease((lt - PAIR_T - PAIR_D) / 0.5)
    if a > 0:
        for g in range(n // 2):
            cx = centers[g]
            sc = sock_scale(n)
            pair_loop(d, cx - 145 * sc, cx + 165 * sc, line_y(cx) - 10, line_y(cx) + 300 * sc, TEAL, a)
            hs = pop((lt - PAIR_T - PAIR_D - g * 0.25) / 0.5)
            if hs > 0: heart(d, cx + 10, line_y(cx) + 300 * sc + 40, 26 * hs, (245, 110, 150))
        if n % 2 == 1:
            cx = xs1[-1]
            for k in range(24):    # dotted orange ring around the lone sock
                ang = k * 2 * math.pi / 24 + t * 0.6
                sc = sock_scale(n)
                px = cx + 28 * sc + 120 * sc * math.cos(ang); py = line_y(cx) + 150 * sc + 175 * sc * math.sin(ang)
                d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=ORANGE + (int(255 * a),))

def number_card(im, n, s, col):
    if s <= 0.02: return
    c = Image.new("RGBA", (260, 260), (0, 0, 0, 0)); cd = ImageDraw.Draw(c)
    cd.ellipse([10, 16, 250, 256], fill=tuple(max(0, v - 40) for v in col))
    cd.ellipse([10, 8, 250, 248], fill=(255, 255, 255))
    cd.ellipse([24, 22, 236, 234], outline=col, width=10)
    f = font(150); w = cd.textlength(str(n), font=f)
    cd.text(((260 - w) / 2, 22), str(n), font=f, fill=INK)
    paste(im, c, 480, 1170, s)

def draw_scene_socks(im, lt, t, sprites, n, word, col):
    draw_socks(im, lt, t, sprites, n, show_lonely=(n % 2 == 1))
    d = ImageDraw.Draw(im)
    # number card appears once all socks are hung
    all_hung = HANG_T + (n - 1) * HANG_GAP + 0.4
    number_card(im, n, pop((lt - all_hung) / 0.5), col if lt > PAIR_T + PAIR_D else (180, 175, 210))
    bs = pop((lt - PAIR_T - PAIR_D - 0.6) / 0.5)
    badge(im, word, 480, 1400, col, bs)
    d = ImageDraw.Draw(im)
    if n % 2 == 1 and lt > PAIR_T + PAIR_D + 0.6:
        a = min(1, (lt - PAIR_T - PAIR_D - 0.6) / 0.4)
        xs1, _ = paired_x(n); x = xs1[-1] + 28
        tf = font(48); txt = "1 left over!"
        tw = d.textlength(txt, font=tf); tx = min(max(x - tw / 2, 60), 910 - tw)
        d.rounded_rectangle([tx - 20, 1005, tx + tw + 20, 1080], radius=30, fill=(255, 245, 225, int(255 * a)), outline=ORANGE + (int(255 * a),), width=5)
        d.text((tx, 1010), txt, font=tf, fill=ORANGE + (int(255 * a),))
    for k in range(6):   # sparkles when the badge appears
        if 0 < bs < 1:
            ang = k * math.pi / 3 + lt
            sparkle(d, 480 + 300 * math.cos(ang), 1400 + 110 * math.sin(ang), 22, 1 - abs(bs - 0.5))

# number chart
ROW_Y = [585 + k * 205 for k in range(5)]
COL_X = {0: 270, 1: 690}       # odd column left, even column right
def tile(im, n, lit, extra_glow, t):
    odd = n % 2 == 1
    cx = COL_X[0 if odd else 1]; cy = ROW_Y[(n - 1) // 2]
    col = ORANGE if odd else TEAL
    s = 1 + 0.12 * math.sin(min(1, lit) * math.pi) if 0 < lit < 1 else 1
    tw, th = 380, 180
    tl = Image.new("RGBA", (tw + 10, th + 14), (0, 0, 0, 0)); td = ImageDraw.Draw(tl)
    base = col if lit > 0 else (205, 200, 225)
    td.rounded_rectangle([5, 12, tw + 5, th + 12], radius=36, fill=tuple(max(0, v - 45) for v in base))
    td.rounded_rectangle([5, 4, tw + 5, th + 4], radius=36, fill=(255, 255, 255) if lit > 0 else (245, 243, 252))
    td.rounded_rectangle([5, 4, tw + 5, th + 4], radius=36, outline=base, width=8)
    f = font(110); num = str(n); nw = td.textlength(num, font=f)
    td.text((80 - nw / 2, 18), num, font=f, fill=INK if lit > 0 else (165, 160, 190))
    # dots in pairs: columns of 2
    pairs, extra = n // 2, n % 2
    x0 = 170; dx = 40
    for p in range(pairs):
        for r in range(2):
            x = x0 + p * dx; y = 64 + r * 50
            td.ellipse([x - 15, y - 15, x + 15, y + 15], fill=col if lit > 0 else (200, 196, 220))
    if extra:
        x = x0 + pairs * dx; y = 64
        g = extra_glow
        rr = 15 + 5 * g
        td.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 190, 60) if lit > 0 else (200, 196, 220))
        if lit > 0:
            td.ellipse([x - 22, y + 30, x + 22, y + 66], outline=(255, 190, 60), width=0)
    paste(im, tl, cx, cy, s)

def draw_chart(im, lt, t):
    d = ImageDraw.Draw(im)
    ha = ease((t - ODD_T[0] + 0.4) / 0.5); he = ease((t - EVEN_T[0] + 0.4) / 0.5)
    text_c(d, "ODD", COL_X[0], 352, 74, (255, 255, 255) if ha > 0 else (225, 220, 240), stroke=ORANGE if ha > 0 else (190, 185, 215))
    text_c(d, "EVEN", COL_X[1], 352, 74, (255, 255, 255) if he > 0 else (225, 220, 240), stroke=TEAL if he > 0 else (190, 185, 215))
    for k in range(5):
        e = 2 * (k + 1); o = 2 * k + 1
        tile(im, e, max(0, (t - EVEN_T[k]) / 0.5), 0, t)
        lo = max(0, (t - ODD_T[k]) / 0.5)
        tile(im, o, lo, abs(math.sin(t * 5)) if lo > 0 else 0, t)
    d = ImageDraw.Draw(im)
    for k in range(5):
        for times, col, xc in [(EVEN_T, TEAL, COL_X[1]), (ODD_T, ORANGE, COL_X[0])]:
            lt2 = t - times[k]
            if 0 < lt2 < 0.7:
                a = 1 - lt2 / 0.7
                for j in range(5):
                    ang = j * 2 * math.pi / 5 + lt2 * 3
                    sparkle(d, xc + 220 * math.cos(ang) * (0.6 + lt2), ROW_Y[k] + 100 * math.sin(ang) * (0.6 + lt2), 16, a)

def draw_outro(im, lt, t):
    d = ImageDraw.Draw(im)
    for k, (word, col, sprites, n, cx) in enumerate([("EVEN", TEAL, SP1, 4, 270), ("ODD", ORANGE, SP2, 5, 690)]):
        s = pop((lt - 0.3 - k * 0.5) / 0.5)
        if s <= 0: continue
        cw, ch = 400, 470
        cd_im = Image.new("RGBA", (cw + 10, ch + 14), (0, 0, 0, 0)); cd = ImageDraw.Draw(cd_im)
        cd.rounded_rectangle([5, 12, cw + 5, ch + 12], radius=40, fill=tuple(max(0, v - 45) for v in col))
        cd.rounded_rectangle([5, 4, cw + 5, ch + 4], radius=40, fill=(255, 255, 255))
        cd.rounded_rectangle([5, 4, cw + 5, ch + 4], radius=40, outline=col, width=9)
        f = font(76); w = cd.textlength(word, font=f)
        cd.text(((cw + 10 - w) / 2, 24), word, font=f, fill=col)
        # mini socks
        small = [sp.resize((76, 112), Image.BILINEAR) for sp in sprites]
        positions = [(70, 150), (140, 150), (240, 150), (310, 150)] if n == 4 else \
                    [(70, 150), (140, 150), (240, 150), (310, 150), (190, 290)]
        for i, (px, py) in enumerate(positions):
            cd_im.alpha_composite(small[i], (int(px - 30), int(py)))
        if n == 4:
            for gx in (105, 275): cd.rounded_rectangle([gx - 80, 140, gx + 85, 275], radius=30, outline=TEAL, width=5)
            sub = "pairs!"
        else:
            for gx in (105, 275): cd.rounded_rectangle([gx - 80, 140, gx + 85, 275], radius=30, outline=TEAL, width=5)
            cd.ellipse([140, 280, 260, 415], outline=ORANGE, width=6)
            sub = "+1"
        f2 = font(54); w2 = cd.textlength(sub, font=f2)
        if n == 4: cd.text(((cw + 10 - w2) / 2, 320), sub, font=f2, fill=INK)
        else: cd.text((300, 320), sub, font=f2, fill=ORANGE)
        paste(im, cd_im, cx, 760 + math.sin(t * 2 + k) * 6, s)
    mo = talking(t) and int(t * 8) % 2 == 0
    tk = talking(t)
    bob = math.sin(t * 3) * 12 - (abs(math.sin(t * 10)) * 14 if tk else 0)
    paste(im, TWK_BIG[mo], 480, 1260 + bob, pop((lt - 1.2) / 0.6), math.sin(t * 2.5) * 8)
    d = ImageDraw.Draw(im)
    if lt > 2.0:
        for j in range(8):
            ang = j * math.pi / 4 + lt * 0.8
            sparkle(d, 480 + 260 * math.cos(ang), 1260 + 200 * math.sin(ang), 18, 0.5 + 0.5 * math.sin(lt * 3 + j))

# ---------- caption panel (Twinkle sits on the left of it) ----------
def wrap(d, txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw: cur = trial
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def draw_caption(im, t, show_twinkle=True):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([40, 96, 925, 336], radius=48, fill=(255, 253, 248), outline=(240, 170, 120), width=8)
    cx_txt = 575 if show_twinkle else 482
    maxw = 640 if show_twinkle else 800
    for a, b, txt in LINES:
        if a <= t < b:
            al = min(1, (t - a) / 0.25, (b - t) / 0.25)
            sz = 64; lines = wrap(d, txt, sz, maxw)
            while len(lines) > 2: sz -= 4; lines = wrap(d, txt, sz, maxw)
            lh = sz * 1.2; y0 = 216 - lh * len(lines) / 2 - 8
            for k, ln in enumerate(lines):
                f = font(sz); w = d.textlength(ln, font=f)
                d.text((cx_txt - w / 2, y0 + k * lh), ln, font=f, fill=INK + (int(255 * al),))
            break
    if show_twinkle:
        tk = talking(t); mo = tk and int(t * 8) % 2 == 0
        bob = math.sin(t * 3) * 6 + (abs(math.sin(t * 11)) * -10 if tk else 0)
        paste(im, TWK[mo], 158, 216 + bob, 1.0, math.sin(t * 2) * 5)

def frame(t):
    if t < INTRO:
        im = BG_CHART.copy(); d = ImageDraw.Draw(im)
        mo = talking(t) and int(t * 8) % 2 == 0
        paste(im, TWK_BIG[mo], 480, 1050 + math.sin(t * 3) * 14 - (abs(math.sin(t * 10)) * 12 if talking(t) else 0),
              pop(t / 0.8), math.sin(t * 2) * 6)
        d = ImageDraw.Draw(im)
        s1 = pop((t - 1.0) / 0.5); s2 = pop((t - 1.6) / 0.5); s3 = pop((t - 2.2) / 0.5)
        if s1 > 0: text_c(d, "ODD", 480, 470 + (1 - s1) * 30, 130 * max(s1, 0.05), (255, 255, 255), stroke=ORANGE, sw=10)
        if s2 > 0: text_c(d, "&", 480, 620, 80 * max(s2, 0.05), INK, stroke=(255, 255, 255), sw=6)
        if s3 > 0: text_c(d, "EVEN", 480, 720 + (1 - s3) * 30, 130 * max(s3, 0.05), (255, 255, 255), stroke=TEAL, sw=10)
        # little dot pairs dancing below Twinkle
        for k in range(5):
            a = pop((t - 2.6 - k * 0.15) / 0.4)
            if a > 0:
                x = 260 + k * 110; y = 1330 + math.sin(t * 4 + k) * 10
                col = TEAL if k < 4 else ORANGE
                rows = 2 if k < 4 else 1
                for r in range(rows):
                    d.ellipse([x - 20 * a, y + r * 54 - 20 * a, x + 20 * a, y + r * 54 + 20 * a], fill=col)
        draw_caption(im, t, show_twinkle=False)
    elif t < S2:
        im = BG_ROOM.copy(); draw_scene_socks(im, t - S1, t, SP1, 4, "EVEN", TEAL)
        draw_caption(im, t)
    elif t < S3:
        im = BG_ROOM.copy(); draw_scene_socks(im, t - S2, t, SP2, 5, "ODD", ORANGE)
        draw_caption(im, t)
    elif t < T_OUT:
        im = BG_CHART.copy(); draw_chart(im, t - S3, t)
        draw_caption(im, t)
    else:
        im = BG_OUT.copy(); draw_outro(im, t - T_OUT, t)
        draw_caption(im, t, show_twinkle=False)
    for edge, col in [(S1, (240, 250, 245, 255)), (S2, (240, 250, 245, 255)), (S3, (240, 236, 255, 255)), (T_OUT, (255, 240, 230, 255))]:
        if abs(t - edge) < 0.25:
            k = abs(t - edge) / 0.25
            im = Image.blend(Image.new("RGBA", (W, H), col), im, k)
    if t < 0.4 or t > TOTAL - 0.6:
        k = min(t / 0.4, (TOTAL - t) / 0.6)
        im = Image.blend(Image.new("RGBA", (W, H), (255, 236, 222, 255)), im, max(0, min(1, k)))
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

    # ---------- audio: original plucked-string tune in G major (4/4) ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    rng = np.random.RandomState(5)
    def pluck(freq, dur, vol=0.2):
        n = int(dur * SR); period = max(2, int(SR / freq))
        buf = rng.uniform(-1, 1, period); out = np.zeros(n)
        for i in range(n):
            out[i] = buf[i % period]
            buf[i % period] = 0.996 * 0.5 * (buf[i % period] + buf[(i + 1) % period])
        return vol * out * np.minimum(1, np.arange(n) / 200)
    cache = {}
    def pl(freq, dur, vol):
        key = (round(freq, 2), dur)
        if key not in cache: cache[key] = pluck(freq, dur, 1.0)
        return cache[key] * vol
    def bell(freq, dur, vol=0.1, decay=5):
        tt = np.arange(int(dur * SR)) / SR
        return vol * (np.sin(2 * np.pi * freq * tt) + 0.3 * np.sin(2 * np.pi * freq * 2.76 * tt) * np.exp(-8 * tt)) * np.exp(-decay * tt) * np.minimum(1, tt * 400)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N and j > i: audio[i:j] += sig[:j - i]
    NT = {"G2": 98.0, "C3": 130.81, "D3": 146.83, "E3": 164.81, "G3": 196.0, "B3": 246.94, "C4": 261.63, "D4": 293.66,
          "E4": 329.63, "F#4": 369.99, "G4": 392.0, "A4": 440.0, "B4": 493.88, "D5": 587.33}
    bass = ["G2", "E3", "C3", "D3"]
    chord = [["G3", "B3", "D4"], ["E3", "G3", "B3"], ["C4", "E4", "G3"], ["D4", "F#4", "A4"]]
    mel = ["B4", None, "D5", "B4", "A4", None, "G4", None, "E4", "G4", "A4", None, "B4", "A4", "G4", None,
           "C4", "E4", "G4", "E4", "A4", None, "B4", None, "A4", "F#4", "D4", "F#4", "G4", None, None, None]
    beat = 0.6 / 2; k = 0     # eighth notes at 100 bpm
    while k * beat < TOTAL - 1:
        bar = (k // 8) % 4
        if k % 8 == 0: add(pl(NT[bass[bar]] * 2, 1.2, 0.10), k * beat)
        if k % 2 == 1:
            add(pl(NT[chord[bar][(k // 2) % 3]], 0.6, 0.03), k * beat)
        m = mel[k % 32]
        if m: add(pl(NT[m], 0.8, 0.055), k * beat)
        k += 1
    # sound effects
    for base, n in [(S1, 4), (S2, 5)]:
        for i in range(n): add(bell(880 * 2 ** (i / 12 * 2), 0.3, 0.06, 12), base + HANG_T + i * HANG_GAP)   # sock pop
        tt = np.arange(int(PAIR_D * SR)) / SR; fr = 500 + 500 * tt / PAIR_D                                   # soft slide
        add(0.03 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.sin(np.pi * tt / PAIR_D), base + PAIR_T)
    for j, f_ in enumerate([587.33, 739.99, 880, 1174.66]): add(bell(f_, 1.0, 0.09, 3), S1 + PAIR_T + PAIR_D + 0.6 + j * 0.12)  # even chime
    for j, f_ in enumerate([659.25, 587.33, 783.99]): add(bell(f_, 0.5, 0.08, 6), S2 + PAIR_T + PAIR_D + 0.6 + j * 0.22)    # curious odd "boop-boop-bing"
    for k2 in range(5):
        add(bell(784 * 2 ** (k2 / 12 * 2), 0.5, 0.06, 7), EVEN_T[k2])
        add(bell(659 * 2 ** (k2 / 12 * 2), 0.5, 0.06, 7), ODD_T[k2])
    for j, f_ in enumerate([587.33, 783.99, 987.77, 1174.66]): add(bell(f_, 1.3, 0.09, 2.5), T_OUT + 2.0 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
