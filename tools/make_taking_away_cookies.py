"""Dreamforge Kids — Simple taking away with cookies.
Cozy teal kitchen with a window, a green chalkboard and a glass cookie jar. Each round,
fresh cookies pop onto a plate; some wiggle, then hop one by one into the jar, leaving
a dotted crumb outline behind. The cookies still on the plate are counted and the
chalkboard shows the full sum (3-1=2, 4-2=2, 5-1=4, 5-3=2). Twinkle the star narrates
from the right side of the caption panel. Original art & music."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/taking_away_cookies.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (70, 45, 35)
CHALK = (250, 250, 240)
random.seed(44)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, RD, OUTRO = 5.0, 8.6, 7.0
PROBS = [(3, 1), (4, 2), (5, 1), (5, 3)]
WORD = ["zero", "one", "two", "three", "four", "five"]
R = [INTRO + i * RD for i in range(4)]
T_OUT = INTRO + 4 * RD
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

T_IN, IGAP = 0.2, 0.22     # cookies pop onto the plate
T_MINUS = 2.4              # "- b" appears on chalkboard, taken cookies wiggle
T_HOP, HGAP, HDUR = 2.9, 0.55, 0.8
T_CNT, CGAP = 5.2, 0.42    # count the cookies left

def pl(n, w): return f"{WORD[n]} {w}{'s' if n != 1 else ''}"
LINES = [(0.3, INTRO - 0.2, "Hi! I'm Twinkle! Let's take away cookies!")]
for i, (a, b) in enumerate(PROBS):
    LINES.append((R[i] + 0.2, R[i] + T_MINUS - 0.05, f"{pl(a, 'cookie').capitalize()} on the plate."))
    LINES.append((R[i] + T_MINUS, R[i] + T_CNT - 0.1, f"Take away {pl(b, 'cookie')}..."))
    LINES.append((R[i] + T_CNT, R[i] + RD - 0.1, f"...{pl(a - b, 'cookie')} left!"))
LINES.append((T_OUT + 0.3, T_OUT + 3.6, "Taking away makes fewer!"))
LINES.append((T_OUT + 3.7, TOTAL - 0.3, "Great job, cookie counters!"))
TALK = [(a, a + min(b - a - 0.2, len(txt.split()) * 0.4 + 0.5)) for a, b, txt in LINES]
def talking(t): return any(a <= t < b for a, b in TALK)

# ---------- layout (all key content left of x=930, above y=1570) ----------
PLATE_X, PLATE_Y = 365, 1085
CK_Y = 1040
CGX = 124
JAR_X, JAR_TOP, JAR_BOT = 812, 800, 1110
def plate_pos(n): return [PLATE_X + (k - (n - 1) / 2) * CGX for k in range(n)]
def taken_idx(a, b):  # take cookies from the right end of the row
    return list(range(a - b, a))

# ---------- helpers ----------
def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def paste(canvas, sp, cx, cy, s=1.0, rot=0):
    if s <= 0.02: return
    if s != 1.0:
        sp = sp.resize((max(2, int(sp.width * s)), max(2, int(sp.height * s))), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)))

def text_c(d, txt, cx, y, sz, fill, stroke=INK, sw=8, maxw=None):
    f = font(sz)
    if maxw:
        while d.textlength(txt, font=f) > maxw and sz > 20:
            sz -= 2; f = font(sz)
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

# ---------- art ----------
def make_cookie(r=54, kind=0):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    base = [(225, 170, 95), (240, 190, 120), (150, 95, 60)][kind]
    edge = tuple(max(0, v - 50) for v in base)
    d.ellipse([c - r, c - r * 0.92, c + r, c + r], fill=edge)
    d.ellipse([c - r * 0.97, c - r, c + r * 0.97, c + r * 0.9], fill=base)
    rnd = random.Random(kind * 7 + 1)
    if kind == 1:  # pink icing with sprinkles
        d.ellipse([c - r * 0.8, c - r * 0.84, c + r * 0.8, c + r * 0.72], fill=(255, 175, 200))
        for _ in range(14):
            a = rnd.uniform(0, 6.28); rr = rnd.uniform(0.2, 0.7) * r
            x, y = c + math.cos(a) * rr, c - r * 0.06 + math.sin(a) * rr * 0.85
            if abs(y - (c + r * 0.12)) < r * 0.32 and abs(x - c) < r * 0.55: continue
            col = rnd.choice([(255, 255, 255), (120, 200, 255), (255, 230, 90), (150, 220, 140)])
            d.line([x - 5, y - 3, x + 5, y + 3], fill=col, width=5)
    else:
        chip = (95, 55, 35) if kind == 0 else (245, 235, 215)
        for _ in range(8):
            a = rnd.uniform(0, 6.28); rr = rnd.uniform(0.35, 0.8) * r
            x, y = c + math.cos(a) * rr, c + math.sin(a) * rr * 0.9
            if abs(x - c) < r * 0.5 and abs(y - c) < r * 0.45: continue
            d.ellipse([x - r * 0.1, y - r * 0.08, x + r * 0.1, y + r * 0.1], fill=chip)
    hl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r * 0.7, c - r * 0.8, c - r * 0.2, c - r * 0.45], fill=(255, 255, 255, 90))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(r * 0.08))); d = ImageDraw.Draw(im)
    eye = (55, 30, 25) if kind != 2 else (40, 20, 15)
    e = r * 0.1
    for dx in (-r * 0.26, r * 0.26):
        d.ellipse([c + dx - e, c - e * 1.5, c + dx + e, c + e * 1.1], fill=eye)
        d.ellipse([c + dx - e * 0.55, c - e * 1.2, c + dx, c - e * 0.55], fill=(255, 255, 255))
    d.arc([c - r * 0.17, c + r * 0.05, c + r * 0.17, c + r * 0.34], 20, 160, fill=eye, width=max(3, int(r * 0.07)))
    for dx in (-r * 0.48, r * 0.48):
        d.ellipse([c + dx - r * 0.12, c + r * 0.12, c + dx + r * 0.12, c + r * 0.26], fill=(255, 140, 150, 170))
    return im

def make_outline(r=54):
    s = int(r * 2.8); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    for k in range(18):
        a = k * 2 * math.pi / 18
        x, y = c + math.cos(a) * r * 0.95, c + math.sin(a) * r * 0.9
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(190, 140, 90, 200))
    for (dx, dy) in [(-0.2, 0.1), (0.25, -0.15), (0.05, 0.35), (-0.3, -0.3)]:
        d.ellipse([c + dx * r - 4, c + dy * r - 4, c + dx * r + 4, c + dy * r + 4], fill=(205, 150, 95, 200))
    return im

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

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

def background():
    bg = Image.new("RGBA", (W, H), (150, 212, 205, 255)); d = ImageDraw.Draw(bg)
    # wallpaper: soft vertical stripes + tiny hearts
    for x in range(0, W, 90):
        d.rectangle([x, 0, x + 44, 1000], fill=(162, 220, 212))
    for y in range(420, 960, 120):
        for x in range(45, W, 180):
            xx = x + (60 if (y // 120) % 2 else 0)
            d.ellipse([xx - 7, y - 5, xx, y + 2], fill=(255, 235, 225)); d.ellipse([xx, y - 5, xx + 7, y + 2], fill=(255, 235, 225))
            d.polygon([(xx - 7, y), (xx + 7, y), (xx, y + 9)], fill=(255, 235, 225))
    # chalkboard with wooden frame
    d.rounded_rectangle([70, 90, 870, 360], radius=26, fill=(160, 110, 70))
    d.rounded_rectangle([90, 110, 850, 340], radius=16, fill=(55, 105, 80))
    for _ in range(40):
        x, y = random.randint(110, 830), random.randint(125, 325)
        d.line([x, y, x + random.randint(10, 40), y + random.randint(-3, 3)], fill=(70, 120, 94), width=2)
    d.rectangle([300, 340, 640, 356], fill=(140, 95, 60))
    d.rectangle([340, 332, 380, 342], fill=(250, 250, 240)); d.rectangle([560, 332, 590, 342], fill=(255, 190, 200))
    # window with afternoon sky
    d.rounded_rectangle([110, 430, 520, 820], radius=18, fill=(250, 245, 235))
    sky = Image.new("RGBA", (380, 360)); arr = np.zeros((360, 380, 4), np.uint8)
    g = np.linspace(0, 1, 360)[:, None]
    arr[..., :3] = (np.array([150, 205, 255]) * (1 - g) + np.array([255, 225, 200]) * g)[:, None, :].astype(np.uint8)
    arr[..., 3] = 255; sky = Image.fromarray(arr)
    bg.alpha_composite(sky, (125, 445)); d = ImageDraw.Draw(bg)
    d.ellipse([380, 480, 470, 570], fill=(255, 235, 150))
    for (x, y) in [(190, 520), (300, 600)]:
        for dx, rr in [(-30, 26), (0, 36), (32, 26)]:
            d.ellipse([x + dx - rr, y - rr, x + dx + rr, y + rr], fill=(255, 255, 255))
    d.ellipse([90, 700, 380, 900], fill=(140, 200, 120)); d.ellipse([260, 720, 560, 920], fill=(120, 185, 105))
    bg.alpha_composite(Image.new("RGBA", (W, H - 805), (150, 212, 205, 255)), (0, 805)); d = ImageDraw.Draw(bg)
    d.rectangle([315, 445, 325, 805], fill=(250, 245, 235)); d.rectangle([125, 620, 505, 630], fill=(250, 245, 235))
    d.rounded_rectangle([90, 800, 540, 830], radius=10, fill=(240, 230, 215))
    # little plant pot on sill
    d.polygon([(430, 800), (500, 800), (490, 760), (440, 760)], fill=(225, 120, 90))
    for a in (-0.6, 0, 0.6):
        d.ellipse([465 + a * 40 - 16, 715 - abs(a) * -10, 465 + a * 40 + 16, 765], fill=(110, 175, 95))
    # redraw wall stripes below window
    for x in range(0, W, 90):
        d.rectangle([x, 830, x + 44, 1000], fill=(162, 220, 212))
    for x in range(0, W, 90):
        d.rectangle([x + 44, 830, x + 90, 1000], fill=(150, 212, 205))
    # table with checkered cloth
    d.rectangle([0, 1000, W, H], fill=(245, 240, 232))
    sq = 60
    for yy in range(1000, H, sq):
        for xx in range(0, W, sq):
            if ((xx // sq) + (yy // sq)) % 2 == 0:
                d.rectangle([xx, yy, xx + sq - 1, yy + sq - 1], fill=(250, 180, 170))
    d.rectangle([0, 995, W, 1008], fill=(230, 140, 130))
    # caption panel (Twinkle sits on its right end)
    d.rounded_rectangle([40, 1290, 930, 1545], radius=44, fill=(255, 252, 244), outline=(120, 185, 175), width=8)
    return bg

def make_plate():
    im = Image.new("RGBA", (680, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([20, 40, 660, 190], fill=(200, 200, 215, 120))
    d.ellipse([10, 20, 670, 170], fill=(255, 255, 255)); d.ellipse([10, 20, 670, 170], outline=(120, 170, 220), width=10)
    d.ellipse([80, 45, 600, 145], outline=(200, 225, 245), width=6)
    return im

def jar_parts():
    w, h = 220, 330
    back = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(back)
    d.rounded_rectangle([5, 40, w - 5, h - 5], radius=50, fill=(215, 240, 250, 150))
    front = Image.new("RGBA", (w, h), (0, 0, 0, 0)); f = ImageDraw.Draw(front)
    f.rounded_rectangle([5, 40, w - 5, h - 5], radius=50, outline=(150, 200, 225, 255), width=7)
    f.rounded_rectangle([22, 150, 44, 290], radius=10, fill=(255, 255, 255, 150))
    f.rounded_rectangle([40, 78, w - 40, 138], radius=12, fill=(255, 245, 225, 230), outline=(200, 150, 100), width=4)
    txt = "COOKIES"; ff = font(26); tw = f.textlength(txt, font=ff)
    f.text(((w - tw) / 2, 90), txt, font=ff, fill=(180, 110, 60))
    f.rounded_rectangle([25, 28, w - 25, 52], radius=10, fill=(180, 225, 240, 230))
    lid = Image.new("RGBA", (w, 70), (0, 0, 0, 0)); ld = ImageDraw.Draw(lid)
    ld.rounded_rectangle([15, 25, w - 15, 60], radius=14, fill=(240, 130, 120))
    ld.ellipse([w / 2 - 22, 2, w / 2 + 22, 38], fill=(240, 130, 120)); ld.ellipse([w / 2 - 10, 10, w / 2 + 2, 20], fill=(255, 190, 180))
    return back, front, lid

BG = background()
PLATE = make_plate()
CKS = [make_cookie(54, k) for k in range(3)]
OUTL = make_outline(54)
JB, JF, JL = jar_parts()
TWK = [make_twinkle(80, False), make_twinkle(80, True)]
TWK_BIG = [make_twinkle(165, False), make_twinkle(165, True)]

def wrap(d, txt, sz, maxw):
    f = font(sz); words = txt.split(); lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= maxw: cur = trial
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def draw_caption(im, d, t):
    for a, b, txt in LINES:
        if a <= t < b:
            al = min(1, (t - a) / 0.25, (b - t) / 0.25)
            sz = 64; lines = wrap(d, txt, sz, 620)
            while len(lines) > 3: sz -= 4; lines = wrap(d, txt, sz, 620)
            lh = sz * 1.22; y0 = 1418 - lh * len(lines) / 2 - 6
            for k, ln in enumerate(lines):
                f = font(sz); w = d.textlength(ln, font=f)
                d.text((380 - w / 2, y0 + k * lh), ln, font=f, fill=INK + (int(255 * al),))
            break
    tk = talking(t); mo = tk and int(t * 8) % 2 == 0
    bob = math.sin(t * 3) * 6 + (abs(math.sin(t * 11)) * -10 if tk else 0)
    paste(im, TWK[mo], 800, 1418 + bob, 1.0, math.sin(t * 2) * 5)

def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, 0, 0.35), fill=(255, 250, 200, int(255 * a)))

def draw_board(d, a, b, lt):
    toks = [str(a), "-", str(b), "=", str(a - b)]
    show = [lt >= T_IN, lt >= T_MINUS, lt >= T_MINUS, lt >= T_CNT, lt >= T_CNT + (a - b) * CGAP + 0.15]
    starts = [T_IN, T_MINUS, T_MINUS + 0.15, T_CNT, T_CNT + (a - b) * CGAP + 0.15]
    cols = [CHALK, (255, 200, 120), CHALK, (255, 200, 120), (255, 235, 110)]
    f = font(150); gap = 44
    ws = [d.textlength(tk, font=f) for tk in toks]
    x = 470 - (sum(ws) + gap * 4) / 2
    for k, tk in enumerate(toks):
        if show[k]:
            s = pop((lt - starts[k]) / 0.45)
            ff = font(150 * max(s, 0.05)); w2 = d.textlength(tk, font=ff)
            d.text((x + (ws[k] - w2) / 2, 128 + (150 - 150 * s) * 0.55), tk, font=ff, fill=cols[k])
        x += ws[k] + gap

def draw_jar(im, cookies_in, lid_open):
    im.alpha_composite(JB, (JAR_X - 110, JAR_TOP))
    for k, kind in enumerate(cookies_in):  # resting stack inside the jar
        cx = JAR_X - 45 + (k % 2) * 90 - (k // 2) * 10
        cy = JAR_BOT - 55 - (k // 2) * 60
        paste(im, CKS[kind], cx, cy, 0.78, (k * 37) % 30 - 15)
    im.alpha_composite(JF, (JAR_X - 110, JAR_TOP))
    lift = 70 * lid_open
    paste(im, JL, JAR_X - 10 * lid_open, JAR_TOP + 5 - lift, 1.0, -22 * lid_open)

def draw_round(im, i, lt, t):
    a, b = PROBS[i]; n = a - b
    pos = plate_pos(a); taken = taken_idx(a, b)
    paste(im, PLATE, PLATE_X, PLATE_Y)
    d = ImageDraw.Draw(im)
    in_jar = []; flying = []
    # lid opens while cookies hop
    last_land = T_HOP + (b - 1) * HGAP + HDUR
    lid = ease((lt - (T_HOP - 0.3)) / 0.3) * (1 - ease((lt - last_land - 0.1) / 0.3))
    for k in range(a):
        kind = (k + i) % 3; x = pos[k]
        st = T_IN + k * IGAP
        if lt < st: continue
        if k in taken:
            j = taken.index(k); hs = T_HOP + j * HGAP
            if lt >= hs:
                paste(im, OUTL, x, CK_Y, pop((lt - hs) / 0.4))
                if lt >= hs + HDUR: in_jar.append(kind); continue
                u = (lt - hs) / HDUR
                fx = x + (JAR_X - x) * ease(u)
                ty = JAR_TOP + 70
                fy = CK_Y + (ty - CK_Y) * u - math.sin(u * math.pi) * 260
                if u > 0.75: fy += (u - 0.75) / 0.25 * 110
                flying.append((kind, fx, fy, 1.0 - 0.22 * u, u * 360))
                continue
        rot = 0; y = CK_Y
        if k in taken and T_MINUS <= lt:  # wiggle before hopping
            rot = math.sin(lt * 18) * 10
        # count hop for remaining cookies
        if k < n:
            ct = T_CNT + k * CGAP
            if ct <= lt < ct + 0.35: y -= math.sin((lt - ct) / 0.35 * math.pi) * 45
        y += math.sin(t * 2.5 + k) * 3
        paste(im, CKS[kind], x, y, pop((lt - st) / 0.45), rot)
    draw_jar(im, in_jar, lid)
    for kind, fx, fy, s, rot in flying:
        paste(im, CKS[kind], fx, fy, s, rot)
    d = ImageDraw.Draw(im)
    # count bubbles over remaining cookies
    for k in range(n):
        ct = T_CNT + k * CGAP
        if lt >= ct:
            s = pop((lt - ct) / 0.4)
            f = font(64 * s); c = str(k + 1); cw = d.textlength(c, font=f)
            d.ellipse([pos[k] - 42 * s, 900 - 42 * s, pos[k] + 42 * s, 900 + 42 * s], fill=(255, 255, 255, 240), outline=(120, 185, 175), width=5)
            d.text((pos[k] - cw / 2, 900 - 44 * s), c, font=f, fill=(200, 110, 50))
    ans_t = T_CNT + n * CGAP + 0.15
    if lt > ans_t:
        for k in range(10):
            ang = k * 2 * math.pi / 10 + t
            rr = 120 + (lt - ans_t) * 140
            if rr < 420:
                sparkle(d, PLATE_X + math.cos(ang) * rr * 1.1, 1040 + math.sin(ang) * rr * 0.45, 15, max(0, 1 - rr / 420))
    draw_board(d, a, b, lt)

# ---------- render ----------
if __name__ == "__main__":
    import sys
    only = [float(x) for x in sys.argv[1:]]
    if only:
        for tt in only:
            pass
    proc = None if only else subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)
    frames = [int(x * FPS) for x in only] if only else range(NFR)
    for fi in frames:
        t = fi / FPS
        im = BG.copy(); d = ImageDraw.Draw(im)
        if t < INTRO:
            mo = talking(t) and int(t * 8) % 2 == 0
            paste(im, TWK_BIG[mo], 470, 760 + math.sin(t * 3) * 14, pop(t / 0.8), math.sin(t * 2) * 6)
            paste(im, PLATE, PLATE_X, PLATE_Y)
            d = ImageDraw.Draw(im)
            if t > 0.8: text_c(d, "Take Away!", 470, 145, 120, CHALK, stroke=(40, 80, 60), sw=6)
            if t > 1.6:
                for k in range(3):
                    paste(im, CKS[k], plate_pos(3)[k], CK_Y, pop((t - 1.6 - k * 0.25) / 0.5))
            draw_jar(im, [], 0)
        elif t >= T_OUT:
            lt = t - T_OUT
            mo = talking(t) and int(t * 8) % 2 == 0
            paste(im, PLATE, PLATE_X, PLATE_Y)
            draw_jar(im, [0, 1, 2, 0], 0)
            paste(im, TWK_BIG[mo], 440, 720 + math.sin(t * 3) * 14 - abs(math.sin(t * 4)) * 20, pop(lt / 0.8), math.sin(t * 3) * 8)
            d = ImageDraw.Draw(im)
            if lt > 0.5: text_c(d, "Great job!", 470, 150, 120, (255, 235, 110), stroke=(40, 80, 60), sw=6, maxw=700)
            for k in range(3):
                if lt > 1.0 + k * 0.25:
                    paste(im, CKS[k], plate_pos(3)[k], CK_Y - abs(math.sin(t * 4 + k)) * 25, pop((lt - 1.0 - k * 0.25) / 0.5))
            d = ImageDraw.Draw(im)
            if lt > 2.3:
                for k in range(12):
                    ang = k * math.pi / 6 + t * 0.8
                    sparkle(d, 440 + math.cos(ang) * 250, 720 + math.sin(ang) * 220, 14 + 6 * math.sin(t * 5 + k), 0.9)
        else:
            i = min(3, int((t - INTRO) // RD)); lt = t - R[i]
            draw_round(im, i, lt, t)
        d = ImageDraw.Draw(im)
        draw_caption(im, d, t)
        if t < 0.4 or t > TOTAL - 0.6:
            k = min(t / 0.4, (TOTAL - t) / 0.6)
            im = Image.blend(Image.new("RGBA", (W, H), (150, 212, 205, 255)), im, max(0, min(1, k)))
        if only:
            im.convert("RGB").save(f"_preview_{t:.1f}.png")
        else:
            proc.stdin.write(im.convert("RGB").tobytes())
    if only: sys.exit(0)
    proc.stdin.close(); proc.wait()

    # ---------- audio: soft original marimba lullaby (G major, 4/4) ----------
    N = int(TOTAL * SR); audio = np.zeros(N)
    def marimba(freq, dur, vol=0.2, decay=7):
        tt = np.arange(int(dur * SR)) / SR
        w = np.sin(2 * np.pi * freq * tt) + 0.25 * np.sin(2 * np.pi * freq * 4 * tt) * np.exp(-20 * tt)
        return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 400)
    def add(sig, at):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N: audio[i:j] += sig[:j - i]
    NT = {"G2": 98.0, "C3": 130.81, "D3": 146.83, "E3": 164.81, "G3": 196.0, "B3": 246.94, "D4": 293.66,
          "E4": 329.63, "G4": 392.0, "A4": 440.0, "B4": 493.88, "D5": 587.33, "E5": 659.25}
    bassl = ["G2", "E3", "C3", "D3"]
    arp = [["G3", "B3", "D4", "B3"], ["E3", "G3", "B3", "G3"], ["C3", "E3", "G3", "E3"], ["D3", "G3", "B3", "A4"]]
    mel = ["B4", None, "D5", "B4", "A4", None, "G4", None, "E4", "G4", "A4", None, "B4", "A4", "G4", None]
    beat = 0.5; k = 0
    while k * beat < TOTAL - 1:
        bar = (k // 4) % 4
        if k % 4 == 0: add(marimba(NT[bassl[bar]], 1.8, 0.09, 2.2), k * beat)
        add(marimba(NT[arp[bar][k % 4]] * 2, 0.5, 0.03, 8), k * beat + 0.25)
        m = mel[k % 16]
        if m: add(marimba(NT[m], 0.9, 0.045, 4.5), k * beat)
        k += 1
    for i, (a, b) in enumerate(PROBS):
        n = a - b
        for k in range(a): add(marimba(1174.66, 0.2, 0.08, 18), R[i] + T_IN + k * IGAP)  # pop in
        add(marimba(659.25, 0.4, 0.08, 7), R[i] + T_MINUS)
        for j in range(b):
            hs = R[i] + T_HOP + j * HGAP
            tt = np.arange(int(0.35 * SR)) / SR  # gentle rising "boing"
            fr = 400 + 500 * tt / 0.35
            add(0.07 * np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-5 * tt), hs)
            add(marimba(1568, 0.3, 0.07, 12), hs + HDUR)  # soft clink into jar
        sc = [523.25, 587.33, 659.25, 698.46, 783.99]
        for k in range(n): add(marimba(sc[k], 0.35, 0.16, 8), R[i] + T_CNT + k * CGAP)
        at = R[i] + T_CNT + n * CGAP + 0.15
        for j, f in enumerate([783.99, 987.77, 1174.66]): add(marimba(f, 0.9, 0.11, 4), at + j * 0.1)
    for j, f in enumerate([587.33, 783.99, 987.77, 1174.66]): add(marimba(f, 1.2, 0.13, 3), T_OUT + 0.1 + j * 0.15)
    fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
    audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
    with wave.open("_audio_v.wav", "wb") as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
    print("done", round(TOTAL, 1))
