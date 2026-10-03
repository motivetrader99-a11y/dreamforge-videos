"""SKYFORGE SAGA Ep 2: The Cracked Blade  (no-voice build: music + sfx + timed captions).
Reuses the Ep 1 effect/caption helpers; all shots, layouts and the score are new."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, glow_dot, SPEED, cam, shake, flash,
                                            VIG, light_rays, text_center, glow_text, paste_bust, ease, blink, KING_BG, KING_DOT,
                                            EMBERS, make_wide)

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/02_the_cracked_blade.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 2, "The Cracked Blade", "Hollow Soldiers"

SHOTS = [("title", 0.0, 4.0), ("anvil", 4.0, 10.5), ("ren_calm", 10.5, 16.5), ("fusion", 16.5, 21.5),
         ("ren_shock", 21.5, 26.5), ("reveal", 26.5, 34.0), ("mire", 34.0, 42.5), ("king", 42.5, 48.0),
         ("resolve", 48.0, 53.5), ("next", 53.5, 57.5)]
TOTAL = 57.5
FLASH_T = 26.5
LINES = [
    ("NARRATOR", "The shard had fallen. Now... it wanted something.", 4.4, 10.1),
    ("REN", "Grandpa's old sword. Snapped in half... just like the sky.", 10.9, 16.2),
    ("NARRATOR", "And the shard answered.", 17.0, 20.8),
    ("REN", "Wait, wait! It's fusing with the blade?!", 21.8, 26.2),
    ("REN", "Cracked... but stronger than it's ever been.", 28.2, 33.6),
    ("CAPTAIN MIRE", "My King. The shard chose a bearer. A village boy.", 34.6, 41.9),
    ("HOLLOW KING", "Then bring me the boy... and the blade.", 43.0, 47.6),
    ("REN", "Let them come. This blade just woke up... and so did I.", 48.4, 53.3),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "HOLLOW KING": (190, 120, 255), "CAPTAIN MIRE": (255, 150, 90)}
draw_caption, speaking = e1.draw_caption, e1.speaking

# ------------------------------------------------------------ backgrounds
def make_forge():
    im = Image.fromarray(grad(W, H, [(0, (20, 14, 20)), (0.45, (46, 30, 34)), (0.62, (70, 40, 34)), (1, (26, 18, 22))])).convert("RGBA")
    d = ImageDraw.Draw(im); r = random.Random(4)
    for row in range(16):  # stone wall bricks
        y = row*80
        off = 0 if row % 2 else 70
        for x in range(-140 + off, W + 140, 140):
            sh = r.randint(-8, 8)
            d.rectangle([x+4, y+4, x+136, y+76], fill=(56+sh, 40+sh, 42+sh), outline=(24, 16, 20), width=3)
    # round window with dusk sky + a floating island
    d.ellipse([640, 180, 960, 500], fill=(240, 140, 80), outline=(20, 14, 18), width=10)
    win = Image.fromarray(grad(300, 300, [(0, (30, 60, 100)), (0.55, (220, 120, 80)), (1, (250, 180, 110))])).convert("RGBA")
    m = Image.new("L", (300, 300), 0); ImageDraw.Draw(m).ellipse([0, 0, 300, 300], fill=255)
    im.paste(win, (650, 190), m); d = ImageDraw.Draw(im)
    d.polygon([(740, 360), (860, 360), (820, 420), (790, 430)], fill=(40, 30, 44)); d.ellipse([736, 350, 864, 372], fill=(50, 96, 86))
    d.line([(800, 190), (800, 490)], fill=(20, 14, 18), width=8); d.line([(650, 340), (950, 340)], fill=(20, 14, 18), width=8)
    # furnace on the left
    d.rectangle([-20, 700, 300, 1250], fill=(70, 50, 48), outline=(20, 14, 18), width=6)
    d.polygon([(40, 1040), (260, 1040), (240, 860), (60, 860)], fill=(255, 120, 40), outline=(20, 14, 18))
    d.polygon([(70, 1040), (230, 1040), (210, 930), (90, 930)], fill=(255, 210, 90))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([-200, 700, 500, 1300], fill=(255, 120, 40, 120))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(90)))
    d = ImageDraw.Draw(im)
    # hanging tools
    for i, x in enumerate((420, 500, 570)):
        d.line([(x, 560), (x, 640 + i*20)], fill=(30, 24, 26), width=6)
        d.rectangle([x-20, 640 + i*20, x+20, 700 + i*20], fill=(120, 120, 130), outline=(20, 14, 18), width=3)
    # floor
    d.rectangle([0, 1250, W, H], fill=(40, 30, 32)); d.line([(0, 1250), (W, 1250)], fill=(20, 14, 18), width=6)
    return im

FORGE = make_forge()
FORGE_BLUR = FORGE.filter(ImageFilter.GaussianBlur(7))

def anvil(im, cx, top):
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    d.polygon([(cx-300, top), (cx+220, top), (cx+330, top-10), (cx+250, top+40), (cx+160, top+70), (cx-200, top+70), (cx-260, top+40)], fill=(70, 74, 86), outline=o)
    d.polygon([(cx-280, top+4), (cx+200, top+4), (cx+190, top+16), (cx-270, top+16)], fill=(150, 156, 170))
    d.polygon([(cx-120, top+70), (cx+80, top+70), (cx+60, top+200), (cx+140, top+260), (cx-180, top+260), (cx-100, top+200)], fill=(52, 54, 64), outline=o)
    d.rectangle([cx-220, top+260, cx+180, top+300], fill=(80, 56, 44), outline=o, width=4)

DECK = None
def make_deck():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (30, 14, 40)), (0.35, (120, 50, 70)), (0.55, (230, 120, 70)), (0.7, (110, 60, 90)), (1, (30, 20, 40))])).convert("RGBA")
    stars(im, 60, 500, 31)
    clouds(im, 1100, 1700, 41, tint=(220, 120, 110))
    d = ImageDraw.Draw(im)
    # dark warship sails + rigging
    for x, top, wd in ((260, 200, 300), (820, 120, 360)):
        d.line([(x, top - 60), (x, 1500)], fill=(30, 20, 30), width=18)
        d.polygon([(x - wd/2, top), (x + wd/2, top + 30), (x + wd/2 - 30, top + 620), (x - wd/2 + 20, top + 600)], fill=(56, 30, 66), outline=(14, 10, 20))
        d.polygon([(x - 20, top + 220), (x + 30, top + 210), (x + 50, top + 290), (x, top + 340), (x - 40, top + 280)], fill=(150, 80, 220))
        d.line([(x, top - 60), (x + 560, 1300)], fill=(30, 20, 30), width=4)
    # rail
    d.rectangle([0, 1500, w, 1560], fill=(50, 34, 40), outline=(14, 10, 20), width=5)
    for x in range(0, w, 90): d.rectangle([x, 1560, x + 30, 1720], fill=(40, 28, 34))
    d.rectangle([0, 1720, w, h], fill=(34, 24, 30))
    return im.convert("RGB")

def make_dawn():
    im = make_wide(False)
    return im.filter(ImageFilter.GaussianBlur(5))

# ------------------------------------------------------------ helpers
def rot_paste(im, sprite, ang, cx, cy):
    s = sprite.rotate(ang, Image.BICUBIC, expand=True)
    im.alpha_composite(s, (int(cx - s.width/2), int(cy - s.height/2)))

def sparks(im, t, cx, cy, n=26, spread=1.0, seed=3, col=(255, 200, 90)):
    r = random.Random(seed); d = ImageDraw.Draw(im)
    for i in range(n):
        ph = r.random(); per = r.uniform(0.6, 1.2)
        a = ((t + ph*per) % per)/per
        ang = r.uniform(-math.pi*0.95, -math.pi*0.05); sp = r.uniform(250, 650)*spread
        x = cx + math.cos(ang)*sp*a; y = cy + math.sin(ang)*sp*a + 500*a*a
        L = 14*(1 - a) + 4
        d.line([(x, y), (x - math.cos(ang)*L, y - math.sin(ang)*L + 6)], fill=col, width=4)

def energy_bolts(im, t, x0, y0, x1, y1, n=3, seed=0, col=(140, 240, 255)):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(n):
        r = random.Random(int(t*20)*7 + k + seed)
        pts = []
        for i in range(9):
            p = i/8
            pts.append((x0 + (x1 - x0)*p + (r.uniform(-40, 40) if 0 < i < 8 else 0), y0 + (y1 - y0)*p + (r.uniform(-20, 20) if 0 < i < 8 else 0)))
        d.line(pts, fill=col + (255,), width=5)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8))); im.alpha_composite(lay)

BLADE_BROKEN = blade_img(0, True, 1.0, 1.0)
_bc = {}
def blade(frac, glow=1.0, sc=1.0):
    k = (round(frac, 2), round(glow, 1), sc)
    if k not in _bc: _bc[k] = blade_img(frac, False, glow, sc)
    return _bc[k]

def fist(im, cx, cy, sc=1.0):
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    # sleeve
    d.polygon([(cx + 40*sc, cy + 20*sc), (cx + 380*sc, cy + 300*sc), (cx + 330*sc, cy + 420*sc), (cx - 10*sc, cy + 110*sc)], fill=COAT, outline=o, width=5)
    d.polygon([(cx - 10*sc, cy + 110*sc), (cx + 40*sc, cy + 20*sc), (cx + 80*sc, cy + 50*sc), (cx + 30*sc, cy + 140*sc)], fill=COAT_HL, outline=o, width=4)
    d.rounded_rectangle([cx - 62*sc, cy - 70*sc, cx + 62*sc, cy + 70*sc], 30*sc, fill=SKIN, outline=o, width=5)
    for k in range(3):
        y = cy - 40*sc + k*36*sc
        d.line([(cx - 60*sc, y), (cx + 10*sc, y)], fill=SKIN_SH, width=int(5*sc))
    d.ellipse([cx - 80*sc, cy - 30*sc, cx - 30*sc, cy + 30*sc], fill=SKIN, outline=o, width=4)

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(FORGE_BLUR, 1.0 + 0.05*lt, 540, 900).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 8, 18, 255)), 0.5)
    im.alpha_composite(light_rays(t, (110, 220, 255), 540, -120, 65))
    a = ease(lt/0.7)
    b = blade(1.0, 0.6 + 0.4*a, 0.62)
    rot_paste(im, b, -8 + 8*(1 - a), 540, 560 + 40*(1 - a))
    embers(im, t, 0.6, True)
    if lt > 0.5: glow_text(im, "SKYFORGE SAGA", 930, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.9:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.9)/0.4)*300
        d.rectangle([540 - w, 1080, 540 + w, 1086], fill=(255, 170, 80))
        text_center(d, "—  Ep %d  —" % EP, 1110, 60, (255, 190, 110))
    if lt > 1.3: glow_text(im, TITLE, 1200, 92, (255, 255, 255), (255, 120, 50))
    return flash(im, max(0, 1 - lt/0.35))

def shot_anvil(t, lt):
    z = 1.0 + 0.12*ease(lt/6.5)
    im = FORGE.copy()
    anvil(im, 560, 1000)
    rot_paste(im, BLADE_BROKEN.resize((200, 846), Image.LANCZOS), 90, 560, 960)
    # shard hovering, slowly descending
    sh = shard(200); bob = 10*math.sin(t*2.2)
    hal = glow_dot(30, True).resize((360, 360), Image.BILINEAR)
    sy = 600 + 120*ease(lt/6.5) + bob
    im.alpha_composite(hal, (int(560 - 180), int(sy - 180)))
    im.alpha_composite(sh, (560 - sh.width//2, int(sy - sh.height//2)))
    sparks(im, t, 260, 950, 18, 0.6, 5)
    im = cam(im, z, 560, 900 - 40*ease(lt/6.5)).convert("RGBA")
    embers(im, t, 0.5, False, 0.7)
    return im

def shot_ren_calm(t, lt):
    im = cam(FORGE_BLUR, 1.15, 360 + 20*lt, 900).convert("RGBA")
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([-300, 500, 400, 1400], fill=(255, 130, 50, 110))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(80)))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("calm", m, blink(t), int(t*6) % 8, False), 1.12, 560, 800)
    # he holds the broken sword up in the foreground
    ang = 14 + 2*math.sin(t)
    rot_paste(im, BLADE_BROKEN.resize((220, 930), Image.LANCZOS), ang, 230, 880)
    fist(im, 230 + 339*math.sin(math.radians(ang)), 880 + 339*math.cos(math.radians(ang)), 0.85)
    sparks(im, t, 120, 1150, 10, 0.5, 9)
    embers(im, t, 0.4)
    return im

def shot_fusion(t, lt):
    k = ease(lt/5.0)
    im = Image.fromarray(grad(W, H, [(0, (4, 10, 24)), (0.5, (14, 50, 80)), (1, (4, 10, 24))])).convert("RGBA")
    im.alpha_composite(SPEED[int(t*15) % 4])
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([140, 300, 940, 1300], fill=(80, 220, 255, int(60 + 140*k)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
    # the blade, rising and turning upright as it repairs
    frac = ease((lt - 1.0)/3.6)
    b = blade(frac, 0.6 + 0.4*k, 1.0) if frac > 0.02 else BLADE_BROKEN
    rot_paste(im, b, 25*(1 - k), 540, 830 - 40*k)
    # shard dives into the guard socket
    if lt < 1.4:
        p = ease(lt/1.4); sh = shard(int(140 - 60*p))
        sx, sy = 540 + 260*(1 - p), 220 + 1000*p*0.9
        im.alpha_composite(sh, (int(sx - sh.width/2), int(sy - sh.height/2)))
    else:
        energy_bolts(im, t, 540, 1250, 540, 1250 - 950*frac, 3, 1)
        energy_bolts(im, t, 300, 300 + 600*k, 540, 1200, 1, 7)
        energy_bolts(im, t, 800, 1300 - 500*k, 540, 1200, 1, 9)
    embers(im, t, 1.0, True, 2.4)
    im = shake(im, 4 + 14*k, t, 2)
    return flash(im, max(0, 1 - (lt - 1.4)/0.25) if 1.4 <= lt < 1.65 else 0)

def shot_ren_shock(t, lt):
    k = ease(lt/5.0)
    im = Image.fromarray(grad(W, H, [(0, (10, 60, 90)), (0.5, (60, 170, 200)), (1, (10, 30, 50))])).convert("RGBA")
    im.alpha_composite(SPEED[int(t*15) % 4])
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked", m, False, int(t*10) % 8, False), 1.5 + 0.08*ease(lt/0.4), 520, 760)
    # cyan up-light from the blade below frame
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([100, 1100, 1000, 2200], fill=(120, 240, 255, int(90 + 110*k)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(100)))
    energy_bolts(im, t, 80, 1500, 300, 1000, 1, 3); energy_bolts(im, t, 1000, 1500, 780, 1050, 1, 5)
    im.alpha_composite(light_rays(t, (160, 240, 255), 540, 2000, 40 + 50*k))
    return shake(im, 3 + 9*k, t, 4)

def shot_reveal(t, lt):
    im = Image.fromarray(grad(W, H, [(0, (8, 30, 60)), (0.45, (30, 120, 160)), (1, (8, 24, 40))])).convert("RGBA")
    im.alpha_composite(SPEED[int(t*8) % 4])
    im.alpha_composite(light_rays(t, (150, 240, 255), 330, 200, 70))
    m = speaking("REN", t)
    expr = "determined"
    zoom = 1.08 - 0.06*ease(lt/7.5)
    paste_bust(im, ren_bust(expr, m, blink(t, 0.6), int(t*8) % 8, False), zoom, 610, 780)
    b = blade(1.0, 0.85 + 0.15*math.sin(t*5), 1.0)
    rot_paste(im, b, -6, 300, 760)
    fist(im, 282, 1190, 1.0)
    sparks(im, t, 330, 320, 14, 0.5, 13, (170, 245, 255))
    embers(im, t, 0.8, True, 1.2)
    a = t - FLASH_T
    im = shake(im, 20*max(0, 1 - a/0.8), t, 6)
    return flash(im, max(0, 1 - a/0.6))

def shot_mire(t, lt):
    global DECK
    if DECK is None: DECK = make_deck()
    im = cam(DECK, 1.0 + 0.06*ease(lt/8.5), 640 - 30*lt, 1150).convert("RGBA")
    # clouds streaming past (airship moving)
    d = ImageDraw.Draw(im)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for i in range(7):
        x = (i*260 - t*420) % (W + 600) - 300; y = 300 + (i*173) % 900
        ld.ellipse([x - 220, y - 40, x + 220, y + 40], fill=(255, 190, 170, 70))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)))
    m = speaking("CAPTAIN MIRE", t)
    paste_bust(im, mire_bust(m, blink(t, 1.7)), 1.08, 500, 760 + 6*math.sin(t*1.4))
    embers(im, t, 0.4, False, 1.0)
    return im

def shot_king(t, lt):
    im = cam(KING_BG, 1.12 - 0.06*ease(lt/5.5), 600, 1050).convert("RGBA")
    m = speaking("HOLLOW KING", t)
    lvl = {1: 2, 2: 4}[m] if m else int(1 + 0.8*math.sin(t*2))
    paste_bust(im, e1.hollow_king(max(0, min(4, lvl))), 1.35 + 0.06*ease(lt/5.5), 540, 700)
    for i, (x0, y0, sp, ph, r, cy) in enumerate(EMBERS[:30]):
        y = (y0 - sp*0.6*t) % (H + 100) - 50; x = x0 + 30*math.sin(t + ph)
        im.alpha_composite(KING_DOT, (int(x - 12), int(y - 12)))
    if 2.6 < lt < 2.75: im = flash(im, 0.3, (150, 90, 220))
    return shake(im, 3 if m == 2 else 0, t)

DAWN = None
def shot_resolve(t, lt):
    global DAWN
    if DAWN is None: DAWN = make_dawn()
    im = cam(DAWN, 1.2, 720 - 25*lt, 1050).convert("RGBA")
    im.alpha_composite(light_rays(t, (255, 180, 90), 200, -200, 70))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("determined", m, blink(t, 2.0), int(t*9) % 8, False), 1.12 + 0.05*ease(lt/5.5), 590, 800)
    # blade resting on his shoulder, glowing
    rot_paste(im, blade(1.0, 0.8 + 0.2*math.sin(t*4), 0.85), 35, 860, 640)
    embers(im, t, 1.0, False, 1.6)
    return im

def shot_next(t, lt):
    im = shot_resolve(t, 5.5 + lt*0.2)
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.72, lt/0.3*0.72))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 700 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 820, 104, (255, 255, 255), (170, 90, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 990, 540 + 300*a, 996], fill=(170, 110, 255))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 1040, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1140, 50, (255, 220, 150), sw=6)
    embers(im, t, 0.5, True)
    return im

SHOT_FN = {"title": shot_title, "anvil": shot_anvil, "ren_calm": shot_ren_calm, "fusion": shot_fusion, "ren_shock": shot_ren_shock,
           "reveal": shot_reveal, "mire": shot_mire, "king": shot_king, "resolve": shot_resolve, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    if t - s < 0.08 and name not in ("title", "next", "reveal"):
        im = flash(im, 0.45)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio (new score: E minor, 100 bpm)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(21)
    def tv(n): return np.arange(n)/SR
    def add(sig, at, pan=0.0, vol=1.0):
        i = int(at*SR); j = min(N, i + len(sig))
        if j <= i or i < 0: return
        L[i:j] += sig[:j-i]*vol*(1 - pan)*0.5; R[i:j] += sig[:j-i]*vol*(1 + pan)*0.5
    def saw(f, dur, nh=7, det=0.0):
        t = tv(int(dur*SR)); s = np.zeros_like(t)
        for h in range(1, nh+1): s += np.sin(2*np.pi*f*h*t*(1 + det))/h
        return s
    def env(n, a, r):
        e = np.ones(n); ai, ri = int(a*SR), int(r*SR)
        if ai: e[:ai] = np.linspace(0, 1, ai)
        if ri: e[-ri:] *= np.linspace(1, 0, ri)
        return e
    def note(m): return 440*2**((m - 69)/12)
    def lp_noise(dur, c0, c1):
        n = int(dur*SR); x = rs.randn(n); y = np.zeros(n); a = 0.0; cut = np.linspace(c0, c1, n)
        for i in range(n): a += cut[i]*(x[i] - a); y[i] = a
        return y
    def whoosh(dur=0.6, up=True):
        y = lp_noise(dur, 0.02, 0.35) if up else lp_noise(dur, 0.35, 0.02)
        return y*np.sin(np.pi*np.linspace(0, 1, len(y)))**2*3
    bpm = 100; beat = 60/bpm; bar = beat*4
    chords = [[52, 55, 59], [48, 52, 55], [50, 54, 57], [47, 51, 54]]  # Em C D B
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.7
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.4), (16.5, 0.6), (21.5, 0.9), (26.5, 1.0), (34, 0.65), (42.5, 0.55), (48, 0.85), (53.5, 1.0), (57.5, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.35, 0.5)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.034*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.4), t0, vol=0.06*inten(t0))
        t0 += bar; ci += 1
    # staccato string ostinato (16ths) in the action sections
    t0, k = 0.0, 0
    while t0 < TOTAL:
        if (16.5 <= t0 < 34.0) or (48.0 <= t0 < 53.5):
            ch = chords[int(t0 // bar) % 4]; m = [ch[0], ch[0] + 12, ch[1] + 12, ch[0] + 12][k % 4]
            n = int(0.12*SR); s = saw(note(m), 0.12, 5)*np.exp(-22*tv(n))
            add(s, t0, pan=0.35*(1 if k % 2 else -1), vol=0.045)
        t0 += beat/4; k += 1
    # forge bell melody (own motif) in calm parts
    motif = [76, 79, 81, 79, 76, 74, 71, 74]
    for i, m in enumerate(motif*3):
        tt = 4.2 + i*beat
        if tt >= 16.3: break
        n = int(1.0*SR); x = tv(n)
        s = (np.sin(2*np.pi*note(m)*x) + 0.35*np.sin(2*np.pi*note(m)*2.76*x)*np.exp(-6*x))*np.exp(-3.5*x)
        add(s, tt, pan=0.2*math.sin(i), vol=0.045)
    # drums
    def kick():
        n = int(0.4*SR); x = tv(n); f = 48 + 100*np.exp(-32*x)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-8*x)
    def snare():
        n = int(0.22*SR); x = tv(n)
        return (np.random.RandomState(3).randn(n)*0.6 + 0.4*np.sin(2*np.pi*200*x))*np.exp(-17*x)
    def taiko():
        n = int(0.8*SR); x = tv(n); f = 66 + 44*np.exp(-12*x)
        return (np.sin(2*np.pi*np.cumsum(f)/SR) + 0.2*np.random.RandomState(4).randn(n)*np.exp(-30*x))*np.exp(-5*x)
    KICK, SNARE, TAIKO = kick(), snare(), taiko()
    b = 0
    while b*beat < TOTAL:
        tb = b*beat
        if (21.5 <= tb < 34.0) or (48.0 <= tb < 53.5):
            if b % 4 in (0, 2) or (b % 8 == 7): add(KICK, tb, vol=0.5)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.18)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.09)
        elif 34.0 <= tb < 42.5:  # Mire's march
            add(TAIKO, tb, vol=0.25 if b % 2 else 0.4)
        elif 42.5 <= tb < 48.0 and b % 4 == 0:
            add(TAIKO, tb, vol=0.5)
        elif 4.0 <= tb < 21.5 and b % 4 == 0:
            add(TAIKO, tb, vol=0.28)
        b += 1
    # cut whooshes
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        if name != "reveal": add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.33)
    # title hit
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # metallic anvil clangs + crackle in the forge
    def clang(f0=420):
        n = int(1.6*SR); x = tv(n)
        return sum(np.sin(2*np.pi*f0*r*x)*np.exp(-d*x) for r, d in ((1, 3), (2.41, 4), (3.93, 6), (5.6, 9)))/3
    for tc in (5.0, 8.2, 11.0): add(clang(), tc, pan=-0.3, vol=0.12)
    n = int(17.0*SR); fire = lp_noise(17.0, 0.08, 0.08)*(0.5 + 0.5*(rs.rand(n) > 0.997))
    add(fire*env(n, 0.5, 1.0), 4.0, pan=-0.5, vol=0.06)
    # fusion: rising whistle + hum to the flash
    dur = FLASH_T - 16.5; n = int(dur*SR); x = tv(n)
    f = np.linspace(180, 1500, n); amp = np.linspace(0.1, 1, n)**2
    add((np.sin(2*np.pi*np.cumsum(f)/SR)*0.25 + whoosh(dur, True)*0.5)*amp, 16.5, vol=0.3)
    add(clang(660), 17.9, vol=0.2)  # shard locks into the guard
    for k in range(18):  # electric zaps
        tk = 18.0 + rs.uniform(0, 8.0); m = int(0.08*SR)
        add(rs.randn(m)*np.exp(-40*tv(m)), tk, pan=rs.uniform(-0.8, 0.8), vol=0.07)
    # flash: boom + blade ring
    n = int(3.5*SR); x = tv(n); f = 40 + 60*np.exp(-6*x)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-1.4*x) + 0.6*whoosh(3.5, False)*np.exp(-1.2*x), FLASH_T, vol=0.85)
    add(clang(880)*1.0, FLASH_T + 0.05, pan=-0.3, vol=0.22)
    n = int(6.0*SR); x = tv(n)
    ring = sum(np.sin(2*np.pi*fq*x) for fq in (659.3, 987.8, 1318.5))*np.exp(-0.5*x)/3
    add(ring, FLASH_T + 0.1, vol=0.06)
    # Hollow King drone
    n = int(5.5*SR); x = tv(n)
    add((saw(note(40), 5.5, 5) + 0.5*np.sin(2*np.pi*note(47)*x*(1 + 0.003*np.sin(2*np.pi*5*x))))*env(n, 0.8, 1.0), 42.5, vol=0.08)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 53.5, vol=0.6)
    for i, m in enumerate([64, 71, 76, 79, 83]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 53.55, pan=-0.6 + 0.3*i, vol=0.05)
    st = np.stack([L, R], 1)
    fade = np.ones(N); fl = int(1.5*SR); fade[-fl:] = np.linspace(1, 0, fl); fi = int(0.02*SR); fade[:fi] = np.linspace(0, 1, fi)
    st *= fade[:, None]
    st = np.tanh(st/max(1e-9, np.abs(st).max())*1.6)*0.85
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
