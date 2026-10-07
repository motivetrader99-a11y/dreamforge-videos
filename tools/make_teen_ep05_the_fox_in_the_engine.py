"""SKYFORGE SAGA Ep 5: The Fox in the Engine  (no-voice build: music + sfx + timed captions).
Introduces Kuro (teen_art.kuro). Reuses Ep 1-4 helpers; new shots and a new mystic score."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, SPEED, cam, shake, flash,
                                            VIG, light_rays, text_center, glow_text, paste_bust, ease, blink)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, blade
from make_teen_ep03_hollow_soldiers import violet_fog, CLOUDSKY
from make_teen_ep04_lyras_airship import ENGINE, COCKPIT, kestrel, wind_lines, blue_eyes

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/05_the_fox_in_the_engine.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 5, "The Fox in the Engine", "Chain-Bridge Chase"

SHOTS = [("title", 0.0, 4.0), ("engine", 4.0, 10.4), ("lyra", 10.4, 16.0), ("ren", 16.0, 21.6),
         ("burst", 21.6, 29.0), ("kuro", 29.0, 35.6), ("ren_shock", 35.6, 40.6), ("lyra_deal", 40.6, 45.8),
         ("warn", 45.8, 52.6), ("next", 52.6, 57.0)]
TOTAL = 57.0
LINES = [
    ("NARRATOR", "Something was hiding in the Kestrel's engine. Something with blue fire.", 4.4, 10.1),
    ("LYRA", "If that's a rat, I'm charging it rent.", 10.8, 15.7),
    ("REN", "Rats don't have glowing eyes, Lyra.", 16.4, 21.3),
    ("NARRATOR", "Three tails. Black fur. Flames that didn't burn.", 23.2, 28.6),
    ("KURO", "You carry the shard, boy. I have waited a long time for you.", 29.4, 35.3),
    ("REN", "Wait... did the fox just talk?", 36.0, 40.3),
    ("LYRA", "Great. A talking stowaway. Still charging rent.", 41.0, 45.5),
    ("KURO", "Turn the ship. Mire is waiting at the chain-bridge.", 46.4, 52.2),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255)}
draw_caption, speaking = e1.draw_caption, e1.speaking

def paste_kuro(im, k, scale, fx, fy, ang=0):
    """place Kuro so his face centre (450,360) lands at (fx,fy)."""
    s = k.resize((int(900*scale), int(900*scale)), Image.BILINEAR)
    if ang:
        s = s.rotate(ang, Image.BICUBIC, expand=True)
        im.alpha_composite(s, (int(fx - s.width/2), int(fy - s.height/2 - (360 - 450)*scale)))
    else:
        im.alpha_composite(s, (int(fx - 450*scale), int(fy - 360*scale)))

def blue_fire_glow(im, cx, cy, r, a):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(50, 120, 255, int(120*a)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r*0.35)))

def blue_embers(im, t, cx, cy, n=24, seed=7, spread=420):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(n):
        x0 = cx + r.uniform(-spread, spread); sp = r.uniform(60, 180); ph = r.uniform(0, 10)
        y = cy + 200 - ((t*sp + ph*80) % 900); x = x0 + 30*math.sin(t*2 + ph)
        s = r.uniform(4, 10)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(140, 200, 255, 220))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2))); im.alpha_composite(lay)

def make_bridge_view():
    """dusk sky ahead of the Kestrel: a long chain-bridge between two islands, violet glow of Mire's ship."""
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (12, 18, 46)), (0.35, (70, 50, 110)), (0.55, (220, 110, 90)), (0.7, (250, 170, 110)), (1, (70, 60, 100))])).convert("RGBA")
    stars(im, 80, 600, 71); clouds(im, 1300, 2200, 72, tint=(255, 180, 150))
    island(im, 180, 1050, 420, 420, 73, houses=1)
    island(im, 1140, 980, 380, 380, 74, houses=1)
    for dy in (0, 26):
        chain(im, (370, 1040 + dy), (950, 980 + dy), 150)
    d = ImageDraw.Draw(im)
    for i in range(1, 12):  # bridge planks
        t = i/12; x = 370 + 580*t; y = 1053 - 60*t + 150*4*t*(1 - t)
        d.rectangle([x - 12, y - 4, x + 12, y + 16], fill=(90, 66, 50), outline=(20, 14, 12))
    # Mire's dark warship silhouette behind the right island
    d.polygon([(860, 820), (1260, 800), (1220, 880), (900, 890)], fill=(30, 22, 40), outline=(10, 8, 14))
    d.polygon([(980, 820), (1040, 700), (1100, 810)], fill=(40, 30, 54), outline=(10, 8, 14))
    return im.convert("RGB")
BRIDGE = make_bridge_view()

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(ENGINE, 1.15 + 0.04*lt, 650, 1000).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), 0.55)
    blue_eyes(im, 540, 1480, 0.6 + 0.4*math.sin(t*3), 0.9)
    blue_embers(im, t, 540, 1400, 16, 3)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 700, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 850, 540 + w, 856], fill=(110, 170, 255))
        text_center(d, "—  Ep %d  —" % EP, 880, 60, (255, 190, 110))
    if lt > 1.2: glow_text(im, TITLE, 970, 88, (255, 255, 255), (60, 120, 255))
    return flash(im, max(0, 1 - lt/0.35))

def shot_engine(t, lt):
    k = ease(lt/6.4)
    im = cam(ENGINE, 1.0 + 0.22*k, 650, 1000 + 40*k).convert("RGBA")
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([300, 600, 1000, 1300], fill=(255, 140, 60, int(40 + 20*math.sin(t*6))))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    ga = 0.5 + 0.5*math.sin(t*2.4)
    blue_eyes(im, 540, 1030 + 30*k, ga, 1.0 + 0.25*k)
    blue_fire_glow(im, 540, 1030, 260, 0.4 + 0.3*ga)
    sparks(im, t, 820, 300, 8, 0.4, 17)
    return shake(im, 2 + 3*abs(math.sin(t*14)), t, 12)

def shot_lyra(t, lt):
    im = cam(ENGINE, 1.25, 820, 900).convert("RGBA")
    blue_fire_glow(im, 900, 1150, 220, 0.5 + 0.2*math.sin(t*3))
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("smirk" if lt > 0.5 else "calm", m, blink(t, 0.9)), 1.05, 470, 700)
    # wrench raised in her hand (left)
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    a = math.radians(-20 + 6*math.sin(t*2)); cx, cy = 170, 1250
    ex, ey = cx + 340*math.sin(a), cy - 340*math.cos(a)
    d.line([(cx, cy), (ex, ey)], fill=o, width=40); d.line([(cx, cy), (ex, ey)], fill=(170, 170, 185), width=26)
    d.ellipse([ex - 50, ey - 50, ex + 50, ey + 50], fill=(170, 170, 185), outline=o, width=7)
    d.rectangle([ex - 18, ey - 60, ex + 18, ey - 10], fill=(60, 34, 26))
    d.ellipse([cx - 50, cy - 40, cx + 50, cy + 50], fill=SKIN, outline=o, width=6)
    embers(im, t, 0.2)
    return im

def shot_ren(t, lt):
    k = ease(lt/5.6)
    im = cam(ENGINE, 1.3, 400, 1100).convert("RGBA")
    m = speaking("REN", t)
    paste_bust(im, ren_bust("determined", m, False, int(t*6) % 8, False), 1.08 + 0.05*k, 560, 760)
    rot_paste(im, blade(1.0, 0.7 + 0.3*math.sin(t*5), 0.85), 18, 190, 900)
    blue_fire_glow(im, 160, 600, 200, 0.4)
    sparks(im, t, 120, 560, 6, 0.3, 4, (170, 245, 255))
    embers(im, t, 0.3, True)
    return im

GRILLE = None
def grille_sprite():
    global GRILLE
    if GRILLE is None:
        g = Image.new("RGBA", (460, 380), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        d.rounded_rectangle([5, 5, 455, 375], 30, fill=(18, 14, 18), outline=(14, 12, 22), width=6)
        for y in range(30, 360, 52): d.rectangle([14, y, 446, y + 18], fill=(90, 92, 108), outline=(14, 12, 22), width=3)
        GRILLE = g
    return GRILLE

def shot_burst(t, lt):
    im = cam(ENGINE, 1.1, 650, 1050).convert("RGBA")
    if lt < 1.2:  # grille rattles, glow builds
        a = lt/1.2
        blue_fire_glow(im, 540, 1050, 300, 0.4 + 0.6*a)
        blue_eyes(im, 540, 1050, 1.0, 1.0)
        return shake(im, 4 + 10*a, t, 3)
    p = lt - 1.2
    blue_fire_glow(im, 540, 1050, 360, max(0.3, 1 - p*0.3))
    # grille panel flies off up-left, spinning
    if p < 1.4:
        rot_paste(im, grille_sprite(), 200*p, 540 - 700*p, 1050 - 900*p + 500*p*p)
    # Kuro leaps out in an arc then lands centre
    if p < 0.9:
        q = p/0.9
        x = 540 + 60*q; y = 1050 - 600*math.sin(math.pi*q*0.9) + 250*q
        paste_kuro(im, kuro(0, False, int(t*12) % 8, "narrow"), 0.5 + 0.5*q, x, y, -25*(1 - q))
        im.alpha_composite(SPEED[int(t*15) % 4])
    else:
        q = ease((p - 0.9)/0.6)
        paste_kuro(im, kuro(0, blink(t, 0.3), int(t*10) % 8, "calm"), 1.0 + 0.06*q, 540, 820 - 20*q)
    blue_embers(im, t, 540, 1100, 30, 11)
    sparks(im, t, 540, 1050, 20, 0.8, 21, (150, 210, 255))
    im = shake(im, 14*max(0, 1 - p/0.5), t, 5)
    return flash(im, max(0, 1 - p/0.25)*0.9, (190, 220, 255))

def shot_kuro(t, lt):
    k = ease(lt/6.6)
    im = cam(ENGINE, 1.35 + 0.08*k, 650, 1000).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.35)
    blue_fire_glow(im, 540, 700, 420, 0.7)
    m = speaking("KURO", t)
    paste_kuro(im, kuro(m, blink(t, 1.7), int(t*10) % 8, "calm" if lt < 3 else "narrow"), 1.35 + 0.08*k, 540, 640)
    blue_embers(im, t, 540, 900, 26, 13, 500)
    return im

def shot_ren_shock(t, lt):
    im = cam(ENGINE, 1.25, 420, 900).convert("RGBA")
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked", m, False, int(t*6) % 8, True), 1.15, 540, 760)
    # Kuro peeking in from the right edge (inside the safe zone)
    paste_kuro(im, kuro(0, blink(t, 0.6), int(t*10) % 8, "narrow"), 0.38, 790, 1040)
    if lt < 0.6:
        d = ImageDraw.Draw(im)
        for i in range(10):  # shock lines
            a = i*math.pi/5; d.line([(540 + 330*math.cos(a), 600 + 330*math.sin(a)), (540 + 420*math.cos(a), 600 + 420*math.sin(a))], fill=(255, 255, 255), width=8)
    return shake(im, 6*max(0, 1 - lt/0.5), t, 2)

def shot_lyra_deal(t, lt):
    k = ease(lt/5.2)
    im = cam(COCKPIT, 1.05, 650, 1000).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(4)
    for i in range(12):
        x = (r.uniform(0, W + 600) - 900*t) % (W + 600) - 300; y = r.uniform(400, 1000)
        d.ellipse([x - 160, y - 30, x + 160, y + 30], fill=(255, 220, 190, 120))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("smirk" if lt < 1.5 or lt > 3.2 else "calm", m, blink(t, 1.5)), 1.0 + 0.04*k, 540, 720)
    # Kuro sitting on the console bottom-left, tails flickering
    paste_kuro(im, kuro(0, blink(t, 2.2), int(t*10) % 8, "calm"), 0.46, 230, 1000)
    return shake(im, 2, t, 8)

def shot_warn(t, lt):
    k = ease(lt/6.8)
    im = cam(BRIDGE, 1.05 + 0.18*k, 650, 1000).convert("RGBA")
    im.alpha_composite(violet_fog(t, 700, 1000, 90, 41))
    wind_lines(im, t, 16, 9, 90)
    # Kestrel's bow rail he sits on
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    d.polygon([(-20, 870), (620, 858), (700, 890), (640, 960), (-20, 1010)], fill=(110, 68, 42), outline=o)
    d.polygon([(-20, 940), (660, 930), (640, 960), (-20, 1010)], fill=(80, 48, 30))
    d.rectangle([-20, 846, 640, 872], fill=BRASS, outline=o, width=4)
    m = speaking("KURO", t)
    paste_kuro(im, kuro(m, blink(t, 0.4), int(t*10) % 8, "narrow"), 0.62, 330, 560)
    # a chain snaps on the bridge (hook)
    if lt > 4.6:
        p = lt - 4.6
        sparks(im, t, 650, 470 + 40*k, 14, 0.6, 33, (255, 200, 120))
        if p < 0.3: im = flash(im, 0.5*(1 - p/0.3), (255, 220, 180))
    embers(im, t, 0.4)
    return shake(im, 8 if 4.6 < lt < 5.0 else 1, t, 6)

def shot_next(t, lt):
    im = shot_warn(t, 6.8)
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.72, lt/0.3*0.72))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 760, 100, (255, 255, 255), (255, 120, 60))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(255, 160, 100))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 970, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1070, 50, (255, 220, 150), sw=6)
    return im

SHOT_FN = {"title": shot_title, "engine": shot_engine, "lyra": shot_lyra, "ren": shot_ren, "burst": shot_burst,
           "kuro": shot_kuro, "ren_shock": shot_ren_shock, "lyra_deal": shot_lyra_deal, "warn": shot_warn, "next": shot_next}

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
# ------------------------------------------------------------ audio (new mystic score: D minor, 100 bpm, celesta-like bells for Kuro)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(55)
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
    chords = [[50, 53, 57], [46, 50, 53], [41, 45, 48], [48, 52, 55]]  # Dm Bb F C
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.7
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.45), (10.4, 0.55), (21.6, 0.7), (22.8, 1.0), (29, 0.6), (35.6, 0.7), (45.8, 0.85), (52.6, 1.0), (57, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.005) + saw(note(m), dur, 6, -0.005))*0.5*env(int(dur*SR), 0.5, 0.6)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.03*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.05, 0.4), t0, vol=0.06*inten(t0))
        t0 += bar; ci += 1
    # bell arpeggio (sine + inharmonic partial) - Kuro's mystic colour
    def bell(f, dur=0.9):
        n = int(dur*SR); x = tv(n)
        return (np.sin(2*np.pi*f*x) + 0.4*np.sin(2*np.pi*f*2.76*x)*np.exp(-6*x))*np.exp(-4*x)
    t0, k = 0.0, 0
    while t0 < TOTAL:
        ch = chords[int(t0 // bar) % 4]; m = (ch + [ch[0] + 12])[[0, 2, 1, 3, 2, 1][k % 6]] + 24
        add(bell(note(m)), t0, pan=0.5*(1 if k % 2 else -1), vol=0.035*speech_duck(t0)*(1.3 if 29 <= t0 < 35.6 else 1))
        t0 += beat/2; k += 1
    # Kuro's motif (own melody) at his reveal and at the warning
    motif = [(62, 1), (65, 0.5), (69, 0.5), (74, 1.5), (72, 0.5), (69, 1), (70, 1), (69, 2)]
    for tt in (23.0, 46.0):
        for m, bb in motif:
            dur = bb*beat; n = int(dur*SR)
            s = saw(note(m), dur, 8)*env(n, 0.04, 0.12)*(1 + 0.15*np.sin(2*np.pi*5*tv(n)))
            add(s, tt, pan=0.1, vol=0.035*speech_duck(tt)); tt += dur
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
        if 22.8 <= tb < 29.0 or 45.8 <= tb < 52.6:
            if b % 4 in (0, 2) or b % 8 == 7: add(KICK, tb, vol=0.45)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.16)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.08)
        elif 4.0 <= tb < 21.6 and b % 2 == 0:
            add(TAIKO, tb, vol=0.25)
        elif 35.6 <= tb < 45.8 and b % 4 == 0:
            add(KICK, tb, vol=0.3)
        b += 1
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # engine hum + growl in the engine room
    for s0, e0, v in ((0.0, 21.6, 0.07), (21.6, 40.6, 0.05)):
        dur = e0 - s0; n = int(dur*SR); x = tv(n)
        eng = (saw(55, dur, 6)*(0.6 + 0.4*np.sign(np.sin(2*np.pi*16*x))) + 0.4*lp_noise(dur, 0.05, 0.05))*env(n, 0.8, 0.8)
        add(eng, s0, pan=0.2, vol=v)
    dur = 6.0; n = int(dur*SR); x = tv(n)
    add((saw(70, dur, 8)*(0.5 + 0.5*np.sin(2*np.pi*11*x)))*env(n, 1.0, 1.0), 4.2, vol=0.08)
    n = int(TOTAL*SR); add(lp_noise(TOTAL, 0.02, 0.02)*1.2, 0, vol=0.04)
    # grille rattle then burst
    for i in range(12):
        nn = int(0.06*SR); add(rs.randn(nn)*np.exp(-50*tv(nn)), 21.7 + i*0.1, pan=rs.uniform(-0.3, 0.3), vol=0.14)
    n = int(1.5*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(50 + 90*np.exp(-20*x))/SR)*np.exp(-4*x) + 0.5*rs.randn(n)*np.exp(-10*x), 22.8, vol=0.6)
    add(whoosh(0.9, True)*1.4, 22.8, vol=0.4)
    # metal clang when the grille lands
    n = int(1.2*SR); x = tv(n)
    add((np.sin(2*np.pi*620*x) + 0.6*np.sin(2*np.pi*1710*x))*np.exp(-6*x), 24.0, pan=-0.6, vol=0.12)
    # shock sting for Ren
    add(bell(note(86), 1.2), 35.65, vol=0.12)
    # chain snap in the warning shot
    n = int(0.6*SR); x = tv(n)
    add((np.sin(2*np.pi*900*x) + rs.randn(n)*0.8)*np.exp(-12*x), 50.4, pan=0.3, vol=0.3)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 52.6, vol=0.6)
    for i, m in enumerate([62, 69, 74, 77, 81]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 52.65, pan=-0.6 + 0.3*i, vol=0.05)
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
