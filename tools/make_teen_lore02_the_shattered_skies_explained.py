"""SKYFORGE SAGA Lore: The Shattered Skies Explained  (no-voice build: music + sfx + timed captions).
World-lore Short. Reuses Ep 1-6 / Lore 1 helpers; new shots: the one sky-kingdom breaking apart, a holo world map,
shard rain, and a tilt-down into the Cloud Sea. New score (D minor, 84 bpm)."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, SPEED, cam, shake, flash,
                                            VIG, light_rays, text_center, glow_text, paste_bust, ease, blink, KING_BG, KING_DOT,
                                            EMBERS, WIDE, sky_cracks)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, energy_bolts, blade
from make_teen_ep04_lyras_airship import COCKPIT, wind_lines
from make_teen_ep05_the_fox_in_the_engine import BRIDGE, paste_kuro, blue_embers, blue_fire_glow
from make_teen_lore01_who_is_ren_asaka import panel, callout, pulse_rings, SCAN, FILE_BG, bust_pt

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/lore02_the_shattered_skies_explained.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
TITLE, NEXT, NEXT_EP = "The Shattered Skies Explained", "Into the Cloud Sea", 7

SHOTS = [("title", 0.0, 4.0), ("kingdom", 4.0, 11.0), ("lyra", 11.0, 16.8), ("map", 16.8, 23.2), ("ren", 23.2, 28.8),
         ("shards", 28.8, 34.8), ("king", 34.8, 39.8), ("kuro", 39.8, 44.8), ("deep", 44.8, 52.4), ("next", 52.4, 56.4)]
TOTAL = 56.4
BREAK_T = 8.9
LINES = [
    ("NARRATOR", "Long ago, the whole sky was one kingdom... until the day it shattered.", 4.3, 8.8),
    ("LYRA", "Now it's a thousand floating islands. And I've crashed into most of them.", 11.4, 16.4),
    ("NARRATOR", "The islands drift on sky-winds. Only chain-bridges and airships connect them.", 17.2, 22.8),
    ("REN", "Rule one out here: never look down. Rule two: seriously. Never look down.", 23.6, 28.4),
    ("NARRATOR", "When the kingdom broke, its power fell as sky-shards. Whoever gathers them... rules the sky.", 29.2, 34.4),
    ("HOLLOW KING", "Then the sky will have one ruler again. Me.", 35.2, 39.4),
    ("KURO", "Everyone looks up at the shards. Nobody asks what fell down.", 40.2, 44.4),
    ("NARRATOR", "Below the islands lies the Cloud Sea. No map shows what's under it.", 45.2, 49.0),
    ("NARRATOR", "And the Kestrel is about to fall right into it.", 49.3, 52.2),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255),
          "HOLLOW KING": (190, 120, 255)}
draw_caption, speaking = e1.draw_caption, e1.speaking

# ------------------------------------------------------------ the old sky-kingdom (one giant island + palace)
KX, KY = 550, 470   # sprite centre used for the break
def make_kingdom():
    sp = Image.new("RGBA", (1100, 1050), (0, 0, 0, 0))
    island(sp, 550, 560, 1000, 460, 91, houses=0, lit=False)
    d = ImageDraw.Draw(sp); o = OUT
    wall, wall_sh, roof, gold = (232, 224, 206), (196, 186, 170), (36, 96, 110), (255, 206, 110)
    d.rectangle([180, 470, 920, 560], fill=wall, outline=o, width=4)
    for x in range(180, 921, 46): d.rectangle([x, 450, x + 24, 472], fill=wall, outline=o, width=3)
    d.rectangle([700, 470, 920, 560], fill=wall_sh)
    towers = [(250, 70, 200), (380, 90, 290), (550, 130, 420), (720, 90, 300), (850, 70, 210)]
    for x, w, h in towers:
        top = 560 - h
        d.rectangle([x - w/2, top, x + w/2, 560], fill=wall, outline=o, width=4)
        d.rectangle([x + w*0.15, top, x + w/2, 560], fill=wall_sh)
        d.polygon([(x - w*0.65, top), (x + w*0.65, top), (x, top - w*1.3)], fill=roof, outline=o)
        d.polygon([(x, top - w*1.3), (x + w*0.65, top), (x + w*0.15, top)], fill=(22, 66, 80))
        for k in range(int(h/70)):
            wy = top + 30 + k*64
            d.rounded_rectangle([x - w*0.16, wy, x + w*0.12, wy + 34], 8, fill=gold, outline=o, width=2)
        d.line([(x, top - w*1.3), (x, top - w*1.3 - 40)], fill=o, width=4)
        d.polygon([(x, top - w*1.3 - 40), (x + 36, top - w*1.3 - 30), (x, top - w*1.3 - 20)], fill=(90, 220, 255), outline=o)
    # great crowning shard above the central spire
    s = shard(90); sp.alpha_composite(s, (550 - s.width//2, int(560 - 420 - 130*1.3 - 150)))
    return sp
KINGDOM = make_kingdom()

def make_fragments():
    frags = []
    angs = [-100, -40, 10, 60, 115, 170, 220, 260]
    for i in range(len(angs) - 1):
        a0, a1 = math.radians(angs[i]), math.radians(angs[i + 1])
        m = Image.new("L", KINGDOM.size, 0); md = ImageDraw.Draw(m)
        pts = [(KX, KY)] + [(KX + 2000*math.cos(a0 + (a1 - a0)*k/6), KY + 2000*math.sin(a0 + (a1 - a0)*k/6)) for k in range(7)]
        md.polygon(pts, fill=255)
        piece = KINGDOM.copy(); piece.putalpha(Image.composite(KINGDOM.split()[3], Image.new("L", KINGDOM.size, 0), m))
        bb = piece.getbbox()
        if not bb: continue
        crop = piece.crop(bb)
        cx, cy = (bb[0] + bb[2])/2, (bb[1] + bb[3])/2
        mid = (a0 + a1)/2
        frags.append((crop, cx, cy, math.cos(mid), math.sin(mid), (i % 3 - 1)*7))
    return frags
FRAGS = make_fragments()

def crack_lines():
    lay = Image.new("RGBA", KINGDOM.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for ang in [-100, -40, 10, 60, 115, 170, 220, 260]:
        a = math.radians(ang); r = random.Random(ang)
        pts = [(KX, KY)]
        for k in range(1, 8):
            rr = k*80; pts.append((KX + rr*math.cos(a) + r.uniform(-14, 14), KY + rr*math.sin(a) + r.uniform(-14, 14)))
        d.line(pts, fill=(140, 245, 255, 255), width=8)
    m = KINGDOM.split()[3]
    lay.putalpha(Image.composite(lay.split()[3], Image.new("L", lay.size, 0), m))
    glow = lay.filter(ImageFilter.GaussianBlur(10)); glow.alpha_composite(lay)
    return glow
CRACKS = crack_lines()

def make_old_sky():
    im = Image.fromarray(grad(W, H, [(0, (30, 50, 96)), (0.4, (80, 130, 160)), (0.62, (250, 180, 110)), (0.75, (255, 214, 150)), (1, (120, 110, 140))])).convert("RGBA")
    clouds(im, 1300, 1920, 93, tint=(255, 220, 180))
    return im
OLD_SKY = make_old_sky()

# ------------------------------------------------------------ holo world map
def blob(d, cx, cy, rx, ry, seed, fill, outline):
    r = random.Random(seed); pts = []
    for k in range(16):
        a = 2*math.pi*k/16; f = r.uniform(0.75, 1.15)
        pts.append((cx + rx*f*math.cos(a), cy + ry*f*math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=4)

MAP_ISLES = [  # name, x, y, rx, ry, label dx, dy, colour
    ("EDGE ISLES", 250, 1010, 70, 46, -10, 56, (255, 190, 110)),
    ("CHAIN REACH", 470, 790, 110, 60, -40, 64, (120, 235, 255)),
    ("SHARD MARKET", 760, 960, 80, 52, -150, 60, (120, 235, 255)),
    ("STORM WALL", 700, 470, 120, 50, -110, -100, (200, 210, 255)),
    ("HOLLOW CITADEL", 330, 420, 90, 60, -130, 62, (200, 140, 255)),
]
def make_map():
    im = FILE_BG.copy(); im.alpha_composite(SCAN)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([110, 230, 920, 1180], 30, fill=(8, 20, 40, 230), outline=(90, 220, 255, 255), width=4)
    for x in range(110, 921, 81): d.line([(x, 232), (x, 1178)], fill=(90, 220, 255, 30), width=2)
    for y in range(230, 1181, 79): d.line([(112, y), (918, y)], fill=(90, 220, 255, 30), width=2)
    # cloud-sea swirl (uncharted)
    for k in range(6):
        r = 60 + k*22
        d.arc([560 - r, 700 - r*0.7, 560 + r, 700 + r*0.7], 20*k, 20*k + 250, fill=(70, 120, 160, 110), width=5)
    im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    for nm, x, y, rx, ry, dx, dy, col in MAP_ISLES:
        blob(d, x, y, rx, ry, sum(map(ord, nm)) % 97, (24, 70, 84), col)
        blob(d, x - rx*0.2, y - ry*0.2, rx*0.45, ry*0.35, sum(map(ord, nm)) % 31, (50, 120, 110), None)
    # chain-bridges (dotted)
    for a, b in (((300, 990), (400, 820)), ((570, 800), (710, 930)), ((420, 760), (360, 470))):
        for k in range(15):
            p = k/14; x = a[0] + (b[0] - a[0])*p; y = a[1] + (b[1] - a[1])*p
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(230, 230, 230))
    for nm, x, y, rx, ry, dx, dy, col in MAP_ISLES:
        f = font(34)
        d.text((x + dx, y + dy), nm, font=f, fill=col, stroke_width=5, stroke_fill=(6, 8, 16))
    d.text((150, 255), "THE SHATTERED SKIES", font=font(44), fill=(255, 255, 255), stroke_width=5, stroke_fill=(6, 8, 16))
    d.text((150, 312), "drift chart  //  partial", font=font(30), fill=(120, 235, 255))
    d.text((470, 640), "CLOUD SEA", font=font(30), fill=(150, 190, 220), stroke_width=4, stroke_fill=(6, 8, 16))
    d.text((470, 676), "uncharted", font=font(26), fill=(150, 190, 220))
    return im
MAP = make_map()
ROUTE = [(250, 1010), (300, 990), (400, 820), (470, 790), (570, 800), (640, 760), (600, 700)]

def route_pt(p):
    segs = list(zip(ROUTE[:-1], ROUTE[1:])); L = [math.dist(a, b) for a, b in segs]; tot = sum(L)
    target = p*tot
    for (a, b), l in zip(segs, L):
        if target <= l:
            q = target/l; return (a[0] + (b[0] - a[0])*q, a[1] + (b[1] - a[1])*q)
        target -= l
    return ROUTE[-1]

# ------------------------------------------------------------ the deep (tall pan background)
def make_deep():
    w, h = 1300, 4000
    im = Image.fromarray(grad(w, h, [(0, (14, 22, 52)), (0.18, (90, 70, 120)), (0.3, (240, 150, 100)), (0.38, (255, 190, 130)),
                                     (0.5, (120, 120, 150)), (0.62, (40, 60, 90)), (0.8, (10, 22, 40)), (1, (2, 6, 14))])).convert("RGBA")
    stars(im, 120, 700, 94)
    island(im, 260, 900, 300, 260, 95, houses=2); island(im, 1050, 760, 360, 300, 96, houses=1)
    island(im, 700, 1250, 420, 360, 97, houses=3)
    chain(im, (410, 900), (500, 1250), 50); chain(im, (870, 760), (900, 1250), 50)
    # thick cloud layer
    clouds(im, 1550, 2300, 98, tint=(255, 200, 170))
    clouds(im, 1750, 2500, 99, tint=(200, 180, 200))
    # sunken ruins far below: broken spires in silhouette
    d = ImageDraw.Draw(im)
    for x, wdt, top in ((300, 110, 3050), (520, 150, 2850), (760, 100, 3100), (1000, 130, 2950)):
        d.polygon([(x - wdt/2, 4000), (x - wdt/2, top), (x - wdt*0.1, top - 60), (x + wdt*0.15, top + 30), (x + wdt/2, top - 20), (x + wdt/2, 4000)],
                  fill=(16, 30, 46), outline=(40, 80, 110))
        for k in range(4):
            wy = top + 120 + k*170
            d.rectangle([x - wdt*0.15, wy, x + wdt*0.1, wy + 50], fill=(30, 80, 100))
    # faint mist over the ruins
    mist = Image.new("RGBA", (w, h), (0, 0, 0, 0)); md = ImageDraw.Draw(mist)
    r = random.Random(100)
    for _ in range(60):
        x, y = r.uniform(0, w), r.uniform(2600, 3900)
        md.ellipse([x - 260, y - 60, x + 260, y + 60], fill=(60, 110, 140, 60))
    im.alpha_composite(mist.filter(ImageFilter.GaussianBlur(30)))
    return im.convert("RGB")
DEEP = make_deep()

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(WIDE, 1.05 + 0.05*lt, 760, 1150).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 8, 20, 255)), 0.5)
    im.alpha_composite(light_rays(t, (110, 220, 255), 540, -120, 55))
    embers(im, t, 0.6, True)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 700, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 850, 540 + w, 856], fill=(90, 220, 255))
        text_center(d, "—  LORE #2  —", 880, 60, (255, 190, 110))
    if lt > 1.2:
        glow_text(im, "The Shattered Skies", 970, 92, (255, 255, 255), (60, 160, 255))
        glow_text(im, "Explained", 1080, 80, (255, 255, 255), (60, 160, 255))
    return flash(im, max(0, 1 - lt/0.35))

def shot_kingdom(t, lt):
    a = t - BREAK_T
    im = OLD_SKY.copy()
    im.alpha_composite(light_rays(t, (255, 220, 150), 540, -150, 50))
    sc = 0.86 + 0.04*ease(lt/4.9)
    ox, oy = 540, 820 + 8*math.sin(t*1.2)
    if a < 0:
        sp = KINGDOM
        c = min(1, max(0, (lt - 2.6)/1.8))
        if c > 0:
            sp = KINGDOM.copy(); cr = CRACKS.copy()
            cr.putalpha(cr.split()[3].point(lambda v: int(v*c)))
            sp.alpha_composite(cr)
        s = sp.resize((int(sp.width*sc), int(sp.height*sc)), Image.BILINEAR)
        im.alpha_composite(s, (int(ox - KX*sc), int(oy - KY*sc)))
        embers(im, t, 0.3)
        return shake(im, 6*c if c > 0 else 0, t, 2)
    p = ease(min(1, a/1.6))*1.0 + 0.25*max(0, a - 1.6)
    im = Image.blend(im, Image.new("RGBA", im.size, (40, 30, 70, 255)), min(0.5, a*0.4))
    sky_cracks(im, 7)
    for crop, cx, cy, dx, dy, rot in FRAGS:
        s = crop.resize((max(1, int(crop.width*sc)), max(1, int(crop.height*sc))), Image.BILINEAR)
        px = ox + (cx - KX)*sc + dx*420*p; py = oy + (cy - KY)*sc + dy*300*p + 120*p
        rot_paste(im, s, rot*p*2, px, py)
    sparks(im, t, ox, oy, 30, 1.4, 12, (150, 240, 255))
    # tiny shards scattering
    r = random.Random(5)
    for k in range(12):
        ang = r.uniform(0, 2*math.pi); sp = r.uniform(300, 700)
        x = ox + math.cos(ang)*sp*min(1.5, a); y = oy + math.sin(ang)*sp*min(1.5, a)*0.7 + 200*a*a
        sh = shard(26 + k % 3*8); im.alpha_composite(sh, (int(x - sh.width/2), int(y - sh.height/2)))
    im.alpha_composite(SPEED[int(t*15) % 4])
    embers(im, t, 1.0, True, 2.0)
    im = shake(im, 22*max(0, 1 - a/0.9) + 3, t, 6)
    return flash(im, max(0, 1 - a/0.35))

def shot_lyra(t, lt):
    im = cam(COCKPIT, 1.05 + 0.03*ease(lt/5.8), 650, 1000).convert("RGBA")
    wind_lines(im, t, 16, 7, 90)
    m = speaking("LYRA", t)
    expr = "smirk" if lt < 3.2 else "calm"
    paste_bust(im, lyra_bust(expr, m, blink(t, 0.6)), 1.02, 540, 760)
    # dashboard "dent counter" gag
    if lt > 3.2:
        d = ImageDraw.Draw(im); a = ease((lt - 3.2)/0.3)
        panel(im, [580, 260 - 20*(1 - a), 900, 420 - 20*(1 - a)], (255, 190, 110), int(200*a))
        d = ImageDraw.Draw(im)
        d.text((610, 280 - 20*(1 - a)), "HULL DENTS", font=font(34), fill=(255, 190, 110))
        n = 40 + int(min(1, (lt - 3.3)/1.2)*87)
        d.text((610, 324 - 20*(1 - a)), "%d" % n, font=font(60), fill=(255, 255, 255), stroke_width=5, stroke_fill=(8, 8, 16))
    return shake(im, 2, t, 4)

def shot_map(t, lt):
    k = ease(lt/6.4)
    im = MAP.copy()
    # pulsing "home" pin and animated route + tiny Kestrel marker
    p = ease((lt - 1.0)/4.5)
    if p > 0:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        n = 60
        for i in range(int(n*p)):
            if i % 2 == 0:
                a, b = route_pt(i/n), route_pt((i + 1)/n)
                d.line([a, b], fill=(255, 190, 110, 255), width=6)
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5))); im.alpha_composite(lay)
        kx, ky = route_pt(p)
        ks = airship(1.0, int(t*20) % 8).resize((120, 69), Image.BILINEAR)
        im.alpha_composite(ks, (int(kx - 60), int(ky - 60)))
    d = ImageDraw.Draw(im)
    r = 18 + 6*math.sin(t*6)
    d.ellipse([250 - r, 1010 - r, 250 + r, 1010 + r], outline=(255, 190, 110), width=5)
    if lt > 4.6:
        pulse_rings(im, t, 560, 700, 2, (150, 200, 255))
    sc = 0.84 + 0.04*k
    crop = im.crop((100, 220, 930, 1190)); crop = crop.resize((int(830*sc), int(970*sc)), Image.BILINEAR)
    out = FILE_BG.copy(); out.alpha_composite(SCAN)
    out.alpha_composite(crop, (int(530 - crop.width/2), int(140 + 20*(1 - k))))
    embers(out, t, 0.3, True)
    return out

def shot_ren(t, lt):
    im = cam(BRIDGE, 1.2 + 0.03*ease(lt/5.6), 650, 1080 + 30*lt).convert("RGBA")
    wind_lines(im, t, 18, 9, 120)
    m = speaking("REN", t)
    punch = lt > 2.9
    expr = "shocked" if punch else "determined"
    sc = 1.05 + (0.25*ease((lt - 2.9)/0.25) if punch else 0)
    paste_bust(im, ren_bust(expr, m, blink(t, 0.3) and not punch, int(t*16) % 8, True), sc, 540, 760 + (70 if punch else 0))
    embers(im, t, 0.5)
    if punch and lt < 3.2: im = flash(im, 0.25)
    return shake(im, 7 if 2.9 < lt < 3.4 else 1, t, 3)

def shot_shards(t, lt):
    k = ease(lt/6)
    im = cam(WIDE, 1.15 + 0.1*k, 760, 700).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 28, 255)), 0.35)
    sky_cracks(im, 11)
    r = random.Random(17)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    falls = []
    for i in range(10):
        x0 = r.uniform(80, 900); ph = r.uniform(0, 1); sp = r.uniform(0.5, 0.9); sz = r.choice([30, 40, 55])
        q = (lt*sp*0.5 + ph) % 1.0
        x = x0 - 240*q; y = -120 + 1700*q
        d.line([(x + 140, y - 520), (x, y)], fill=(140, 240, 255, 150), width=int(sz*0.35))
        falls.append((x, y, sz))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    for x, y, sz in falls:
        sh = shard(sz); im.alpha_composite(sh, (int(x - sh.width/2), int(y - sh.height/2)))
    # hero shard rises in front with a callout
    if lt > 2.4:
        a = ease((lt - 2.4)/0.8)
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([240, 380, 840, 1100], fill=(80, 230, 255, int(110*a)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(90)))
        sh = shard(int(80 + 140*a)); cy = 760 + 16*math.sin(t*2.5)
        im.alpha_composite(sh, (int(540 - sh.width/2), int(cy - sh.height/2)))
        callout(im, (560, cy - 60), (540, 210), "SKY-SHARD", "pure sky-magic", (lt - 2.9)/1.6)
    embers(im, t, 0.8, True, 1.5)
    return shake(im, 2, t, 8)

def shot_king(t, lt):
    im = cam(KING_BG, 1.12 - 0.05*ease(lt/5), 620, 1060).convert("RGBA")
    m = speaking("HOLLOW KING", t)
    lvl = {1: 2, 2: 4}[m] if m else int(1 + 0.8*math.sin(t*2))
    paste_bust(im, hollow_king(max(0, min(4, lvl))), 1.25 + 0.06*ease(lt/5), 540, 720)
    # small shards orbiting his empty crown
    for i in range(5):
        a = t*1.4 + i*2*math.pi/5
        sh = shard(26); x = 540 + 300*math.cos(a); y = 330 + 70*math.sin(a)
        if math.sin(a) < 0 or True:
            im.alpha_composite(sh, (int(x - sh.width/2), int(y - sh.height/2)))
    for i, (x0, y0, sp, ph, r, cy) in enumerate(EMBERS[:30]):
        yy = (y0 - sp*0.6*t) % (H + 100) - 50; xx = x0 + 30*math.sin(t + ph)
        im.alpha_composite(KING_DOT, (int(xx - 12), int(yy - 12)))
    if 3.4 < lt < 3.55: im = flash(im, 0.35, (150, 90, 220))
    return shake(im, 4 if lt > 3.4 else 0, t)

def shot_kuro(t, lt):
    k = ease(lt/5)
    im = cam(DEEP, 1.25, 650, 1500 + 120*k).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.3)
    blue_fire_glow(im, 540, 700, 380, 0.6)
    m = speaking("KURO", t)
    eyes = "calm" if lt < 2.4 else "narrow"
    paste_kuro(im, kuro(m, blink(t, 1.2) and eyes == "calm", int(t*10) % 8, eyes), 1.2 + 0.08*k, 540, 660 + 8*math.sin(t*2))
    blue_embers(im, t, 540, 900, 22, 15, 480)
    return im

def shot_deep(t, lt):
    k = ease(lt/6.8)
    im = cam(DEEP, 1.0, 650, 1150 + 1700*k).convert("RGBA")
    # shard glow pulses deep below
    if k > 0.6:
        a = (k - 0.6)/0.4
        pulse_rings(im, t, 560, 1350, 2, (90, 200, 255))
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([380, 1150, 740, 1550], fill=(90, 220, 255, int(120*a*(0.7 + 0.3*math.sin(t*3)))))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    # the Kestrel tumbling down past camera
    if lt > 4.5:
        q = (lt - 4.5)/3.1
        ks = airship(0.6, int(t*30) % 8).resize((560, 323), Image.BILINEAR)
        x = 760 - 260*q; y = -200 + 900*q
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).line([(x + 120, y - 600), (x, y)], fill=(255, 255, 255, 70), width=90)
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30)))
        rot_paste(im, ks, -18 - 10*math.sin(t*4), x, y)
        im.alpha_composite(SPEED[int(t*15) % 4])
    embers(im, t, 0.4, True)
    return shake(im, 5 if lt > 4.5 else 0, t, 5)

def shot_next(t, lt):
    im = cam(DEEP, 1.05, 650, 2200).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.62, lt/0.3*0.62))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, "Ep %d: %s" % (NEXT_EP, NEXT), 760, 96, (255, 255, 255), (60, 160, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(90, 220, 255))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA", 960, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1060, 50, (255, 220, 150), sw=6)
    embers(im, t, 0.5, True)
    return im

SHOT_FN = {"title": shot_title, "kingdom": shot_kingdom, "lyra": shot_lyra, "map": shot_map, "ren": shot_ren,
           "shards": shot_shards, "king": shot_king, "kuro": shot_kuro, "deep": shot_deep, "next": shot_next}

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

# ------------------------------------------------------------ audio (new world-wonder score: D minor, 84 bpm)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(72)
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
    bpm = 84; beat = 60/bpm; bar = beat*4
    chords = [[50, 53, 57], [46, 50, 53], [41, 45, 48], [48, 52, 55]]  # Dm Bb F C
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.68
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.5), (8.9, 1.0), (11, 0.6), (16.8, 0.55), (23.2, 0.65), (28.8, 0.85), (34.8, 0.6), (39.8, 0.45),
               (44.8, 0.5), (49.3, 1.0), (52.4, 1.0), (56.4, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.5, 0.6)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.03*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.4), t0, vol=0.05*inten(t0))
        # airy "choir": stacked sines with slow vibrato
        n = int(dur*SR); x = tv(n); vib = 1 + 0.004*np.sin(2*np.pi*4.5*x)
        ch_s = sum(np.sin(2*np.pi*note(m + 12)*x*vib) for m in ch)/3*env(n, 0.8, 0.8)
        add(ch_s, t0, pan=0.0, vol=0.025*speech_duck(t0 + 1))
        t0 += bar; ci += 1
    # harp-like plucks (own pattern) during map / lyra
    t0, k = 11.0, 0
    while t0 < 28.8:
        ch = chords[int(t0 // bar) % 4]; m = [ch[0] + 24, ch[2] + 24, ch[1] + 24, ch[0] + 36, ch[2] + 24, ch[1] + 12][k % 6]
        n = int(0.8*SR); x = tv(n)
        add((np.sin(2*np.pi*note(m)*x) + 0.3*np.sin(2*np.pi*note(m)*2*x)*np.exp(-6*x))*np.exp(-5*x), t0, pan=0.4*(1 if k % 2 else -1), vol=0.04*speech_duck(t0))
        t0 += beat/2; k += 1
    # lead melody over the shard rain (own melody)
    motif = [(62, 1), (65, 0.5), (69, 0.5), (74, 1.5), (72, 0.5), (69, 1), (70, 1), (69, 2)]
    tt = 29.0
    for m, b in motif:
        dur = b*beat; n = int(dur*SR)
        s = saw(note(m), dur, 8)*env(n, 0.04, 0.12)*(1 + 0.15*np.sin(2*np.pi*5*tv(n)))
        add(s, tt, pan=0.1, vol=0.035); tt += dur
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
        if 28.8 <= tb < 34.8 or 49.3 <= tb < 52.4:
            if b % 4 in (0, 2) or b % 8 == 7: add(KICK, tb, vol=0.5)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.16)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.07)
        elif 16.8 <= tb < 28.8:
            if b % 2 == 0: add(KICK, tb, vol=0.22)
        elif 34.8 <= tb < 39.8 and b % 4 == 0:
            add(TAIKO, tb, vol=0.5)
        elif 6.5 <= tb < BREAK_T:
            add(TAIKO, tb, vol=0.2 + 0.12*(tb - 6.5))
        b += 1
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    def blip(f=1400):
        n = int(0.09*SR); x = tv(n); return np.sin(2*np.pi*f*x)*np.exp(-30*x)
    add(blip(1300), 16.8 + 0.2, vol=0.12); add(blip(900), 16.8 + 4.6, vol=0.12)
    add(blip(1500), 28.8 + 3.0, vol=0.12)
    for i in range(6): add(blip(1100 + 60*i), 11.0 + 3.3 + 0.2*i, vol=0.06)
    # title hit
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # cracking rumble + rising whine into the break
    dur = BREAK_T - 6.6; n = int(dur*SR)
    f = np.linspace(200, 1400, n); amp = np.linspace(0.05, 1, n)**2
    add((np.sin(2*np.pi*np.cumsum(f)/SR)*0.2 + whoosh(dur, True)*0.5)*amp, 6.6, vol=0.28)
    add(lp_noise(dur, 0.01, 0.04)*amp*3, 6.6, vol=0.25)
    # the shattering: big impact + glassy ring
    n = int(4.0*SR); x = tv(n); f = 38 + 60*np.exp(-6*x)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-1.3*x) + 0.7*whoosh(4.0, False)*np.exp(-1.0*x), BREAK_T, vol=0.9)
    n = int(4.0*SR); x = tv(n)
    add(sum(np.sin(2*np.pi*fq*x)*np.exp(-(0.8 + i*0.3)*x) for i, fq in enumerate((1174.7, 1568.0, 2093.0, 2637.0)))/4, BREAK_T + 0.03, vol=0.08)
    # wind gusts
    add(lp_noise(5.6, 0.05, 0.12)*env(int(5.6*SR), 0.5, 1.0), 11.0, pan=0.3, vol=0.07)
    add(lp_noise(5.6, 0.05, 0.12)*env(int(5.6*SR), 0.5, 1.0), 23.2, pan=-0.3, vol=0.08)
    # comedic sting on "seriously"
    add(TAIKO, 26.1, vol=0.35)
    # shard shimmer falls
    for i in range(8):
        n = int(0.6*SR); x = tv(n); fq = 1800 + 300*(i % 4)
        add(np.sin(2*np.pi*np.cumsum(np.linspace(fq, fq*0.6, n))/SR)*np.exp(-5*x), 28.9 + i*0.7, pan=-0.6 + 0.17*i, vol=0.04)
    # Hollow King drone + hit on "Me."
    n = int(5.0*SR); x = tv(n)
    add((saw(note(38), 5.0, 5) + 0.5*np.sin(2*np.pi*note(45)*x*(1 + 0.003*np.sin(2*np.pi*5*x))))*env(n, 0.8, 1.0), 34.8, vol=0.08)
    n = int(2.0*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(40 + 50*np.exp(-6*x))/SR)*np.exp(-2*x), 38.2, vol=0.5)
    # Kuro: soft blue-flame crackle bed
    add(lp_noise(5.0, 0.2, 0.25)*0.3*env(int(5*SR), 0.6, 0.8), 39.8, vol=0.06)
    # descent into the deep: falling sweep + low drone
    dur = 7.6; n = int(dur*SR); x = tv(n)
    add((saw(note(26), dur, 4)*0.6 + np.sin(2*np.pi*note(33)*x))*env(n, 1.5, 1.0), 44.8, vol=0.09)
    dur = 3.0; n = int(dur*SR); f = np.linspace(900, 160, n)
    add((np.sin(2*np.pi*np.cumsum(f)/SR)*0.25 + whoosh(dur, False)*0.6)*np.linspace(0.2, 1, n), 49.3, vol=0.35)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 52.4, vol=0.6)
    for i, m in enumerate([62, 69, 74, 77, 81]):
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
