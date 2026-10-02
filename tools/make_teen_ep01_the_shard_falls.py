"""SKYFORGE SAGA Ep 1: The Shard Falls  (no-voice build: music + sfx + timed captions)."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/01_the_shard_falls.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 1, "The Shard Falls", "The Cracked Blade"
rng = random.Random(11)

# ------------------------------------------------------------ timeline
SHOTS = [("title", 0.0, 4.0), ("wide", 4.0, 10.5), ("ren_calm", 10.5, 17.0), ("sky", 17.0, 22.5),
         ("ren_shock", 22.5, 28.0), ("impact", 28.0, 33.0), ("crater", 33.0, 40.0),
         ("king", 40.0, 47.5), ("ren_resolve", 47.5, 53.0), ("next", 53.0, 57.0)]
TOTAL = 57.0
IMPACT = 29.6
LINES = [  # speaker, text, start, end
    ("NARRATOR", "Long ago, the sky broke apart... and its pieces still fall.", 4.4, 10.2),
    ("REN", "Another quiet night on Ember Isle. Nothing ever happens here.", 10.9, 16.7),
    ("NARRATOR", "Then... the stars began to move.", 17.4, 21.0),
    ("REN", "That's no star... it's coming straight for us!", 22.8, 27.7),
    ("REN", "A sky-shard... and it's glowing. Like it knows me.", 33.6, 39.6),
    ("NARRATOR", "Far across the clouds, someone else was watching.", 40.3, 43.7),
    ("HOLLOW KING", "At last. The first shard has woken.", 44.0, 47.3),
    ("REN", "Whoever comes for this... they'll have to get through me.", 47.8, 52.8),
]
TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "HOLLOW KING": (190, 120, 255)}

# ------------------------------------------------------------ backgrounds
def grad(w, h, stops):
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3))
    for c in range(3):
        out[:, c] = np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops])
    return np.repeat(out[:, None, :], w, axis=1).astype(np.uint8)

def stars(im, n, ymax, seed=1):
    r = random.Random(seed); d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = r.randint(0, im.width), r.randint(0, ymax); s = r.choice([1, 1, 2, 2, 3])
        d.ellipse([x-s, y-s, x+s, y+s], fill=(255, 250, 230))

def sky_cracks(im, seed=2):
    r = random.Random(seed)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for _ in range(3):
        x, y = r.randint(0, im.width), r.randint(40, im.height//4)
        pts = [(x, y)]
        for _ in range(7):
            x += r.randint(60, 140) * r.choice([-1, 1]); y += r.randint(10, 60); pts.append((x, y))
        d.line(pts, fill=(90, 230, 255, 140), width=4)
    glow = lay.filter(ImageFilter.GaussianBlur(10))
    im.alpha_composite(glow); im.alpha_composite(lay)

def clouds(im, y0, y1, seed=3, tint=(255, 170, 120)):
    r = random.Random(seed)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(160):
        x = r.randint(-200, im.width+200); y = r.randint(y0, y1)
        rw, rh = r.randint(120, 320), r.randint(40, 100)
        k = (y - y0) / max(1, (y1 - y0))
        col = tuple(int(tint[c]*(1-k) + (40, 70, 100)[c]*k) for c in range(3))
        d.ellipse([x-rw, y-rh, x+rw, y+rh], fill=col + (200,))
    lay = lay.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(lay)

def island(im, cx, ty, w, depth, seed, houses=0, lit=True):
    r = random.Random(seed); d = ImageDraw.Draw(im)
    pts = [(cx - w/2, ty)]
    n = 9
    for i in range(1, n):
        x = cx - w/2 + w*i/n
        y = ty + depth*(1 - abs(i - n/2)/(n/2))**0.7 * (0.75 + 0.35*r.random())
        pts.append((x, y))
    pts.append((cx + w/2, ty))
    d.polygon(pts, fill=(58, 46, 60), outline=(14, 12, 22))
    for i in range(1, n, 2):  # rock strata cel shading
        d.polygon([pts[i], pts[i+1], (pts[i+1][0], ty+12)], fill=(42, 34, 48))
    d.ellipse([cx - w/2 - 6, ty - w*0.07, cx + w/2 + 6, ty + w*0.07], fill=(52, 104, 92), outline=(14, 12, 22), width=3)
    d.ellipse([cx - w/2 + 20, ty - w*0.06, cx + w/4, ty + w*0.02], fill=(70, 130, 110))
    # glowing shard veins in rock
    for _ in range(2):
        x = cx + r.uniform(-w*0.25, w*0.25); y = ty + depth*r.uniform(0.2, 0.5)
        d.polygon([(x, y-14), (x+7, y), (x, y+14), (x-7, y)], fill=(100, 230, 255))
    for hidx in range(houses):
        hx = cx - w*0.33 + hidx * (w*0.66 / max(1, houses-1)) + r.uniform(-8, 8)
        hw, hh = w*0.09, w*0.08
        by = ty - w*0.02
        d.rectangle([hx-hw/2, by-hh, hx+hw/2, by], fill=(92, 70, 72), outline=(14, 12, 22), width=2)
        d.polygon([(hx-hw*0.65, by-hh), (hx+hw*0.65, by-hh), (hx, by-hh*1.8)], fill=(150, 64, 54), outline=(14, 12, 22))
        if lit:
            d.rectangle([hx-hw*0.2, by-hh*0.7, hx+hw*0.15, by-hh*0.35], fill=(255, 210, 110))

def chain(im, a, b, sag=60):
    d = ImageDraw.Draw(im)
    for i in range(0, 41):
        t = i/40; x = a[0] + (b[0]-a[0])*t; y = a[1] + (b[1]-a[1])*t + sag*4*t*(1-t)
        d.ellipse([x-4, y-3, x+4, y+3], outline=(30, 26, 36), width=2)

def make_wide(night=True):
    w, h = 1500, 2300
    stops = [(0, (6, 18, 36)), (0.38, (16, 52, 74)), (0.62, (190, 96, 66)), (0.72, (240, 150, 80)), (1, (60, 70, 100))] if night else \
            [(0, (20, 40, 80)), (0.4, (60, 100, 120)), (0.62, (250, 150, 80)), (0.75, (255, 200, 120)), (1, (80, 90, 120))]
    im = Image.fromarray(grad(w, h, stops)).convert("RGBA")
    stars(im, 260 if night else 80, int(h*0.5), 4)
    sky_cracks(im)
    island(im, 260, 900, 300, 260, 1)
    island(im, 1260, 760, 260, 240, 2)
    clouds(im, int(h*0.66), h, 5)
    island(im, 760, 1250, 640, 520, 3, houses=5)
    island(im, 1240, 1500, 300, 260, 6, houses=1)
    chain(im, (1030, 1250), (1120, 1500), 40)
    chain(im, (440, 1250), (400, 900), 30)
    return im.convert("RGB")

WIDE = make_wide(True)
WIDE_ARR = np.array(WIDE)
WIDE_BLUR = WIDE.filter(ImageFilter.GaussianBlur(6))

def make_king_bg():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (6, 2, 14)), (0.5, (40, 14, 60)), (0.7, (90, 30, 90)), (1, (20, 10, 30))])).convert("RGBA")
    stars(im, 120, 900, 9)
    d = ImageDraw.Draw(im)
    # dark spire fortress island
    d.polygon([(250, 1500), (400, 900), (470, 1100), (560, 600), (650, 1080), (740, 820), (900, 1500)], fill=(18, 10, 26))
    d.polygon([(200, 1500), (1000, 1500), (640, 2000)], fill=(14, 8, 20))
    for x, y in ((560, 700), (420, 1000), (740, 900)):
        d.rectangle([x-6, y, x+6, y+20], fill=(170, 90, 255))
    clouds(im, 1550, 2200, 12, tint=(120, 60, 140))
    return im.convert("RGB").filter(ImageFilter.GaussianBlur(3))

KING_BG = make_king_bg()

def make_crater_bg():
    im = Image.fromarray(grad(W, H, [(0, (6, 16, 32)), (0.3, (18, 50, 72)), (0.5, (60, 70, 90)), (1, (30, 26, 36))])).convert("RGBA")
    stars(im, 140, 600, 21); sky_cracks(im, 8)
    d = ImageDraw.Draw(im)
    # village silhouettes behind the crater
    for i, x in enumerate(range(-40, 1200, 170)):
        hh = 120 + (i*37) % 70
        d.rectangle([x, 900-hh, x+120, 900], fill=(24, 22, 34))
        d.polygon([(x-14, 900-hh), (x+134, 900-hh), (x+60, 900-hh-80)], fill=(30, 24, 38))
        if i % 2: d.rectangle([x+40, 900-hh+40, x+70, 900-hh+70], fill=(255, 190, 100))
    d.rectangle([0, 900, W, H], fill=(44, 36, 46))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([140, 960, 940, 1400], fill=(60, 220, 255, 120))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(70)))
    return im

CRATER_BG = make_crater_bg()

def make_crater_fg():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([120, 1120, 960, 1420], fill=(18, 30, 40), outline=(100, 230, 255), width=6)
    d.ellipse([200, 1170, 880, 1380], fill=(10, 20, 30))
    pts = [(0, 1260), (120, 1240), (200, 1310), (330, 1330), (540, 1350), (760, 1330), (900, 1300), (980, 1250), (1080, 1270), (1080, 1920), (0, 1920)]
    d.polygon(pts, fill=(36, 30, 40), outline=(14, 12, 22))
    r = random.Random(5)
    for _ in range(18):  # rocks on the rim
        x = r.randint(60, 1000); y = r.randint(1300, 1480); s = r.randint(18, 50)
        d.polygon([(x-s, y), (x-s*0.4, y-s*0.8), (x+s*0.6, y-s*0.6), (x+s, y)], fill=(56, 46, 58), outline=(14, 12, 22))
    return im

CRATER_FG = make_crater_fg()

# ------------------------------------------------------------ effects
EMBERS = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(30, 120), rng.uniform(0, 6.28),
           rng.choice([3, 4, 5, 6]), rng.random() < 0.3) for _ in range(70)]
_glow_cache = {}
def glow_dot(r, cyan):
    k = (r, cyan)
    if k not in _glow_cache:
        s = r*6; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        col = (110, 230, 255) if cyan else (255, 150, 60)
        d.ellipse([s/2-r*1.8, s/2-r*1.8, s/2+r*1.8, s/2+r*1.8], fill=col + (90,))
        im = im.filter(ImageFilter.GaussianBlur(r*0.8)); d = ImageDraw.Draw(im)
        d.ellipse([s/2-r*0.6, s/2-r*0.6, s/2+r*0.6, s/2+r*0.6], fill=(255, 245, 220, 255))
        _glow_cache[k] = im
    return _glow_cache[k]

def embers(im, t, amt=1.0, cyan_bias=False, speed=1.0):
    for i, (x0, y0, sp, ph, r, cy) in enumerate(EMBERS):
        if i > len(EMBERS)*amt: break
        y = (y0 - sp*speed*t) % (H + 100) - 50
        x = x0 + 30*math.sin(t*0.9 + ph)
        g = glow_dot(r, cy or cyan_bias)
        im.alpha_composite(g, (int(x - g.width/2), int(y - g.height/2)))

SPEED = []
for v in range(4):
    r = random.Random(40+v); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, cy = 500, 700
    for _ in range(90):
        a = r.uniform(0, 2*math.pi); r0 = r.uniform(420, 600); r1 = r0 + r.uniform(500, 1400)
        wdt = r.uniform(0.004, 0.012)
        d.polygon([(cx + r0*math.cos(a), cy + r0*math.sin(a)), (cx + r1*math.cos(a-wdt), cy + r1*math.sin(a-wdt)),
                   (cx + r1*math.cos(a+wdt), cy + r1*math.sin(a+wdt))], fill=(255, 255, 255, r.randint(90, 200)))
    SPEED.append(lay)

def cam(src, zoom, cx, cy):
    """crop source (PIL RGB/RGBA) around (cx,cy) in source px so output is W x H at zoom (1 = cover)."""
    sw, sh = src.size
    base = max(W/sw, H/sh); z = base*zoom
    cw, ch = W/z, H/z
    x0 = min(max(cx - cw/2, 0), sw - cw); y0 = min(max(cy - ch/2, 0), sh - ch)
    return src.resize((W, H), Image.BILINEAR, box=(x0, y0, x0+cw, y0+ch))

def shake(im, amp, t, seed=0):
    if amp <= 0: return im
    ox = amp*math.sin(t*53 + seed)*math.cos(t*31); oy = amp*math.sin(t*47 + 1.7 + seed)
    s = 1 + amp/400
    return im.transform((W, H), Image.AFFINE, (1/s, 0, ox + W*(1-1/s)/2, 0, 1/s, oy + H*(1-1/s)/2), Image.BILINEAR)

def flash(im, a, col=(220, 250, 255)):
    if a <= 0: return im
    return Image.blend(im, Image.new(im.mode, im.size, col + ((255,) if im.mode == "RGBA" else ())), min(1, a))

def vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W/2)/(W*0.75))**2 + ((y - H/2)/(H*0.7))**2)
    a = np.clip((d - 0.55)*1.4, 0, 0.6)
    lay = np.zeros((H, W, 4), np.uint8); lay[..., 3] = (a*255).astype(np.uint8)
    return Image.fromarray(lay, "RGBA")
VIG = vignette()

def light_rays(t, col=(255, 190, 110), cx=540, cy=-200, alpha=60):
    lay = Image.new("RGBA", (W//4, H//4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(9):
        a = math.radians(55 + k*8 + 3*math.sin(t*0.6 + k))
        L = 3000/4; w = 0.025
        d.polygon([(cx/4, cy/4), (cx/4 + L*math.cos(a-w), cy/4 + L*math.sin(a-w)), (cx/4 + L*math.cos(a+w), cy/4 + L*math.sin(a+w))],
                  fill=col + (int(alpha*(0.6 + 0.4*math.sin(t*1.3 + k*2))),))
    return lay.filter(ImageFilter.GaussianBlur(6)).resize((W, H), Image.BILINEAR)

# ------------------------------------------------------------ text
def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        tst = (cur + " " + wd).strip()
        if f.getlength(tst) <= maxw: cur = tst
        else: lines.append(cur); cur = wd
    lines.append(cur); return lines

CX_TEXT, MAXW = 540, 740  # text centred at 540, max 740 wide -> spans 170..910 (clear of right 150px)
_cap_cache = {}
def caption_img(speaker, text):
    k = (speaker, text)
    if k in _cap_cache: return _cap_cache[k]
    f = font(64); lines = wrap(text, f, MAXW)
    lh = 84; tagf = font(36)
    hgt = 70 + lh*len(lines) + 20
    im = Image.new("RGBA", (W, hgt), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    tw = tagf.getlength(speaker); col = TAG[speaker]
    d.rounded_rectangle([CX_TEXT - tw/2 - 22, 0, CX_TEXT + tw/2 + 22, 56], 16, fill=(10, 10, 20, 210), outline=col, width=4)
    d.text((CX_TEXT - tw/2, 6), speaker, font=tagf, fill=col)
    for i, ln in enumerate(lines):
        lw = f.getlength(ln)
        d.text((CX_TEXT - lw/2, 70 + i*lh), ln, font=f, fill=(255, 255, 255), stroke_width=9, stroke_fill=(8, 8, 16))
    _cap_cache[k] = im; return im

CAP_BOTTOM = 1555  # keep everything above the bottom 350px (1570)

def draw_caption(im, t):
    for sp, tx, s, e in LINES:
        if s <= t < e:
            c = caption_img(sp, tx)
            a = min(1, (t - s)/0.15, (e - t)/0.15)
            y = CAP_BOTTOM - c.height + int(12*(1 - min(1, (t - s)/0.2)))
            if a < 1:
                c = c.copy(); c.putalpha(c.split()[3].point(lambda v: int(v*a)))
            im.alpha_composite(c, (0, y))

def speaking(who, t):
    """returns mouth state 0/1/2 for a character from caption timing (syllable-ish pattern)."""
    for sp, tx, s, e in LINES:
        if sp == who and s <= t < e:
            p = (t - s)/(e - s); ci = int(p*len(tx))
            ch = tx[min(ci, len(tx)-1)]
            if ch in ".,!?" or tx[max(0, ci-2):ci+1].count(".") >= 2: return 0
            v = math.sin(t*2*math.pi*5.2) + 0.5*math.sin(t*2*math.pi*8.3 + 1)
            return 2 if v > 0.7 else (1 if v > -0.4 else 0)
    return 0

def blink(t, seed=0):
    return ((t + seed) % 3.7) < 0.12

def text_center(d, txt, y, sz, fill, sw=8, stroke=(8, 8, 16)):
    f = font(sz)
    while f.getlength(txt) > MAXW and sz > 20:
        sz -= 2; f = font(sz)
    d.text((CX_TEXT - f.getlength(txt)/2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def glow_text(im, txt, y, sz, fill, glow):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    text_center(d, txt, y, sz, glow + (255,), sw=14, stroke=glow + (255,))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(im); text_center(d, txt, y, sz, fill, sw=8)

def paste_bust(im, bust, scale, fx, fy):
    """place bust so its face centre (450,480 in bust px) lands at (fx,fy)."""
    b = bust.resize((int(BW*scale), int(BH*scale)), Image.BILINEAR) if scale != 1 else bust
    im.alpha_composite(b, (int(fx - 450*scale), int(fy - 480*scale)))

def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(WIDE, 1.0 + 0.04*lt, 750, 1200).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 8, 20, 255)), 0.45)
    im.alpha_composite(light_rays(t, (110, 220, 255), 540, -100, 70))
    sh = shard(240); a = ease(lt/0.6)
    s = sh.resize((int(sh.width*(0.4 + 0.6*a)),)*2, Image.BILINEAR).rotate(8*math.sin(t*2), Image.BILINEAR)
    im.alpha_composite(s, (int(540 - s.width/2), int(560 - s.height/2 + 12*math.sin(t*2))))
    embers(im, t, 0.6, True)
    if lt > 0.5: glow_text(im, "SKYFORGE SAGA", 860, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.9:
        d = ImageDraw.Draw(im)
        w = min(1, (lt - 0.9)/0.4)*300
        d.rectangle([540 - w, 1010, 540 + w, 1016], fill=(255, 170, 80))
        text_center(d, "—  Ep %d  —" % EP, 1040, 60, (255, 190, 110))
    if lt > 1.3: glow_text(im, TITLE, 1130, 92, (255, 255, 255), (255, 120, 50))
    return flash(im, max(0, 1 - lt/0.35))

def shot_wide(t, lt):
    z = 1.0 + 0.06*lt/6.5
    im = cam(WIDE, z, 500 + 50*lt, 1150 - 10*lt).convert("RGBA")
    embers(im, t, 0.8)
    return im

def ren_bg(t, lt, night=True):
    src = WIDE_BLUR
    return cam(src, 1.15, 640 + 10*lt, 1000).convert("RGBA")

def shot_ren_calm(t, lt):
    im = ren_bg(t, lt)
    im.alpha_composite(light_rays(t, (255, 170, 90), 900, -150, 40))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("calm", m, blink(t), int(t*6) % 8), 1.18 + 0.02*lt/6.5, 500, 820)
    embers(im, t, 0.5)
    return im

def meteor_pos(t):
    p = (t - 19.0)/(IMPACT - 19.0)
    return p

def draw_meteor(im, x, y, r, tail_dx, tail_dy):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.polygon([(x - r*0.8*tail_dy/math.hypot(tail_dx, tail_dy), y + r*0.8*tail_dx/math.hypot(tail_dx, tail_dy)),
               (x + r*0.8*tail_dy/math.hypot(tail_dx, tail_dy), y - r*0.8*tail_dx/math.hypot(tail_dx, tail_dy)),
               (x + tail_dx, y + tail_dy)], fill=(80, 220, 255, 160))
    d.ellipse([x - r*2.2, y - r*2.2, x + r*2.2, y + r*2.2], fill=(80, 220, 255, 140))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(max(4, r*0.6))))
    d = ImageDraw.Draw(im)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(240, 255, 255))

def ren_back_silhouette(im, x, y, sc, phase):
    d = ImageDraw.Draw(im); o = (10, 10, 18)
    a = math.sin(phase)
    d.polygon([(x-20*sc, y-150*sc), (x-60*sc, y-160*sc - 12*a*sc), (x-150*sc, y-140*sc - 30*a*sc), (x-120*sc, y-125*sc), (x-30*sc, y-135*sc)], fill=(200, 36, 50))
    d.polygon([(x-48*sc, y-150*sc), (x+48*sc, y-150*sc), (x+56*sc, y-40*sc), (x-56*sc, y-40*sc)], fill=(20, 28, 56))
    d.rectangle([x-36*sc, y-45*sc, x-10*sc, y], fill=o); d.rectangle([x+10*sc, y-45*sc, x+36*sc, y], fill=o)
    d.rectangle([x-40*sc, y-165*sc, x+40*sc, y-140*sc], fill=(200, 36, 50))
    cx, cy, R = x, y-200*sc, 42*sc; pts = []
    for i in range(14):
        ang = math.pi*2*i/14; rr = R*(1.35 if i % 2 else 1.0)
        pts.append((cx + rr*math.cos(ang), cy + rr*math.sin(ang)))
    d.polygon(pts, fill=o)
    d.polygon([(cx-14*sc, cy-40*sc), (cx-2*sc, cy-44*sc), (cx-6*sc, cy-10*sc)], fill=(220, 220, 235))

def shot_sky(t, lt):
    im = cam(WIDE, 1.25 - 0.05*lt/5.5, 750, 650 + 40*lt).convert("RGBA")
    d = ImageDraw.Draw(im)
    for k in range(10):  # stars that start to drift
        drift = max(0, lt - 1.0)
        x = (k*211 + 90) % 900 + 60 + drift*18*math.cos(k); y = 120 + (k*137) % 600 + drift*25
        s = 3 + 2*math.sin(t*4 + k)
        d.ellipse([x-s, y-s, x+s, y+s], fill=(255, 250, 220))
    if t >= 19.0:
        p = meteor_pos(t)
        x, y = 860 - 300*p, 120 + 520*p
        draw_meteor(im, x, y, 10 + 20*p, 260, -200)
    # foreground ledge + Ren from behind
    d = ImageDraw.Draw(im)
    d.polygon([(0, 1380), (260, 1350), (520, 1400), (640, 1480), (700, 1920), (0, 1920)], fill=(22, 18, 28))
    ren_back_silhouette(im, 330, 1370, 1.1, t*5)
    embers(im, t, 0.4)
    return im

def shot_ren_shock(t, lt):
    im = Image.fromarray(grad(W, H, [(0, (10, 60, 90)), (0.5, (40, 140, 170)), (1, (10, 30, 50))])).convert("RGBA")
    im.alpha_composite(SPEED[int(t*15) % 4])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    k = ease(lt/5.5); gd.ellipse([700 - 500*k, -500 - 300*k, 1200 + 300*k, 300 + 300*k], fill=(140, 240, 255, int(120 + 100*k)))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80)))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked", m, False, int(t*10) % 8), 1.55 + 0.1*ease(lt/0.4), 500, 760)
    im.alpha_composite(light_rays(t, (160, 240, 255), 1000, -200, 50 + 40*k))
    return shake(im, 4 + 10*k, t)

def shot_impact(t, lt):
    pre = t < IMPACT
    im = cam(WIDE, 1.1, 760, 1050).convert("RGBA")
    if pre:
        p = (t - 28.0)/(IMPACT - 28.0)
        x, y = 1050 - 300*p, -50 + 1120*p**1.4
        draw_meteor(im, x, y, 34, 380, -520)
        embers(im, t, 0.5, True, 2.0)
        return shake(im, 6*p, t)
    a = t - IMPACT
    # shockwave + glow at the impact site
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    R = 80 + 1400*ease(a/1.2)
    d.ellipse([700 - R, 1060 - R*0.35, 700 + R, 1060 + R*0.35], outline=(200, 250, 255, int(255*max(0, 1 - a/1.4))), width=26)
    d.ellipse([560, 900, 840, 1180], fill=(120, 240, 255, 220))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    # debris and dust
    r = random.Random(77); d = ImageDraw.Draw(im)
    for i in range(40):
        ang = r.uniform(math.pi*1.05, math.pi*1.95); sp = r.uniform(300, 900)
        x = 700 + math.cos(ang)*sp*a; y = 1040 + math.sin(ang)*sp*a + 500*a*a
        s = r.randint(6, 16)
        d.polygon([(x-s, y), (x, y-s), (x+s, y+s*0.4)], fill=(70, 56, 70), outline=(14, 12, 22))
    dust = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(dust)
    for i in range(14):
        ang = math.pi*(1 + i/13); rr = 120 + 300*ease(a/2)
        x, y = 700 + math.cos(ang)*rr*1.6, 1070 + math.sin(ang)*rr*0.5
        dd.ellipse([x-120, y-80, x+120, y+80], fill=(150, 160, 180, int(150*max(0, 1 - a/3.4))))
    im.alpha_composite(dust.filter(ImageFilter.GaussianBlur(20)))
    embers(im, t, 1.0, True, 2.5)
    im = shake(im, 30*max(0, 1 - a/1.6), t, 3)
    return flash(im, max(0, 1 - a/0.5))

def shot_crater(t, lt):
    im = CRATER_BG.copy()
    im.alpha_composite(light_rays(t, (110, 230, 255), 540, 1200, 35))
    # Ren with cyan rim light from below
    m = speaking("REN", t)
    b = ren_bust("calm" if lt < 3.5 else "determined", m, blink(t, 1.2), int(t*6) % 8)
    paste_bust(im, b, 0.95, 470, 620 - 15*ease(lt/7))
    tint = Image.new("RGBA", (W, H), (0, 0, 0, 0)); td = ImageDraw.Draw(tint)
    td.ellipse([200, 900, 900, 1500], fill=(80, 220, 255, 90))
    im.alpha_composite(tint.filter(ImageFilter.GaussianBlur(90)))
    im.alpha_composite(CRATER_FG)
    pulse = 0.5 + 0.5*math.sin(t*3.2)
    sh = shard(260)
    hal = glow_dot(30, True).resize((int(420 + 60*pulse),)*2, Image.BILINEAR)
    im.alpha_composite(hal, (int(540 - hal.width/2), int(1180 - hal.height/2)))
    im.alpha_composite(sh, (540 - sh.width//2, 1170 - sh.height//2 + int(6*math.sin(t*2))))
    embers(im, t, 0.7, True, 0.6)
    return im

def shot_king(t, lt):
    im = cam(KING_BG, 1.0 + 0.08*lt/7.5, 650, 1100).convert("RGBA")
    d = ImageDraw.Draw(im)
    if 1.5 < lt < 1.7 or 4.9 < lt < 5.05:  # distant violet lightning
        d.line([(200, 0), (260, 200), (220, 320), (300, 520)], fill=(220, 180, 255), width=6)
        im = flash(im, 0.25, (150, 90, 220))
    m = speaking("HOLLOW KING", t)
    lvl = {0: 0, 1: 2, 2: 4}[m] if m else int(1 + 0.8*math.sin(t*2))
    sc = 1.15 + 0.06*ease(lt/7.5)
    paste_bust(im, hollow_king(max(0, min(4, lvl))), sc, 520, 760)
    # violet embers
    for i, (x0, y0, sp, ph, r, cy) in enumerate(EMBERS[:30]):
        y = (y0 - sp*0.6*t) % (H + 100) - 50; x = x0 + 30*math.sin(t + ph)
        im.alpha_composite(KING_DOT, (int(x - 12), int(y - 12)))
    return shake(im, 3 if m == 2 else 0, t)

KING_DOT = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
ImageDraw.Draw(KING_DOT).ellipse([4, 4, 20, 20], fill=(190, 110, 255, 150))
KING_DOT = KING_DOT.filter(ImageFilter.GaussianBlur(3))

RESOLVE_BG = None
def shot_resolve(t, lt):
    global RESOLVE_BG
    if RESOLVE_BG is None:
        bg = make_wide(False).filter(ImageFilter.GaussianBlur(5))
        RESOLVE_BG = bg
    im = cam(RESOLVE_BG, 1.2, 760 - 20*lt, 1050).convert("RGBA")
    im.alpha_composite(light_rays(t, (255, 180, 90), 200, -200, 70))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("determined", m, blink(t, 2.0), int(t*9) % 8), 1.22 + 0.05*ease(lt/5.5), 500, 800)
    embers(im, t, 1.0, False, 1.6)
    return im

def shot_next(t, lt):
    im = shot_resolve(t, 5.5 + lt*0.2)
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.72, lt/0.3*0.72))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3)
        d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 700 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 820, 104, (255, 255, 255), (40, 200, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 990, 540 + 300*a, 996], fill=(90, 220, 255))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 1040, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1140, 50, (255, 220, 150), sw=6)
    embers(im, t, 0.5, True)
    return im

SHOT_FN = {"title": shot_title, "wide": shot_wide, "ren_calm": shot_ren_calm, "sky": shot_sky, "ren_shock": shot_ren_shock,
           "impact": shot_impact, "crater": shot_crater, "king": shot_king, "ren_resolve": shot_resolve, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    # quick white wipe-in on cuts
    if t - s < 0.08 and name not in ("title", "next"):
        im = flash(im, 0.5)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    tt_cache = {}
    def tvec(n):
        if n not in tt_cache: tt_cache[n] = np.arange(n)/SR
        return tt_cache[n]
    def add(sig, at, pan=0.0, vol=1.0):
        i = int(at*SR); j = min(N, i + len(sig))
        if j <= i: return
        L[i:j] += sig[:j-i]*vol*(1 - pan)*0.5*2/2; R[i:j] += sig[:j-i]*vol*(1 + pan)*0.5
    def saw(f, dur, nh=7, detune=0.0):
        t = tvec(int(dur*SR)); s = np.zeros_like(t)
        for h in range(1, nh+1):
            s += np.sin(2*np.pi*f*h*t*(1 + detune)) / h
        return s
    def env(n, a, r):
        e = np.ones(n); ai = int(a*SR); ri = int(r*SR)
        if ai: e[:ai] = np.linspace(0, 1, ai)
        if ri: e[-ri:] *= np.linspace(1, 0, ri)
        return e
    def note(f): return 440*2**((f - 69)/12)
    bpm = 90; beat = 60/bpm; bar = beat*4
    chords = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]  # Dm Bb F C (own progression voicing)
    # strings pad with intensity curve
    def inten(t):
        pts = [(0, 0.5), (4, 0.45), (17, 0.55), (22.5, 0.8), (29.6, 1.0), (33, 0.6), (40, 0.5), (47.5, 0.8), (53, 1.0), (57, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0 = 0.0; ci = 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar*2 + 0.4
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.003) + saw(note(m), dur, 6, -0.003))*0.5
            s *= env(len(s), 0.5, 0.8)
            add(s, t0, pan=(-0.4 + 0.27*k), vol=0.035*inten(t0))
        bs = saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.05, 0.6)
        add(bs, t0, vol=0.06*inten(t0))
        t0 += bar*2; ci += 1
    # plucked arpeggio from 10.5s
    t0 = 10.5; k = 0
    while t0 < TOTAL - 1:
        ci = int(t0 // (bar*2)) % 4; ch = chords[ci]
        m = (ch + [ch[0] + 12, ch[1] + 12])[[0, 1, 2, 3, 4, 3, 2, 1][k % 8]] + 12
        n = int(0.4*SR); tv = tvec(n)
        s = (np.sin(2*np.pi*note(m)*tv) + 0.3*np.sin(4*np.pi*note(m)*tv))*np.exp(-9*tv)
        if not (40.0 <= t0 < 47.5): add(s, t0, pan=0.3*math.sin(k), vol=0.05)
        t0 += beat/2; k += 1
    # drums
    def kick():
        n = int(0.45*SR); tv = tvec(n)
        f = 50 + 90*np.exp(-30*tv); ph = 2*np.pi*np.cumsum(f)/SR
        return np.sin(ph)*np.exp(-7*tv)
    def snare():
        n = int(0.25*SR); tv = tvec(n)
        return (np.random.RandomState(1).randn(n)*0.6 + 0.4*np.sin(2*np.pi*190*tv))*np.exp(-16*tv)
    def taiko():
        n = int(0.8*SR); tv = tvec(n)
        f = 70 + 40*np.exp(-12*tv); ph = 2*np.pi*np.cumsum(f)/SR
        return (np.sin(ph) + 0.2*np.random.RandomState(2).randn(n)*np.exp(-30*tv))*np.exp(-5*tv)
    KICK, SNARE, TAIKO = kick(), snare(), taiko()
    b = 0
    while b*beat < TOTAL:
        tb = b*beat
        sec = (22.5 <= tb < 29.6) or (47.5 <= tb < 53.0)
        if sec:
            if b % 4 in (0, 2): add(KICK, tb, vol=0.5)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.18)
            add(SNARE[:2000]*0.5, tb + beat/2, pan=0.4, vol=0.1)
        elif (4.0 <= tb < 22.5) and b % 4 == 0:
            add(TAIKO, tb, vol=0.32)
        elif 40.0 <= tb < 47.5 and b % 8 == 0:
            add(TAIKO, tb, vol=0.45)
        b += 1
    # whooshes on cuts
    rs = np.random.RandomState(9)
    def whoosh(dur=0.6, up=True):
        n = int(dur*SR); x = rs.randn(n); y = np.zeros(n); a = 0.0
        cut = np.linspace(0.02, 0.35, n) if up else np.linspace(0.35, 0.02, n)
        for i in range(n):
            a += cut[i]*(x[i] - a); y[i] = a
        e = np.sin(np.pi*np.linspace(0, 1, n))**2
        return y*e*3
    WH = whoosh(); WH2 = whoosh(0.9, False)
    for name, s, e in SHOTS[1:]:
        add(WH if name != "impact" else WH2, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.35)
    # title hit + shimmer
    n = int(2.5*SR); tv = tvec(n)
    add((np.sin(2*np.pi*55*tv)*np.exp(-2.5*tv) + 0.4*rs.randn(n)*np.exp(-12*tv)), 0.05, vol=0.55)
    for i, m in enumerate([74, 77, 81, 86]):
        n = int(1.6*SR); tv = tvec(n)
        add(np.sin(2*np.pi*note(m)*tv)*np.exp(-2.2*tv), 0.6 + i*0.12, pan=-0.5 + i*0.33, vol=0.07)
    # meteor whistle 19 -> impact
    n = int((IMPACT - 19.0)*SR); tv = tvec(n)
    f = np.linspace(1400, 220, n); ph = 2*np.pi*np.cumsum(f)/SR
    amp = np.linspace(0, 1, n)**2
    nz = whoosh(IMPACT - 19.0, True)
    add((np.sin(ph)*0.25 + nz*0.5)*amp, 19.0, vol=0.35)
    # impact boom
    n = int(3.5*SR); tv = tvec(n)
    f = 38 + 60*np.exp(-6*tv); ph = 2*np.pi*np.cumsum(f)/SR
    boom = np.sin(ph)*np.exp(-1.3*tv) + 0.7*whoosh(3.5, False)*np.exp(-1.0*tv)
    add(boom, IMPACT, vol=0.9)
    for k in range(25):  # debris clatter
        tk = IMPACT + 0.3 + rs.uniform(0, 2.2); n = int(0.06*SR); tv = tvec(n)
        add(rs.randn(n)*np.exp(-60*tv), tk, pan=rs.uniform(-0.8, 0.8), vol=0.08)
    # shard hum 33-40 + sparkles
    n = int(7.0*SR); tv = tvec(n)
    hum = sum(np.sin(2*np.pi*fq*tv) for fq in (293.7, 440, 587.3, 880))*(0.6 + 0.4*np.sin(2*np.pi*3.2/ (2*np.pi) * 2*np.pi*tv/1))/4
    add(hum*env(n, 0.8, 1.0), 33.0, vol=0.09)
    for k in range(14):
        tk = 33.4 + k*0.45; n = int(0.5*SR); tv = tvec(n)
        add(np.sin(2*np.pi*note(rs.choice([86, 89, 93, 98]))*tv)*np.exp(-8*tv), tk, pan=rs.uniform(-0.6, 0.6), vol=0.05)
    # Hollow King drone
    n = int(7.5*SR); tv = tvec(n)
    dr = (saw(note(38), 7.5, 5) + 0.5*np.sin(2*np.pi*note(45)*tv*(1 + 0.003*np.sin(2*np.pi*5*tv))))*env(n, 1.0, 1.2)
    add(dr, 40.0, vol=0.08)
    # final hit for NEXT
    n = int(3.5*SR); tv = tvec(n)
    add(np.sin(2*np.pi*55*tv)*np.exp(-1.6*tv) + 0.5*whoosh(3.5, False)*np.exp(-2*tv), 53.0, vol=0.6)
    for i, m in enumerate([62, 69, 74, 77, 81]):
        n = int(3.0*SR); tv = tvec(n)
        add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv)*env(n, 0.02, 0.5), 53.05, pan=-0.6 + 0.3*i, vol=0.05)
    st = np.stack([L, R], 1)
    fade = np.ones(N); fl = int(1.5*SR); fade[-fl:] = np.linspace(1, 0, fl); fi = int(0.02*SR); fade[:fi] = np.linspace(0, 1, fi)
    st *= fade[:, None]
    st = np.tanh(st/ max(1e-9, np.abs(st).max())*1.6)*0.85
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((st*32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    if os.environ.get("PREVIEW"):
        for ts in os.environ["PREVIEW"].split(","):
            frame(float(ts)).save(os.path.join(TMP, "prev_%s.png" % ts))
        sys.exit()
    vpath, apath = os.path.join(TMP, "_ep_v.mp4"), os.path.join(TMP, "_ep_a.wav")
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
