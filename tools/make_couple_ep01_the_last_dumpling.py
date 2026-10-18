"""CHIKU & GOLA Ep 1: The Last Dumpling  (no-voice build: music + sfx + timed captions).
Chiku saves the last dumpling; sleepy Gola gulps it; epic sulk; he makes her a whole plate; tap-tap make-up.
Uses tools/couple_art.py for the characters. Original ukulele/marimba-style synth score + code-made sfx."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from couple_art import *

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "couple/01_the_last_dumpling.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 1, "The Last Dumpling", "Who Is Fizz?"

SHOTS = [("title", 0.0, 3.5), ("save", 3.5, 9.5), ("gulp", 9.5, 15.5), ("angry", 15.5, 20.5), ("panic", 20.5, 25.5),
         ("sulk", 25.5, 31.0), ("plate", 31.0, 37.0), ("tap", 37.0, 42.5), ("next", 42.5, 46.5)]
TOTAL = 46.5
LINES = [
    ("CHIKU", "The very last dumpling... I'm saving you for later!", 3.8, 8.8),
    ("GOLA", "Ooh, a lonely little dumpling. Nobody wants it?", 9.8, 13.0),
    ("CHIKU", "GOLA! Where. Is. My. Dumpling?!", 15.8, 20.0),
    ("GOLA", "What dumpling? I've never seen a dumpling in my life.", 20.8, 25.0),
    ("CHIKU", "Hmph. I'm sulking now. Forever.", 25.9, 30.6),
    ("GOLA", "Sorry, Chiku... I made you a WHOLE plate!", 31.4, 36.6),
    ("CHIKU", "...Fine. Forgiven. But you only get ONE.", 37.3, 40.3),
    ("GOLA", "Deal!", 40.6, 42.2),
]
TAG = {"CHIKU": ((96, 196, 160), "Chiku"), "GOLA": ((240, 140, 50), "Gola")}
TAPS = [38.4, 41.0]          # tap-tap moments (signature sound)
GULP_T = 13.4

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
KITCHEN = treehouse_kitchen()
KITCHEN_BLUE = treehouse_kitchen(tint=(70, 90, 150, 95))
KITCHEN_PINK = treehouse_kitchen(tint=(255, 170, 200, 60))
TABLE = table_layer()
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
def shot_title(t, lt):
    im = SKY_TITLE.copy()
    L = fx_layer(); d = ImageDraw.Draw(L)
    float_hearts(d, t, 12, 60, 900, 100, 1700, 3)
    hb = 1 + 0.12*math.sin(lt*7)
    heart(d, 490, 640, 110*hb, (255, 96, 132), ow=6)
    im.alpha_composite(fx_done(L))
    sx, sy = squash(lt, 1.6, 0.05)
    paste_char(im, chiku("joy", 0, False, "up"), 270, 1330, 1.05, sx, sy)
    sx, sy = squash(lt + 0.3, 1.6, 0.05)
    paste_char(im, gola("happy", 0, False, "up"), 710, 1330, 1.05, sx, sy)
    put_center(im, text_img("CHIKU & GOLA", 118, (255, 255, 255)), 490, 300, pop((lt - 0.2)/0.35) if lt > 0.2 else 0.01)
    if lt > 0.7:
        put_center(im, text_img(f"Ep {EP}: {TITLE}", 64, (255, 236, 150)), 490, 450, pop((lt - 0.7)/0.35))
    return im

def shot_save(t, lt):
    im = KITCHEN.copy()
    im.alpha_composite(TABLE)
    L = fx_layer(); d = ImageDraw.Draw(L)
    plate(d, 500, 1000, 0.75)
    dumpling(d, 500, 1000, 0.9)
    steam(d, 500, 920, t, 0.8)
    if lt > 1.2:
        flag(d, 540, 960)
    float_hearts(d, t, 5, 200, 420, 450, 900, 7, (22, 34))
    twinkles(d, t, 6, 420, 700, 800, 1000, 2)
    im.alpha_composite(fx_done(L))
    if lt > 1.2:
        put_center(im, text_img("CHIKU'S!", 26, (240, 80, 110), sw=0), 618, 865, pop((lt - 1.2)/0.3), -2)
    sx, sy = squash(lt, 1.2, 0.03)
    expr = "love" if lt < 1.8 or lt > 4.4 else "happy"
    paste_char(im, chiku(expr, mouth("CHIKU", t), blinking(t, 0.0), "front"), 290, 1250, 1.0, sx, sy)
    return cam(im, 1.0 + 0.08*ease(lt/6), 470, 960)

def shot_gulp(t, lt):
    im = KITCHEN.copy()
    im.alpha_composite(TABLE)
    L = fx_layer(); d = ImageDraw.Draw(L)
    plate(d, 500, 1000, 0.75)
    eaten = t >= GULP_T
    if not eaten:
        dumpling(d, 500, 1000, 0.9)
        steam(d, 500, 920, t, 0.8)
        flag(d, 540, 960)
        if lt > 2.6:   # dumpling is nervous
            sweat(d, 410, 915, 0.8)
    else:
        for (cx, cy) in ((460, 992), (530, 996), (550, 986)):
            ell(d, [cx-6, cy-5, cx+6, cy+5], (246, 222, 168), ow=2.5)
    im.alpha_composite(fx_done(L))
    if not eaten:
        put_center(im, text_img("CHIKU'S!", 26, (240, 80, 110), sw=0), 618, 865, 1.0, -2)
    # Gola walks in from the right
    wx = 1030 - 290*ease(lt/1.6)
    walk = lt < 1.6
    by = -abs(math.sin(lt*9))*14 if walk else 0
    lean = 0.0
    if 3.0 < lt < 3.9 and not eaten:   # leans toward dumpling
        lean = 8*ease((lt - 3.0)/0.4)
    if eaten:
        expr, chk, cr = ("happy", True, False) if t < GULP_T + 1.0 else ("happy", False, True)
        sx, sy = (1.12, 0.9) if t < GULP_T + 0.15 else squash(lt, 2, 0.03)
    else:
        expr, chk, cr = ("sleepy" if lt < 2.4 else "sparkle"), False, False
        sx, sy = squash(lt, 2.4 if walk else 1.0, 0.04)
    paste_char(im, gola(expr, mouth("GOLA", t), blinking(t, 0.7) and not eaten, "down", cr, chk), wx, 1250 + by, 1.0, sx, sy, rot=lean)
    if eaten and t < GULP_T + 1.6:
        k = (t - GULP_T)/0.3
        put_center(im, text_img("GULP!", 120, (255, 220, 90)), 470, 640, pop(k), 8)
    if not walk and not eaten and lt > 0.2 and lt < 2.4:
        L2 = fx_layer(); d2 = ImageDraw.Draw(L2)
        for k in range(3):   # sniff lines
            arc(d2, [580 + k*26, 860, 620 + k*26, 900], 120, 240, 4)
        im.alpha_composite(fx_done(L2))
    z = 1.0 + (0.12*ease((t - GULP_T)/0.25) if eaten else 0)
    return cam(im, z, 600, 980, shake=10 if eaten and t < GULP_T + 0.35 else 0, t=t)

def shot_angry(t, lt):
    im = burst_bg((255, 170, 170), (255, 196, 190), 18, lt*0.4)
    expr = "shocked" if lt < 0.8 else "angry"
    sx, sy = (1.0, 1.0)
    if lt < 0.25: sx, sy = 0.92, 1.1
    paste_char(im, chiku(expr, mouth("CHIKU", t) if lt > 0.3 else 0, False, "down"), 490, 1720, 1.9, sx, sy)
    L = fx_layer(); d = ImageDraw.Draw(L)
    if lt > 0.8:
        puff_cloud(d, 160 - 20*math.sin(lt*6), 900 - 40*((lt*1.5) % 1), 0.9)
        puff_cloud(d, 830 + 20*math.sin(lt*6), 860 - 40*((lt*1.5 + 0.5) % 1), 0.8)
        anger_mark(d, 760, 640, 2.0 + 0.3*math.sin(lt*14))
    else:
        for k in range(5):   # shock lines
            a = math.radians(-150 + k*30)
            line(d, [(490 + 360*math.cos(a), 540 + 300*math.sin(a)), (490 + 440*math.cos(a), 540 + 380*math.sin(a))], 9, (255, 255, 255))
    im.alpha_composite(fx_done(L))
    z = 1.0 + 0.06*max(0, 1 - lt/0.4)
    return cam(im, z, 490, 900, shake=(16 if 0.8 < lt < 1.4 else 0), t=t)

def shot_panic(t, lt):
    im = burst_bg((190, 236, 220), (214, 246, 234), 16, -lt*0.4)
    sx, sy = squash(lt, 5, 0.025)
    paste_char(im, gola("panic", mouth("GOLA", t), False, "down", True), 500 + 6*math.sin(lt*30), 1720, 1.9, sx, sy)
    L = fx_layer(); d = ImageDraw.Draw(L)
    for k, (x, y0) in enumerate(((150, 640), (830, 600), (880, 820))):
        y = y0 + ((lt*120 + k*60) % 140)
        sweat(d, x, y, 1.3)
    if lt > 3.3:
        put = True
    im.alpha_composite(fx_done(L))
    if lt > 2.8:
        put_center(im, text_img("*crumbs*", 46, (255, 236, 170)), 770, 650, pop((lt - 2.8)/0.3), -10)
    return cam(im, 1.0 + 0.04*lt/5, 500, 900)

def shot_sulk(t, lt):
    im = KITCHEN_BLUE.copy()
    expr = "pout" if lt < 2.2 else "sulk"
    paste_char(im, chiku(expr, mouth("CHIKU", t), blinking(t, 1.1), "cross"), 330, 1250, 1.05, flip=True)
    L = fx_layer(); d = ImageDraw.Draw(L)
    rain_cloud(d, 330, 470, t, 1.0)
    im.alpha_composite(fx_done(L))
    # Gola peeks in, guilty
    if lt > 2.0:
        px = 1000 - 180*ease((lt - 2.0)/0.8)
        paste_char(im, gola("guilty", 0, blinking(t, 0.4), "front"), px, 1250, 0.72)
        L = fx_layer(); d = ImageDraw.Draw(L)
        sweat(d, px + 110, 860, 1.0)
        im.alpha_composite(fx_done(L))
    if lt < 1.6:
        put_center(im, text_img("HMPH!", 96, (255, 255, 255)), 330, 300, pop(lt/0.3), 6)
    return cam(im, 1.04, 520, 960)

def shot_plate(t, lt):
    im = KITCHEN.copy()
    L = fx_layer(); d = ImageDraw.Draw(L)
    twinkles(d, t, 10, 400, 900, 700, 1200, 9)
    im.alpha_composite(fx_done(L))
    ce = "sulk" if lt < 1.2 else ("shocked" if lt < 2.0 else "sparkle")
    paste_char(im, chiku(ce, 0, blinking(t, 0.2), "cross" if lt < 1.2 else "front"), 270, 1250, 1.0)
    gx = 980 - 330*ease(lt/1.2)
    by = -abs(math.sin(lt*9))*12 if lt < 1.2 else 0
    sx, sy = squash(lt, 1.4, 0.03)
    paste_char(im, gola("happy" if not speaking("GOLA", t) else "sparkle", mouth("GOLA", t), False, "front"), gx, 1250 + by, 1.0, sx, sy)
    L = fx_layer(); d = ImageDraw.Draw(L)
    px, py = gx, 1180 + by
    plate(d, px, py, 0.85)
    for row, (n, yy) in enumerate(((3, py), (2, py - 40), (1, py - 80))):
        for k in range(n):
            dumpling(d, px + (k - (n - 1)/2)*88, yy, 0.5, face=True)
    steam(d, px, py - 140, t, 0.6)
    if lt > 1.4:
        float_hearts(d, t, 6, 120, 420, 350, 850, 5, (22, 34))
    im.alpha_composite(fx_done(L))
    if lt > 1.2:
        put_center(im, text_img("TA-DA!", 84, (255, 220, 90)), 640, 360, pop((lt - 1.2)/0.3), -6)
    return cam(im, 1.0 + 0.06*ease(lt/6), 480, 960)

def shot_tap(t, lt):
    im = KITCHEN_PINK.copy()
    # lean in for each tap-tap
    lean = 0.0
    for tt in TAPS:
        for k in (0, 0.42):
            x = (t - (tt + k - 0.18))/0.36
            if 0 <= x <= 1: lean = max(lean, math.sin(x*math.pi))
    cx_c = 320 + 34*lean; cx_g = 700 - 34*lean
    ce = "joy" if not speaking("CHIKU", t) else "happy"
    if lt > 3.3: ce = "love"
    paste_char(im, chiku(ce, mouth("CHIKU", t), False, "down"), cx_c, 1250, 1.0, rot=-9*lean)
    paste_char(im, gola("love" if not speaking("GOLA", t) else "happy", mouth("GOLA", t), False, "down"), cx_g, 1250, 1.0, flip=True, rot=9*lean)
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
    im.alpha_composite(fx_done(L))
    for tt in TAPS:
        if tt <= t < tt + 1.3:
            put_center(im, text_img("tap-tap!", 92, (255, 150, 190)), 500, 380, pop((t - tt)/0.3), -5)
    return cam(im, 1.05, 510, 960)

def feather(d, x, y, ang, s=1.0):
    pts = rot_ellipse(x, y, 34*s, 110*s, ang)
    poly(d, pts, (60, 150, 230), ow=4)
    poly(d, rot_ellipse(x, y, 18*s, 70*s, ang), (40, 200, 190))
    a = math.radians(ang)
    line(d, [(x - 130*s*math.sin(-a), y - 130*s*math.cos(a)), (x + 130*s*math.sin(-a), y + 130*s*math.cos(a))], 4)

def shot_next(t, lt):
    im = SKY_NEXT.copy()
    L = fx_layer(); d = ImageDraw.Draw(L)
    float_hearts(d, t, 8, 60, 900, 200, 1500, 13)
    feather(d, 500 + 90*math.sin(lt*2.2), 560 + 60*lt, 25*math.sin(lt*2.2), 1.0)
    im.alpha_composite(fx_done(L))
    sx, sy = squash(lt, 1.5, 0.04)
    paste_char(im, chiku("happy", mouth("CHIKU", t), blinking(t, 0.3), "front"), 310, 1300, 0.95, sx, sy)
    paste_char(im, gola("shocked" if lt > 1.0 else "sleepy", 0, False, "down"), 680, 1300, 0.95)
    L = fx_layer(); d = ImageDraw.Draw(L)
    dumpling(d, 310, 1150, 0.42)
    if lt > 1.0:
        puff = "?"
    im.alpha_composite(fx_done(L))
    if lt > 1.0:
        put_center(im, text_img("?!", 90, (255, 255, 255)), 840, 680, pop((lt - 1.0)/0.3), 10)
    put_center(im, text_img("NEXT:", 70, (255, 236, 150)), 490, 230, pop(lt/0.3))
    put_center(im, text_img(NEXT, 104, (255, 255, 255)), 490, 350, pop((lt - 0.25)/0.35) if lt > 0.25 else 0.01)
    put_center(im, text_img("Follow for Ep 2!", 58, (255, 200, 220)), 490, 1450, pop((lt - 0.8)/0.3) if lt > 0.8 else 0.01)
    return im

SHOT_FN = {"title": shot_title, "save": shot_save, "gulp": shot_gulp, "angry": shot_angry, "panic": shot_panic,
           "sulk": shot_sulk, "plate": shot_plate, "tap": shot_tap, "next": shot_next}

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
    happy_section(0.0, 25.5)
    sad_section(25.5, 31.0)
    happy_section(31.0, TOTAL, 1.0)
    # duck music under captions
    duck = np.ones(N)
    for _, _, s, e in LINES:
        i, j = int((s - 0.15)*SR), int((e + 0.2)*SR); duck[i:j] = 0.62
    duck = np.convolve(duck, np.ones(2205)/2205, mode="same")
    L *= duck; R *= duck

    # --- sfx
    add(popfx(800), 0.2, vol=0.5); add(popfx(1000), 0.7, vol=0.5); add(boing(260, 620), 1.2, vol=0.35)
    for name, s, e in SHOTS[1:]: add(whoosh(0.4), s - 0.2, vol=0.22)
    for k in range(6): add(popfx(260, 0.08), 9.6 + k*0.27, pan=0.4, vol=0.35)   # pitter-patter
    for k in range(3): add(lp(noise(0.12), 6)*np.exp(-np.arange(int(0.12*SR))/SR*20), 10.4 + 0.5*0 + k*0.2, vol=0.18)  # sniff
    add(gulp(), GULP_T, vol=0.7); add(popfx(1200), GULP_T + 0.25, vol=0.5)
    add(boing(500, 200, 0.4), 15.5, vol=0.5)
    stab = sum(np.sin(2*np.pi*note(m)*np.arange(int(0.6*SR))/SR) for m in (61, 67, 70))*np.exp(-np.arange(int(0.6*SR))/SR*4)
    add(stab, 16.3, vol=0.18)
    for k in range(3): add(boing(700, 380, 0.3), 20.7 + k*1.4, pan=(-0.4 + 0.4*k), vol=0.25)
    add(wahwah(), 25.6, vol=0.45)
    for k in range(4): add(marimba(note(84 + [0, 4, 7, 12][k]), 0.5), 32.2 + k*0.07, vol=0.3)
    add(boing(300, 700), 32.0, vol=0.3)
    for tt in TAPS: add(taptap(), tt - 0.05, vol=0.9)
    for k in range(5): add(marimba(note(96 - k*3), 0.5), 42.6 + k*0.06, vol=0.25)
    add(boing(350, 650), 43.6, vol=0.3)

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
