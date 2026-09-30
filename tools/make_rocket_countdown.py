import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/rocket_countdown_10_to_1.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (40, 35, 80)
random.seed(21)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

WORDS = {10: "Ten", 9: "Nine", 8: "Eight", 7: "Seven", 6: "Six", 5: "Five", 4: "Four", 3: "Three", 2: "Two", 1: "One"}
NUMCOL = {10: (255, 120, 140), 9: (255, 170, 90), 8: (255, 215, 80), 7: (150, 225, 110), 6: (90, 210, 190),
          5: (110, 180, 255), 4: (170, 140, 255), 3: (230, 130, 230), 2: (255, 140, 180), 1: (255, 225, 110)}

# ---------- timeline ----------
INTRO, SEG, LAUNCH, OUTRO = 4.6, 2.5, 7.0, 6.0
T_COUNT = INTRO
T_LAUNCH = INTRO + 10 * SEG
T_OUTRO = T_LAUNCH + LAUNCH
TOTAL = T_OUTRO + OUTRO
NFR = int(TOTAL * FPS)

def cstart(k): return T_COUNT + k * SEG  # k = 0 for "10" ... 9 for "1"
LINES = [
    (0.4, INTRO - 0.2, "Hi! I'm Twinkle. Let's count down to blast off!"),
    (cstart(0) + 0.3, cstart(3) - 0.2, "Ten... nine... eight..."),
    (cstart(3) + 0.3, cstart(6) - 0.2, "Seven... six... five..."),
    (cstart(6) + 0.3, T_LAUNCH - 0.2, "Four... three... two... one!"),
    (T_LAUNCH + 0.3, T_OUTRO - 0.2, "Blast off! Up, up, up the rocket goes!"),
    (T_OUTRO + 0.3, TOTAL - 0.4, "We counted backwards! Bye bye!"),
]

# ---------- art ----------
def vgrad(w, h, top, bot):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, w, axis=1))

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

SKY_DUSK = vgrad(W, H, (70, 80, 170), (255, 190, 170)).convert("RGBA")
SKY_NIGHT = vgrad(W, H, (25, 25, 75), (120, 90, 170)).convert("RGBA")
STARS = [(random.randint(20, W - 20), random.randint(20, 1150), random.uniform(3, 7), random.uniform(0, 6)) for _ in range(70)]

def ground_layer():
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse([-500, 1330, 800, 2200], fill=(120, 105, 175))
    d.ellipse([300, 1360, 1600, 2250], fill=(100, 90, 160))
    d.ellipse([-300, 1420, 1400, 2400], fill=(130, 190, 140))
    d.rectangle([0, 1700, W, H], fill=(130, 190, 140))
    for _ in range(30):
        x, y = random.randint(20, W - 20), random.randint(1560, 1890)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=random.choice([(255, 250, 200), (255, 200, 220), (210, 240, 255)]))
    return g
GROUND = ground_layer()

def moon():
    s = 240; im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gl = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([20, 20, 220, 220], fill=(255, 245, 200, 120))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(im)
    d.ellipse([50, 50, 190, 190], fill=(255, 245, 205))
    for (x, y, r) in [(95, 95, 16), (140, 130, 12), (105, 150, 9)]:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(240, 225, 180))
    return im
MOON = moon()

PAD_Y = 1325   # top of launch pad
RX = 470       # rocket center x

def make_pad():
    im = Image.new("RGBA", (440, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 0, 420, 44], 18, fill=(170, 175, 200))
    d.rounded_rectangle([20, 0, 420, 16], 10, fill=(200, 205, 225))
    for x in (70, 370):
        d.rectangle([x - 14, 40, x + 14, 118], fill=(140, 145, 175))
    return im
PAD = make_pad()

def make_rocket():
    w, h = 300, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = w / 2
    # fins
    d.polygon([(cx - 80, 330), (cx - 140, 470), (cx - 140, 520), (cx - 70, 470)], fill=(110, 210, 180))
    d.polygon([(cx + 80, 330), (cx + 140, 470), (cx + 140, 520), (cx + 70, 470)], fill=(110, 210, 180))
    # body
    d.rounded_rectangle([cx - 85, 200, cx + 85, 500], 50, fill=(250, 245, 235))
    d.rectangle([cx - 85, 240, cx - 55, 480], fill=(232, 225, 215))  # soft shade
    # nose cone
    nose = [(cx - 86 * math.sqrt(u), 20 + 230 * u) for u in np.linspace(0, 1, 40)]
    nose += [(2 * cx - x, y) for (x, y) in reversed(nose)]
    d.polygon(nose, fill=(255, 130, 130))
    # band
    d.rectangle([cx - 85, 420, cx + 85, 450], fill=(255, 200, 90))
    # porthole
    d.ellipse([cx - 52, 270, cx + 52, 374], fill=(140, 150, 190))
    d.ellipse([cx - 40, 282, cx + 40, 362], fill=(150, 215, 255))
    d.ellipse([cx - 28, 292, cx - 6, 314], fill=(255, 255, 255))
    # middle fin + nozzle
    d.rounded_rectangle([cx - 14, 400, cx + 14, 520], 10, fill=(90, 185, 160))
    d.polygon([(cx - 50, 500), (cx + 50, 500), (cx + 65, 540), (cx - 65, 540)], fill=(150, 150, 175))
    return im
ROCKET = make_rocket()

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
TW = [make_twinkle(95, False), make_twinkle(95, True)]
TW_BIG = [make_twinkle(150, False), make_twinkle(150, True)]

def puff(r, a):
    im = Image.new("RGBA", (int(r * 2.4), int(r * 2.4)), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([r * 0.2, r * 0.2, r * 2.2, r * 2.2], fill=(255, 255, 255, int(a)))
    return im.filter(ImageFilter.GaussianBlur(r * 0.12))

# countdown light tower (right side, inside safe area)
TX, TY0, TGAP, TR = 800, 560, 76, 31
def light_y(n): return TY0 + (10 - n) * TGAP   # 10 at top, 1 at bottom

def ease_in(x): x = min(1, max(0, x)); return x * x * x
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
        if s <= t < e: return True, t - s
    return False, 0

def caption(im, t):
    for s, e, txt in LINES:
        if s <= t < e:
            a = min(1, (t - s) / 0.25, (e - t) / 0.25)
            f = font(62); d = ImageDraw.Draw(im)
            words, lines, cur = txt.split(), [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if d.textlength(test, font=f) > 770: lines.append(cur); cur = w
                else: cur = test
            lines.append(cur)
            lh = 82; bh = lh * len(lines) + 56
            y0 = 1470 - bh / 2
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle([45, y0, 915, y0 + bh], 44, fill=(255, 255, 255, int(238 * a)), outline=(140, 170, 255, int(255 * a)), width=8)
            for k, ln in enumerate(lines):
                lw = od.textlength(ln, font=f)
                od.text((480 - lw / 2, y0 + 22 + k * lh), ln, font=f, fill=INK + (int(255 * a),))
            im.alpha_composite(ov)
            return

def current_count(t):
    """number currently being said (10..1) or None"""
    if T_COUNT <= t < T_LAUNCH:
        k = int((t - T_COUNT) // SEG); return 10 - k, t - cstart(k)
    return None, 0

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_r.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi / FPS
    # sky darkens as the countdown goes on
    night = min(1, max(0, (t - T_COUNT) / (T_LAUNCH + 2 - T_COUNT)))
    im = Image.blend(SKY_DUSK, SKY_NIGHT, night)
    d = ImageDraw.Draw(im)
    sa = 0.35 + 0.65 * night
    for (x, y, r, ph) in STARS:
        tw = 0.6 + 0.4 * math.sin(t * 2.5 + ph)
        d.polygon(star_poly(x, y, r * (0.8 + 0.3 * tw), inner=0.45), fill=(255, 250, 220, int(255 * sa * tw)))
    paste(im, MOON, 930, 170)

    n, lt = current_count(t)
    launch_t = t - T_LAUNCH
    # rocket position
    ry = PAD_Y - ROCKET.height / 2 + 20
    rx = RX
    shake = 0
    if n is not None and n <= 3:
        shake = math.sin(t * 60) * (4 - n) * 1.5
    if launch_t >= 0:
        lift = ease_in(launch_t / 3.2) * 2600
        ry -= lift
        shake = math.sin(t * 60) * 3 * max(0, 1 - launch_t / 1.5)

    im.alpha_composite(GROUND)
    paste(im, PAD, RX, PAD_Y + 60)

    # smoke puffs
    if n is not None and n <= 3:
        for k in range(4):
            ph = (t * 0.8 + k * 0.25) % 1
            px = RX + (-1 if k % 2 else 1) * (60 + ph * 140)
            paste(im, puff(38 + ph * 30, 170 * (1 - ph) * (4 - n) / 3), px, PAD_Y + 10 - ph * 40)
    if launch_t >= 0:
        for k in range(10):
            ph = min(1, launch_t / 2.5 + k * 0.03)
            side = -1 if k % 2 else 1
            px = RX + side * (60 + ph * (180 + k * 30))
            fade = max(0, 1 - max(0, launch_t - 3) / 3)
            paste(im, puff(50 + ph * 50 + k * 4, 220 * fade), px, PAD_Y + 20 - ph * (30 + k * 10))

    # flame
    if launch_t >= -0.8 and ry > -700:
        fl = 1 + 0.2 * math.sin(t * 40)
        fy = ry + ROCKET.height / 2 - 10
        big = min(1, (launch_t + 0.8) / 1.0)
        fla = Image.new("RGBA", (220, 360), (0, 0, 0, 0)); fd = ImageDraw.Draw(fla)
        fd.ellipse([40, 0, 180, 320 * fl * big], fill=(255, 150, 70, 230))
        fd.ellipse([65, 0, 155, 230 * fl * big], fill=(255, 215, 90, 240))
        fd.ellipse([88, 0, 132, 130 * fl * big], fill=(255, 250, 220, 255))
        im.alpha_composite(fla.filter(ImageFilter.GaussianBlur(4)), (int(rx + shake - 110), int(fy)))
    if ry > -600:
        paste(im, ROCKET, rx + shake, ry)

    # countdown light tower
    d = ImageDraw.Draw(im)
    if launch_t < 1.5:
        ta = 1 if launch_t < 0.5 else max(0, 1 - (launch_t - 0.5))
        tower = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tower)
        td.rounded_rectangle([TX - 50, TY0 - 55, TX + 50, light_y(1) + 55], 30, fill=(90, 95, 140, 230))
        td.rectangle([TX - 12, light_y(1) + 50, TX + 12, PAD_Y + 60], fill=(90, 95, 140, 230))
        fn = font(34)
        for m in range(10, 0, -1):
            y = light_y(m)
            # a light switches off once its number has been said
            off = (n is not None and m > n) or launch_t >= 0
            if n == m and lt > 0.2:
                off = False
            col = (70, 70, 100) if off else NUMCOL[m]
            if not off and n == m:
                g = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
                ImageDraw.Draw(g).ellipse([15, 15, 125, 125], fill=NUMCOL[m] + (170,))
                tower.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)), (TX - 70, int(y - 70)))
            td.ellipse([TX - TR, y - TR, TX + TR, y + TR], fill=col, outline=(255, 255, 255), width=4)
            s = str(m); w = td.textlength(s, font=fn)
            td.text((TX - w / 2, y - 25), s, font=fn, fill=(255, 255, 255) if not off else (140, 140, 170))
        if ta < 1:
            arr = np.array(tower); arr[..., 3] = (arr[..., 3] * ta).astype(np.uint8); tower = Image.fromarray(arr)
        im.alpha_composite(tower)
    d = ImageDraw.Draw(im)

    talk, lt_talk = speaking(t)
    mouth = talk and (int(lt_talk * 7) % 2 == 0) and lt_talk > 0.1
    bounce = abs(math.sin(lt_talk * 7 * math.pi / 2)) * 14 if talk else 0

    if t < T_COUNT:
        paste(im, TW_BIG[1 if mouth else 0], 470, 560 - bounce, pop(t / 0.8))
        d = ImageDraw.Draw(im)
        if t > 0.8:
            f = font(100)
            for tx, y, c in (("Count Down", 150, (255, 255, 255)), ("10 to 1!", 270, (255, 215, 90))):
                w = d.textlength(tx, font=f)
                d.text((470 - w / 2, y), tx, font=f, fill=c, stroke_width=10, stroke_fill=INK)
    else:
        tx_, ty_ = (160, 250) if launch_t < 3.5 else (470, 800)
        if launch_t >= 3.5:
            paste(im, TW_BIG[1 if mouth else 0], tx_, ty_ - bounce, ease_out((launch_t - 3.5) / 0.6))
        else:
            paste(im, TW[1 if mouth else 0], tx_, ty_ - bounce)
        d = ImageDraw.Draw(im)
        if n is not None:
            ns = pop((lt - 0.2) / 0.6)
            if ns > 0:
                f = font(250 * ns); s = str(n); w = d.textlength(s, font=f)
                d.text((500 - w / 2, 110 + (250 - 250 * ns) * 0.55), s, font=f, fill=NUMCOL[n], stroke_width=13, stroke_fill=INK)
            if lt > 0.5:
                f = font(72); s = WORDS[n]; w = d.textlength(s, font=f)
                d.text((500 - w / 2, 420), s, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=INK)
        elif 0 <= launch_t < LAUNCH:
            sc = pop((launch_t - 0.1) / 0.7)
            if sc > 0:
                f = font(120 * sc); s = "Blast off!"; w = d.textlength(s, font=f)
                d.text((480 - w / 2, 400 + (120 - 120 * sc)), s, font=f, fill=(255, 150, 90), stroke_width=12, stroke_fill=INK)
            if launch_t > 3.8:
                # tiny rocket crossing the moon
                u = (launch_t - 3.8) / 3.2
                paste(im, ROCKET, 200 + u * 600, 700 - u * 420, 0.18)
        else:
            lt2 = t - T_OUTRO
            u = min(1, lt2 / 6)
            paste(im, ROCKET, 800 - u * 50, 260 - u * 40, 0.14)
            if lt2 > 0.5:
                f = font(92); s = "10  9  8  7  6"; w = d.textlength(s, font=f)
                d.text((470 - w / 2, 960), s, font=f, fill=(255, 255, 255), stroke_width=9, stroke_fill=INK)
                s = "5  4  3  2  1"; w = d.textlength(s, font=f)
                d.text((470 - w / 2, 1070), s, font=f, fill=(255, 215, 90), stroke_width=9, stroke_fill=INK)
            if lt2 > 1.2:
                f = font(60); s = "Subscribe for more!"; w = d.textlength(s, font=f)
                d.text((470 - w / 2, 1195), s, font=f, fill=(255, 255, 255), stroke_width=7, stroke_fill=INK)
    caption(im, t)
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio (original) ----------
N = int(TOTAL * SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, decay=5, harm=(1.0, 0.3, 0.1)):
    tt = np.arange(int(dur * SR)) / SR
    w = sum(h * np.sin(2 * np.pi * freq * (k + 1) * tt) for k, h in enumerate(harm))
    return vol * w * np.exp(-decay * tt) * np.minimum(1, tt * 150)
def pad(freqs, dur, vol):
    tt = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, tt / 0.8) * np.minimum(1, (dur - tt) / 0.8)
    return vol * env * sum(np.sin(2 * np.pi * f * tt) for f in freqs) / len(freqs)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if j > i: audio[i:j] += sig[:j - i]

# soft space pad: Cmaj7 -> Am7 -> Fmaj7 -> G6, 4 s each (original progression)
chords = [[130.81, 196.0, 246.94, 329.63], [110.0, 164.81, 196.0, 261.63],
          [87.31, 174.61, 220.0, 329.63], [98.0, 146.83, 196.0, 246.94]]
t0, c = 0.0, 0
while t0 < TOTAL:
    add(pad(chords[c % 4], 4.4, 0.10), t0)
    t0 += 4.0; c += 1
# gentle music-box sparkle pattern
mb = [659.25, 783.99, 987.77, 783.99, 880.0, 783.99, 659.25, 587.33]
k = 0; tt0 = 0.2
while tt0 < TOTAL:
    add(tone(mb[k % 8], 0.5, 0.02, 7, (1.0, 0.15)), tt0); tt0 += 1.0; k += 1
# countdown blips, pitch steps down 10 -> 1
scale = [1046.5, 987.77, 880.0, 783.99, 698.46, 659.25, 587.33, 523.25, 493.88, 440.0]
for i in range(10):
    add(tone(scale[i], 0.6, 0.12, 6, (1.0, 0.2, 0.05)), cstart(i) + 0.2)
# soft whoosh (filtered noise swell) for lift-off
rng = np.random.default_rng(3)
wl = int(4.0 * SR); noise = rng.standard_normal(wl)
noise = np.convolve(noise, np.ones(60) / 60, mode="same")
env = np.sin(np.pi * np.arange(wl) / wl) ** 2
add(noise * env * 0.35, T_LAUNCH - 0.3)
for i, f in enumerate([523.25, 659.25, 783.99, 1046.5]):
    add(tone(f, 1.2, 0.12, 3), T_LAUNCH + 0.2 + i * 0.15)
for i, f in enumerate([783.99, 987.77, 1174.66, 1567.98]):
    add(tone(f, 1.0, 0.1, 3), T_OUTRO + 0.6 + i * 0.2)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl); fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.75, -1, 1)
with wave.open("_audio_r.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_r.mp4", "-i", "_audio_r.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", round(TOTAL, 1))
