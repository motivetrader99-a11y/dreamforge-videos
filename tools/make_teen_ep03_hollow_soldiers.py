"""SKYFORGE SAGA Ep 3: Hollow Soldiers  (no-voice build: music + sfx + timed captions).
Reuses the Ep 1/2 effect + caption helpers; new shots, Hollow Soldier designs and a new battle score."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
import make_teen_ep02_the_cracked_blade as e2
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, glow_dot, SPEED, cam, shake, flash,
                                            VIG, light_rays, text_center, glow_text, paste_bust, ease, blink, KING_BG, KING_DOT,
                                            EMBERS, WIDE, WIDE_BLUR, CRATER_BG, ren_back_silhouette)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, energy_bolts, blade, fist

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/03_hollow_soldiers.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 3, "Hollow Soldiers", "Lyra's Airship"

SHOTS = [("title", 0.0, 4.0), ("fog", 4.0, 10.0), ("ren_alert", 10.0, 16.0), ("mire", 16.0, 23.0), ("charge", 23.0, 28.8),
         ("slash", 28.8, 34.0), ("scatter", 34.0, 40.0), ("king", 40.0, 46.0), ("resolve", 46.0, 51.5),
         ("airship", 51.5, 55.0), ("next", 55.0, 58.5)]
TOTAL = 58.5
SLASH_T = 29.6
LINES = [
    ("NARRATOR", "Word travels fast in the Shattered Skies. Too fast.", 4.4, 9.7),
    ("REN", "Is that fog? No... fog doesn't march.", 10.4, 15.6),
    ("CAPTAIN MIRE", "Hollow Soldiers! Take the blade. Leave the village standing.", 16.5, 22.6),
    ("REN", "You want the shard? Come and take it!", 23.3, 28.4),
    ("NARRATOR", "The cracked blade answered for him.", 30.0, 33.7),
    ("REN", "No faces... they're just armor full of shadow!", 34.4, 39.6),
    ("HOLLOW KING", "Ten scattered. A hundred more are coming, boy.", 40.5, 45.6),
    ("REN", "Then I can't stay. I need a way off this island.", 46.4, 51.2),
    ("NARRATOR", "And somewhere above... an engine roared.", 51.8, 54.8),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "HOLLOW KING": (190, 120, 255), "CAPTAIN MIRE": (255, 150, 90)}
draw_caption, speaking = e1.draw_caption, e1.speaking

# ------------------------------------------------------------ helpers
def violet_fog(t, y0, y1, alpha=110, seed=1):
    lay = Image.new("RGBA", (W//4, H//4), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(14):
        x = ((r.uniform(0, W) + t*r.uniform(20, 60)) % (W + 400) - 200)/4
        y = r.uniform(y0, y1)/4; rw = r.uniform(140, 300)/4; rh = r.uniform(40, 90)/4
        d.ellipse([x - rw, y - rh, x + rw, y + rh], fill=(110, 50, 170, alpha))
    return lay.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)

def soldier(im, x, foot_y, sc, t, glow=1.0, fade=1.0, seed=0):
    s = hollow_soldier(round(glow, 1), int(t*8 + seed) % 8)
    s = s.resize((max(1, int(420*sc)), max(1, int(820*sc))), Image.BILINEAR)
    if fade < 1:
        s = s.copy(); s.putalpha(s.split()[3].point(lambda v: int(v*max(0, fade))))
    bob = 6*sc*math.sin(t*3 + seed)
    im.alpha_composite(s, (int(x - s.width/2), int(foot_y - s.height + bob)))

def mist_puff(im, x, y, p, sc=1.0, seed=0):
    """violet mist expanding as a shadow scatters (p 0..1)."""
    if p <= 0 or p >= 1: return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for k in range(9):
        a = r.uniform(0, 2*math.pi); dist = (60 + 220*p)*sc*r.uniform(0.5, 1.2); rad = (40 + 120*p)*sc*r.uniform(0.6, 1.1)
        cx, cy = x + dist*math.cos(a), y + dist*math.sin(a)*0.8 - 120*p*sc
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=(140, 70, 210, int(170*(1 - p))))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(26*sc)))

def slash_arc(im, p, cx, cy, R, a0, a1, col=(140, 240, 255)):
    """cyan crescent sweep; p 0..1 progress."""
    if p <= 0: return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    end = a0 + (a1 - a0)*min(1, p); start = a0 + (a1 - a0)*max(0, p - 0.55)
    fade = 1 if p < 1 else max(0, 1 - (p - 1)*2.5)
    n = 30; outer, inner = [], []
    for i in range(n + 1):
        a = math.radians(start + (end - start)*i/n); th = 70*math.sin(math.pi*i/n)
        outer.append((cx + (R + th)*math.cos(a), cy + (R + th)*math.sin(a)))
        inner.append((cx + R*math.cos(a), cy + R*math.sin(a)))
    d.polygon(outer + inner[::-1], fill=col + (int(255*fade),))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(22)))
    d2 = ImageDraw.Draw(lay); d2.polygon(outer + inner[::-1], fill=(235, 255, 255, int(255*fade)))
    im.alpha_composite(lay)

# ------------------------------------------------------------ backgrounds
STREET = Image.alpha_composite(CRATER_BG.copy(), Image.new("RGBA", (W, H), (60, 20, 90, 70)))
STREET_BLUR = STREET.filter(ImageFilter.GaussianBlur(6))

def make_edge():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (6, 14, 34)), (0.4, (20, 50, 80)), (0.62, (120, 70, 110)), (0.75, (60, 50, 90)), (1, (20, 20, 40))])).convert("RGBA")
    stars(im, 200, 1000, 17); clouds(im, 1300, 2200, 23, tint=(150, 110, 170))
    island(im, 300, 1000, 220, 200, 31); island(im, 1050, 1150, 180, 160, 32)
    return im.convert("RGB").filter(ImageFilter.GaussianBlur(4))
EDGE = make_edge()

def make_cloudsky():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (8, 16, 40)), (0.35, (30, 60, 100)), (0.6, (200, 110, 90)), (0.72, (240, 160, 100)), (1, (70, 60, 100))])).convert("RGBA")
    stars(im, 120, 800, 44); clouds(im, 1250, 2200, 45, tint=(255, 180, 140))
    return im.convert("RGB")
CLOUDSKY = make_cloudsky()

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(STREET_BLUR, 1.0 + 0.05*lt, 540, 960).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 4, 18, 255)), 0.5)
    im.alpha_composite(light_rays(t, (180, 120, 255), 540, -120, 55))
    a = ease(lt/0.7)
    # a row of visor glows opening in the dark
    for i, x in enumerate((180, 360, 540, 720, 900)):
        if lt > 0.2 + 0.12*i:
            soldier(im, x, 1880, 0.55 if i != 2 else 0.62, t, 1.0, 0.7, i)
    b = blade(1.0, 0.7 + 0.3*a, 0.5)
    rot_paste(im, b, 0, 540, 470 + 30*(1 - a))
    embers(im, t, 0.5, True)
    if lt > 0.5: glow_text(im, "SKYFORGE SAGA", 800, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.9:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.9)/0.4)*300
        d.rectangle([540 - w, 950, 540 + w, 956], fill=(200, 130, 255))
        text_center(d, "—  Ep %d  —" % EP, 980, 60, (255, 190, 110))
    if lt > 1.3: glow_text(im, TITLE, 1070, 96, (255, 255, 255), (150, 80, 255))
    return flash(im, max(0, 1 - lt/0.35))

def shot_fog(t, lt):
    im = cam(WIDE, 1.08 + 0.08*ease(lt/6), 900 - 25*lt, 1250).convert("RGBA")
    # soldiers marching down the chain-bridge toward the village
    for k in range(6):
        p = (lt*0.09 + k*0.14) % 1.0
        x = 1020 - 260*p + (k % 2)*30; y = 1360 - 300*p
        soldier(im, x - 25*lt*0.0, y, 0.16 + 0.05*p, t, 1.0, min(1, p*4), k)
    im.alpha_composite(violet_fog(t, 1000, 1700, 120, 3))
    embers(im, t, 0.5)
    return im

def shot_ren_alert(t, lt):
    im = cam(STREET_BLUR, 1.2, 540 + 15*lt, 900).convert("RGBA")
    im.alpha_composite(violet_fog(t, 700, 1300, 90, 5))
    m = speaking("REN", t)
    expr = "calm" if lt < 2.6 else "shocked"
    paste_bust(im, ren_bust(expr, m, blink(t) and expr == "calm", int(t*6) % 8, False), 1.1 + 0.04*ease(lt/6), 560, 780)
    rot_paste(im, blade(1.0, 0.7 + 0.2*math.sin(t*4), 0.9), 18, 200, 900)
    fist(im, 200 + 300*math.sin(math.radians(18)), 900 + 300*math.cos(math.radians(18)), 0.8)
    embers(im, t, 0.4, True)
    return shake(im, 3 if expr == "shocked" and lt < 3.2 else 0, t)

def shot_mire(t, lt):
    im = cam(STREET, 1.05 + 0.05*ease(lt/7), 560 - 10*lt, 1000).convert("RGBA")
    # ranks of soldiers behind him
    for row, (fy, sc) in enumerate(((1100, 0.42), (1250, 0.55))):
        for i in range(5):
            x = 100 + i*220 + (110 if row else 0) - 8*lt
            soldier(im, x, fy, sc, t, 1.0, 1.0, row*5 + i)
    im.alpha_composite(violet_fog(t, 900, 1500, 110, 7))
    m = speaking("CAPTAIN MIRE", t)
    paste_bust(im, mire_bust(m, blink(t, 1.7)), 1.0, 500, 760)
    if lt < 0.4: im = shake(im, 10*(1 - lt/0.4), t)
    embers(im, t, 0.3)
    return im

def shot_charge(t, lt):
    k = ease(lt/5.8)
    im = Image.fromarray(grad(W, H, [(0, (40, 14, 60)), (0.5, (90, 40, 120)), (1, (20, 10, 30))])).convert("RGBA")
    im.alpha_composite(SPEED[int(t*15) % 4])
    m = speaking("REN", t)
    paste_bust(im, ren_bust("determined", m, False, int(t*10) % 8, False), 1.22 + 0.12*k, 600, 760)
    # blade raised high, glowing brighter
    rot_paste(im, blade(1.0, 0.8 + 0.2*math.sin(t*6), 1.0), -20, 250, 820)
    fist(im, 250 - 339*math.sin(math.radians(20)), 820 + 339*math.cos(math.radians(20)), 1.0)
    energy_bolts(im, t, 120, 300, 300, 650, 1, 11)
    sparks(im, t, 230, 400, 16, 0.5, 21, (170, 245, 255))
    embers(im, t, 0.9, True, 2.0)
    return shake(im, 4 + 6*k, t, 3)

def shot_slash(t, lt):
    a = t - SLASH_T
    im = cam(STREET, 1.12, 540, 1050).convert("RGBA")
    xs = (160, 360, 560, 760, 950)
    p_br = ease((a - 0.25)/1.6)
    for i, x in enumerate(xs):
        fade = 1 if a < 0.25 + i*0.08 else max(0, 1 - (a - 0.25 - i*0.08)/1.2)
        soldier(im, x, 1300 + (i % 2)*40, 0.62, t, 1.0, fade, i)
    for i, x in enumerate(xs):
        if a > 0.25 + i*0.08:
            mist_puff(im, x, 1050, (a - 0.25 - i*0.08)/2.4, 0.8, i)
            # empty helm drops
            q = min(1, (a - 0.25 - i*0.08)/0.6)
            hm = soldier_helm(100)
            hm = hm.rotate(-30*q*(1 if i % 2 else -1), Image.BICUBIC, expand=True)
            im.alpha_composite(hm, (int(x - hm.width/2), int(840 + 480*q*q + (i % 2)*40 - hm.height/2)))
    # Ren from behind, foreground
    d = ImageDraw.Draw(im)
    d.polygon([(0, 1500), (1080, 1460), (1080, 1920), (0, 1920)], fill=(24, 20, 32))
    ren_back_silhouette(im, 540, 1560, 1.6, t*6)
    ang = -60 + 120*ease(a/0.35) if a > 0 else -60
    hx, hy = 610, 1330
    rot_paste(im, blade(1.0, 1.0, 0.55), ang, hx - 220*math.sin(math.radians(ang)), hy - 220*math.cos(math.radians(ang)))
    dd = ImageDraw.Draw(im); dd.ellipse([hx - 22, hy - 22, hx + 22, hy + 22], fill=SKIN, outline=(14, 12, 22), width=4)
    dd.line([(565, 1420), (hx, hy)], fill=(20, 28, 56), width=34)
    slash_arc(im, (a + 0.1)/0.45 if a > -0.1 else 0, 540, 1300, 520, 200, 340)
    im.alpha_composite(light_rays(t, (150, 240, 255), 540, 1200, 60*max(0, 1 - a/2)) if a > 0 else Image.new("RGBA", (W, H)))
    embers(im, t, 0.8, True, 1.6)
    im = shake(im, 22*max(0, 1 - a/0.9) if a > 0 else 2, t, 7)
    return flash(im, max(0, 1 - a/0.5) if a > 0.1 else 0)

def shot_scatter(t, lt):
    im = cam(STREET_BLUR, 1.15, 600, 980).convert("RGBA")
    # far soldiers dissolving behind him
    for i, x in enumerate((140, 900)):
        soldier(im, x, 1200, 0.5, t, 0.8, max(0, 1 - lt/3.5), i + 3)
        mist_puff(im, x, 950, lt/4.5, 0.7, i + 9)
    hm = soldier_helm(150)
    im.alpha_composite(hm, (90, 1300)); im.alpha_composite(hm.transpose(Image.FLIP_LEFT_RIGHT).rotate(20, expand=True), (800, 1290))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked" if lt < 3.2 else "determined", m, blink(t, 0.6) and lt >= 3.2, int(t*8) % 8, False), 1.1, 560, 790)
    rot_paste(im, blade(1.0, 0.8, 0.85), -12, 230, 920)
    fist(im, 230 - 280*math.sin(math.radians(12)), 920 + 280*math.cos(math.radians(12)), 0.8)
    embers(im, t, 0.6, True)
    return im

def shot_king(t, lt):
    im = cam(KING_BG, 1.12 - 0.06*ease(lt/6), 600, 1050).convert("RGBA")
    # silhouettes of an army behind him
    for i in range(7):
        soldier(im, 60 + i*160, 1450, 0.34, t, 0.7, 0.8, i)
    m = speaking("HOLLOW KING", t)
    lvl = {1: 2, 2: 4}[m] if m else int(1 + 0.8*math.sin(t*2))
    paste_bust(im, e1.hollow_king(max(0, min(4, lvl))), 1.3 + 0.06*ease(lt/6), 540, 690)
    for i, (x0, y0, sp, ph, r, cy) in enumerate(EMBERS[:30]):
        y = (y0 - sp*0.6*t) % (H + 100) - 50; x = x0 + 30*math.sin(t + ph)
        im.alpha_composite(KING_DOT, (int(x - 12), int(y - 12)))
    if 2.5 < lt < 2.65: im = flash(im, 0.3, (150, 90, 220))
    return shake(im, 3 if m == 2 else 0, t)

def shot_resolve(t, lt):
    im = cam(EDGE, 1.15, 700 - 20*lt, 1100).convert("RGBA")
    im.alpha_composite(light_rays(t, (160, 220, 255), 900, -200, 45))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("determined", m, blink(t, 2.0), int(t*9) % 8, False), 1.1 + 0.05*ease(lt/5.5), 560, 800)
    rot_paste(im, blade(1.0, 0.8 + 0.2*math.sin(t*4), 0.85), 35, 860, 640)
    embers(im, t, 0.8, False, 1.4)
    return im

def shot_airship(t, lt):
    k = ease(lt/3.5)
    im = cam(CLOUDSKY, 1.05 + 0.05*k, 650, 1200 - 80*k).convert("RGBA")
    # searchlight beam sweeping down
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ax, ay = 560 + 60*k, 1180 - 380*k
    bx = 300 + 160*math.sin(t*0.9)
    d.polygon([(ax + 180, ay + 120), (bx - 160, 1560), (bx + 160, 1560)], fill=(255, 230, 160, 60))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(20)))
    sh = airship(1.0, int(t*20) % 8)
    sc = 0.9 + 0.15*k
    sh = sh.resize((int(900*sc), int(520*sc)), Image.BILINEAR)
    im.alpha_composite(sh, (int(ax - sh.width/2), int(ay - sh.height/2)))
    # it rises out of the cloud sea: clouds drawn in front
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fr)
    for i in range(8):
        x = (i*170 - t*60) % (W + 400) - 200; y = 1280 + (i*53) % 120
        fd.ellipse([x - 200, y - 70, x + 200, y + 70], fill=(250, 190, 160, 220))
    im.alpha_composite(fr.filter(ImageFilter.GaussianBlur(14)))
    embers(im, t, 0.4)
    return shake(im, 3*k, t, 9)

def shot_next(t, lt):
    im = shot_airship(t, 3.5 + lt*0.2)
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.72, lt/0.3*0.72))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 700 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 820, 104, (255, 255, 255), (255, 140, 60))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 990, 540 + 300*a, 996], fill=(255, 170, 90))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 1040, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1140, 50, (255, 220, 150), sw=6)
    embers(im, t, 0.5, True)
    return im

SHOT_FN = {"title": shot_title, "fog": shot_fog, "ren_alert": shot_ren_alert, "mire": shot_mire, "charge": shot_charge,
           "slash": shot_slash, "scatter": shot_scatter, "king": shot_king, "resolve": shot_resolve,
           "airship": shot_airship, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    if t - s < 0.08 and name not in ("title", "next"):
        im = flash(im, 0.45)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio (new battle score: D minor, 112 bpm)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(33)
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
    bpm = 112; beat = 60/bpm; bar = beat*4
    chords = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]]  # Dm Bb C A
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.7
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.45), (16, 0.65), (23, 0.9), (28.8, 1.0), (34, 0.7), (40, 0.55), (46, 0.7), (51.5, 0.8), (55, 1.0), (58.5, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.3, 0.5)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.032*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.4), t0, vol=0.06*inten(t0))
        t0 += bar; ci += 1
    # driving 8th-note low strings through the battle
    t0, k = 0.0, 0
    while t0 < TOTAL:
        if 16.0 <= t0 < 40.0 or 51.5 <= t0 < 55.0:
            ch = chords[int(t0 // bar) % 4]; m = [ch[0], ch[0], ch[0] + 12, ch[0]][k % 4]
            n = int(0.18*SR); add(saw(note(m), 0.18, 5)*np.exp(-14*tv(n)), t0, pan=0.3*(1 if k % 2 else -1), vol=0.05)
        t0 += beat/2; k += 1
    # brass-like heroic motif when Ren charges (own melody)
    motif = [(62, 1), (65, 0.5), (69, 0.5), (74, 1.5), (72, 0.5), (69, 1), (70, 1), (69, 2)]
    tt = 23.2
    for m, b in motif:
        dur = b*beat; n = int(dur*SR)
        s = saw(note(m), dur, 8)*env(n, 0.04, 0.12)*(1 + 0.15*np.sin(2*np.pi*5*tv(n)))
        add(s, tt, pan=0.1, vol=0.045); tt += dur
    # eerie bell motif during the fog
    for i, m in enumerate([74, 77, 76, 72, 74, 69]):
        tt = 4.3 + i*beat*1.5; n = int(1.2*SR); x = tv(n)
        add((np.sin(2*np.pi*note(m)*x) + 0.3*np.sin(2*np.pi*note(m)*2.76*x)*np.exp(-6*x))*np.exp(-3*x), tt, pan=-0.2, vol=0.04)
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
        if 23.0 <= tb < 34.0 or 51.5 <= tb < 55.0:
            if b % 4 in (0, 2) or b % 8 == 7: add(KICK, tb, vol=0.5)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.18)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.09)
        elif 4.0 <= tb < 23.0:  # marching: steady taiko pulse
            add(TAIKO, tb, vol=0.36 if b % 2 == 0 else 0.2)
        elif 40.0 <= tb < 46.0 and b % 4 == 0:
            add(TAIKO, tb, vol=0.5)
        elif 34.0 <= tb < 40.0 and b % 2 == 0:
            add(KICK, tb, vol=0.3)
        b += 1
    # armored footsteps (metal clinks) under the march
    def clink(f0=900):
        n = int(0.25*SR); x = tv(n)
        return sum(np.sin(2*np.pi*f0*r*x)*np.exp(-d*x) for r, d in ((1, 30), (2.7, 40), (4.1, 55)))/3
    for i in range(int((23.0 - 6.0)/(beat))):
        tc = 6.0 + i*beat + beat/2
        add(clink(800 + rs.uniform(-80, 80)), tc, pan=rs.uniform(-0.6, 0.6), vol=0.06)
    # cut whooshes
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.33)
    # title hit
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # Mire's entrance: spear slam
    n = int(1.5*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(50 + 80*np.exp(-20*x))/SR)*np.exp(-4*x), 16.05, vol=0.45); add(clink(500)*2, 16.05, vol=0.45)
    # charge: rising whine to the slash
    dur = SLASH_T - 26.0; n = int(dur*SR)
    f = np.linspace(200, 1400, n); amp = np.linspace(0.05, 1, n)**2
    add((np.sin(2*np.pi*np.cumsum(f)/SR)*0.22 + whoosh(dur, True)*0.5)*amp, 26.0, vol=0.28)
    # slash: big swoosh + impact boom + ring
    add(whoosh(0.5, False)*2.0, SLASH_T - 0.1, pan=-0.3, vol=0.5)
    n = int(3.5*SR); x = tv(n); f = 40 + 60*np.exp(-6*x)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-1.4*x) + 0.6*whoosh(3.5, False)*np.exp(-1.2*x), SLASH_T + 0.2, vol=0.85)
    n = int(5.0*SR); x = tv(n)
    add(sum(np.sin(2*np.pi*fq*x) for fq in (587.3, 880.0, 1174.7))*np.exp(-0.6*x)/3, SLASH_T + 0.25, vol=0.06)
    # helms clattering + mist hiss
    for i in range(5):
        add(clink(600 + 70*i)*1.5, SLASH_T + 0.9 + i*0.12, pan=-0.6 + 0.3*i, vol=0.1)
    n = int(6.0*SR); hiss = lp_noise(6.0, 0.3, 0.05)*env(n, 0.2, 2.0)
    add(hiss, SLASH_T + 0.4, vol=0.08)
    # Hollow King drone
    n = int(6.0*SR); x = tv(n)
    add((saw(note(38), 6.0, 5) + 0.5*np.sin(2*np.pi*note(45)*x*(1 + 0.003*np.sin(2*np.pi*5*x))))*env(n, 0.8, 1.0), 40.0, vol=0.08)
    # airship engine: low drone with propeller flutter
    dur = TOTAL - 51.3; n = int(dur*SR); x = tv(n)
    eng = (saw(55, dur, 6)*(0.6 + 0.4*np.sign(np.sin(2*np.pi*18*x))) + 0.4*lp_noise(dur, 0.05, 0.05))*env(n, 1.2, 1.5)
    add(eng, 51.3, pan=0.2, vol=0.09)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 55.0, vol=0.6)
    for i, m in enumerate([62, 69, 74, 77, 81]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 55.05, pan=-0.6 + 0.3*i, vol=0.05)
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
