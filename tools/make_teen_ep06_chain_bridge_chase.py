"""SKYFORGE SAGA Ep 6: Chain-Bridge Chase  (no-voice build: music + sfx + timed captions).
Captain Mire chases Ren, Lyra and Kuro across a collapsing chain-bridge. Reuses Ep 1-5 helpers;
new bridge-deck background, side-view chase, bridge split, and a new driving chase score."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, SPEED, cam, shake, flash,
                                            VIG, text_center, glow_text, paste_bust, ease, blink)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, blade
from make_teen_ep03_hollow_soldiers import violet_fog, slash_arc, CLOUDSKY
from make_teen_ep04_lyras_airship import COCKPIT, kestrel, wind_lines
from make_teen_ep05_the_fox_in_the_engine import BRIDGE, paste_kuro, blue_embers, blue_fire_glow

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/06_chain_bridge_chase.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 6, "Chain-Bridge Chase", "Into the Cloud Sea"

SHOTS = [("title", 0.0, 4.0), ("wide", 4.0, 10.0), ("mire", 10.0, 15.4), ("lyra", 15.4, 20.4), ("ren", 20.4, 25.6),
         ("run", 25.6, 28.4), ("kuro", 28.4, 32.6), ("mire_charge", 32.6, 37.4), ("ren_slash", 37.4, 41.8),
         ("cut", 41.8, 47.4), ("lyra_fall", 47.4, 52.4), ("next", 52.4, 57.0)]
TOTAL = 57.0
SLASH_T = 40.7
LINES = [
    ("NARRATOR", "One chain-bridge stood between the Kestrel and freedom. Captain Mire was waiting on it.", 4.4, 9.7),
    ("CAPTAIN MIRE", "End of the line, shard-thief. Hand over the blade.", 10.4, 15.0),
    ("LYRA", "They've hooked the Kestrel! Run for the far side!", 15.8, 20.0),
    ("REN", "Across THAT? Half the chains are already gone!", 20.8, 25.2),
    ("KURO", "Then run faster than they fall.", 28.8, 32.2),
    ("CAPTAIN MIRE", "Run all you like. This bridge breaks before I do.", 33.0, 37.0),
    ("REN", "Then let's break it first!", 37.8, 40.6),
    ("NARRATOR", "The bridge split. Mire was cut off. And the Kestrel was right below them...", 42.2, 47.0),
    ("LYRA", "Wait... why is the ship still falling?", 47.8, 52.0),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255),
          "CAPTAIN MIRE": (230, 120, 90)}
draw_caption, speaking = e1.draw_caption, e1.speaking
O = (14, 12, 22)

# ------------------------------------------------------------ backgrounds
def make_deck():
    """standing ON the chain-bridge, looking along it: planks in perspective, chain rails converging, gaps."""
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (10, 18, 46)), (0.28, (70, 50, 110)), (0.42, (230, 120, 90)), (0.5, (250, 175, 110)),
                                     (0.7, (120, 80, 110)), (1, (40, 34, 66))])).convert("RGBA")
    stars(im, 70, 500, 81); clouds(im, 1050, 2200, 82, tint=(255, 180, 150))
    island(im, 650, 930, 520, 380, 83, houses=2)
    island(im, 140, 760, 200, 180, 84); island(im, 1180, 820, 160, 150, 85)
    d = ImageDraw.Draw(im)
    vx, vy = 650, 940
    rnd = random.Random(86)
    # planks from horizon to bottom
    z = 1.0
    rows = []
    while True:
        y = vy + 1260/z*0.12
        if y > h + 60: break
        rows.append(y); z *= 0.86
    for i in range(len(rows) - 1):
        y0, y1 = rows[i], rows[i + 1]
        hw0 = 60 + (y0 - vy)*0.55; hw1 = 60 + (y1 - vy)*0.55
        gy = y0 + (y1 - y0)*0.12
        if rnd.random() < 0.18 and i > 3:  # missing plank: show cloud sea through the gap
            continue
        col = (110, 76, 52) if i % 2 else (124, 86, 58)
        d.polygon([(vx - hw0, gy), (vx + hw0, gy), (vx + hw1, y1), (vx - hw1, y1)], fill=col, outline=O)
        d.line([(vx - hw1 + 6, y1 - 4), (vx + hw1 - 6, y1 - 4)], fill=(80, 54, 38), width=max(1, int((y1 - y0)*0.1)))
    # chain rails (two on each side) and posts
    for s in (-1, 1):
        for k, off in enumerate((0, 1)):
            x0, y0 = vx + s*(70 + 40*off), vy - 30 - 20*off
            x1, y1 = vx + s*(760 + 300*off), h - 600 - 300*off
            n = 60
            for j in range(n + 1):
                p = j/n; x = x0 + (x1 - x0)*p; y = y0 + (y1 - y0)*p + 50*math.sin(math.pi*p)
                r = 3 + 26*p*p
                d.ellipse([x - r, y - r*0.7, x + r, y + r*0.7], outline=(30, 26, 36), width=max(2, int(r*0.35)))
        for p in (0.25, 0.5, 0.8):
            x = vx + s*(70 + 690*p**1.4); yb = vy + (h - vy)*p**1.4; ht = 40 + 360*p**1.4
            d.rectangle([x - 4 - 22*p, yb - ht, x + 4 + 22*p, yb], fill=(90, 62, 44), outline=O, width=3)
    return im.convert("RGB")
DECK = make_deck()

# ------------------------------------------------------------ small full figures (side view, running)
def runner(im, x, y, sc, t, who, face=1):
    """side-view running chibi silhouette; y = feet. who in REN/LYRA/MIRE."""
    d = ImageDraw.Draw(im); ph = t*14
    a = math.sin(ph); b = math.sin(ph + math.pi)
    body = {"REN": COAT, "LYRA": LY_JACKET, "MIRE": MIRE_ARM}[who]
    leg = (24, 22, 34)
    hip = (x, y - 70*sc - 6*sc*abs(a))
    for k in (a, b):  # legs
        d.line([hip, (x + 34*sc*k*face, y - 30*sc), (x + 46*sc*k*face, y - 6*sc*abs(k))], fill=leg, width=int(16*sc), joint="curve")
    if who == "REN":  # scarf streaming back
        d.polygon([(x - 6*sc*face, y - 140*sc), (x - 90*sc*face, y - 150*sc + 10*a*sc), (x - 130*sc*face, y - 128*sc + 14*b*sc),
                   (x - 70*sc*face, y - 128*sc)], fill=SCARF, outline=O)
    if who == "MIRE":  # cloak + spear
        d.polygon([(x, y - 150*sc), (x - 70*sc*face, y - 60*sc + 8*a*sc), (x - 20*sc*face, y - 70*sc)], fill=MIRE_CLOAK, outline=O)
        d.line([(x - 80*sc*face, y - 40*sc), (x + 120*sc*face, y - 200*sc)], fill=(60, 46, 40), width=int(9*sc))
        d.polygon([(x + 120*sc*face, y - 200*sc), (x + 150*sc*face, y - 250*sc), (x + 110*sc*face, y - 214*sc)], fill=(200, 210, 222), outline=O)
        d.polygon([(x - 80*sc*face, y - 40*sc), (x - 112*sc*face, y + 6*sc), (x - 70*sc*face, y - 30*sc)], fill=(200, 210, 222), outline=O)
    d.rounded_rectangle([x - 26*sc, y - 160*sc, x + 26*sc, y - 64*sc], int(14*sc), fill=body, outline=O, width=max(2, int(4*sc)))
    # arms pumping
    d.line([(x, y - 140*sc), (x - 38*sc*a*face, y - 104*sc)], fill=body, width=int(14*sc))
    hx, hy = x + 6*sc*face, y - 192*sc
    if who == "REN":
        pts = []
        for i in range(14):
            an = math.pi*2*i/14; rr = 40*sc*(1.3 if i % 2 else 1.0)
            pts.append((hx - 6*sc*face + rr*math.cos(an), hy + rr*math.sin(an)))
        d.polygon(pts, fill=HAIR, outline=O)
        d.ellipse([hx - 4*sc + 10*sc*face, hy - 18*sc, hx + 30*sc*face + 4*sc if face > 0 else hx + 4*sc, hy + 30*sc], fill=SKIN)
        d.polygon([(hx - 10*sc, hy - 40*sc), (hx + 4*sc, hy - 44*sc), (hx, hy - 12*sc)], fill=(236, 238, 248))
    elif who == "LYRA":
        d.ellipse([hx - 36*sc, hy - 36*sc, hx + 36*sc, hy + 38*sc], fill=LY_HAIR, outline=O, width=max(2, int(3*sc)))
        d.ellipse([hx + 4*sc*face - 14*sc, hy - 10*sc, hx + 4*sc*face + 22*sc, hy + 30*sc], fill=SKIN)
        d.rectangle([hx - 34*sc, hy - 30*sc, hx + 34*sc, hy - 16*sc], fill=BRASS, outline=O)
    else:
        d.ellipse([hx - 34*sc, hy - 34*sc, hx + 34*sc, hy + 34*sc], fill=MIRE_ARM, outline=O, width=max(2, int(3*sc)))
        d.polygon([(hx, hy - 30*sc), (hx - 60*sc*face, hy - 80*sc), (hx - 20*sc*face, hy - 24*sc)], fill=MIRE_HL, outline=O)
        d.rectangle([hx + 4*sc*face - 14*sc, hy - 4*sc, hx + 4*sc*face + 18*sc, hy + 8*sc], fill=(190, 120, 255))

def mini_kuro(im, x, y, sc, t):
    k = kuro(0, False, int(t*12) % 8, "narrow")
    paste_kuro(im, k, 0.2*sc, x, y - 120*sc)

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(BRIDGE, 1.1 + 0.05*lt, 650, 1000).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 4, 16, 255)), 0.55)
    im.alpha_composite(violet_fog(t, 1100, 1500, 70, 3))
    embers(im, t, 0.4)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 700, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 850, 540 + w, 856], fill=(255, 150, 90))
        text_center(d, "—  Ep %d  —" % EP, 880, 60, (255, 190, 110))
    if lt > 1.2: glow_text(im, TITLE, 970, 92, (255, 255, 255), (255, 110, 60))
    return flash(im, max(0, 1 - lt/0.35))

def shot_wide(t, lt):
    k = ease(lt/6.0)
    im = cam(BRIDGE, 1.0 + 0.2*k, 640 + 40*k, 1000 - 40*k).convert("RGBA")
    # Kestrel flying in from the right toward the bridge
    kestrel(im, 1000 - 380*k, 1300 - 160*k, 0.55 + 0.15*k, t)
    im.alpha_composite(violet_fog(t, 700, 1000, 60, 11))
    wind_lines(im, t, 12, 4, 80)
    embers(im, t, 0.3)
    return shake(im, 2, t, 3)

def shot_mire(t, lt):
    k = ease(lt/5.4)
    im = cam(DECK, 1.15 + 0.06*k, 650, 1050).convert("RGBA")
    im.alpha_composite(violet_fog(t, 1100, 1600, 110, 21))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([140, 300, 940, 1300], fill=(140, 60, 220, 70))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(80)))
    m = speaking("CAPTAIN MIRE", t)
    paste_bust(im, mire_bust(m, blink(t, 1.7)), 1.02 + 0.05*k, 500, 760)
    wind_lines(im, t, 10, 2, 70)
    embers(im, t, 0.3)
    if lt < 0.4: im = shake(im, 10*(1 - lt/0.4), t)
    return im

HOOK = None
def hook_sprite():
    global HOOK
    if HOOK is None:
        g = Image.new("RGBA", (300, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
        for s in (-1, 1):
            d.polygon([(150, 120), (150 + 110*s, 190), (150 + 120*s, 270), (150 + 70*s, 210), (150, 170)], fill=(70, 66, 92), outline=O)
        d.polygon([(130, 40), (170, 40), (170, 180), (130, 180)], fill=(70, 66, 92), outline=O)
        d.ellipse([136, 110, 164, 138], fill=(190, 120, 255), outline=O, width=3)
        HOOK = g
    return HOOK

def shot_lyra(t, lt):
    im = cam(COCKPIT, 1.05, 650, 1000).convert("RGBA")
    # grapple hooks slam onto the window frame, chains trailing up-left
    for i, (hx, hy, ang, t0) in enumerate(((240, 380, 20, 0.1), (840, 340, -25, 0.5))):
        if lt > t0:
            p = min(1, (lt - t0)/0.25)
            cx, cy = hx - 400*(1 - p), hy - 500*(1 - p)
            chain(im, (cx - 500, cy - 600), (cx, cy - 60), 80)
            rot_paste(im, hook_sprite(), ang, cx, cy)
    # red alarm pulse
    a = 0.5 + 0.5*math.sin(t*9)
    g = Image.new("RGBA", (W, H), (255, 30, 40, int(50*a))); im.alpha_composite(g)
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("shocked" if lt < 2.2 else "calm", m, blink(t, 0.9)), 1.02, 540, 760)
    return shake(im, 3 + (12*(1 - (lt - 0.1)/0.3) if 0.1 < lt < 0.4 else 0) + (10*(1 - (lt - 0.5)/0.3) if 0.5 < lt < 0.8 else 0), t, 4)

def shot_ren(t, lt):
    k = ease(lt/5.2)
    im = cam(DECK, 1.2 + 0.1*k, 650, 1000).convert("RGBA")
    # a chain rail snaps in the distance
    if lt > 2.6:
        p = lt - 2.6
        sparks(im, t, 820, 900, 12, 0.5, 9, (255, 200, 120))
        if p < 0.25: im = flash(im, 0.4*(1 - p/0.25), (255, 220, 180))
    wind_lines(im, t, 18, 8, 100)
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked", m, False, int(t*6) % 8, True), 1.12, 540, 760)
    embers(im, t, 0.3)
    if lt < 0.6:
        d = ImageDraw.Draw(im)
        for i in range(10):
            a = i*math.pi/5; d.line([(540 + 330*math.cos(a), 600 + 330*math.sin(a)), (540 + 420*math.cos(a), 600 + 420*math.sin(a))], fill=(255, 255, 255), width=8)
    return shake(im, 3 + (8 if 2.6 < lt < 3.0 else 0), t, 5)

PLANK_W = 46
def side_bridge(im, t, scroll, base_y, fall_from_x=700, holes=0.28, seed=5):
    """horizontal bridge crossing the screen; random planks drop after they pass fall_from_x."""
    d = ImageDraw.Draw(im); r = random.Random(seed)
    i0 = int(scroll // PLANK_W) - 2
    for i in range(i0, i0 + W//PLANK_W + 5):
        x = i*PLANK_W - scroll
        rr = random.Random(i*7919 + seed)
        y = base_y + 26*math.sin((i*PLANK_W)/300.0)
        falls = rr.random() < holes
        if falls and x < fall_from_x:
            ft = (fall_from_x - x)/500.0
            yy = y + 0.5*1800*ft*ft; ang = rr.uniform(-1, 1)*200*ft
            if yy > H: continue
            pl = Image.new("RGBA", (PLANK_W - 4, 26), (118, 82, 56, 255)); ImageDraw.Draw(pl).rectangle([0, 0, PLANK_W - 5, 25], outline=O, width=3)
            rot_paste(im, pl, ang, x + PLANK_W/2, yy)
            continue
        d.rectangle([x + 2, y, x + PLANK_W - 2, y + 26], fill=(124, 86, 58) if i % 2 else (108, 74, 50), outline=O, width=3)
    # chain rails above and below the deck
    for off, sag in ((-120, 30), (34, 10)):
        pts = []
        for j in range(0, W + 40, 22):
            y = base_y + off + 26*math.sin((j + scroll)/300.0) + sag*math.sin((j + scroll)/90.0)
            pts.append((j, y))
        for (x, y) in pts:
            d.ellipse([x - 8, y - 5, x + 8, y + 5], outline=(30, 26, 36), width=3)
    for j in range(-(int(scroll) % 230), W + 230, 230):
        y = base_y + 26*math.sin((j + scroll)/300.0)
        d.line([(j, y - 120), (j, y)], fill=(60, 46, 40), width=10)

def shot_run(t, lt):
    im = cam(CLOUDSKY, 1.05, 650 + 60*lt, 1100).convert("RGBA")
    scroll = 900*lt
    side_bridge(im, t, scroll, 1180)
    bob = lambda ph: -abs(math.sin(t*14 + ph))*18
    runner(im, 700, 1180 + bob(0), 1.0, t, "REN")
    runner(im, 860, 1180 + bob(1.3), 0.95, t + 0.2, "LYRA")
    mini_kuro(im, 560, 1180 + bob(2), 1.0, t)
    # Mire leaping in from the left, violet trail
    mx = -80 + 160*ease(lt/2.8)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([mx - 160, 880, mx + 160, 1220], fill=(140, 60, 220, 110)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    runner(im, mx, 1160 - 60*abs(math.sin(lt*2.2)), 1.15, t + 0.4, "MIRE")
    im.alpha_composite(SPEED[int(t*15) % 4])
    wind_lines(im, t, 22, 13, 120)
    return shake(im, 5, t, 7)

def shot_kuro(t, lt):
    k = ease(lt/4.2)
    im = cam(DECK, 1.3 + 0.05*math.sin(t*10), 650, 1020 - 40*k).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.25)
    blue_fire_glow(im, 540, 700, 380, 0.6)
    m = speaking("KURO", t)
    paste_kuro(im, kuro(m, blink(t, 1.2), int(t*10) % 8, "narrow"), 1.25 + 0.06*k, 540, 640 + 10*math.sin(t*14))
    blue_embers(im, t, 540, 900, 22, 15, 480)
    im.alpha_composite(SPEED[int(t*15) % 4])
    return shake(im, 3, t, 9)

def shot_mire_charge(t, lt):
    k = ease(lt/4.8)
    im = cam(DECK, 1.25 + 0.12*k, 650, 1000).convert("RGBA")
    im.alpha_composite(violet_fog(t, 900, 1600, 120, 31))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([100, 260, 980, 1300], fill=(150, 60, 230, 90))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(70)))
    im.alpha_composite(SPEED[int(t*15) % 4])
    m = speaking("CAPTAIN MIRE", t)
    paste_bust(im, mire_bust(m, blink(t, 0.7)), 1.08 + 0.1*k, 500 + 8*math.sin(t*12), 740)
    sparks(im, t, 300, 1350, 10, 0.5, 12, (200, 140, 255))
    return shake(im, 5 + 3*k, t, 11)

def shot_ren_slash(t, lt):
    im = cam(DECK, 1.15, 650, 1000).convert("RGBA")
    im.alpha_composite(violet_fog(t, 1200, 1600, 80, 41))
    m = speaking("REN", t)
    glow = 0.7 + 0.3*math.sin(t*6) + (0.5 if lt > 2.2 else 0)
    paste_bust(im, ren_bust("determined", m, False, int(t*6) % 8, False), 1.1, 560, 780)
    p = (t - (SLASH_T - 0.35))/0.35
    ang = 30 if p < 0 else 30 - 120*min(1, p)
    rot_paste(im, blade(1.0, min(1.0, glow), 0.9), ang, 200 + (180*min(1, max(0, p))), 900 + 380*min(1, max(0, p)))
    blue_fire_glow(im, 200, 600, 240, 0.3 + 0.3*(lt > 2.2))
    if lt > 2.2:  # charging the cut
        sparks(im, t, 200, 560, 14, 0.6, 4, (170, 245, 255))
    if p > 0:
        slash_arc(im, p*1.2, 540, 1050, 520, 200, 340)
        if p < 0.5: im = flash(im, 0.6*(1 - p/0.5), (210, 250, 255))
    embers(im, t, 0.3, True)
    return shake(im, 2 + (14*max(0, 1 - max(0, p)/0.6) if p > 0 else 0), t, 6)

def shot_cut(t, lt):
    k = ease(lt/5.6)
    im = cam(CLOUDSKY, 1.0 + 0.08*k, 650, 1150).convert("RGBA")
    d = ImageDraw.Draw(im)
    # left island (Mire's side) and right island
    island(im, 40, 680, 300, 280, 91, houses=1)
    island(im, 1060, 640, 300, 280, 92, houses=1)
    # left half: stays up, held by its chains; Mire stranded at the broken end
    brk = 520
    for x in range(180, brk, 34):
        y = 692 + 30*math.sin((x - 180)/(brk - 180)*math.pi*0.8)
        d.rectangle([x, y, x + 30, y + 18], fill=(118, 82, 56), outline=O, width=3)
    chain(im, (180, 580), (brk, 640), 40)
    # right half swings down from the right hinge
    hx, hy = 920, 660
    ang = math.radians(-8 - 42*ease(min(1, lt/2.2)))
    L = hx - brk
    segs = []
    for j in range(0, int(L), 34):
        px = hx - j*math.cos(ang); py = hy - j*math.sin(ang)
        segs.append((px, py))
        d.polygon([(px - 15, py - 9), (px + 15, py - 9), (px + 15, py + 9), (px - 15, py + 9)], fill=(118, 82, 56), outline=O)
    end = segs[-1]
    d.line([(hx, hy - 110), end], fill=(30, 26, 36), width=4)
    # cyan cut glow at the break
    if lt < 1.6:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.ellipse([brk - 120, 580, brk + 120, 820], fill=(90, 230, 255, int(200*(1 - lt/1.6))))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
        sparks(im, t, brk, 700, 16, 0.6, 8, (170, 245, 255))
    # Mire stranded on the left end (safe on the bridge), glaring
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([330, 480, 530, 740], fill=(150, 60, 230, 90)); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
    runner(im, 430, 702, 0.75, 0.0, "MIRE", face=1)
    # the Kestrel below, rising into view
    kx, ky = 420, 1040 - 110*k
    kestrel(im, kx, ky, 0.75, t)
    # heroes leap from the swinging end down to the Kestrel's deck
    if lt > 1.4:
        for idx, (who, dl) in enumerate((("REN", 0), ("LYRA", 0.25), ("KURO", 0.5))):
            p = min(1, max(0, (lt - 1.4 - dl)/1.4))
            sx, sy = end[0], end[1]
            tx, ty = kx - 80 + idx*90, ky - 80
            x = sx + (tx - sx)*p; y = sy + (ty - sy)*p - 260*math.sin(math.pi*p)
            if who == "KURO": mini_kuro(im, x, y, 0.8, t)
            else: runner(im, x, y, 0.6, t, who, face=-1)
    wind_lines(im, t, 14, 21, 90)
    embers(im, t, 0.3)
    return shake(im, 10*max(0, 1 - lt/0.6) + 2, t, 13)

UP = []
for v in range(4):
    r = random.Random(60 + v); lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    for _ in range(40):
        x = r.uniform(0, W); y = r.uniform(0, H); L = r.uniform(150, 420)
        dd.line([(x, y), (x, y - L)], fill=(255, 255, 255, r.randint(80, 170)), width=r.choice([2, 3, 4]))
    UP.append(lay)

def shot_lyra_fall(t, lt):
    im = cam(CLOUDSKY, 1.2, 650, 1500 - 300*ease(lt/5.0)).convert("RGBA")
    # clouds rushing upward past them
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(14)
    for i in range(14):
        x = r.uniform(-100, W + 100); y = (r.uniform(0, H + 600) - 1400*t) % (H + 600) - 300
        d.ellipse([x - 220, y - 70, x + 220, y + 70], fill=(255, 225, 200, 130))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(UP[int(t*15) % 4])
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("calm" if lt < 1.2 else "shocked", m, blink(t, 0.4), lt > 2.8), 1.04, 540, 760)
    return shake(im, 4 + 4*ease(lt/5), t, 15)

def shot_next(t, lt):
    im = shot_lyra_fall(t, 5.0)
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.72, lt/0.3*0.72))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 760, 100, (255, 255, 255), (60, 160, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(120, 200, 255))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 970, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1070, 50, (255, 220, 150), sw=6)
    return im

SHOT_FN = {"title": shot_title, "wide": shot_wide, "mire": shot_mire, "lyra": shot_lyra, "ren": shot_ren, "run": shot_run,
           "kuro": shot_kuro, "mire_charge": shot_mire_charge, "ren_slash": shot_ren_slash, "cut": shot_cut,
           "lyra_fall": shot_lyra_fall, "next": shot_next}

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

# ------------------------------------------------------------ audio (new chase score: E minor, 136 bpm, string ostinato + war drums)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(66)
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
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.65
        return 1.0
    def inten(t):
        pts = [(0, 0.5), (4, 0.5), (10, 0.65), (15.4, 0.8), (25.6, 1.0), (28.4, 0.85), (32.6, 0.95), (37.4, 0.8), (41.8, 1.0),
               (47.4, 0.7), (52.4, 1.0), (57, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    bpm = 136; beat = 60/bpm; bar = beat*4
    chords = [[52, 55, 59], [48, 52, 55], [43, 47, 50], [50, 54, 57]]  # Em C G D
    # sustained pad
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.3, 0.5)
            add(s, t0, pan=-0.4 + 0.4*k, vol=0.022*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.3), t0, vol=0.05*inten(t0))
        t0 += bar; ci += 1
    # 16th-note string ostinato (the chase engine) from the first line on
    t0, k = 4.0, 0
    while t0 < TOTAL - 0.5:
        ch = chords[int(t0 // bar) % 4]; m = [ch[0] + 12, ch[0] + 12, ch[2], ch[1] + 12][k % 4]
        dur = beat/4; n = int(dur*SR)
        add(saw(note(m), dur, 6)*env(n, 0.005, 0.05), t0, pan=0.35*(1 if (k // 4) % 2 else -1), vol=0.022*inten(t0)*speech_duck(t0))
        t0 += beat/4; k += 1
    # heroic brass-ish motif during the run + after the cut
    motif = [(64, 1), (67, 0.5), (71, 0.5), (72, 1), (71, 0.5), (67, 0.5), (69, 2)]
    for tt in (25.7, 41.9):
        for m, bb in motif:
            dur = bb*beat; n = int(dur*SR)
            s = (saw(note(m), dur, 8) + 0.5*saw(note(m - 12), dur, 6))*env(n, 0.03, 0.1)*(1 + 0.12*np.sin(2*np.pi*5.5*tv(n)))
            add(s, tt, pan=0.05, vol=0.03*speech_duck(tt)); tt += dur
    def kick():
        n = int(0.4*SR); x = tv(n); f = 48 + 110*np.exp(-30*x)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-8*x)
    def snare():
        n = int(0.22*SR); x = tv(n)
        return (np.random.RandomState(3).randn(n)*0.6 + 0.4*np.sin(2*np.pi*190*x))*np.exp(-17*x)
    def taiko():
        n = int(0.8*SR); x = tv(n); f = 62 + 46*np.exp(-12*x)
        return (np.sin(2*np.pi*np.cumsum(f)/SR) + 0.2*np.random.RandomState(4).randn(n)*np.exp(-30*x))*np.exp(-5*x)
    KICK, SNARE, TAIKO = kick(), snare(), taiko()
    b = 0
    while b*beat < TOTAL - 1:
        tb = b*beat
        if 25.6 <= tb < 37.4 or 41.8 <= tb < 47.4:
            if b % 2 == 0: add(KICK, tb, vol=0.45)
            if b % 2 == 1: add(SNARE, tb, vol=0.17)
            add(SNARE[:1600]*0.5, tb + beat/2, pan=-0.4, vol=0.07)
            if b % 4 == 3: add(TAIKO, tb + beat/2, pan=0.3, vol=0.22)
        elif 4.0 <= tb < 25.6:
            if b % 2 == 0: add(TAIKO, tb, vol=0.22)
            if b % 4 == 3: add(TAIKO, tb + beat/2, pan=0.3, vol=0.15)
        elif 37.4 <= tb < SLASH_T - 0.3 and b % 1 == 0:
            add(KICK, tb, vol=0.25 + 0.1*(tb - 37.4))  # build-up into the slash
        b += 1
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    # opening boom
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # constant wind on the bridge
    add(lp_noise(TOTAL, 0.03, 0.03)*1.4, 0, vol=0.05)
    # Kestrel props in the wide shot
    dur = 6.0; n = int(dur*SR); x = tv(n)
    add(saw(60, dur, 6)*(0.6 + 0.4*np.sign(np.sin(2*np.pi*18*x)))*env(n, 1.0, 1.0), 4.0, pan=0.4, vol=0.05)
    # grapple clanks
    for tt, pn in ((15.55, -0.5), (15.95, 0.5)):
        n = int(1.0*SR); x = tv(n)
        add((np.sin(2*np.pi*480*x) + 0.7*np.sin(2*np.pi*1310*x) + 0.5*rs.randn(n)*np.exp(-30*x))*np.exp(-7*x), tt, pan=pn, vol=0.2)
    # alarm beeps in the cockpit
    for i in range(8):
        n = int(0.18*SR); x = tv(n); add(np.sign(np.sin(2*np.pi*880*x))*env(n, 0.005, 0.03), 15.6 + i*0.55, vol=0.03)
    # chain snaps (distant in ren shot; during run)
    def snap(): n = int(0.6*SR); x = tv(n); return (np.sin(2*np.pi*900*x) + rs.randn(n)*0.8)*np.exp(-12*x)
    for tt in (23.0, 26.3, 27.5, 30.4):
        add(snap(), tt, pan=rs.uniform(-0.6, 0.6), vol=0.22)
    # plank creaks / falling wood knocks during the run
    for i in range(10):
        n = int(0.12*SR); x = tv(n)
        add(np.sin(2*np.pi*rs.uniform(160, 260)*x)*np.exp(-30*x), 25.7 + i*0.27, pan=rs.uniform(-0.7, 0.7), vol=0.18)
    # rising charge + SLASH
    dur = 2.0; n = int(dur*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(200 + 900*(x/dur)**2)/SR)*(x/dur)*0.6, SLASH_T - 2.0, vol=0.08)
    add(whoosh(0.5, True)*1.6, SLASH_T - 0.35, vol=0.45)
    n = int(1.6*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(60 + 120*np.exp(-18*x))/SR)*np.exp(-3*x) + 0.5*rs.randn(n)*np.exp(-9*x), SLASH_T, vol=0.6)
    add(snap(), SLASH_T + 0.05, vol=0.4)
    # bridge groan + rumble as it splits
    dur = 5.0; n = int(dur*SR); x = tv(n)
    add((saw(42, dur, 5)*(0.7 + 0.3*np.sin(2*np.pi*3*x)) + lp_noise(dur, 0.04, 0.02))*env(n, 0.1, 1.5), 41.8, vol=0.12)
    n = int(1.0*SR); x = tv(n)
    add((np.sin(2*np.pi*300*x) + 0.5*np.sin(2*np.pi*820*x))*np.exp(-5*x), 44.7, pan=-0.2, vol=0.12)  # landing thump on deck
    # falling wind for Lyra's hook
    dur = 5.0; add(lp_noise(dur, 0.05, 0.3)*env(int(dur*SR), 0.5, 0.3)*2.0, 47.4, vol=0.12)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 52.4, vol=0.6)
    for i, m in enumerate([64, 71, 76, 79, 83]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 52.45, pan=-0.6 + 0.3*i, vol=0.05)
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
