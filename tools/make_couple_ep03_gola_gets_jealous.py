"""CHIKU & GOLA Ep 3: Gola Gets Jealous  (no-voice build: music + sfx + timed captions).
At the café, Fizz the parrot calls Chiku's mint bow 'FABULOUS' -> Gola puffs up like a balloon,
tries to show off a 'fabulous tail' made of leaves and topples over; Chiku calls him her favourite
puffball, cheek boop, tap-tap... and still only ONE dumpling.
Uses tools/couple_art.py (Chiku, Gola, Fizz, café). Original synth score + code-made sfx."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from couple_art import *

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "couple/03_gola_gets_jealous.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 3, "Gola Gets Jealous", "The Silent Treatment"

SHOTS = [("title", 0.0, 3.5), ("compliment", 3.5, 9.6), ("puff", 9.6, 15.0), ("showoff", 15.0, 21.4),
         ("caught", 21.4, 28.0), ("makeup", 28.0, 37.0), ("dumpling", 37.0, 41.8), ("next", 41.8, 46.0)]
TOTAL = 46.0
LINES = [
    ("FIZZ", "Chiku, darling! Your bow is FABULOUS today!", 3.8, 6.9),
    ("CHIKU", "Aww, thank you, Fizz!", 7.1, 9.2),
    ("GOLA", "Fabulous?! I can be fabulous too!", 10.0, 13.6),
    ("GOLA", "Behold... my FABULOUS tail!", 15.4, 18.6),
    ("CHIKU", "Gola... are you JEALOUS?", 21.8, 24.2),
    ("GOLA", "...Maybe a teeny tiny bit.", 24.7, 27.5),
    ("CHIKU", "Silly. You're my favourite puffball.", 28.4, 31.6),
    ("GOLA", "So... TWO dumplings now?", 37.3, 39.3),
    ("CHIKU", "Nope. Still ONE!", 39.6, 41.5),
]
TAG = {"CHIKU": ((96, 196, 160), "Chiku"), "GOLA": ((240, 140, 50), "Gola"), "FIZZ": ((60, 140, 230), "Fizz")}
BOOP = 32.1                  # cheek boop -> deflate
TAPS = [33.9, 35.3]          # tap-tap moments (signature sound)
TOPPLE = 19.2                # Gola falls over

def speaking(who, t):
    return any(w == who and s <= t < e for w, _, s, e in LINES)

def mouth(who, t):
    return [1, 2, 1, 0][int(t*11) % 4] if speaking(who, t) else 0

def blinking(t, off):
    return ((t + off) % 3.3) < 0.12

def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)

def pop(x):
    x = min(1, max(0, x)); return 1 + 0.25*math.sin(x*math.pi)*(1 - x) if x < 1 else 1.0

CAFE = cafe_bg()
CAFE_BLUE = cafe_bg(tint=(70, 90, 150, 95))
CAFE_PINK = cafe_bg(tint=(255, 170, 200, 60))
TABLE = cafe_table_layer(540, 1020)
SKY_TITLE = soft_sky((255, 214, 226), (255, 236, 200))
SKY_NEXT = soft_sky((214, 212, 255), (255, 222, 236))

def _vig():
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
def fx(im, fn):
    L = fx_layer(); d = ImageDraw.Draw(L); fn(d); im.alpha_composite(fx_done(L))

def inflate(t):
    """Gola's balloon-puff amount 0..1: grows 10.0-12.5, stays, deflates at the boop."""
    if t < 10.0: return 0.0
    if t < BOOP: return ease((t - 10.0)/2.5)
    return 1.0 - ease((t - BOOP)/0.6)

def puffed_gola(im, expr, m, cx, feet, scale, t, arms="down", flip=False, rot=0.0, wob=True):
    p = inflate(t)
    w = 1 + 0.03*math.sin(t*9) if (wob and p > 0.5) else 1.0
    sx = (1 + 0.38*p)*w; sy = (1 + 0.12*p)/w
    paste_char(im, gola(expr, m, False, arms, False, p > 0.35 and m == 0), cx, feet, scale, sx, sy, flip=flip, rot=rot)

def shot_title(t, lt):
    im = SKY_TITLE.copy()
    def f(d):
        float_hearts(d, t, 12, 60, 900, 100, 1700, 3)
        hb = 1 + 0.12*math.sin(lt*7)
        heart(d, 490, 640, 110*hb, (255, 96, 132), ow=6)
    fx(im, f)
    sx, sy = squash(lt, 1.6, 0.05)
    paste_char(im, chiku("joy", 0, False, "up"), 270, 1330, 1.05, sx, sy)
    p = 0.35*ease((lt - 1.2)/1.0)
    sx, sy = squash(lt + 0.3, 1.6, 0.05)
    paste_char(im, gola("open" if lt > 1.2 else "happy", 0, False, "up", False, lt > 1.2), 710, 1330, 1.05, sx*(1 + p), sy*(1 + p*0.3))
    put_center(im, text_img("CHIKU & GOLA", 118, (255, 255, 255)), 490, 300, pop((lt - 0.2)/0.35) if lt > 0.2 else 0.01)
    if lt > 0.7:
        put_center(im, text_img(f"Ep {EP}: {TITLE}", 70, (255, 236, 150)), 490, 450, pop((lt - 0.7)/0.35))
    return im

def shot_compliment(t, lt):
    im = CAFE.copy()
    # Fizz perched on the table, fanning
    fan = ease((t - 4.4)/0.5) if t >= 4.4 else 0.0
    talking = speaking("FIZZ", t)
    paste_char(im, fizz("wink" if (talking and lt % 1.4 > 0.9) else ("smug" if t < 7.0 else "laugh"), mouth("FIZZ", t),
                        "point" if talking else "fold", round(fan, 2), blinking(t, 0.5)), 560, 1000, 0.62)
    im.alpha_composite(TABLE)
    def f(d):
        teacup(d, 430, 1010, 0.9, (255, 190, 205)); teacup(d, 690, 1012, 0.9, (190, 230, 255))
        if fan > 0.5: twinkles(d, t, 7, 380, 760, 520, 820, 4)
        if t > 7.0: float_hearts(d, t, 5, 100, 380, 500, 900, 9, (22, 32))
    fx(im, f)
    ce = "sparkle" if t < 7.0 else "love"
    paste_char(im, chiku(ce, mouth("CHIKU", t), blinking(t, 0.2) and ce == "sparkle", "front"), 210, 1300, 0.95, *squash(lt, 1.2, 0.03))
    # Gola: sleepy, then eyes snap wide at 'FABULOUS'
    ge = "sleepy" if t < 5.6 else ("shocked" if t < 8.0 else "guilty")
    paste_char(im, gola(ge, 0, blinking(t, 1.0) and ge == "sleepy", "down"), 900, 1310, 0.95, flip=True)
    if 5.6 <= t < 8.0:
        put_center(im, text_img("!!", 100, (255, 255, 255)), 930, 560, pop((t - 5.6)/0.25), 8)
    if t >= 8.0:
        fx(im, lambda d: sweat(d, 1010, 700 + ((lt*90) % 80), 1.0))
    if t > 4.6:
        put_center(im, text_img("~fabulous~", 54, (180, 230, 255)), 560, 360, pop((t - 4.6)/0.3), -6)
    return cam(im, 1.0 + 0.05*ease(lt/6), 540, 960)

def shot_puff(t, lt):
    im = burst_bg((255, 186, 120), (255, 210, 150), 18, lt*0.5)
    p = inflate(t)
    def f(d):
        if p > 0.3:
            for k, (x, y) in enumerate(((170, 900), (850, 860), (200, 600))):
                puff_cloud(d, x + 20*math.sin(lt*6 + k), y - 40*((lt*1.5 + k*0.33) % 1), 0.8)
            anger_mark(d, 800, 620, 1.8 + 0.3*math.sin(lt*14))
    fx(im, f)
    puffed_gola(im, "panic" if speaking("GOLA", t) else "open", mouth("GOLA", t), 500, 1640, 1.35, t, "down")
    # puff-o-meter (top-left, away from right edge)
    put_center(im, text_img("PUFF LEVEL", 64, (255, 255, 255)), 470, 210, pop(lt/0.3))
    bar = Image.new("RGBA", (640, 80), (0, 0, 0, 0)); bd = ImageDraw.Draw(bar)
    bd.rounded_rectangle([4, 4, 636, 76], 36, fill=(255, 255, 255), outline=(74, 46, 58), width=7)
    fill_w = int(12 + 612*min(1, p*1.0))
    if fill_w > 40: bd.rounded_rectangle([12, 12, fill_w, 68], 28, fill=(255, 110, 120))
    put_center(im, bar, 470, 320)
    pct = int(round(min(1, p)*100)) if lt < 4.4 else 999
    put_center(im, text_img(f"{pct}%", 76, (255, 236, 150) if pct < 999 else (255, 90, 110)), 470, 430,
               pop((lt - 4.4)/0.3) if pct == 999 else 1.0, -6 if pct == 999 else 0)
    return cam(im, 1.0 + 0.04*ease(lt/5), 500, 960, shake=(8 if lt > 4.4 else 0), t=t)

def shot_showoff(t, lt):
    im = CAFE.copy()
    fallen = t >= TOPPLE
    # Chiku + Fizz watching (left)
    ce = "shocked" if fallen and t < TOPPLE + 0.8 else ("happy" if not fallen else "joy")
    paste_char(im, chiku(ce, 0, blinking(t, 0.3), "front"), 230, 1290, 0.9)
    paste_char(im, fizz("shocked" if fallen else "smug", 0, "fold", 0.0, blinking(t, 0.7)), 170, 900, 0.42)
    # Gola strikes a pose with a leaf fan stuck behind him
    gx, gf = 720, 1290
    rot = 0.0
    if fallen:
        x = (t - TOPPLE)/0.45
        rot = -80*ease(x); gf = 1290 - 30*math.sin(min(1, x)*math.pi)
    sway = 0 if fallen else 6*math.sin(lt*5)
    spread = ease((lt - 0.3)/0.6)
    if not fallen and spread > 0:
        def f(d):
            leaf_fan(d, gx + 40 + sway, gf - 300, 2.2, spread)
        fx(im, f)
    puffed_gola(im, "sparkle" if not fallen else "panic", mouth("GOLA", t), gx + sway, gf, 0.95, t,
                "up" if not fallen else "down", rot=rot - sway*0.6, wob=not fallen)
    if fallen:
        def g(d):
            for k in range(5):   # leaves fluttering down
                rs = random.Random(k)
                x0 = 640 + rs.uniform(-200, 220); y = 700 + (t - TOPPLE)*rs.uniform(90, 160)
                poly(d, rot_ellipse(x0 + 30*math.sin(t*4 + k), y, 22, 56, 40*math.sin(t*3 + k)), (130, 206, 120), ow=4)
            for k in range(5):   # dizzy stars
                a = t*5 + k*2*math.pi/5
                star(d, 840 + 130*math.cos(a), 1040 + 40*math.sin(a), 22, (255, 240, 140), ow=3)
        fx(im, g)
        put_center(im, text_img("BOING!", 104, (255, 236, 150)), 700, 440, pop((t - TOPPLE)/0.3), 7)
    else:
        if lt > 0.6:
            put_center(im, text_img("ta-daa!", 72, (255, 255, 255)), 720, 380, pop((lt - 0.6)/0.3), -5)
    return cam(im, 1.02, 540, 960, shake=(14 if TOPPLE <= t < TOPPLE + 0.3 else 0), t=t)

def shot_caught(t, lt):
    sad = t >= 24.4
    im = (CAFE_BLUE if sad else CAFE).copy()
    paste_char(im, chiku("sparkle" if not sad else "love", mouth("CHIKU", t), blinking(t, 0.9), "front"), 280, 1270, 1.0, *squash(lt, 1.0, 0.02))
    ge = "shocked" if not sad else "sad"
    puffed_gola(im, ge, mouth("GOLA", t), 750, 1270, 0.95, t, "front", flip=True, wob=False)
    def f(d):
        if not sad:
            sweat(d, 930, 720 + ((lt*100) % 90), 1.1); sweat(d, 600, 760 + ((lt*100 + 40) % 90), 0.9)
        else:
            rain_cloud(d, 750, 430, t, 1.0)
    fx(im, f)
    if not sad and lt > 0.3:
        put_center(im, text_img("busted~", 70, (255, 190, 210)), 300, 420, pop((lt - 0.3)/0.3), 6)
    return cam(im, 1.0 + (0.08*ease((t - 24.4)/0.6) if sad else 0), 700 if sad else 540, 900)

def shot_makeup(t, lt):
    im = CAFE_PINK.copy()
    lean = 0.0
    for tt in TAPS:
        for k in (0, 0.42):
            x = (t - (tt + k - 0.18))/0.36
            if 0 <= x <= 1: lean = max(lean, math.sin(x*math.pi))
    # Chiku walks over for the boop
    app = ease((t - 31.2)/0.8)
    cx_c = 300 + 90*app + 34*lean
    boop = BOOP <= t < BOOP + 0.5
    ce = "love" if t >= BOOP + 0.5 else ("joy" if boop else ("happy" if speaking("CHIKU", t) else "love"))
    paste_char(im, chiku(ce, mouth("CHIKU", t), False, "front" if boop else "down"), cx_c, 1260, 1.0, rot=-9*lean)
    p = inflate(t)
    ge = "love" if t >= BOOP + 0.7 else ("shocked" if t >= BOOP else "guilty")
    gx = 720 - 34*lean
    puffed_gola(im, ge, 0, gx, 1260, 0.95, t, "down", flip=True, rot=9*lean, wob=False)
    def f(d):
        float_hearts(d, t, 10, 80, 900, 200, 1150, 11)
        if boop:
            heart(d, 560, 820, 60*pop((t - BOOP)/0.3), (255, 110, 150), ow=4)
        if BOOP <= t < BOOP + 0.9:   # air puffs escaping
            x = (t - BOOP)/0.9
            for k in range(4):
                a = math.radians(-160 + k*40)
                puff_cloud(d, gx + 60 + 260*x*math.cos(a), 640 + 220*x*math.sin(a), 0.45*(1 - x*0.5))
        for tt in TAPS:
            x = t - tt
            if 0 <= x < 1.0:
                for k in range(10):
                    a = k*2*math.pi/10; r = 60 + 360*ease(x)
                    heart(d, 510 + r*math.cos(a), 600 + r*math.sin(a)*0.8, 44*(1 - x*0.6), (255, 110, 150), ow=3.5)
                star(d, 510, 600, 70*(1 - x), (255, 250, 210), ow=4)
    fx(im, f)
    if boop:
        put_center(im, text_img("boop!", 90, (255, 150, 190)), 540, 440, pop((t - BOOP)/0.3), 6)
    if BOOP + 0.5 <= t < TAPS[0]:
        put_center(im, text_img("pfffff~", 74, (255, 255, 255)), 760, 420, pop((t - BOOP - 0.5)/0.3), -6)
    for tt in TAPS:
        if tt <= t < tt + 1.3:
            put_center(im, text_img("tap-tap!", 92, (255, 150, 190)), 500, 380, pop((t - tt)/0.3), -5)
    return cam(im, 1.05, 510, 960)

def shot_dumpling(t, lt):
    im = CAFE.copy()
    im.alpha_composite(TABLE)
    two = t >= 39.6
    def f(d):
        plate(d, 540, 990, 0.8)
        dumpling(d, 540, 985, 0.75)
    fx(im, f)
    gexpr = "sparkle" if not two else "panic"
    paste_char(im, gola(gexpr, mouth("GOLA", t), blinking(t, 0.2) and False, "front"), 840, 1290, 0.9, flip=True)
    ce = "happy" if not two else ("pout" if speaking("CHIKU", t) else "joy")
    paste_char(im, chiku(ce, mouth("CHIKU", t), blinking(t, 0.6) and not two, "front"), 230, 1290, 0.9)
    if t >= 37.6 and not two:
        put_center(im, text_img("x2 ?", 96, (255, 236, 150)), 830, 470, pop((t - 37.6)/0.3), 8)
    if two:
        put_center(im, text_img("ONE!", 110, (255, 255, 255)), 280, 430, pop((t - 39.9)/0.3) if t > 39.9 else 0.01, 6)
        fx(im, lambda d: sweat(d, 960, 760, 1.1))
    return cam(im, 1.0 + 0.05*ease(lt/4), 540, 960)

def shot_next(t, lt):
    im = SKY_NEXT.copy()
    fx(im, lambda d: float_hearts(d, t, 8, 60, 900, 200, 1500, 13))
    # back to back, arms crossed, refusing to look
    paste_char(im, chiku("pout", 0, False, "cross"), 300, 1300, 0.9)
    paste_char(im, gola("sad", 0, False, "front", False, True), 700, 1300, 0.9, flip=True)
    def f(d):
        if lt > 0.8:
            puff_cloud(d, 500, 640 - 30*((lt*1.2) % 1), 0.55)
    fx(im, f)
    if lt > 0.8:
        put_center(im, text_img("...", 90, (255, 255, 255)), 500, 600, pop((lt - 0.8)/0.3))
        put_center(im, text_img("hmph!", 54, (255, 190, 210)), 230, 690, pop((lt - 1.1)/0.3), 8)
        put_center(im, text_img("hmph!", 54, (255, 210, 150)), 780, 690, pop((lt - 1.3)/0.3), -8)
    put_center(im, text_img("NEXT:", 70, (255, 236, 150)), 490, 230, pop(lt/0.3))
    put_center(im, text_img(NEXT, 90, (255, 255, 255)), 490, 350, pop((lt - 0.25)/0.35) if lt > 0.25 else 0.01)
    put_center(im, text_img("Follow for Ep 4!", 58, (255, 200, 220)), 490, 1450, pop((lt - 0.8)/0.3) if lt > 0.8 else 0.01)
    return im

SHOT_FN = {"title": shot_title, "compliment": shot_compliment, "puff": shot_puff, "showoff": shot_showoff,
           "caught": shot_caught, "makeup": shot_makeup, "dumpling": shot_dumpling, "next": shot_next}

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

    def inflate_sfx(dur=2.5):   # rising balloon-stretch squeak
        n = int(dur*SR); x = tv(n)
        f = 220 + 520*(x/dur)**1.3
        s = np.sin(2*np.pi*np.cumsum(f)/SR)*(0.6 + 0.4*np.sin(2*np.pi*11*x))
        return s*env(n, 0.05, 0.1)*0.6
    def deflate_sfx(dur=0.9):   # comic pffff: falling whistle + airy noise
        n = int(dur*SR); x = tv(n)
        f = 900*np.exp(-x*2.4) + 140
        s = np.sin(2*np.pi*np.cumsum(f)/SR)*0.5 + lp(noise(dur), 6)*0.35
        return s*env(n, 0.01, 0.2)*np.sin(np.pi*np.clip(x/dur, 0, 1))**0.4

    happy_section(0.0, 9.6)
    # puff: tense rising stabs
    for k in range(5):
        st_ = sum(np.sin(2*np.pi*note(m + k)*tv(int(0.5*SR))) for m in (55, 58, 62))*np.exp(-tv(int(0.5*SR))*5)
        add(st_, 9.7 + k*1.05, vol=0.11)
        add(drum(110, 0.3), 9.7 + k*1.05, vol=0.33)
    happy_section(15.0, 21.4, 0.85)
    happy_section(21.4, 24.4, 0.7)
    sad_section(24.4, 28.0)
    happy_section(28.0, TOTAL, 1.0)
    duck = np.ones(N)
    for _, _, s, e in LINES:
        i, j = int((s - 0.15)*SR), int((e + 0.2)*SR); duck[i:j] = 0.62
    duck = np.convolve(duck, np.ones(2205)/2205, mode="same")
    L *= duck; R *= duck

    # --- sfx
    add(popfx(800), 0.2, vol=0.5); add(popfx(1000), 0.7, vol=0.5); add(boing(260, 620), 1.2, vol=0.35)
    add(inflate_sfx(1.0), 1.8, vol=0.25)
    for name, s, e in SHOTS[1:]: add(whoosh(0.4), s - 0.2, vol=0.22)
    add(squawk(0.25, 1400), 3.8, pan=0.2, vol=0.35)
    for k in range(6): add(marimba(note(84 + [0, 2, 4, 7, 9, 12][k]), 0.5), 4.4 + k*0.06, pan=0.2, vol=0.28)   # fan flourish
    add(boing(500, 900, 0.3), 5.6, pan=0.6, vol=0.45)                                                          # Gola !!
    add(inflate_sfx(2.6), 10.0, vol=0.45)
    add(popfx(500, 0.12), 14.0, vol=0.6); add(drum(160, 0.3), 14.0, vol=0.5)                                 # 999%
    for k in range(7): add(marimba(note(76 + [0, 4, 7, 12, 7, 12, 16][k]), 0.5), 15.6 + k*0.08, pan=0.3, vol=0.25)  # ta-daa
    for k in range(6): add(popfx(260, 0.08), 16.8 + k*0.38, pan=0.3, vol=0.25)                                # wobble steps
    add(boing(700, 160, 0.6), TOPPLE, vol=0.6); add(drum(90, 0.35), TOPPLE + 0.4, vol=0.55)
    for k in range(4): add(marimba(note(96 - k*2), 0.4), TOPPLE + 0.6 + k*0.12, vol=0.18)                    # dizzy stars
    add(squawk(0.18, 1600), TOPPLE + 0.5, pan=-0.5, vol=0.3)
    for k in range(3): add(popfx(1100 + 150*k, 0.08), 22.9 + k*0.18, pan=-0.3, vol=0.3)                       # busted giggle
    add(wahwah(), 24.5, vol=0.4)
    add(popfx(1300, 0.1), BOOP, vol=0.7); add(boing(400, 900, 0.25), BOOP + 0.05, vol=0.4)                    # boop
    add(deflate_sfx(0.9), BOOP + 0.15, vol=0.6)
    for tt in TAPS: add(taptap(), tt - 0.05, vol=0.9)
    add(boing(300, 700), 37.5, vol=0.3)
    add(boing(700, 300, 0.35), 39.9, vol=0.45)
    for k in range(5): add(marimba(note(96 - k*3), 0.5), 42.0 + k*0.06, vol=0.25)
    add(drum(140, 0.25), 42.9, vol=0.35); add(drum(140, 0.25), 43.1, vol=0.35)

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
    vpath, apath = os.path.join(TMP, "_c3_v.mp4"), os.path.join(TMP, "_c3_a.wav")
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
