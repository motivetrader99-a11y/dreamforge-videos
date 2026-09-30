"""Dreamforge Kids — Counting by 2s up to 20.
A bunny hops across numbered stepping stones in a pond, skipping one stone each hop
and landing on 2, 4, 6 ... 20. Twinkle the star narrates. Original art & music."""
import math, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from functools import lru_cache

W, H, FPS, SR = 1080, 1920, 30, 44100
OUT = "kids/counting_by_twos_to_20.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
INK = (35, 60, 80)
random.seed(42)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

WORDS = {2: "Two", 4: "Four", 6: "Six", 8: "Eight", 10: "Ten", 12: "Twelve",
         14: "Fourteen", 16: "Sixteen", 18: "Eighteen", 20: "Twenty"}
HOPCOL = [(255, 120, 150), (255, 165, 90), (250, 205, 70), (130, 210, 110), (80, 200, 190),
          (100, 170, 250), (160, 140, 250), (220, 130, 230), (255, 140, 190), (255, 110, 110)]

# ---------- timeline ----------
INTRO, SEG, FINISH, OUTRO = 4.8, 2.6, 5.0, 8.0
T_HOP = INTRO
T_FIN = INTRO + 10 * SEG
T_OUT = T_FIN + FINISH
TOTAL = T_OUT + OUTRO
NFR = int(TOTAL * FPS)
def hstart(k): return T_HOP + k * SEG      # k = 0 -> hop to 2, ... 9 -> hop to 20

LINES = [
    (0.4, INTRO - 0.2, "Hi! I'm Twinkle. Let's count by twos!"),
    (hstart(0) + 0.2, hstart(3) - 0.2, "Bunny skips a stone and hops. Two, four, six!"),
    (hstart(3) + 0.2, hstart(6) - 0.2, "Eight, ten, twelve!"),
    (hstart(6) + 0.2, hstart(9) - 0.2, "Fourteen, sixteen, eighteen!"),
    (hstart(9) + 0.2, T_FIN + FINISH - 0.2, "Twenty! Bunny made it across the pond!"),
    (T_OUT + 0.3, T_OUT + 4.6, "Counting by twos is super quick!"),
    (T_OUT + 4.8, TOTAL - 0.4, "Two, four, six, eight, ten! Bye bye!"),
]

# ---------- layout: 20 stones in a snake, rows of 5 ----------
COLS_X = [150 + i * 165 for i in range(5)]
ROWS_Y = [640, 840, 1040, 1240]
def stone_pos(n):  # n = 1..20 ; 0 = start bank
    if n == 0: return (150, 470)
    r, c = divmod(n - 1, 5)
    if r % 2 == 1: c = 4 - c
    return (COLS_X[c], ROWS_Y[r])
SR_ST = 64

# ---------- art ----------
def vgrad(w, h, top, bot):
    g = np.linspace(0, 1, h)[:, None, None]
    arr = (np.array(top) * (1 - g) + np.array(bot) * g).astype(np.uint8)
    return Image.fromarray(np.repeat(arr, w, axis=1))

def star_poly(cx, cy, r, rot=0.0, inner=0.5):
    return [(cx + (r if i % 2 == 0 else r * inner) * math.cos(rot - math.pi / 2 + i * math.pi / 5),
             cy + (r if i % 2 == 0 else r * inner) * math.sin(rot - math.pi / 2 + i * math.pi / 5)) for i in range(10)]

def make_bg():
    im = vgrad(W, H, (200, 235, 255), (255, 240, 220)).convert("RGBA")
    d = ImageDraw.Draw(im)
    # soft hills far away
    d.ellipse([-300, 330, 600, 700], fill=(180, 225, 190))
    d.ellipse([400, 350, 1400, 720], fill=(165, 215, 180))
    # bank at top (start) and grass bottom
    d.rectangle([0, 470, W, H], fill=(150, 210, 150))
    # pond
    pond = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(pond)
    pd.rounded_rectangle([40, 545, 1040, 1345], 160, fill=(120, 200, 230))
    pd.rounded_rectangle([70, 575, 1010, 1315], 140, fill=(140, 215, 240))
    im.alpha_composite(pond)
    d = ImageDraw.Draw(im)
    # reeds & flowers on the banks (kept away from right 150px where possible)
    for x in (60, 95, 1000, 1030):
        for k in range(3):
            xx = x + k * 9
            d.line([(xx, 1360), (xx - 6 + k * 6, 1250 - k * 25)], fill=(90, 160, 100), width=7)
            d.ellipse([xx - 10 + k * 6, 1235 - k * 25, xx + 4 + k * 6, 1275 - k * 25], fill=(160, 110, 80))
    for _ in range(26):
        x, y = random.randint(20, W - 20), random.randint(1380, 1900)
        c = random.choice([(255, 250, 210), (255, 200, 225), (225, 210, 255)])
        for a in range(5):
            ang = a * 2 * math.pi / 5
            d.ellipse([x + 9 * math.cos(ang) - 7, y + 9 * math.sin(ang) - 7, x + 9 * math.cos(ang) + 7, y + 9 * math.sin(ang) + 7], fill=c)
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 210, 90))
    # lily pads
    for (x, y) in [(235, 740), (720, 940), (400, 1140), (880, 700), (560, 1300)]:
        d.pieslice([x - 34, y - 22, x + 34, y + 22], 30, 350, fill=(100, 180, 120))
    # sun
    g = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([40, 40, 260, 260], fill=(255, 230, 150, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(25)), (760, 60))
    d.ellipse([845, 145, 975, 275], fill=(255, 225, 120))
    return im
BG = make_bg()

def make_stone(color, big_text, lit):
    s = SR_ST * 2 + 30; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse([c - SR_ST, c - SR_ST * 0.72 + 10, c + SR_ST, c + SR_ST * 0.72 + 10], fill=(90, 150, 180))  # shadow in water
    d.ellipse([c - SR_ST, c - SR_ST * 0.72, c + SR_ST, c + SR_ST * 0.72], fill=color)
    d.ellipse([c - SR_ST * 0.7, c - SR_ST * 0.6, c - SR_ST * 0.1, c - SR_ST * 0.3], fill=tuple(min(255, v + 35) for v in color))
    return im
STONE_DIM = make_stone((190, 185, 195), False, False)
STONE_LIT = [make_stone(col, True, True) for col in HOPCOL]

def make_bunny(squash=0.0, blink=False):
    w, h = 220, 260
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = w / 2
    sy = 1 - squash * 0.25; sx = 1 + squash * 0.18
    def E(x0, y0, x1, y1, **kw):  # squash relative to bottom
        base = 250
        d.ellipse([cx + (x0 - cx) * sx, base - (base - y0) * sy, cx + (x1 - cx) * sx, base - (base - y1) * sy], **kw)
    body = (250, 246, 255); shade = (225, 218, 240)
    # ears
    E(cx - 58, 10, cx - 18, 120, fill=body); E(cx - 48, 28, cx - 28, 105, fill=(255, 190, 205))
    E(cx + 18, 10, cx + 58, 120, fill=body); E(cx + 28, 28, cx + 48, 105, fill=(255, 190, 205))
    # body + head
    E(cx - 78, 150, cx + 78, 250, fill=shade)
    E(cx - 72, 145, cx + 72, 245, fill=body)
    E(cx - 70, 80, cx + 70, 200, fill=body)
    # feet
    E(cx - 70, 225, cx - 20, 250, fill=(255, 225, 235)); E(cx + 20, 225, cx + 70, 250, fill=(255, 225, 235))
    # face
    ey = 250 - (250 - 135) * sy
    for dx in (-28, 28):
        ex = cx + dx * sx
        if blink:
            d.arc([ex - 13, ey - 8, ex + 13, ey + 10], 200, 340, fill=(50, 40, 70), width=5)
        else:
            d.ellipse([ex - 13, ey - 16, ex + 13, ey + 16], fill=(50, 40, 70))
            d.ellipse([ex - 7, ey - 11, ex + 1, ey - 3], fill=(255, 255, 255))
    for dx in (-48, 48):
        d.ellipse([cx + dx * sx - 12, ey + 14, cx + dx * sx + 12, ey + 26], fill=(255, 170, 190))
    d.polygon([(cx - 8, ey + 16), (cx + 8, ey + 16), (cx, ey + 25)], fill=(255, 130, 160))
    d.arc([cx - 14, ey + 18, cx, ey + 34], 20, 160, fill=(50, 40, 70), width=4)
    d.arc([cx, ey + 18, cx + 14, ey + 34], 20, 160, fill=(50, 40, 70), width=4)
    return im
BUNNY = {(q, b): make_bunny(q, b) for q in (0.0, 0.5, 1.0) for b in (False, True)}

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
TW = [make_twinkle(70, False), make_twinkle(70, True)]
TW_BIG = [make_twinkle(140, False), make_twinkle(140, True)]

def ease_out(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def pop(x):
    if x <= 0: return 0
    if x >= 1: return 1
    return (x / 0.35) * 1.2 if x < 0.35 else 1 + math.sin(x * math.pi * 1.5) * 0.25 * (1 - x)

def paste(canvas, sp, x, y, scale=1.0, anchor="center"):
    if scale <= 0.02: return
    if scale != 1.0:
        sp = sp.resize((max(2, int(sp.width * scale)), max(2, int(sp.height * scale))), Image.BILINEAR)
    oy = y - sp.height / 2 if anchor == "center" else y - sp.height
    canvas.alpha_composite(sp, (int(x - sp.width / 2), int(oy)))

def speaking(t):
    for s, e, _ in LINES:
        if s <= t < e: return True, t - s
    return False, 0

def caption(im, t):
    for s, e, txt in LINES:
        if s <= t < e:
            a = min(1, (t - s) / 0.25, (e - t) / 0.25)
            f = font(60); d = ImageDraw.Draw(im)
            lines, cur = [], ""
            for w in txt.split():
                test = (cur + " " + w).strip()
                if d.textlength(test, font=f) > 780: lines.append(cur); cur = w
                else: cur = test
            lines.append(cur)
            lh = 80; bh = lh * len(lines) + 50
            y0 = 1455 - bh / 2
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle([45, y0, 915, y0 + bh], 44, fill=(255, 255, 255, int(240 * a)),
                                 outline=(110, 200, 170, int(255 * a)), width=8)
            for k, ln in enumerate(lines):
                lw = od.textlength(ln, font=f)
                od.text((480 - lw / 2, y0 + 20 + k * lh), ln, font=f, fill=INK + (int(255 * a),))
            im.alpha_composite(ov)
            return

def bunny_state(t):
    """returns (x, y_feet, squash, landed_count k = number of completed hops)"""
    if t < T_HOP:
        x, y = stone_pos(0); return x, y + 30, 0.0, 0
    if t >= T_FIN:
        x, y = stone_pos(20); return x, y + 10, 0.0, 10
    k = int((t - T_HOP) // SEG); lt = t - hstart(k)
    a = stone_pos(2 * k); b = stone_pos(2 * k + 2)
    ay = a[1] + (30 if k == 0 else 10); by = b[1] + 10
    if lt < 0.25:               # crouch
        return a[0], ay, lt / 0.25, k
    if lt < 1.15:               # flight
        u = ease_io((lt - 0.25) / 0.9)
        x = a[0] + (b[0] - a[0]) * u; y = ay + (by - ay) * u - math.sin(u * math.pi) * 170
        return x, y, 0.0, k
    if lt < 1.4:                # landing squash
        return b[0], by, 1 - (lt - 1.15) / 0.25, k + 1
    return b[0], by, 0.0, k + 1

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
    "-pix_fmt", "yuv420p", "_video_b.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    # water ripples
    for k in range(6):
        ph = (t * 0.25 + k / 6) % 1
        x, y = 200 + (k * 173) % 700, 700 + (k * 211) % 560
        rr = 20 + ph * 60
        d.ellipse([x - rr, y - rr * 0.35, x + rr, y + rr * 0.35], outline=(200, 240, 255, int(200 * (1 - ph))), width=3)

    bx, by, sq, landed = bunny_state(t)
    in_outro = t >= T_OUT
    fade_st = 1.0 if not in_outro else max(0.0, 1 - (t - T_OUT) / 0.8)

    if fade_st > 0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
        for n in range(1, 21):
            x, y = stone_pos(n)
            even = n % 2 == 0
            lit = even and landed >= n // 2
            if lit:
                ci = n // 2 - 1
                just = t - (hstart(ci) + 1.15)
                sc = 1 + 0.25 * max(0, 1 - just / 0.4) if just >= 0 else 1
                if 0 <= just < 0.8:  # landing splash ring
                    rr = 60 + just * 110
                    ld.ellipse([x - rr, y - rr * 0.5, x + rr, y + rr * 0.5], outline=(255, 255, 255, int(230 * (1 - just / 0.8))), width=5)
                paste(layer, STONE_LIT[ci], x, y, sc)
                fn = font(54); s = str(n); w = ld.textlength(s, font=fn)
                ld.text((x - w / 2, y - 40), s, font=fn, fill=(255, 255, 255), stroke_width=5, stroke_fill=INK)
            else:
                paste(layer, STONE_DIM, x, y)
                fn = font(44 if even else 36); s = str(n); w = ld.textlength(s, font=fn)
                ld.text((x - w / 2, y - (34 if even else 28)), s, font=fn, fill=(250, 250, 255) if even else (130, 125, 145))
        # little "skip" dots over the odd stone being jumped
        if T_HOP <= t < T_FIN:
            k = int((t - T_HOP) // SEG); lt = t - hstart(k)
            if 0.3 < lt < 1.4:
                x, y = stone_pos(2 * k + 1)
                ld.text((x - 40, y - 110), "skip", font=font(34), fill=(120, 110, 140), stroke_width=4, stroke_fill=(255, 255, 255))
        # start bank sign
        sx, sy = stone_pos(0)
        ld.rounded_rectangle([sx + 90, sy - 70, sx + 250, sy - 10], 16, fill=(255, 250, 235), outline=(170, 130, 90), width=5)
        ld.text((sx + 108, sy - 68), "Start", font=font(38), fill=(150, 100, 70))
        if fade_st < 1:
            arr = np.array(layer); arr[..., 3] = (arr[..., 3] * fade_st).astype(np.uint8); layer = Image.fromarray(arr)
        im.alpha_composite(layer)

    # bunny
    blink = (t % 3.3) < 0.12
    q = 0.0 if sq < 0.25 else (0.5 if sq < 0.75 else 1.0)
    if not in_outro:
        # shadow
        _, groundy, _, _ = bunny_state(t)
        d = ImageDraw.Draw(im)
        paste(im, BUNNY[(q, blink)], bx, by + 12, 0.8, anchor="bottom")
    d = ImageDraw.Draw(im)

    talk, lt_talk = speaking(t)
    mouth = talk and (int(lt_talk * 7) % 2 == 0) and lt_talk > 0.1
    bounce = abs(math.sin(lt_talk * 7 * math.pi / 2)) * 12 if talk else 0

    if t < T_HOP:
        paste(im, TW_BIG[1 if mouth else 0], 480, 440 - bounce, pop(t / 0.8))
        d = ImageDraw.Draw(im)
        if t > 0.8:
            f = font(96)
            for tx, y, c in (("Count by 2s", 90, (255, 255, 255)), ("up to 20!", 200, (255, 150, 170))):
                w = d.textlength(tx, font=f)
                d.text((480 - w / 2, y), tx, font=f, fill=c, stroke_width=10, stroke_fill=INK)
        # redraw bunny on top of intro twinkle? bunny is at start bank, fine
    elif not in_outro:
        paste(im, TW[1 if mouth else 0], 115, 150 - bounce)
        d = ImageDraw.Draw(im)
        if T_HOP <= t < T_FIN:
            k = int((t - T_HOP) // SEG); lt = t - hstart(k)
            n = 2 * k + 2
            ns = pop((lt - 1.15) / 0.5)
            if ns > 0:
                f = font(210 * ns); s = str(n); w = d.textlength(s, font=f)
                d.text((500 - w / 2, 40 + (210 - 210 * ns) * 0.5), s, font=f, fill=HOPCOL[k], stroke_width=12, stroke_fill=INK)
            # "+2" floating during the flight
            if 0.3 < lt < 1.15:
                u = (lt - 0.3) / 0.85
                f = font(70); s = "+2"; w = d.textlength(s, font=f)
                d.text((bx + 70, max(260, by - 260 - u * 30)), s, font=f, fill=(255, 255, 255, int(255 * (1 - u * 0.5))), stroke_width=7, stroke_fill=INK)
            if k > 0 and lt < 1.15:  # previous number stays until the next lands
                f = font(210); s = str(n - 2); w = d.textlength(s, font=f)
                d.text((500 - w / 2, 40), s, font=f, fill=HOPCOL[k - 1], stroke_width=12, stroke_fill=INK)
        else:
            lt = t - T_FIN
            sc = pop(lt / 0.7)
            f = font(150 * max(sc, 0.05)); s = "20!"; w = d.textlength(s, font=f)
            d.text((500 - w / 2, 70 + 150 * (1 - sc) * 0.5), s, font=f, fill=HOPCOL[9], stroke_width=12, stroke_fill=INK)
            # confetti stars
            for i in range(18):
                ph = (lt * 0.45 + i / 18) % 1
                x = 120 + (i * 97) % 780; y = 300 + ph * 900
                d.polygon(star_poly(x, y, 16, rot=lt * 2 + i), fill=HOPCOL[i % 10])
    else:
        lt = t - T_OUT
        # big twinkle + happy bunny side by side
        paste(im, TW_BIG[1 if mouth else 0], 300, 360 - bounce, ease_out(lt / 0.6))
        hop = abs(math.sin(lt * 3)) * 40
        paste(im, BUNNY[(0.0, blink)], 700, 520 - hop, 1.0, anchor="bottom")
        d = ImageDraw.Draw(im)
        rows = [[2, 4, 6, 8, 10], [12, 14, 16, 18, 20]]
        for r, row in enumerate(rows):
            for c, n in enumerate(row):
                idx = r * 5 + c
                appear = pop((lt - 0.6 - idx * 0.3) / 0.5)
                if appear <= 0: continue
                x, y = 140 + c * 170, 700 + r * 220
                # pairs of carrots: n//2 pairs -> just show a pair icon under each number
                rr = 74 * appear
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=HOPCOL[idx], outline=(255, 255, 255), width=6)
                f = font(66 * appear); s = str(n); w = d.textlength(s, font=f)
                d.text((x - w / 2, y - 48 * appear), s, font=f, fill=(255, 255, 255), stroke_width=6, stroke_fill=INK)
        if lt > 4.0:
            f = font(58); s = "Subscribe for more!"; w = d.textlength(s, font=f)
            d.text((480 - w / 2, 1180), s, font=f, fill=(255, 255, 255), stroke_width=7, stroke_fill=INK)
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
    env = np.minimum(1, tt / 0.6) * np.minimum(1, (dur - tt) / 0.6)
    return vol * env * sum(np.sin(2 * np.pi * f * tt) for f in freqs) / len(freqs)
def add(sig, at):
    i = int(at * SR); j = min(N, i + len(sig))
    if j > i: audio[i:j] += sig[:j - i]
def boing(at, base):
    dur = 0.35; tt = np.arange(int(dur * SR)) / SR
    f = base * (1 + 0.8 * tt / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    add(0.10 * np.sin(ph) * np.exp(-5 * tt) * np.minimum(1, tt * 200), at)

# bright pond pad: F -> Dm -> Bb -> C, 2.6 s each (original progression)
chords = [[174.61, 220.0, 261.63], [146.83, 220.0, 293.66], [116.54, 233.08, 293.66], [130.81, 196.0, 329.63]]
t0, c = 0.0, 0
while t0 < TOTAL:
    add(pad(chords[c % 4], 2.9, 0.09), t0); t0 += 2.6; c += 1
# light plucked bass on the beat
bass = [87.31, 73.42, 58.27, 65.41]
tb = 0.0; i = 0
while tb < TOTAL:
    add(tone(bass[(i // 2) % 4] * 2, 0.5, 0.05, 6, (1.0, 0.4)), tb); tb += 1.3; i += 1
# hop boings and landing chimes (rising scale)
up = [523.25, 587.33, 659.25, 698.46, 783.99, 880.0, 987.77, 1046.5, 1174.66, 1318.51]
for k in range(10):
    boing(hstart(k) + 0.25, 260 + k * 18)
    add(tone(up[k], 0.8, 0.11, 5, (1.0, 0.2, 0.05)), hstart(k) + 1.15)
for i, f in enumerate([698.46, 880.0, 1046.5, 1396.91]):
    add(tone(f, 1.2, 0.1, 3), T_FIN + 0.1 + i * 0.15)
for i in range(10):
    add(tone(up[i], 0.5, 0.06, 7), T_OUT + 0.6 + i * 0.3)
fade = np.ones(N); fl = int(1.5 * SR); fade[-fl:] = np.linspace(1, 0, fl); fade[:int(0.3 * SR)] = np.linspace(0, 1, int(0.3 * SR))
audio = np.clip(audio * fade / max(1e-9, np.abs(audio).max()) * 0.7, -1, 1)
with wave.open("_audio_b.wav", "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "_video_b.mp4", "-i", "_audio_b.wav",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", round(TOTAL, 1))
