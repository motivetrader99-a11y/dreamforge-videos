import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/count_the_balloons.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (50, 45, 90)
random.seed(11)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

BALLOONS = [  # (word, color name, rgb)
    ("One", "red", (240, 80, 90)),
    ("Two", "yellow", (255, 205, 60)),
    ("Three", "green", (90, 200, 110)),
    ("Four", "blue", (80, 150, 240)),
    ("Five", "purple", (170, 110, 225)),
]
# balloon rest positions (keep clear of right 150px and bottom 350px)
POS = [(230, 700), (480, 660), (730, 700), (355, 960), (605, 960)]
KNOT = (480, 1215)  # basket where strings are tied

# ---------- timeline & script ----------
INTRO, SEG, RECAP, OUTRO = 4.5, 5.5, 7.5, 6.0
T_COUNT = INTRO
T_RECAP = INTRO + 5 * SEG
T_OUTRO = T_RECAP + RECAP
TOTAL = T_OUTRO + OUTRO
NFR = int(TOTAL * FPS)

LINES = [(0.4, INTRO - 0.2, "Hi! I'm Twinkle. Let's count balloons!")]
for i, (w, c, _) in enumerate(BALLOONS):
    s = T_COUNT + i * SEG
    LINES.append((s + 1.2, s + SEG - 0.2, f"{w}! A {c} balloon."))
LINES.append((T_RECAP + 0.3, T_OUTRO - 0.2, "One, two, three, four, five! Five balloons!"))
LINES.append((T_OUTRO + 0.3, TOTAL - 0.3, "Bye bye, balloons! Great counting!"))

# ---------- art ----------
def vgrad(w, h, top, bot):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, w, axis=1))

def make_cloud(scale):
    s = int(320 * scale); im = Image.new("RGBA", (s, int(s * 0.8)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for (x, y, r) in [(0.28, 0.62, 0.2), (0.5, 0.45, 0.26), (0.72, 0.6, 0.2), (0.5, 0.7, 0.2)]:
        d.ellipse([s * (x - r), s * (y * 0.6 - r) + s * 0.1, s * (x + r), s * (y * 0.6 + r) + s * 0.1], fill=(255, 255, 255, 235))
    return im.filter(ImageFilter.GaussianBlur(2))

def background():
    bg = vgrad(W, H, (150, 210, 250), (255, 222, 230)).convert("RGBA")
    d = ImageDraw.Draw(bg)
    # soft sun rays top right (decorative, faint)
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun)
    sd.ellipse([760, -120, 1160, 280], fill=(255, 240, 170, 170))
    bg.alpha_composite(sun.filter(ImageFilter.GaussianBlur(30)))
    d = ImageDraw.Draw(bg)
    # rolling meadow
    d.ellipse([-400, 1380, 900, 2300], fill=(140, 215, 130))
    d.ellipse([350, 1440, 1600, 2400], fill=(115, 195, 115))
    d.rectangle([0, 1700, W, H], fill=(115, 195, 115))
    for _ in range(40):
        x, y = random.randint(20, W - 20), random.randint(1560, 1880)
        c = random.choice([(255, 255, 255), (255, 170, 200), (255, 230, 110)])
        for a in range(5):
            ang = a * 2 * math.pi / 5
            px, py = x + 9 * math.cos(ang), y + 9 * math.sin(ang)
            d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=c)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 190, 60))
    return bg

def make_balloon(color, num):
    rw, rh = 100, 122
    s = Image.new("RGBA", (rw * 2 + 40, rh * 2 + 70), (0, 0, 0, 0))
    cx, cy = s.width / 2, rh + 20
    d = ImageDraw.Draw(s)
    dark = tuple(max(0, c - 50) for c in color)
    d.polygon([(cx - 14, cy + rh + 18), (cx + 14, cy + rh + 18), (cx, cy + rh - 6)], fill=dark)
    d.ellipse([cx - rw, cy - rh + 4, cx + rw, cy + rh + 4], fill=dark)
    d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh], fill=color)
    hl = Image.new("RGBA", s.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([cx - rw * 0.62, cy - rh * 0.72, cx - rw * 0.2, cy - rh * 0.2], fill=(255, 255, 255, 140))
    s.alpha_composite(hl.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(s)
    f = font(120); t = str(num); tw = d.textlength(t, font=f)
    d.text((cx - tw / 2, cy - 92), t, font=f, fill=(255, 255, 255), stroke_width=7, stroke_fill=dark)
    return s, (cx, cy + rh + 18)  # sprite, knot offset

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def make_twinkle(r, mouth_open):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    g = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(g).polygon(star_poly(s / 2, s / 2, r * 1.08), fill=(255, 235, 140, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.15)))
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(s / 2, s / 2 + r * 0.04, r), fill=(225, 160, 30))
    d.polygon(star_poly(s / 2, s / 2, r), fill=(255, 205, 60))
    cx, cy, e = s / 2, s / 2 + r * 0.05, r * 0.1
    for dx in (-r * 0.22, r * 0.22):
        d.ellipse([cx + dx - e, cy - e * 1.35, cx + dx + e, cy + e * 1.35], fill=(60, 40, 70))
        d.ellipse([cx + dx - e * 0.45, cy - e * 1.05, cx + dx + e * 0.2, cy - e * 0.3], fill=(255, 255, 255))
    for dx in (-r * 0.4, r * 0.4):
        d.ellipse([cx + dx - r * 0.1, cy + r * 0.1, cx + dx + r * 0.1, cy + r * 0.22], fill=(255, 130, 150))
    if mouth_open:
        d.ellipse([cx - r * 0.12, cy + r * 0.14, cx + r * 0.12, cy + r * 0.34], fill=(150, 50, 70))
        d.ellipse([cx - r * 0.07, cy + r * 0.25, cx + r * 0.07, cy + r * 0.33], fill=(255, 130, 150))
    else:
        d.arc([cx - r * 0.16, cy + r * 0.04, cx + r * 0.16, cy + r * 0.28], 20, 160, fill=(60, 40, 70), width=max(3, int(r * 0.05)))
    return im

def make_basket():
    im = Image.new("RGBA", (260, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.arc([40, 0, 220, 150], 180, 360, fill=(170, 110, 60), width=14)
    d.rounded_rectangle([20, 70, 240, 165], 26, fill=(205, 145, 80))
    for y in (95, 125):
        d.line([30, y, 230, y], fill=(170, 110, 60), width=6)
    for x in range(55, 230, 45):
        d.line([x, 75, x, 160], fill=(185, 125, 65), width=4)
    return im

BG = background()
CLOUDS = [(make_cloud(1.0), 120, 0.0, 14), (make_cloud(0.75), 470, 300, -10), (make_cloud(0.6), 290, 700, 18)]
BALL = [make_balloon(c, i + 1) for i, (_, _, c) in enumerate(BALLOONS)]
TW = [make_twinkle(105, False), make_twinkle(105, True)]
TW_BIG = [make_twinkle(170, False), make_twinkle(170, True)]
BASKET = make_basket()

def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def paste(canvas, sp, x, y, scale=1.0):
    if scale <= 0.02: return
    if scale != 1.0:
        sp = sp.resize((max(2, int(sp.width * scale)), max(2, int(sp.height * scale))), Image.BILINEAR)
    canvas.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))

def speaking(t):
    for s, e, _ in LINES:
        if s <= t < e: return True, t - s, e - s
    return False, 0, 0

def caption(im, t):
    for s, e, txt in LINES:
        if s <= t < e:
            a = min(1, (t - s) / 0.25, (e - t) / 0.25)
            f = font(64); d = ImageDraw.Draw(im)
            words, lines, cur = txt.split(), [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if d.textlength(test, font=f) > 760: lines.append(cur); cur = w
                else: cur = test
            lines.append(cur)
            lh = 84; bh = lh * len(lines) + 56
            y0 = 1440 - bh / 2
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle([50, y0, 910, y0 + bh], 44, fill=(255, 255, 255, int(235 * a)), outline=(255, 170, 200, int(255 * a)), width=8)
            for k, ln in enumerate(lines):
                lw = od.textlength(ln, font=f)
                od.text((480 - lw / 2, y0 + 22 + k * lh), ln, font=f, fill=INK + (int(255 * a),))
            im.alpha_composite(ov)
            return

def big_number(d, n, lt, color):
    ns = pop(lt / 0.6)
    if ns <= 0: return
    f = font(230 * ns); t = str(n); w = d.textlength(t, font=f)
    d.text((560 - w / 2, 120 + (230 - 230 * ns) / 2), t, font=f, fill=color, stroke_width=12, stroke_fill=INK)

def draw_string(d, bx, by, kx, ky, t, i):
    mx = (bx + kx) / 2 + math.sin(t * 2 + i) * 25
    my = (by + ky) / 2
    pts = []
    for k in range(21):
        u = k / 20
        pts.append(((1 - u) ** 2 * bx + 2 * (1 - u) * u * mx + u * u * kx, (1 - u) ** 2 * by + 2 * (1 - u) * u * my + u * u * ky))
    d.line(pts, fill=(110, 100, 130), width=4)

def balloon_xy(i, t):
    x, y = POS[i]
    return x + math.sin(t * 1.6 + i * 1.3) * 10, y + math.sin(t * 2.1 + i) * 9

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_v.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi / FPS
    im = BG.copy()
    for sp, y, x0, v in CLOUDS:
        x = (x0 + v * t) % (W + 400) - 200
        im.alpha_composite(sp, (int(x - sp.width / 2), y))
    d = ImageDraw.Draw(im)
    talk, lt_talk, _ = speaking(t)
    mouth = talk and (int(lt_talk * 7) % 2 == 0) and lt_talk > 0.1
    bounce = abs(math.sin(lt_talk * 7 * math.pi / 2)) * 14 if talk else 0

    # which balloons exist & their positions
    if t < T_COUNT:
        shown = 0
    elif t < T_RECAP:
        shown = int((t - T_COUNT) // SEG) + 1
    else:
        shown = 5
    fly = t - T_OUTRO - 1.8 if t >= T_OUTRO else -1  # outro: balloons float away
    blist = []
    for i in range(shown):
        bx, by = balloon_xy(i, t)
        seg_start = T_COUNT + i * SEG
        rise = ease_out((t - seg_start - 0.2) / 1.3)
        by = 2050 + (by - 2050) * rise
        sc = 1.0
        if T_RECAP <= t < T_OUTRO:
            rt = t - T_RECAP - 0.6 - i * 0.9
            if 0 <= rt < 0.9: sc = 1 + 0.18 * math.sin(rt / 0.9 * math.pi)
        if fly > 0:
            by -= (fly * 260 + fly * fly * 120) * (1 + i * 0.12)
            bx += math.sin(fly * 1.5 + i) * 30 * fly
        blist.append((i, bx, by, sc))

    # basket & strings
    if True:
        paste(im, BASKET, KNOT[0], KNOT[1] + 60)
    d = ImageDraw.Draw(im)
    for i, bx, by, sc in blist:
        sp, (ox, oy) = BALL[i]
        kx, ky = bx - sp.width / 2 + ox, by - sp.height / 2 + oy * 1.0
        ky = by + (oy - sp.height / 2) * sc
        if fly > 0:
            d.line([(bx, ky), (bx + math.sin(t * 3 + i) * 12, ky + 120)], fill=(110, 100, 130), width=4)
        else:
            draw_string(d, bx, ky, KNOT[0], KNOT[1] + 20, t, i)
    for i, bx, by, sc in blist:
        if sc > 1.01:
            glow = Image.new("RGBA", (340, 380), (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse([40, 40, 300, 330], fill=(255, 255, 255, int(200 * (sc - 1) / 0.18)))
            paste(im, glow.filter(ImageFilter.GaussianBlur(25)), bx, by - 30)
        paste(im, BALL[i][0], bx, by, sc)
    d = ImageDraw.Draw(im)

    # sparkle when a balloon arrives
    if T_COUNT <= t < T_RECAP:
        i = shown - 1; lt = t - (T_COUNT + i * SEG)
        if 1.3 < lt < 2.3:
            a = 1 - (lt - 1.3); bx, by = balloon_xy(i, t)
            for k in range(8):
                ang = k * math.pi / 4 + 0.3; rr = 140 + (lt - 1.3) * 90
                d.polygon(star_poly(bx + rr * math.cos(ang), by + rr * math.sin(ang), 16), fill=(255, 240, 120, int(255 * a)))

    # Twinkle, number, title
    if t < T_COUNT:
        s = pop(t / 0.8)
        paste(im, TW_BIG[1 if mouth else 0], W / 2 - 60, 640 - bounce, s)
        if t > 0.8:
            f = font(104); tx = "Count the"; w = d.textlength(tx, font=f)
            d.text((480 - w / 2, 180), tx, font=f, fill=(255, 255, 255), stroke_width=10, stroke_fill=INK)
            tx = "Balloons!"; w = d.textlength(tx, font=f)
            d.text((480 - w / 2, 300), tx, font=f, fill=(255, 120, 150), stroke_width=10, stroke_fill=INK)
        if t > 1.5:
            f = font(60); tx = "1 to 5"; w = d.textlength(tx, font=f)
            d.text((480 - w / 2, 930), tx, font=f, fill=(255, 255, 255), stroke_width=7, stroke_fill=INK)
    else:
        paste(im, TW[1 if mouth else 0], 170, 250 - bounce)
        d = ImageDraw.Draw(im)
        if t < T_RECAP:
            i = shown - 1; lt = t - (T_COUNT + i * SEG) - 1.2
            if lt > 0:
                big_number(d, i + 1, lt, BALLOONS[i][2])
                if lt > 0.3:
                    f = font(70); tx = BALLOONS[i][0]; w = d.textlength(tx, font=f)
                    d.text((560 - w / 2, 385), tx, font=f, fill=(255, 255, 255), stroke_width=7, stroke_fill=INK)
        elif t < T_OUTRO:
            rt = t - T_RECAP - 0.6
            k = min(5, max(0, int(rt // 0.9) + 1)) if rt >= 0 else 0
            if k:
                big_number(d, k, rt - (k - 1) * 0.9 if k < 5 else rt - 3.6, BALLOONS[k - 1][2])
            if rt > 4.4:
                f = font(70); tx = "Five balloons!"; w = d.textlength(tx, font=f)
                d.text((560 - w / 2, 385), tx, font=f, fill=(255, 255, 255), stroke_width=7, stroke_fill=INK)
        else:
            lt = t - T_OUTRO
            if lt > 2.2:
                f = font(96); tx = "Great counting!"; w = d.textlength(tx, font=f)
                d.text((480 - w / 2, 800), tx, font=f, fill=(255, 205, 60), stroke_width=10, stroke_fill=INK)
            if lt > 3.2:
                f = font(56); tx = "Subscribe for more!"; w = d.textlength(tx, font=f)
                d.text((480 - w / 2, 950), tx, font=f, fill=(255, 255, 255), stroke_width=6, stroke_fill=INK)
    caption(im, t)
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio (original) ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, decay=5, harm=(1.0, 0.3, 0.1)):
    tt = np.arange(int(dur * SR)) / SR
    w = sum(h * np.sin(2 * np.pi * freq * (k + 1) * tt) for k, h in enumerate(harm))
    return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 150)
def glide(f0, f1, dur, vol):
    tt = np.arange(int(dur * SR)) / SR
    fr = f0 + (f1 - f0) * (tt / dur) ** 0.7
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return vol * np.sin(ph) * np.sin(np.pi * tt / dur)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if j > i: audio[i:j] += sig[:j - i]

# soft 3/4 marimba lullaby in F major, original arpeggio pattern
F = {"F3": 174.61, "A3": 220.0, "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0,
     "A4": 440.0, "Bb3": 233.08, "Bb4": 466.16, "C5": 523.25, "D5": 587.33, "G3": 196.0}
chords = [("F3", ["A4", "C5", "A4"]), ("D4", ["F4", "A4", "D5"]), ("Bb3", ["D4", "F4", "Bb4"]), ("C4", ["E4", "G4", "C5"])]
beat, bar = 0.42, 0
while bar * 3 * beat < TOTAL:
    root, arp = chords[bar % 4]; t0 = bar * 3 * beat
    add(tone(F[root] / 2, 3 * beat + 0.3, 0.08, 1.2, (1.0, 0.2)), t0)
    for k, n in enumerate(arp):
        add(tone(F[n], 0.6, 0.035, 6, (1.0, 0.1, 0.25)), t0 + k * beat)
    bar += 1
for i in range(5):
    s = T_COUNT + i * SEG
    add(glide(300, 700 + i * 60, 1.2, 0.07), s + 0.2)
    add(tone([523.25, 587.33, 659.25, 698.46, 783.99][i], 0.9, 0.16, 4), s + 1.3)
for k in range(5):
    add(tone([523.25, 587.33, 659.25, 698.46, 783.99][k], 0.7, 0.15, 5), T_RECAP + 0.6 + k * 0.9)
for k, f in enumerate([698.46, 880, 1046.5, 1396.9]):
    add(tone(f, 1.0, 0.13, 3), T_OUTRO + 2.2 + k * 0.18)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl); fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.8, -1, 1)
with wave.open("_audio_v.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_v.mp4", "-i", "_audio_v.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", round(TOTAL, 1))
