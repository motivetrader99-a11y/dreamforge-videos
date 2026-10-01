"""Light and dark colors -- Dreamforge Kids lesson Short (Twinkle narrates)."""
import math, random, subprocess, wave
import numpy as np
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/light_and_dark_colors.mp4"
TMPV, TMPA = "/tmp/_ld_v.mp4", "/tmp/_ld_a.wav"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
random.seed(33)
CXC = 495                      # content centre x (keeps away from right Shorts UI)
INK = (55, 40, 85)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

def mix(a, b, k):
    k = max(0.0, min(1.0, k))
    return tuple(int(a[i] * (1 - k) + b[i] * k) for i in range(3))

WHITE, BLACK = (255, 255, 255), (25, 20, 45)
BLUE, GREEN, PINK = (60, 120, 220), (70, 170, 80), (235, 90, 150)

# ---------- script / timeline ----------
LINES = [
    (0.0, 5.0, "Hi friends! I'm Twinkle. Let's learn light and dark colors!"),
    (5.0, 12.0, "Add white paint... and blue gets lighter. Light blue, like the sky!"),
    (12.0, 19.0, "Add black paint... and blue gets darker. Dark blue, like the night!"),
    (19.0, 26.0, "Green can be light... or dark. Light, lighter... dark, darker!"),
    (26.0, 33.0, "The sunny side is light. The shadow side is dark."),
    (33.0, 40.0, "This balloon is light pink. This balloon is dark pink!"),
    (40.0, 46.0, "Great job! Find something light and something dark today!"),
]
TOTAL = 46.0
NFR = int(TOTAL * FPS)

# ---------- art helpers ----------
def vgrad(top, bot):
    g = np.linspace(0, 1, H)[:, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(arr[:, None, :], W, axis=1)).convert("RGBA")

def base_bg():
    bg = vgrad((255, 244, 228), (250, 225, 235))
    d = ImageDraw.Draw(bg)
    # soft polka dots
    for _ in range(40):
        x, y, r = random.randint(0, W), random.randint(0, 1550), random.randint(8, 20)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, 255))
    # table / floor
    d.rounded_rectangle([-40, 1500, W + 40, H + 40], 60, fill=(235, 200, 170))
    d.rectangle([-40, 1540, W + 40, H], fill=(225, 188, 158))
    return bg

BG = base_bg()

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def draw_twinkle(im, cx, cy, r, talk, blink=False):
    s = int(r * 2.8); sp = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(gl).polygon(star_poly(s / 2, s / 2, r * 1.1), fill=(255, 220, 90, 120))
    sp.alpha_composite(gl.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(sp)
    d.polygon(star_poly(s / 2, s / 2 + r * 0.05, r), fill=(225, 165, 40))
    d.polygon(star_poly(s / 2, s / 2, r), fill=(255, 210, 70))
    c, e = s / 2, r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        if blink:
            d.arc([c + dx - e, c - e, c + dx + e, c + e], 200, 340, fill=INK, width=max(3, int(r * 0.05)))
        else:
            d.ellipse([c + dx - e, c - e * 1.4, c + dx + e, c + e * 1.2], fill=INK)
            d.ellipse([c + dx - e * 0.5, c - e * 1.1, c + dx + e * 0.1, c - e * 0.4], fill=WHITE)
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([c + dx - r * 0.1, c + r * 0.12, c + dx + r * 0.1, c + r * 0.24], fill=(255, 130, 150))
    if talk:
        d.ellipse([c - r * 0.1, c + r * 0.12, c + r * 0.1, c + r * 0.34], fill=(150, 50, 70))
        d.ellipse([c - r * 0.06, c + r * 0.24, c + r * 0.06, c + r * 0.33], fill=(255, 140, 150))
    else:
        d.arc([c - r * 0.15, c + r * 0.05, c + r * 0.15, c + r * 0.27], 20, 160, fill=INK, width=max(3, int(r * 0.05)))
    im.alpha_composite(sp, (int(cx - s / 2), int(cy - s / 2)))

def pop(x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return (x / 0.35) * 1.15 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.18 * (1 - x)

def text_c(d, txt, cx, y, sz, fill, stroke=INK, sw=8, alpha=255):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill + (alpha,), stroke_width=sw, stroke_fill=stroke + (alpha,))

def wrap(txt, sz, maxw):
    f = font(sz); words, lines, cur = txt.split(), [], ""
    dd = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for w in words:
        t = (cur + " " + w).strip()
        if dd.textlength(t, font=f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def caption(im, txt, lt):
    a = min(1.0, lt / 0.35)
    sz = 62; lines = wrap(txt, sz, 760)
    while len(lines) > 3: sz -= 4; lines = wrap(txt, sz, 760)
    lh = sz * 1.3; bh = lh * len(lines) + 50
    y0 = 1545 - bh                       # bottom of box at 1545 (> 350px from bottom)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([CXC - 410, y0, CXC + 410, y0 + bh], 40, fill=(255, 255, 255, int(235 * a)),
                        outline=(200, 150, 220, int(255 * a)), width=6)
    for i, ln in enumerate(lines):
        text_c(d, ln, CXC, y0 + 22 + i * lh, sz, (80, 55, 130), stroke=WHITE, sw=3, alpha=int(255 * a))
    im.alpha_composite(ov)

# bowl of paint
def draw_bowl(d, cx, cy, col, swirl_t=None):
    d.ellipse([cx - 230, cy - 60, cx + 230, cy + 60], fill=(250, 250, 255))
    d.pieslice([cx - 230, cy - 230, cx + 230, cy + 230], 0, 180, fill=(170, 200, 235))
    d.pieslice([cx - 200, cy - 190, cx + 200, cy + 190], 15, 100, fill=(200, 222, 245))
    d.ellipse([cx - 205, cy - 48, cx + 205, cy + 48], fill=col)
    if swirl_t is not None:
        for k in range(3):
            a0 = swirl_t * 200 + k * 120
            d.arc([cx - 140 + k * 30, cy - 30 + k * 6, cx + 140 - k * 30, cy + 30 - k * 6], a0, a0 + 80,
                  fill=mix(col, WHITE, 0.35), width=6)
    d.ellipse([cx - 230, cy - 60, cx + 230, cy + 60], outline=(140, 170, 210), width=8)

def draw_tube(d, cx, cy, col, label_col):
    d.rounded_rectangle([cx - 55, cy - 120, cx + 55, cy + 60], 22, fill=(245, 245, 250), outline=INK, width=5)
    d.rectangle([cx - 55, cy - 40, cx + 55, cy + 10], fill=col)
    d.polygon([(cx - 30, cy + 60), (cx + 30, cy + 60), (cx + 18, cy + 100), (cx - 18, cy + 100)],
              fill=(200, 200, 210), outline=INK)
    d.rectangle([cx - 22, cy + 100, cx + 22, cy + 130], fill=label_col, outline=INK, width=4)

def cloud(d, cx, cy, s, col):
    for dx, dy, r in [(-1, 0.2, 0.55), (0, -0.2, 0.75), (1, 0.15, 0.6), (0.5, 0.3, 0.55), (-0.5, 0.3, 0.55)]:
        d.ellipse([cx + dx * s - r * s, cy + dy * s - r * s, cx + dx * s + r * s, cy + dy * s + r * s], fill=col)

def scene_white(im, lt, dark_mode):
    """Bowl of blue; drops of white (or black) fall in and change it."""
    d = ImageDraw.Draw(im)
    drop_col = WHITE if not dark_mode else BLACK
    target = WHITE if not dark_mode else BLACK
    drops = [1.0, 1.9, 2.8]
    k = sum(0.17 for t0 in drops if lt > t0 + 0.55)
    col = mix(BLUE, target, k)
    # header
    hdr = "+ WHITE = LIGHTER" if not dark_mode else "+ BLACK = DARKER"
    if lt > 0.3:
        s = pop((lt - 0.3) / 0.6)
        if not dark_mode: text_c(d, hdr, CXC, 400 - 20 * s, 76 * max(s, 0.1), WHITE, stroke=(70, 110, 190), sw=5)
        else: text_c(d, hdr, CXC, 400 - 20 * s, 76 * max(s, 0.1), (35, 30, 70), stroke=WHITE, sw=5)
    # tube tilting above the bowl
    draw_tube(d, CXC - 210, 610, drop_col, drop_col)
    for t0 in drops:
        p = (lt - t0) / 0.55
        if 0 <= p <= 1:
            y = 760 + p * 90
            d.ellipse([CXC - 210 + p * 200 - 22, y - 30, CXC - 210 + p * 200 + 22, y + 22], fill=drop_col,
                      outline=(150, 150, 170), width=3)
    draw_bowl(d, CXC, 860, col, swirl_t=lt if lt > 1.5 and lt < 4.2 else None)
    # result card
    if lt > 4.0:
        s = pop((lt - 4.0) / 0.6)
        cw, ch = 330 * s, 230 * s
        cx, cy = CXC + 220, 640
        if not dark_mode:
            d.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2], 30, fill=(175, 215, 250),
                                outline=WHITE, width=8)
            if s > 0.5:
                cloud(d, cx - 20, cy + 10, 55 * s, WHITE)
                d.ellipse([cx + 70 * s, cy - 85 * s, cx + 130 * s, cy - 25 * s], fill=(255, 220, 90))
        else:
            d.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2], 30, fill=(30, 45, 105),
                                outline=WHITE, width=8)
            if s > 0.5:
                m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
                md.ellipse([cx - 50, cy - 60, cx + 50, cy + 40], fill=255)
                md.ellipse([cx - 20, cy - 80, cx + 80, cy + 20], fill=0)
                im.paste((255, 240, 180), mask=m); d = ImageDraw.Draw(im)
                for sx, sy in [(-110, -70), (100, 60), (-90, 70), (110, -60)]:
                    d.polygon(star_poly(cx + sx * s, cy + sy * s, 16), fill=(255, 240, 160))
        if lt > 4.5:
            lbl = "LIGHT BLUE" if not dark_mode else "DARK BLUE"
            text_c(d, lbl, CXC, 1110, 84, col, stroke=WHITE if dark_mode else INK, sw=8)

LEAF = None
def leaf_sprite(col):
    s = 220; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([30, 50, 190, 170], fill=col)
    d.line([(40, 150), (180, 70)], fill=mix(col, BLACK, 0.3), width=6)
    for k in range(1, 4):
        x = 40 + k * 35; y = 150 - k * 20
        d.line([(x, y), (x + 15, y - 35)], fill=mix(col, BLACK, 0.3), width=4)
        d.line([(x, y), (x + 30, y + 10)], fill=mix(col, BLACK, 0.3), width=4)
    return im.rotate(20, resample=Image.BICUBIC)

SHADES = [mix(GREEN, WHITE, 0.6), mix(GREEN, WHITE, 0.3), GREEN, mix(GREEN, BLACK, 0.3), mix(GREEN, BLACK, 0.55)]
LEAVES = [leaf_sprite(c) for c in SHADES]

def scene_ladder(im, lt, t):
    d = ImageDraw.Draw(im)
    if lt > 0.2:
        text_c(d, "Light  ...  Dark", CXC, 420, 84, (110, 190, 110), sw=5)
    xs = [135 + i * 180 for i in range(5)]
    times = [0.8, 1.6, 2.6, 3.6, 4.5]
    for i, (x, t0) in enumerate(zip(xs, times)):
        s = pop((lt - t0) / 0.5)
        if s <= 0: continue
        bob = math.sin(t * 2.5 + i) * 10
        sp = LEAVES[i].resize((int(200 * s) + 1, int(200 * s) + 1), Image.BILINEAR)
        im.alpha_composite(sp, (int(x - sp.width / 2), int(740 + bob - sp.height / 2)))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x - 70, 880, x + 70, 1020], 24, fill=SHADES[i] + (255,), outline=WHITE, width=6)
    # arrow under swatches
    if lt > 5.0:
        p = min(1, (lt - 5.0) / 1.0)
        x1 = 120 + p * 740
        d.line([(120, 1080), (x1, 1080)], fill=(120, 110, 150), width=12)
        if p >= 1:
            d.polygon([(870, 1080), (840, 1060), (840, 1100)], fill=(120, 110, 150))
        text_c(d, "light", 170, 1110, 52, mix(GREEN, WHITE, 0.55), sw=5)
        text_c(d, "dark", 820, 1110, 52, mix(GREEN, BLACK, 0.5), stroke=WHITE, sw=5)

# shaded ball (numpy sphere lighting)
def shaded_ball(r, col, light_dir):
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32) / r
    zz2 = 1 - xx ** 2 - yy ** 2; mask = zz2 > 0
    zz = np.sqrt(np.clip(zz2, 0, 1))
    lx, ly, lz = light_dir; n = math.sqrt(lx * lx + ly * ly + lz * lz); lx, ly, lz = lx / n, ly / n, lz / n
    dot = np.clip(xx * lx + yy * ly + zz * lz, 0, 1)
    shade = 0.35 + 0.75 * dot
    c = np.array(col, dtype=np.float32)
    rgb = np.clip(c[None, None, :] * shade[..., None] + 120 * (dot[..., None] ** 25), 0, 255)
    a = (mask * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb.astype(np.uint8), a]), "RGBA")

BALL = shaded_ball(190, (240, 120, 70), (-0.8, -0.7, 0.6))

def scene_sun(im, lt, t):
    d = ImageDraw.Draw(im)
    # sun
    sx, sy = 180, 520
    for k in range(12):
        a = k * math.pi / 6 + t * 0.4
        r1, r2 = 95, 130 + 8 * math.sin(t * 3 + k)
        d.line([(sx + r1 * math.cos(a), sy + r1 * math.sin(a)), (sx + r2 * math.cos(a), sy + r2 * math.sin(a))],
               fill=(255, 190, 50), width=12)
    d.ellipse([sx - 80, sy - 80, sx + 80, sy + 80], fill=(255, 215, 70), outline=(255, 180, 40), width=6)
    # shadow on floor (to the lower right)
    bx, by = 520, 880
    if lt > 0.5:
        p = min(1, (lt - 0.5) / 1.0)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([bx - 60, by + 140, bx + 140 + 180 * p, by + 230], fill=(90, 70, 110, 120))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    im.alpha_composite(BALL, (bx - 190, by - 190))
    d = ImageDraw.Draw(im)
    if lt > 1.5:
        s = pop((lt - 1.5) / 0.5)
        d.rounded_rectangle([150, 640 - 40 * s, 150 + 190 * s, 640 + 40 * s], 30, fill=(255, 250, 220), outline=(255, 190, 60), width=5)
        if s > 0.8: text_c(d, "light", 245, 608, 52, (255, 170, 40), stroke=INK, sw=4)
    if lt > 3.8:
        s = pop((lt - 3.8) / 0.5)
        d.rounded_rectangle([700, 1170 - 40 * s, 700 + 190 * s, 1170 + 40 * s], 30, fill=(70, 60, 100), outline=WHITE, width=5)
        if s > 0.8: text_c(d, "dark", 795, 1138, 52, WHITE, stroke=INK, sw=4)

def balloon(d, cx, cy, col, sway):
    d.line([(cx, cy + 150), (cx + sway * 0.5, cy + 380)], fill=(120, 110, 140), width=5)
    d.polygon([(cx - 18, cy + 160), (cx + 18, cy + 160), (cx, cy + 135)], fill=mix(col, BLACK, 0.15))
    d.ellipse([cx - 125, cy - 160, cx + 125, cy + 150], fill=col)
    d.ellipse([cx - 80, cy - 115, cx - 35, cy - 45], fill=mix(col, WHITE, 0.6))

def scene_balloons(im, lt, t):
    d = ImageDraw.Draw(im)
    lp, dp = mix(PINK, WHITE, 0.55), mix(PINK, BLACK, 0.4)
    y1 = 720 + math.sin(t * 2) * 15; y2 = 720 + math.sin(t * 2 + 1.5) * 15
    if lt > 0.3:
        balloon(d, 285, y1 + (1 - pop((lt - 0.3) / 0.6)) * 600, lp, math.sin(t * 1.7) * 30)
    if lt > 3.2:
        balloon(d, 705, y2 + (1 - pop((lt - 3.2) / 0.6)) * 600, dp, math.sin(t * 1.5) * 30)
    if lt > 1.2:
        text_c(d, "light pink", 285, 420, 64, lp, sw=5)
    if lt > 4.2:
        text_c(d, "dark pink", 705, 420, 64, dp, stroke=WHITE, sw=5)
    if lt > 5.2:
        for k in range(8):
            a = k * math.pi / 4 + t
            for bx, c in ((285, lp), (705, dp)):
                x, y = bx + 175 * math.cos(a), 700 + 200 * math.sin(a)
                d.polygon(star_poly(x, y, 14 + 4 * math.sin(t * 5 + k)), fill=(255, 220, 90))

def scene_intro(im, lt, t):
    d = ImageDraw.Draw(im)
    # light-to-dark rainbow of swatches circling
    cols = [mix(BLUE, WHITE, 0.6), mix(PINK, WHITE, 0.5), mix(GREEN, WHITE, 0.5),
            mix(BLUE, BLACK, 0.5), mix(PINK, BLACK, 0.45), mix(GREEN, BLACK, 0.5)]
    for i, c in enumerate(cols):
        s = pop((lt - 0.3 - i * 0.2) / 0.5)
        if s <= 0: continue
        a = i * math.pi / 3 + t * 0.5
        x, y = CXC + 260 * math.cos(a), 950 + 220 * math.sin(a)
        r = 70 * s
        d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=WHITE, width=6)
    s = pop((lt - 0.8) / 0.6)
    if s > 0:
        sz = 104 * max(s, 0.1); f = font(sz); dd = ImageDraw.Draw(im)
        w1, w2, w3 = dd.textlength("Light ", font=f), dd.textlength("& ", font=f), dd.textlength("Dark", font=f)
        x0 = CXC - (w1 + w2 + w3) / 2; y = 400 - 30 * s
        dd.text((x0, y), "Light", font=f, fill=mix(BLUE, WHITE, 0.4), stroke_width=6, stroke_fill=INK)
        dd.text((x0 + w1, y), "&", font=f, fill=(240, 120, 160), stroke_width=6, stroke_fill=INK)
        dd.text((x0 + w1 + w2, y), "Dark", font=f, fill=mix(BLUE, BLACK, 0.45), stroke_width=6, stroke_fill=WHITE)
        text_c(dd, "COLORS", CXC, 530, 92 * max(s, 0.1), (240, 120, 160), sw=6)

def scene_outro(im, lt, t):
    d = ImageDraw.Draw(im)
    for i in range(14):
        a = i * 2 * math.pi / 14 + t * 0.6
        x, y = CXC + 290 * math.cos(a), 870 + 250 * math.sin(a)
        c = mix(PINK if i % 3 == 0 else BLUE if i % 3 == 1 else GREEN, WHITE if i % 2 else BLACK, 0.45)
        r = 38 + 8 * math.sin(t * 3 + i)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=WHITE, width=5)
    s = pop((lt - 0.3) / 0.6)
    if s > 0:
        text_c(d, "Great job!", CXC, 380, 110 * max(s, 0.1), (255, 200, 70), sw=6)
    if lt > 2.5:
        text_c(d, "Subscribe for more!", CXC, 1170, 54, (120, 90, 190), stroke=WHITE, sw=5)

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                         "-crf", "20", "-pix_fmt", "yuv420p", TMPV], stdin=subprocess.PIPE)
for fi in range(NFR):
    t = fi / FPS
    li = max(i for i, (s, e, _) in enumerate(LINES) if s <= t)
    s0, e0, txt = LINES[li]; lt = t - s0
    im = BG.copy()
    if li == 4:   # warm sunny tint for the sun scene
        tint = Image.new("RGBA", (W, H), (255, 230, 150, 60)); im.alpha_composite(tint)
    if li == 2:   # evening tint for dark scene
        tint = Image.new("RGBA", (W, H), (60, 60, 120, int(70 * min(1, lt / 1.5)))); im.alpha_composite(tint)
    if li == 0: scene_intro(im, lt, t)
    elif li == 1: scene_white(im, lt, False)
    elif li == 2: scene_white(im, lt, True)
    elif li == 3: scene_ladder(im, lt, t)
    elif li == 4: scene_sun(im, lt, t)
    elif li == 5: scene_balloons(im, lt, t)
    else: scene_outro(im, lt, t)
    # Twinkle narrates: top-left, outro centre-big
    talking = lt < (e0 - s0) - 1.0 and int(t * 7) % 2 == 0
    blink = (t % 3.7) < 0.12
    if li == 6:
        draw_twinkle(im, CXC, 870 + math.sin(t * 4) * 18, 160, talking, blink)
    else:
        bounce = abs(math.sin(t * 7)) * 14 if talking else math.sin(t * 2) * 5
        draw_twinkle(im, 140, 230 - bounce, 85, talking, blink)
    caption(im, txt, lt)
    # quick fade between scenes
    edge = min(lt, (e0 - s0) - lt)
    if edge < 0.2 and not (li == 0 and lt < 0.2):
        im.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - edge / 0.2) * 0.6))))
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio: original gentle waltz in F, music-box + soft pads ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, kind="bell", decay=5):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt)
    if kind == "bell": w += 0.35 * np.sin(2 * np.pi * freq * 2.01 * tt) + 0.1 * np.sin(2 * np.pi * freq * 3 * tt)
    if kind == "pad": w = 0.6 * w + 0.4 * np.sin(2 * np.pi * freq * 1.005 * tt)
    env = np.exp(-decay * tt) * np.minimum(1, tt * (200 if kind != "pad" else 4))
    return vol * w * env
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]
F = {"F4": 349.23, "G4": 392.0, "A4": 440.0, "C5": 523.25, "D5": 587.33, "F5": 698.46, "A3": 220.0,
     "F3": 174.61, "C4": 261.63, "D4": 293.66, "Bb3": 233.08}
melody = ["A4", "C5", "D5", "C5", "A4", "G4", "F4", "G4", "A4", "C5", "A4", "G4",
          "F4", "A4", "C5", "F5", "D5", "C5", "A4", "G4", "A4", "G4", "F4", "F4"]
chords = [("F3", "C4"), ("Bb3", "D4"), ("C4", "G4"), ("F3", "A3")]
beat = 0.42
k = 0
while k * beat < TOTAL - 1.5:
    if k % 3 != 2 or k % 6 == 5:
        add(tone(F[melody[k % len(melody)]], 1.0, 0.045, "bell", 3.5), k * beat)
    if k % 6 == 0:
        a, b = chords[(k // 6) % 4]
        add(tone(F[a], beat * 6, 0.05, "pad", 0.6), k * beat); add(tone(F[b], beat * 6, 0.035, "pad", 0.6), k * beat)
    k += 1
# sfx: plip for paint drops, sparkles for reveals
for base in (5.0, 12.0):
    for t0 in (1.0, 1.9, 2.8):
        add(tone(900 if base == 5.0 else 500, 0.25, 0.16, "sine", 14), base + t0 + 0.55)
    add(tone(784, 0.8, 0.12, "bell", 3), base + 4.0); add(tone(1046.5, 1.0, 0.12, "bell", 3), base + 4.2)
for i, t0 in enumerate([0.8, 1.6, 2.6, 3.6, 4.5]):
    add(tone([1046.5, 880, 698.46, 587.33, 523.25][i], 0.5, 0.13, "bell", 6), 19.0 + t0)
add(tone(698.46, 0.8, 0.12, "bell", 3), 27.5); add(tone(392, 0.8, 0.12, "bell", 3), 29.8)
add(tone(880, 0.6, 0.12, "bell", 4), 33.4); add(tone(440, 0.6, 0.12, "bell", 4), 36.3)
for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
    add(tone(f, 1.2, 0.14, "bell", 3), 40.3 + i * 0.15)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open(TMPA, "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", TMPV, "-i", TMPA, "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", TOTAL)
