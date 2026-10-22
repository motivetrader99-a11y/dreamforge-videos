"""CHIKU & GOLA Ep 2: Who Is Fizz?  (no-voice build: music + sfx + timed captions).
Chiku brings dumplings to the park, catches Gola laughing with Fizz the show-off parrot -> jealousy mode;
turns out Fizz was teaching Gola a (terrible) joke for her; giggles, tap-tap, and still only ONE dumpling.
Uses tools/couple_art.py (Chiku, Gola, Fizz, park). Original synth score + code-made sfx."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from couple_art import *

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "couple/02_who_is_fizz.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 2, "Who Is Fizz?", "Gola Gets Jealous"

SHOTS = [("title", 0.0, 3.5), ("walk", 3.5, 9.5), ("bench", 9.5, 15.5), ("jealous", 15.5, 20.5), ("explain", 20.5, 26.0),
         ("joke", 26.0, 32.0), ("tap", 32.0, 40.0), ("next", 40.0, 44.5)]
TOTAL = 44.5
LINES = [
    ("CHIKU", "Dumplings for my Gola... but only ONE for him!", 3.8, 8.4),
    ("GOLA", "Hahaha! Fizz, you're SO funny!", 9.8, 12.4),
    ("FIZZ", "Gola, darling! Behold my FABULOUS feathers!", 12.6, 15.3),
    ("CHIKU", "DARLING?! Who. Is. Fizz?!", 15.8, 19.9),
    ("GOLA", "Chiku, wait! Fizz was teaching me a joke... for YOU!", 20.8, 25.6),
    ("GOLA", "Why did the bunny blush? Because she saw ME!", 26.2, 29.5),
    ("CHIKU", "...That's so bad. Hehe!", 29.9, 31.8),
    ("CHIKU", "Fine. Forgiven, you silly cat.", 32.3, 34.6),
    ("CHIKU", "But still... only ONE dumpling!", 37.6, 39.8),
]
TAG = {"CHIKU": ((96, 196, 160), "Chiku"), "GOLA": ((240, 140, 50), "Gola"), "FIZZ": ((60, 140, 230), "Fizz")}
TAPS = [35.0, 36.4]          # tap-tap moments (signature sound)
PUNCH = 29.5                 # joke punchline (ba-dum)

def speaking(who, t):
    return any(w == who and s <= t < e for w, _, s, e in LINES)

def mouth(who, t):
    return [1, 2, 1, 0][int(t*11) % 4] if speaking(who, t) else 0

def blinking(t, off):
    return ((t + off) % 3.3) < 0.12

def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)

def pop(x):  # 0..1 -> overshoot scale
    x = min(1, max(0, x)); return 1 + 0.25*math.sin(x*math.pi)*(1 - x) if x < 1 else 1.0

# ------------------------------------------------------------ cached backgrounds / layers
PARK = park_bg()
PARK_BLUE = park_bg(tint=(70, 90, 150, 95))
PARK_PINK = park_bg(tint=(255, 170, 200, 60))
BENCH = bench_layer(600)
SKY_TITLE = soft_sky((255, 214, 226), (255, 236, 200))
SKY_NEXT = soft_sky((214, 212, 255), (255, 222, 236))
VIG = None

def _vig():
    a = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W/2)/(W*0.75))**2 + ((yy - H/2)/(H*0.7))**2)
    a = np.clip((r - 0.6)*160, 0, 90).astype(np.uint8)
    im = Image.new("RGBA", (W, H), (70, 40, 60, 0)); im.putalpha(Image.fromarray(a))
    return im
VIG = _vig()

def cam(im, zoom=1.0, cx=540, cy=960, shake=0.0, t=0.0):
    if zoom <= 1.001 and shake <= 0: return im
    sx = shake*math.sin(t*93.0); sy = shake*math.cos(t*71.0)
    w, h = W/zoom, H/zoom
    x0 = min(max(0, cx - w/2 + sx), W - w); y0 = min(max(0, cy - h/2 + sy), H - h)
    return im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))

# ------------------------------------------------------------ text
def text_img(txt, size, fill=(255, 255, 255), stroke=(74, 46, 58), sw=None):
    f = font(size); sw = sw if sw is not None else max(4, size//7)
    bb = f.getbbox(txt, stroke_width=sw)
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((10 - bb[0], 16 - bb[1]), txt, font=f, fill=(74, 46, 58, 120), stroke_width=sw, stroke_fill=(74, 46, 58, 120))
    d.text((10 - bb[0], 10 - bb[1]), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)
    return im

def put_center(frame, img, cx, cy, scale=1.0, rot=0.0):
    if scale != 1.0:
        img = img.resize((max(1, int(img.width*scale)), max(1, int(img.height*scale))), Image.BICUBIC)
    if rot: img = img.rotate(rot, resample=Image.BICUBIC, expand=True)
    blit(frame, img, int(cx - img.width/2), int(cy - img.height/2))

_wrap_cache = {}
def wrap(txt, size, maxw):
    key = (txt, size, maxw)
    if key in _wrap_cache: return _wrap_cache[key]
    f = font(size); words = txt.split(); lines = []; cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        if f.getlength(test) > maxw and cur: lines.append(cur); cur = w
        else: cur = test
    lines.append(cur)
    _wrap_cache[key] = lines
    return lines

_cap_cache = {}
def caption_img(i, nshow):
    key = (i, nshow)
    if key in _cap_cache: return _cap_cache[key]
    who, txt, s, e = LINES[i]
    col, name = TAG[who]
    size = 62
    lines = wrap(txt, size, 840)
    f = font(size); sw = 10
    lh = int(size*1.22)
    im = Image.new("RGBA", (960, 110 + lh*len(lines) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    # speaker pill
    nf = font(40); nw = nf.getlength(name)
    d.rounded_rectangle([480 - nw/2 - 34, 8, 480 + nw/2 + 34, 82], 37, fill=col, outline=(74, 46, 58), width=6)
    d.text((480, 44), name, font=nf, fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(74, 46, 58))
    k = 0
    for li, ln in enumerate(lines):
        ws = ln.split()
        y = 100 + li*lh + lh//2
        x = 480 - (f.getlength(ln) + 6*(len(ws) - 1))/2
        for w in ws:
            if k < nshow:
                d.text((x + 3, y + 6), w, font=f, fill=(74, 46, 58), anchor="lm", stroke_width=sw, stroke_fill=(74, 46, 58))
                d.text((x, y), w, font=f, fill=(255, 255, 255), anchor="lm", stroke_width=sw, stroke_fill=col if False else (74, 46, 58))
            x += f.getlength(w + " ") + 6; k += 1
    _cap_cache[key] = im
    return im

def draw_caption(frame, t):
    for i, (who, txt, s, e) in enumerate(LINES):
        if s <= t < e + 0.25:
            n = len(txt.split())
            nshow = min(n, int((t - s)/max(0.3, (e - s)*0.72)*n) + 1)
            img = caption_img(i, nshow)
            sc = pop((t - s)/0.25)
            put_center(frame, img, 490, 1565 - img.height/2, sc)
            return

# ------------------------------------------------------------ fx helpers (drawn on 2x layers)
def float_hearts(d, t, n, x0, x1, y0, y1, seed, size=(26, 46)):
    rs = random.Random(seed)
    for k in range(n):
        x = rs.uniform(x0, x1); sp = rs.uniform(60, 120); ph = rs.uniform(0, 10); s = rs.uniform(*size)
        y = y1 - ((t*sp + ph*90) % (y1 - y0))
        heart(d, x + 14*math.sin(t*2 + ph), y, s, [(255, 110, 140), (255, 160, 190), (255, 130, 170)][k % 3], ow=3.5)

def twinkles(d, t, n, x0, x1, y0, y1, seed, col=(255, 250, 210)):
    rs = random.Random(seed)
    for k in range(n):
        x = rs.uniform(x0, x1); y = rs.uniform(y0, y1); ph = rs.uniform(0, 6)
        s = 10 + 12*max(0, math.sin(t*4 + ph))
        if s > 12: star(d, x, y, s, col, ow=2.5)

def flag(d, x, y):
    line(d, [(x, y), (x + 4, y - 120)], 5, (150, 100, 66))
    poly(d, [(x + 4, y - 124), (x + 150, y - 118), (x + 146, y - 70), (x + 4, y - 76)], (255, 255, 255), ow=4)

# ------------------------------------------------------------ shots
def feather(d, x, y, ang, s=1.0):
    poly(d, rot_ellipse(x, y, 34*s, 110*s, ang), (44, 140, 226), ow=4)
    poly(d, rot_ellipse(x, y, 18*s, 70*s, ang), (40, 200, 186))
    a = math.radians(ang)
    line(d, [(x - 130*s*math.sin(-a), y - 130*s*math.cos(a)), (x + 130*s*math.sin(-a), y + 130*s*math.cos(a))], 4)

def basket_at(frame, cx, feet_y, scale=1.0, s=0.65):
    L = fx_layer(); d = ImageDraw.Draw(L)
    dumpling_basket(d, cx, feet_y - 120*scale, s*scale)
    frame.alpha_composite(fx_done(L))

def shot_title(t, lt):
    im = SKY_TITLE.copy()
    L = fx_layer(); d = ImageDraw.Draw(L)
    float_hearts(d, t, 12, 60, 900, 100, 1700, 3)
    hb = 1 + 0.12*math.sin(lt*7)
    heart(d, 490, 640, 110*hb, (255, 96, 132), ow=6)
    feather(d, 820 - 40*lt, 560 + 30*math.sin(lt*3), 30*math.sin(lt*2.5), 0.6)
    im.alpha_composite(fx_done(L))
    sx, sy = squash(lt, 1.6, 0.05)
    paste_char(im, chiku("joy", 0, False, "up"), 270, 1330, 1.05, sx, sy)
    sx, sy = squash(lt + 0.3, 1.6, 0.05)
    paste_char(im, gola("happy", 0, False, "up"), 710, 1330, 1.05, sx, sy)
    put_center(im, text_img("CHIKU & GOLA", 118, (255, 255, 255)), 490, 300, pop((lt - 0.2)/0.35) if lt > 0.2 else 0.01)
    if lt > 0.7:
        put_center(im, text_img(f"Ep {EP}: {TITLE}", 70, (255, 236, 150)), 490, 450, pop((lt - 0.7)/0.35))
    return im

def shot_walk(t, lt):
    im = PARK.copy()
    stop = 4.7
    cx = 120 + 280*ease(lt/2.2)
    walking = lt < 2.2
    by = -abs(math.sin(lt*8))*16 if walking else 0
    L = fx_layer(); d = ImageDraw.Draw(L)
    if lt < stop: float_hearts(d, t, 6, 120, 600, 500, 1000, 21, (22, 34))
    im.alpha_composite(fx_done(L))
    if lt < stop:
        expr = "love" if lt < 3.0 else "happy"
        sx, sy = squash(lt, 2.0 if walking else 1.0, 0.04)
    else:
        expr = "shocked"; sx, sy = (0.92, 1.1) if lt < stop + 0.15 else (1.0, 1.0)
    paste_char(im, chiku(expr, mouth("CHIKU", t), blinking(t, 0.2) and lt < stop, "front"), cx, 1270 + by, 1.0, sx, sy)
    basket_at(im, cx, 1270 + by, 1.0)
    if lt >= stop:
        put_center(im, text_img("?!", 120, (255, 255, 255)), cx + 230, 560, pop((lt - stop)/0.25), 10)
        put_center(im, text_img("*giggling nearby*", 44, (255, 236, 150)), 640, 330, pop((lt - stop)/0.3), -4)
    z = 1.0 + (0.1*ease((lt - stop)/0.3) if lt >= stop else 0)
    return cam(im, z, cx + 60, 900, shake=(10 if stop <= lt < stop + 0.3 else 0), t=t)

def shot_bench(t, lt):
    im = PARK.copy()
    im.alpha_composite(BENCH)
    talking_f = speaking("FIZZ", t)
    fan = ease((t - 12.6)/0.5) if t >= 12.6 else 0.0
    paste_char(im, fizz("laugh" if t < 12.4 else ("smug" if not talking_f or lt % 1.4 < 0.9 else "wink"),
                        mouth("FIZZ", t), "point" if talking_f else "fold", round(fan, 2), blinking(t, 0.5)),
               770, 905 + (-abs(math.sin(lt*7))*8 if t < 12.4 else 0), 0.74)
    laughing = t < 12.6
    sx, sy = squash(lt, 3.0 if laughing else 1.0, 0.05 if laughing else 0.02)
    gm = mouth("GOLA", t) if speaking("GOLA", t) else (1 + int(t*8) % 2 if laughing else 0)
    gexpr = "happy" if laughing else "sparkle"
    paste_char(im, gola(gexpr, gm, False, "front"), 470, 1260, 1.0, sx, sy)
    if laughing:
        for k, (x, y, r) in enumerate(((250, 560, -8), (700, 470, 8))):
            if lt > 0.2 + k*0.4:
                put_center(im, text_img("HA HA!", 64, (255, 236, 150)), x, y + 10*math.sin(lt*9 + k), pop((lt - 0.2 - k*0.4)/0.25), r)
    if fan > 0.5:
        L = fx_layer(); d = ImageDraw.Draw(L)
        twinkles(d, t, 9, 620, 930, 560, 900, 4, (255, 250, 210))
        im.alpha_composite(fx_done(L))
        put_center(im, text_img("~fabulous~", 54, (180, 230, 255)), 640, 330, pop((t - 13.0)/0.3), -6)
    # Chiku peeks in from the left edge at the end
    if lt > 4.9:
        px = -120 + 220*ease((lt - 4.9)/0.35)
        paste_char(im, chiku("shocked", 0, False, "down"), px, 1300, 0.85, rot=-12)
    return cam(im, 1.0 + 0.05*ease(lt/6), 560, 960)

def shot_jealous(t, lt):
    im = burst_bg((255, 160, 170), (255, 192, 190), 18, lt*0.5)
    expr = "shocked" if lt < 0.6 else ("angry" if lt < 2.6 else "pout")
    sx, sy = (0.92, 1.1) if lt < 0.25 else (1.0, 1.0)
    paste_char(im, chiku(expr, mouth("CHIKU", t) if lt > 0.3 else 0, False, "down"), 490, 1720, 1.9, sx, sy)
    L = fx_layer(); d = ImageDraw.Draw(L)
    if lt > 0.6:
        puff_cloud(d, 160 - 20*math.sin(lt*6), 900 - 40*((lt*1.5) % 1), 0.9)
        puff_cloud(d, 830 + 20*math.sin(lt*6), 860 - 40*((lt*1.5 + 0.5) % 1), 0.8)
        anger_mark(d, 770, 640, 2.0 + 0.3*math.sin(lt*14))
    else:
        for k in range(5):
            a = math.radians(-150 + k*30)
            line(d, [(490 + 360*math.cos(a), 540 + 300*math.sin(a)), (490 + 440*math.cos(a), 540 + 380*math.sin(a))], 9, (255, 255, 255))
    im.alpha_composite(fx_done(L))
    if lt > 0.6:
        put_center(im, text_img("JEALOUSY MODE:", 78, (255, 255, 255)), 490, 250, pop((lt - 0.6)/0.3))
        flick = 1.0 if (lt*6) % 1 > 0.25 or lt > 1.6 else 0.0
        if flick: put_center(im, text_img("ON", 120, (255, 80, 110)), 490, 380, pop((lt - 0.9)/0.3) if lt > 0.9 else 0.01)
    z = 1.0 + 0.06*max(0, 1 - lt/0.4)
    return cam(im, z, 490, 900, shake=(16 if 0.6 < lt < 1.3 else 0), t=t)

def shot_explain(t, lt):
    im = PARK_BLUE.copy()
    paste_char(im, chiku("pout" if lt < 2.5 else "sulk", 0, blinking(t, 1.1), "cross"), 300, 1250, 1.0, flip=True)
    L = fx_layer(); d = ImageDraw.Draw(L)
    rain_cloud(d, 300, 470, t, 1.0)
    im.alpha_composite(fx_done(L))
    gx = 1100 - 380*ease(lt/0.9)
    run = lt < 0.9
    by = -abs(math.sin(lt*12))*18 if run else 0
    sx, sy = squash(lt, 4, 0.03)
    paste_char(im, gola("panic", mouth("GOLA", t), False, "front"), gx + (5*math.sin(lt*28) if not run else 0), 1250 + by, 0.95, sx, sy)
    L = fx_layer(); d = ImageDraw.Draw(L)
    for k, (x, y0) in enumerate(((gx + 170, 760), (gx - 160, 800))):
        sweat(d, x, y0 + ((lt*110 + k*50) % 110), 1.0)
    im.alpha_composite(fx_done(L))
    if lt < 1.4:
        put_center(im, text_img("HMPH!", 96, (255, 255, 255)), 300, 260, pop(lt/0.3), 6)
    return cam(im, 1.03, 520, 960)

def shot_joke(t, lt):
    im = PARK.copy()
    giggle = t >= 29.9
    ce = "joy" if giggle and not speaking("CHIKU", t) else ("happy" if giggle else ("pout" if lt < 1.5 else "sulk"))
    paste_char(im, chiku(ce, mouth("CHIKU", t), blinking(t, 0.4) and not giggle, "front" if giggle else "cross"), 290, 1250, 1.0,
               *(squash(lt, 3, 0.04) if giggle else (1, 1)))
    punch = 28.4 <= t < PUNCH + 0.3
    gexpr = "sparkle" if not punch else "happy"
    paste_char(im, gola(gexpr, mouth("GOLA", t), False, "up" if punch else "front"), 720, 1250, 1.0, *squash(lt, 1.4, 0.03))
    if lt > 3.8:   # Fizz pops in, winks + wing up
        fy = 640 + 340*(1 - ease((lt - 3.8)/0.4))
        paste_char(im, fizz("wink", 0, "point", 0.0), 820, fy, 0.42)
    L = fx_layer(); d = ImageDraw.Draw(L)
    if giggle: float_hearts(d, t, 7, 120, 480, 400, 900, 31, (22, 34))
    if punch: twinkles(d, t, 8, 560, 900, 500, 800, 6)
    im.alpha_composite(fx_done(L))
    if t >= PUNCH:
        put_center(im, text_img("ba-dum-tss!", 60, (255, 236, 150)), 470, 330, pop((t - PUNCH)/0.3), -5)
    if giggle:
        put_center(im, text_img("hehe", 54, (255, 190, 210)), 200, 560, pop((t - 29.9)/0.3), 8)
    return cam(im, 1.0 + 0.06*ease(lt/6), 500, 960)

def shot_tap(t, lt):
    im = PARK_PINK.copy()
    lean = 0.0
    for tt in TAPS:
        for k in (0, 0.42):
            x = (t - (tt + k - 0.18))/0.36
            if 0 <= x <= 1: lean = max(lean, math.sin(x*math.pi))
    cx_c = 320 + 34*lean; cx_g = 700 - 34*lean
    late = t >= 37.4
    ce = ("pout" if speaking("CHIKU", t) and late else "happy") if late else ("joy" if not speaking("CHIKU", t) else "happy")
    if 36.4 <= t < 37.4: ce = "love"
    paste_char(im, chiku(ce, mouth("CHIKU", t), False, "front" if late else "down"), cx_c, 1250, 1.0, rot=-9*lean)
    gexpr = ("sparkle" if t < 38.6 else "panic") if late else ("love" if not speaking("GOLA", t) else "happy")
    gx = cx_g - (40*ease((t - 37.4)/0.5) if late and t < 38.6 else 0)
    paste_char(im, gola(gexpr, 0, False, "front" if late else "down"), gx, 1250, 1.0, flip=True, rot=9*lean)
    if late:
        basket_at(im, cx_c - 30*ease((t - 38.4)/0.3), 1250, 1.0)
    L = fx_layer(); d = ImageDraw.Draw(L)
    float_hearts(d, t, 10, 80, 900, 200, 1200, 11)
    for tt in TAPS:
        x = t - tt
        if 0 <= x < 1.0:
            for k in range(10):
                a = k*2*math.pi/10
                r = 60 + 360*ease(x)
                heart(d, 510 + r*math.cos(a), 760 + r*math.sin(a)*0.8, 44*(1 - x*0.6), (255, 110, 150), ow=3.5)
            star(d, 510, 760, 70*(1 - x), (255, 250, 210), ow=4)
    if t > 38.6: sweat(d, gx + 120, 820, 1.1)
    im.alpha_composite(fx_done(L))
    for tt in TAPS:
        if tt <= t < tt + 1.3:
            put_center(im, text_img("tap-tap!", 92, (255, 150, 190)), 500, 380, pop((t - tt)/0.3), -5)
    if t >= 38.4:
        put_center(im, text_img("ONE!", 110, (255, 255, 255)), 300, 380, pop((t - 38.4)/0.3), 6)
    return cam(im, 1.05, 510, 960)

def shot_next(t, lt):
    im = SKY_NEXT.copy()
    L = fx_layer(); d = ImageDraw.Draw(L)
    float_hearts(d, t, 8, 60, 900, 200, 1500, 13)
    im.alpha_composite(fx_done(L))
    paste_char(im, chiku("sparkle", 0, blinking(t, 0.3), "front"), 290, 1300, 0.9)
    paste_char(im, fizz("wink", 0, "point", 0.0), 520, 980, 0.5)
    sx, sy = (1 + 0.06*min(1, lt), 1 + 0.06*min(1, lt))
    paste_char(im, gola("open", 0, False, "down", False, lt > 0.9), 720, 1300, 0.9, sx, sy)
    L = fx_layer(); d = ImageDraw.Draw(L)
    if lt > 0.9:
        anger_mark(d, 820, 760, 1.4 + 0.2*math.sin(lt*12))
        puff_cloud(d, 840, 640 - 30*((lt*1.5) % 1), 0.5)
    im.alpha_composite(fx_done(L))
    if lt > 0.5:
        put_center(im, text_img("cute bow~", 46, (180, 230, 255)), 430, 690, pop((lt - 0.5)/0.3), -6)
    put_center(im, text_img("NEXT:", 70, (255, 236, 150)), 490, 230, pop(lt/0.3))
    put_center(im, text_img(NEXT, 96, (255, 255, 255)), 490, 350, pop((lt - 0.25)/0.35) if lt > 0.25 else 0.01)
    put_center(im, text_img("Follow for Ep 3!", 58, (255, 200, 220)), 490, 1450, pop((lt - 0.8)/0.3) if lt > 0.8 else 0.01)
    return im

SHOT_FN = {"title": shot_title, "walk": shot_walk, "bench": shot_bench, "jealous": shot_jealous, "explain": shot_explain,
           "joke": shot_joke, "tap": shot_tap, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    if t - s < 0.07 and name != "title":
        im = Image.blend(im, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.5)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(11)
    def tv(n): return np.arange(n)/SR
    def add(sig, at, pan=0.0, vol=1.0):
        i = int(at*SR); j = min(N, i + len(sig))
        if j <= i or i < 0: return
        s = sig[:j - i]*vol
        L[i:j] += s*(1 - pan)*0.5*2**0.5*0.71; R[i:j] += s*(1 + pan)*0.5*2**0.5*0.71
    def note(m): return 440*2**((m - 69)/12)
    def env(n, a, r):
        e = np.ones(n); ai = max(1, int(a*SR)); ri = max(1, min(n, int(r*SR)))
        e[:ai] = np.linspace(0, 1, ai); e[-ri:] *= np.linspace(1, 0, ri); return e
    def uke(f, dur=0.9):   # plucked-string-ish: harmonics with faster decay up high
        n = int(dur*SR); x = tv(n); s = np.zeros(n)
        for h in range(1, 8):
            s += (0.9/h**1.1)*np.sin(2*np.pi*f*h*x + h)*np.exp(-x*(3.0 + 2.2*h))
        return s*env(n, 0.003, 0.05)
    def marimba(f, dur=0.6):
        n = int(dur*SR); x = tv(n)
        s = np.sin(2*np.pi*f*x)*np.exp(-x*6) + 0.35*np.sin(2*np.pi*f*3.98*x)*np.exp(-x*22)
        return s*env(n, 0.002, 0.04)
    def epiano(f, dur=1.6):
        n = int(dur*SR); x = tv(n)
        s = np.sin(2*np.pi*f*x) + 0.3*np.sin(2*np.pi*2*f*x)*np.exp(-x*2) + 0.1*np.sin(2*np.pi*3*f*x)*np.exp(-x*4)
        return s*np.exp(-x*1.6)*env(n, 0.01, 0.2)
    def noise(dur): return rs.randn(int(dur*SR))
    def lp(sig, k):
        out = np.convolve(sig, np.ones(k)/k, mode="same"); return out
    def whoosh(dur=0.45):
        n = int(dur*SR); x = np.linspace(0, 1, n)
        return lp(noise(dur), 18)*np.sin(np.pi*x)**2*0.9
    def boing(f0=300, f1=600, dur=0.45):
        n = int(dur*SR); x = tv(n)
        f = f0 + (f1 - f0)*(x/dur) ; f = f*(1 + 0.12*np.sin(2*np.pi*14*x)*np.exp(-x*5))
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*5)*env(n, 0.003, 0.05)
    def popfx(f=900, dur=0.09):
        n = int(dur*SR); x = tv(n); f = f*np.exp(-x*18)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*30)
    def gulp():
        n = int(0.32*SR); x = tv(n); f = 320*np.exp(-x*4.5)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*x/0.32)**0.5*1.2
    def taptap():
        out = np.zeros(int(1.1*SR))
        for k, (f0, f1) in enumerate(((760, 980), (940, 1220))):
            n = int(0.11*SR); x = tv(n)
            f = f0 + (f1 - f0)*(x/0.11)
            s = (np.sin(2*np.pi*np.cumsum(f)/SR) + 0.3*np.sin(4*np.pi*np.cumsum(f)/SR))*np.exp(-x*26)*env(n, 0.002, 0.02)
            i = int(k*0.12*SR); out[i:i + n] += s*1.1
        for k, m in enumerate((84, 88, 91, 96)):
            s = marimba(note(m), 0.5); i = int((0.26 + k*0.05)*SR); out[i:i + len(s)] += s*0.35
        return out
    def wahwah():
        out = np.zeros(int(2.8*SR))
        for k, (m, d) in enumerate(((58, 0.45), (57, 0.45), (56, 0.45), (55, 1.0))):
            n = int(d*SR); x = tv(n); f = note(m)*(1 + (0.02*np.sin(2*np.pi*6*x) if k == 3 else 0))
            ph = 2*np.pi*np.cumsum(np.ones(n)*f)/SR
            s = sum(np.sin(h*ph)/h for h in range(1, 9))
            s *= (0.6 + 0.4*np.sin(np.pi*np.clip(x/d, 0, 1)))*env(n, 0.03, 0.08)
            i = int(k*0.48*SR); out[i:i + n] += s*0.5
        return out

    # --- happy score: 116 bpm, C - Am - F - G, uke strums + marimba melody + bass
    bpm = 116; beat = 60/bpm
    chords = [[60, 64, 67, 72], [57, 60, 64, 69], [53, 57, 60, 65], [55, 59, 62, 67]]
    mel = [72, 74, 76, 79, 76, 74, 72, None, 69, 72, 74, 76, 74, 72, 69, None,
           65, 69, 72, 74, 72, 69, 67, None, 67, 71, 74, 76, 74, 71, 67, 69]
    def happy_section(t0, t1, vol=1.0):
        b = 0
        while True:
            at = t0 + b*beat
            if at >= t1: break
            ch = chords[(b//4) % 4]
            pat = b % 4
            for k, m in enumerate(ch):
                add(uke(note(m), 0.8), at + k*0.012, pan=-0.3, vol=0.16*vol*(1.0 if pat in (0, 2) else 0.7))
            if pat in (1, 3):
                for k, m in enumerate(ch[::-1]):
                    add(uke(note(m + 12), 0.4), at + beat/2 + k*0.01, pan=-0.3, vol=0.07*vol)
            if pat == 0: add(epiano(note(ch[0] - 24), 1.8)*0.8, at, vol=0.18*vol)
            for hh in (0, 0.5):
                m = mel[(b*2 + int(hh*2)) % len(mel)]
                if m and at + hh*beat < t1: add(marimba(note(m), 0.5), at + hh*beat, pan=0.3, vol=0.13*vol)
            b += 1
    def sad_section(t0, t1):
        sb = 60/72
        prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
        line_ = [76, 74, 72, 71, 72, 69, 67, 64]
        b = 0
        while t0 + b*sb < t1:
            at = t0 + b*sb; ch = prog[(b//2) % 4]
            if b % 2 == 0:
                for m in ch: add(epiano(note(m), 2.4), at, vol=0.13)
                add(epiano(note(ch[0] - 12), 2.4), at, vol=0.16)
            add(epiano(note(line_[b % len(line_)]), 1.2), at + 0.02, pan=0.2, vol=0.11)
            b += 1
    def squawk(dur=0.22, f0=1300):
        n = int(dur*SR); x = tv(n)
        f = f0*(1 + 0.35*np.sin(2*np.pi*9*x)) * (1 - 0.3*x/dur)
        s = np.sin(2*np.pi*np.cumsum(f)/SR + 2.5*np.sin(2*np.pi*f*1.5*x))
        return s*np.sin(np.pi*x/dur)**0.6*0.8
    def drum(f0=150, dur=0.25):
        n = int(dur*SR); x = tv(n); f = f0*np.exp(-x*6)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*14)
    def cymbal(dur=0.7):
        n = int(dur*SR); x = tv(n); s = noise(dur); s = s - lp(s, 4)
        return s*np.exp(-x*5)*0.6
    def heartbeat_ding(m):
        return marimba(note(m), 0.6)

    happy_section(0.0, 15.5)
    # jealous: tense minor stabs
    for k in range(5):
        st_ = sum(np.sin(2*np.pi*note(m)*tv(int(0.5*SR))) for m in (57, 60, 63))*np.exp(-tv(int(0.5*SR))*5)
        add(st_, 15.6 + k*0.95, vol=0.12)
        add(drum(110, 0.3), 15.6 + k*0.95, vol=0.35)
    sad_section(20.5, 26.0)
    happy_section(26.0, TOTAL, 1.0)
    duck = np.ones(N)
    for _, _, s, e in LINES:
        i, j = int((s - 0.15)*SR), int((e + 0.2)*SR); duck[i:j] = 0.62
    duck = np.convolve(duck, np.ones(2205)/2205, mode="same")
    L *= duck; R *= duck

    # --- sfx
    add(popfx(800), 0.2, vol=0.5); add(popfx(1000), 0.7, vol=0.5); add(boing(260, 620), 1.2, vol=0.35)
    for name, s, e in SHOTS[1:]: add(whoosh(0.4), s - 0.2, vol=0.22)
    for k in range(8): add(popfx(300, 0.08), 3.6 + k*0.27, pan=-0.3, vol=0.3)       # hoppy footsteps
    add(boing(600, 250, 0.35), 8.2, vol=0.5)                                          # stop + ?!
    for k in range(4): add(popfx(700 + 120*(k % 2), 0.1), 9.7 + k*0.45, pan=0.2, vol=0.3)   # laugh bops
    add(squawk(0.25, 1400), 12.4, pan=0.4, vol=0.4)
    for k in range(6): add(marimba(note(84 + [0, 2, 4, 7, 9, 12][k]), 0.5), 12.7 + k*0.06, pan=0.4, vol=0.28)  # fan flourish
    add(boing(500, 200, 0.4), 15.5, vol=0.5)
    add(wahwah(), 20.9, vol=0.4)
    for k in range(4): add(popfx(250, 0.08), 20.5 + k*0.2, pan=0.5, vol=0.35)        # running in
    add(drum(170, 0.2), PUNCH, vol=0.6); add(drum(130, 0.25), PUNCH + 0.18, vol=0.6); add(cymbal(0.8), PUNCH + 0.42, vol=0.5)
    add(squawk(0.18, 1600), 29.9, pan=0.5, vol=0.3)
    for k in range(3): add(popfx(1100 + 150*k, 0.08), 30.1 + k*0.18, pan=-0.3, vol=0.3)   # giggle pops
    for tt in TAPS: add(taptap(), tt - 0.05, vol=0.9)
    add(boing(300, 700), 37.5, vol=0.3)
    add(boing(700, 300, 0.35), 38.4, vol=0.45)
    for k in range(5): add(marimba(note(96 - k*3), 0.5), 40.1 + k*0.06, vol=0.25)
    add(squawk(0.2, 1500), 40.6, vol=0.3)
    add(boing(350, 650), 41.0, vol=0.3)

    st = np.stack([L, R], 1)
    fade = np.ones(N); fl = int(1.2*SR); fade[-fl:] = np.linspace(1, 0, fl); fi = int(0.02*SR); fade[:fi] = np.linspace(0, 1, fi)
    st *= fade[:, None]
    st = np.tanh(st/max(1e-9, np.abs(st).max())*1.4)*0.86
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((st*32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        for ts in os.environ["PREVIEW"].split(","):
            frame(float(ts)).save(os.path.join(TMP, "prev_%s.png" % ts))
        sys.exit()
    vpath, apath = os.path.join(TMP, "_c_v.mp4"), os.path.join(TMP, "_c_a.wav")
    build_audio(apath)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", vpath],
                            stdin=subprocess.PIPE)
    NF = int(TOTAL*FPS)
    for fi in range(NF):
        proc.stdin.write(frame(fi/FPS).tobytes())
        if fi % 150 == 0: print("frame", fi, "/", NF, flush=True)
    proc.stdin.close(); proc.wait()
    os.makedirs(os.path.dirname(OUTFILE) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", vpath, "-i", apath, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", OUTFILE], check=True)
    print("done", TOTAL)
