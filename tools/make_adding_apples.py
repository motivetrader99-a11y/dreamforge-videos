"""Dreamforge Kids — Simple adding: 1 + 1 to 5 with apples.
Warm golden-morning orchard: a big apple tree with a hanging wooden sign. Each round,
apples ripen in two clusters in the tree, drop onto the grass in two groups with a
plus sign between, then roll together into one group and get counted; the sign shows
the full sum (1+1=2, 2+1=3, 2+2=4, 3+2=5). Twinkle the star narrates from the caption
panel. Original art & music."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/adding_apples_1_to_5.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (92, 52, 38)
random.seed(33)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

# ---------- timeline ----------
INTRO, RD, OUTRO = 5.0, 8.6, 7.0
PROBS = [(1, 1), (2, 1), (2, 2), (3, 2)]
WORD = ["zero", "one", "two", "three", "four", "five"]
R = [INTRO + i * RD for i in range(4)]
T_OUT = INTRO + 4 * RD
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)

# per-round local times
T_A = 0.4            # first group starts falling
GAP = 0.35
T_PLUS = 1.9
T_B = 2.2
T_JOIN = 4.0         # groups roll together
T_CNT = 5.0          # counting starts
CGAP = 0.4

LINES = [(0.3, INTRO - 0.2, "Hi! I'm Twinkle! Let's add apples together!")]
for i, (a, b) in enumerate(PROBS):
    LINES.append((R[i] + 0.2, R[i] + T_JOIN - 0.1,
                  f"{WORD[a].capitalize()} apple{'s' if a > 1 else ''} plus {WORD[b]} apple{'s' if b > 1 else ''}..."))
    LINES.append((R[i] + T_JOIN, R[i] + RD - 0.1, f"...makes {WORD[a + b]} apples!"))
LINES.append((T_OUT + 0.3, T_OUT + 3.6, "Adding means putting together!"))
LINES.append((T_OUT + 3.7, TOTAL - 0.3, "Great job, little adders!"))
TALK = [(a, a + min(b - a - 0.2, len(txt.split()) * 0.38 + 0.4)) for a, b, txt in LINES]
def talking(t): return any(a <= t < b for a, b in TALK)

# ---------- layout ----------
GROUND_Y = 1070           # apples rest here (centre y)
LCX, RCX, MIDX = 250, 690, 470   # everything kept left of x=930
AGAP = 128
def group_pos(n, cx):
    return [cx + (i - (n - 1) / 2) * AGAP for i in range(n)]
def tree_pos(n, cx):  # hanging positions in the canopy
    return [(cx + (i - (n - 1) / 2) * 110, 600 + (i % 2) * 70) for i in range(n)]

# ---------- helpers ----------
def ease(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)
def fall(x):  # 0..1 -> 0..1 with a bounce at the end
    if x <= 0: return 0
    if x >= 1: return 1
    if x < 0.7: return (x / 0.7) ** 2
    b = (x - 0.7) / 0.3
    return 1 - 0.08 * math.sin(b * math.pi)

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
def make_apple(r=58, hue=0):
    s = int(r * 3); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    base = [(230, 55, 60), (215, 45, 70), (240, 80, 55)][hue % 3]
    dark = tuple(max(0, v - 60) for v in base)
    d.ellipse([c - r * 0.98, c - r * 0.78, c + r * 0.98, c + r * 0.98], fill=dark)
    d.ellipse([c - r, c - r * 0.84, c + r, c + r * 0.9], fill=base)
    d.ellipse([c - r * 0.16, c - r * 0.92, c + r * 0.16, c - r * 0.7], fill=dark)  # top dimple
    hl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([c - r * 0.7, c - r * 0.6, c - r * 0.3, c - r * 0.05], fill=(255, 255, 255, 140))
    im.alpha_composite(hl.filter(ImageFilter.GaussianBlur(r * 0.08))); d = ImageDraw.Draw(im)
    d.line([c, c - r * 0.75, c + r * 0.08, c - r * 1.15], fill=(110, 70, 40), width=int(r * 0.12))
    d.ellipse([c + r * 0.05, c - r * 1.2, c + r * 0.7, c - r * 0.85], fill=(90, 175, 80))
    # sweet face
    e = r * 0.1
    for dx in (-r * 0.3, r * 0.3):
        d.ellipse([c + dx - e, c + r * 0.02 - e * 1.3, c + dx + e, c + r * 0.02 + e * 1.3], fill=(60, 30, 30))
        d.ellipse([c + dx - e * 0.5, c - e * 0.9, c + dx, c - e * 0.3], fill=(255, 255, 255))
    d.arc([c - r * 0.18, c + r * 0.12, c + r * 0.18, c + r * 0.42], 20, 160, fill=(60, 30, 30), width=max(3, int(r * 0.07)))
    for dx in (-r * 0.52, r * 0.52):
        d.ellipse([c + dx - r * 0.12, c + r * 0.2, c + dx + r * 0.12, c + r * 0.34], fill=(255, 160, 170, 170))
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
    top, bot = np.array([255, 214, 170]), np.array([255, 243, 214])
    g = np.linspace(0, 1, H)[:, None]
    arr = (top * (1 - g) + bot * g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:, None, :], W, axis=1).reshape(H, W, 3)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # soft rising sun behind hills
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([620, 700, 1040, 1120], fill=170)
    bg.paste((255, 200, 130), mask=m.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(bg)
    d.ellipse([700, 780, 960, 1040], fill=(255, 200, 120))
    # far hills
    d.ellipse([-300, 860, 700, 1300], fill=(170, 205, 130))
    d.ellipse([400, 880, 1500, 1350], fill=(150, 195, 120))
    # distant tiny trees
    for x in (90, 980):
        d.rectangle([x - 6, 900, x + 6, 950], fill=(130, 90, 60))
        d.ellipse([x - 40, 840, x + 40, 920], fill=(110, 170, 90))
    # meadow
    d.rectangle([0, 1000, W, H], fill=(135, 200, 105))
    d.ellipse([-200, 960, 1300, 1120], fill=(135, 200, 105))
    for _ in range(140):
        x, y = random.randint(0, W), random.randint(1010, H)
        d.line([x, y, x + random.randint(-6, 6), y - random.randint(10, 22)], fill=(105, 175, 85), width=3)
    for _ in range(22):
        x, y = random.randint(20, W - 20), random.randint(1150, H - 40)
        col = random.choice([(255, 255, 255), (255, 220, 120), (255, 190, 210)])
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([x + 9 * math.cos(a) - 6, y + 9 * math.sin(a) - 6, x + 9 * math.cos(a) + 6, y + 9 * math.sin(a) + 6], fill=col)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 180, 60))
    # apple tree trunk
    d.polygon([(430, 1080), (510, 1080), (495, 760), (445, 760)], fill=(140, 95, 60))
    d.line([(470, 830), (360, 740)], fill=(140, 95, 60), width=26)
    d.line([(475, 800), (600, 720)], fill=(140, 95, 60), width=26)
    d.ellipse([400, 1060, 540, 1100], fill=(115, 175, 90))
    # canopy
    for (x, y, r, col) in [(200, 620, 150, (95, 165, 85)), (740, 620, 150, (95, 165, 85)),
                           (330, 540, 170, (110, 180, 95)), (610, 540, 170, (110, 180, 95)),
                           (470, 500, 180, (120, 190, 100)), (260, 690, 130, (105, 175, 90)),
                           (680, 690, 130, (105, 175, 90)), (470, 680, 160, (115, 185, 98))]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for _ in range(40):
        x, y = random.randint(120, 820), random.randint(420, 760)
        d.ellipse([x - 14, y - 9, x + 14, y + 9], fill=(140, 205, 115))
    # hanging wooden sign (ropes + board)
    d.line([(250, 120), (250, 90)], fill=(160, 120, 80), width=6)
    d.line([(690, 120), (690, 90)], fill=(160, 120, 80), width=6)
    d.rounded_rectangle([90, 120, 850, 340], radius=34, fill=(170, 115, 70))
    d.rounded_rectangle([104, 134, 836, 326], radius=28, fill=(215, 160, 105))
    for yy in (190, 260):
        d.line([(120, yy), (820, yy)], fill=(200, 145, 92), width=4)
    # caption panel
    d.rounded_rectangle([40, 1290, 920, 1540], radius=40, fill=(255, 252, 240), outline=(230, 150, 90), width=8)
    return bg

BG = background()
APPLES = [make_apple(58, h) for h in range(3)]
TWK = [make_twinkle(78, False), make_twinkle(78, True)]
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
            sz = 62
            lines = wrap(d, txt, sz, 610)
            while len(lines) > 3: sz -= 4; lines = wrap(d, txt, sz, 610)
            lh = sz * 1.22; y0 = 1415 - lh * len(lines) / 2
            for k, ln in enumerate(lines):
                f = font(sz); w = d.textlength(ln, font=f)
                d.text((600 - w / 2, y0 + k * lh), ln, font=f, fill=INK + (int(255 * al),))
            break
    tk = talking(t); mo = tk and int(t * 8) % 2 == 0
    bob = math.sin(t * 3) * 6 + (abs(math.sin(t * 11)) * -10 if tk else 0)
    paste(im, TWK[mo], 160, 1415 + bob, 1.0, math.sin(t * 2) * 5)

def sparkle(d, x, y, r, a):
    d.polygon(star_poly(x, y, r, 0, 0.35), fill=(255, 250, 200, int(255 * a)))

def draw_sign(d, a, b, lt):
    parts = []
    if lt >= T_A: parts.append(str(a))
    if lt >= T_PLUS: parts.append("+")
    if lt >= T_B: parts.append(str(b))
    ans_t = T_CNT + (a + b) * CGAP + 0.1
    if lt >= T_JOIN: parts.append("=")
    if lt >= ans_t: parts.append(str(a + b))
    if not parts: return
    f = font(150); txt = "  ".join(parts)
    full = f"{a}  +  {b}  =  {a + b}"; fw = d.textlength(full, font=f)
    x = 470 - fw / 2
    cols = [(230, 55, 60), (255, 255, 255), (230, 55, 60), (255, 255, 255), (60, 150, 60)]
    toks = full.split("  ")
    for k, tok in enumerate(toks):
        if k >= len(parts): break
        s = 1.0
        if k == 4: s = pop((lt - ans_t) / 0.5)
        ff = font(150 * max(s, 0.05))
        tw = d.textlength(tok, font=f); tw2 = d.textlength(tok, font=ff)
        d.text((x + (tw - tw2) / 2, 138 + (150 - 150 * s) * 0.6), tok, font=ff, fill=cols[k], stroke_width=9, stroke_fill=INK)
        x += tw + d.textlength("  ", font=f)

def draw_round(im, d, i, lt, t):
    a, b = PROBS[i]; n = a + b
    # ripening apples appear in the tree
    pos_tree = tree_pos(a, 300) + tree_pos(b, 640)
    ga = group_pos(a, LCX); gb = group_pos(b, RCX); gall = group_pos(n, MIDX)
    starts = [T_A + k * GAP for k in range(a)] + [T_B + k * GAP for k in range(b)]
    ground = ga + gb
    for k in range(n):
        tx, ty = pos_tree[k]; st = starts[k]
        hue = (k + i) % 3
        if lt < st:  # hanging, gently swinging, grows in at round start
            s = pop(lt / 0.5)
            paste(im, APPLES[hue], tx, ty + 30, s * 0.85, math.sin(t * 2.5 + k) * 8)
            continue
        fx = fall((lt - st) / 0.75)
        x = tx + (ground[k] - tx) * ease((lt - st) / 0.75)
        y = ty + 30 + (GROUND_Y - ty - 30) * fx
        sc = 0.85 + 0.15 * min(1, (lt - st) / 0.75)
        if lt >= T_JOIN:  # roll together into one group
            j = ease((lt - T_JOIN) / 0.9)
            x = ground[k] + (gall[k] - ground[k]) * j
            y = GROUND_Y - math.sin(j * math.pi) * 40
        rot = 0
        if T_JOIN <= lt < T_JOIN + 0.9:
            rot = -(gall[k] - ground[k]) * 0.6 * ease((lt - T_JOIN) / 0.9)
        # count hop
        ct = T_CNT + k * CGAP
        if ct <= lt < ct + 0.35: y -= math.sin((lt - ct) / 0.35 * math.pi) * 45
        # shadow
        d.ellipse([x - 55, GROUND_Y + 58, x + 55, GROUND_Y + 78], fill=(90, 150, 70, 110))
        paste(im, APPLES[hue], x, y, sc, rot)
    d = ImageDraw.Draw(im)
    # plus sign between groups
    if T_PLUS <= lt < T_JOIN + 0.3:
        s = pop((lt - T_PLUS) / 0.5) * (1 - ease((lt - T_JOIN) / 0.3))
        if s > 0.05: text_c(d, "+", 478, GROUND_Y - 105 * s, 150 * s, (255, 255, 255), sw=int(8 * s) + 1)
    # count bubbles over each apple
    for k in range(n):
        ct = T_CNT + k * CGAP
        if lt >= ct:
            s = pop((lt - ct) / 0.4)
            f = font(64 * s); c = str(k + 1); cw = d.textlength(c, font=f)
            d.ellipse([gall[k] - 42 * s, 900 - 42 * s, gall[k] + 42 * s, 900 + 42 * s], fill=(255, 255, 255, 235), outline=(230, 150, 90), width=5)
            d.text((gall[k] - cw / 2, 900 - 44 * s), c, font=f, fill=(230, 55, 60))
    # celebration sparkles after answer
    ans_t = T_CNT + n * CGAP + 0.1
    if lt > ans_t:
        for k in range(10):
            ang = k * 2 * math.pi / 10 + t
            rr = 150 + (lt - ans_t) * 140
            if rr < 480:
                sparkle(d, MIDX + math.cos(ang) * rr * 1.2, 1000 + math.sin(ang) * rr * 0.5, 16, max(0, 1 - rr / 480))
    draw_sign(d, a, b, lt)

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    # drifting butterflies-ish petals in sky
    for k in range(6):
        x = (k * 173 + t * 40) % 900 + 20; y = 380 + 25 * math.sin(t * 1.5 + k) + (k % 3) * 8 - 20
        d.ellipse([x - 7, y - 5, x + 7, y + 5], fill=(255, 190, 210, 200))
    if t < INTRO:
        mo = talking(t) and int(t * 8) % 2 == 0
        paste(im, TWK_BIG[mo], 470, 820 + math.sin(t * 3) * 14, pop(t / 0.8), math.sin(t * 2) * 6)
        d = ImageDraw.Draw(im)
        if t > 0.8: text_c(d, "Let's Add!", 470, 150, 120, (230, 55, 60), sw=9)
        if t > 1.6:
            for k in range(2):
                paste(im, APPLES[k], 330 + k * 280, 1110, pop((t - 1.6 - k * 0.3) / 0.5))
            d = ImageDraw.Draw(im)
            if t > 2.2: text_c(d, "+", 470, 1030, 130, (255, 255, 255), sw=8)
    elif t >= T_OUT:
        lt = t - T_OUT
        mo = talking(t) and int(t * 8) % 2 == 0
        paste(im, TWK_BIG[mo], 470, 800 + math.sin(t * 3) * 14 - abs(math.sin(t * 4)) * 20, pop(lt / 0.8), math.sin(t * 3) * 8)
        d = ImageDraw.Draw(im)
        if lt > 0.5: text_c(d, "Great adding!", 470, 162, 96, (230, 55, 60), sw=9, maxw=650)
        for k in range(5):
            if lt > 1.0 + k * 0.25:
                paste(im, APPLES[k % 3], group_pos(5, MIDX)[k], GROUND_Y - abs(math.sin(t * 4 + k)) * 25, pop((lt - 1.0 - k * 0.25) / 0.5))
        d = ImageDraw.Draw(im)
        if lt > 2.5:
            for k in range(12):
                ang = k * math.pi / 6 + t * 0.8
                sparkle(d, 470 + math.cos(ang) * 260, 800 + math.sin(ang) * 230, 14 + 6 * math.sin(t * 5 + k), 0.9)
    else:
        i = min(3, int((t - INTRO) // RD)); lt = t - R[i]
        draw_round(im, d, i, lt, t)
        d = ImageDraw.Draw(im)
    draw_caption(im, d, t)
    # soft fade in/out
    if t < 0.4 or t > TOTAL - 0.6:
        k = min(t / 0.4, (TOTAL - t) / 0.6)
        im = Image.blend(Image.new("RGBA", (W, H), (255, 243, 214, 255)), im, max(0, min(1, k)))
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio: gentle original plucked-strings waltz (F major, 3/4) ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def pluck(freq, dur, vol):
    n = int(dur * SR); p = max(2, int(SR / freq))
    buf = np.random.uniform(-1, 1, p); out = np.zeros(n)
    for k in range(n):
        out[k] = buf[k % p]
        buf[k % p] = 0.5 * (buf[k % p] + buf[(k + 1) % p]) * 0.996
    return vol * out
@lru_cache(None)
def pl(freq, dur, vol): return pluck(freq, dur, vol)
def tone(freq, dur, vol=0.2, decay=5):
    tt = np.arange(int(dur * SR)) / SR
    w = np.sin(2 * np.pi * freq * tt) + 0.35 * np.sin(4 * np.pi * freq * tt)
    return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 300)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if i < N: audio[i:j] += sig[:j - i]

np.random.seed(5)
F = {"F3": 174.61, "C3": 130.81, "Bb2": 116.54, "A3": 220.0, "C4": 261.63, "F4": 349.23, "A4": 440.0,
     "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "G4": 392.0, "E4": 329.63, "F5": 698.46}
chords = [("F3", ["A3", "C4", "F4"]), ("Bb2", ["F4", "Bb4", "D5"]), ("C3", ["E4", "G4", "C5"]), ("F3", ["A3", "C4", "F4"])]
melody = ["A4", "C5", "A4", "Bb4", "D5", "C5", "G4", "C5", "Bb4", "A4", "F4", None]
beat = 0.42; k = 0
while k * beat < TOTAL - 1:
    bar = k // 3; root, up = chords[bar % 4]
    if k % 3 == 0: add(pl(F[root], 1.2, 0.10), k * beat)
    else: [add(pl(F[nm], 0.6, 0.035), k * beat + j * 0.012) for j, nm in enumerate(up)]
    if k % 3 == 0:
        m = melody[(bar % 4) * 3 // 1 % 12]
        if m: add(tone(F[m], 0.9, 0.035, 3.5), k * beat)
    k += 1
# sfx
for i, (a, b) in enumerate(PROBS):
    n = a + b
    starts = [T_A + k * GAP for k in range(a)] + [T_B + k * GAP for k in range(b)]
    for st in starts: add(tone(300, 0.25, 0.12, 14), R[i] + st + 0.55)  # soft thump on landing
    add(tone(880, 0.4, 0.1, 6), R[i] + T_PLUS)
    add(tone(523.25, 0.5, 0.08, 5), R[i] + T_JOIN); add(tone(659.25, 0.5, 0.08, 5), R[i] + T_JOIN + 0.2)
    sc = [523.25, 587.33, 659.25, 698.46, 783.99]
    for k in range(n): add(tone(sc[k], 0.35, 0.16, 8), R[i] + T_CNT + k * CGAP)
    at = R[i] + T_CNT + n * CGAP + 0.1
    for j, f in enumerate([783.99, 1046.5, 1318.5]): add(tone(f, 0.9, 0.12, 4), at + j * 0.1)
for j, f in enumerate([523.25, 659.25, 783.99, 1046.5]): add(tone(f, 1.2, 0.14, 3), T_OUT + 0.1 + j * 0.15)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl)
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
print("done", round(TOTAL, 1))
