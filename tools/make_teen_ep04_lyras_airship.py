"""SKYFORGE SAGA Ep 4: Lyra's Airship  (no-voice build: music + sfx + timed captions).
Introduces Lyra Vell (teen_art.lyra_bust) and the Kestrel. Reuses Ep 1-3 helpers; new shots and a new flight score."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, SPEED, cam, shake, flash,
                                            VIG, light_rays, text_center, glow_text, paste_bust, ease, blink, WIDE,
                                            ren_back_silhouette)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, blade, fist
from make_teen_ep03_hollow_soldiers import violet_fog, soldier, EDGE, CLOUDSKY

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/04_lyras_airship.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 4, "Lyra's Airship", "The Fox in the Engine"

SHOTS = [("title", 0.0, 4.0), ("arrive", 4.0, 10.2), ("lyra_intro", 10.2, 17.0), ("ren_broke", 17.0, 23.0),
         ("lyra_deal", 23.0, 29.2), ("leap", 29.2, 35.2), ("mire", 35.2, 41.2), ("cockpit", 41.2, 47.0),
         ("engine", 47.0, 53.0), ("next", 53.0, 57.5)]
TOTAL = 57.5
LINES = [
    ("NARRATOR", "The engine belonged to the Kestrel. Its pilot belonged to no one.", 4.4, 9.8),
    ("LYRA", "Need a lift off this rock, shard boy? It isn't free.", 10.6, 16.6),
    ("REN", "I don't have any money. I have... a glowing sword?", 17.4, 22.7),
    ("LYRA", "Then you owe me. With interest. Grab the ladder!", 23.4, 28.8),
    ("NARRATOR", "The soldiers reached the edge one breath too late.", 29.6, 34.6),
    ("CAPTAIN MIRE", "Mark that airship. The Kestrel can't hide in the sky forever.", 35.5, 40.8),
    ("LYRA", "Relax. Nobody has ever caught my Kestrel.", 41.5, 46.5),
    ("REN", "Then why is your engine... growling?", 47.4, 52.6),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "CAPTAIN MIRE": (255, 150, 90)}
draw_caption, speaking = e1.draw_caption, e1.speaking

# ------------------------------------------------------------ backgrounds
def make_hull():
    """Kestrel's gondola side at dusk: brass-trimmed wooden hull, portholes, rigging, sky behind."""
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (14, 26, 56)), (0.35, (60, 70, 120)), (0.55, (230, 130, 90)), (0.7, (250, 180, 110)), (1, (80, 70, 110))])).convert("RGBA")
    stars(im, 60, 500, 51); clouds(im, 1300, 2200, 52, tint=(255, 190, 150))
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    # envelope underside at top
    d.polygon([(-50, 0), (1350, 0), (1350, 260), (650, 340), (-50, 260)], fill=(52, 60, 84), outline=o)
    for x in range(60, 1300, 160): d.line([(x, 0), (x + 20, 300)], fill=(30, 34, 52), width=6)
    for x in (200, 520, 840, 1160): d.line([(x, 290), (x - 40, 1000)], fill=(30, 22, 26), width=5)
    # hull (right part, she leans out of the hatch on the left)
    d.polygon([(-50, 980), (1350, 940), (1350, 1500), (1200, 1640), (100, 1660), (-50, 1560)], fill=(110, 68, 42), outline=o)
    d.polygon([(-50, 1300), (1350, 1280), (1350, 1500), (1200, 1640), (100, 1660), (-50, 1560)], fill=(80, 48, 30))
    d.rectangle([-50, 960, 1350, 1000], fill=BRASS, outline=o, width=4)
    for x in range(0, 1300, 70): d.line([(x, 1000), (x - 10, 1640)], fill=(86, 52, 32), width=3)
    for x in (820, 1020, 1220):
        d.ellipse([x - 60, 1080, x + 60, 1200], fill=BRASS, outline=o, width=4)
        d.ellipse([x - 44, 1096, x + 44, 1184], fill=(255, 210, 130))
    # open hatch frame
    d.rectangle([180, 700, 760, 1500], fill=(40, 26, 22), outline=o, width=6)
    d.rectangle([200, 720, 740, 1480], fill=(70, 46, 34))
    d.rectangle([180, 700, 760, 740], fill=BRASS, outline=o, width=4)
    return im.convert("RGB")
HULL = make_hull()

def make_cockpit():
    w, h = 1300, 2200
    im = Image.new("RGBA", (w, h), (40, 26, 22, 255))
    # big window with rushing clouds (static; motion added per frame)
    sky = Image.fromarray(grad(w, 1100, [(0, (20, 40, 80)), (0.5, (220, 120, 90)), (0.75, (250, 180, 120)), (1, (120, 90, 120))])).convert("RGBA")
    clouds(sky, 650, 1100, 61, tint=(255, 200, 160))
    im.alpha_composite(sky, (0, 120))
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    # window frame struts
    d.rectangle([0, 0, w, 140], fill=(60, 40, 30)); d.rectangle([0, 1180, w, h], fill=(60, 40, 30))
    for x in (0, 430, 860, 1290):
        d.polygon([(x - 26, 120), (x + 26, 120), (x + 40, 1220), (x - 40, 1220)], fill=(80, 54, 38), outline=o)
    d.rectangle([-10, 110, w + 10, 150], fill=BRASS, outline=o, width=4)
    d.rectangle([-10, 1170, w + 10, 1210], fill=BRASS, outline=o, width=4)
    # console with gauges
    d.polygon([(-20, 1300), (1320, 1260), (1320, h), (-20, h)], fill=(70, 46, 34), outline=o)
    for i, (gx, gy, r) in enumerate(((180, 1420, 80), (420, 1390, 60), (900, 1390, 70), (1120, 1430, 84))):
        d.ellipse([gx - r - 10, gy - r - 10, gx + r + 10, gy + r + 10], fill=BRASS, outline=o, width=4)
        d.ellipse([gx - r, gy - r, gx + r, gy + r], fill=(236, 226, 200), outline=o, width=3)
        for k in range(9):
            a = math.radians(200 + k*17.5)
            d.line([(gx + r*0.75*math.cos(a), gy + r*0.75*math.sin(a)), (gx + r*0.9*math.cos(a), gy + r*0.9*math.sin(a))], fill=o, width=3)
    return im.convert("RGB")
COCKPIT = make_cockpit()

def make_engine_room():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (20, 14, 18)), (0.5, (60, 34, 26)), (1, (24, 16, 18))])).convert("RGBA")
    d = ImageDraw.Draw(im); o = (14, 12, 22)
    # pipes
    for x, c in ((120, (150, 110, 60)), (300, (120, 86, 50)), (1020, (150, 110, 60)), (1180, (110, 80, 46))):
        d.rectangle([x - 34, 0, x + 34, h], fill=c, outline=o, width=5)
        for y in range(120, h, 340): d.rectangle([x - 44, y, x + 44, y + 36], fill=BRASS, outline=o, width=4)
    d.rectangle([0, 280, w, 330], fill=(120, 86, 50), outline=o, width=5)
    # engine block with vent grille (where Kuro hides)
    d.rounded_rectangle([340, 520, 960, 1500], 60, fill=(70, 72, 86), outline=o, width=7)
    d.rounded_rectangle([380, 560, 920, 1460], 40, fill=(54, 56, 70))
    d.rounded_rectangle([430, 860, 870, 1220], 30, fill=(18, 14, 18), outline=o, width=6)
    for y in range(890, 1200, 52):
        d.rectangle([440, y, 860, y + 18], fill=(90, 92, 108), outline=o, width=3)
    for x, y in ((400, 600), (900, 600), (400, 1420), (900, 1420)):
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=BRASS, outline=o, width=3)
    return im.convert("RGB")
ENGINE = make_engine_room()

# ------------------------------------------------------------ helpers
def kestrel(im, x, y, sc, t, lit=1.0):
    sh = airship(lit, int(t*20) % 8)
    sh = sh.resize((max(1, int(900*sc)), max(1, int(520*sc))), Image.BILINEAR)
    im.alpha_composite(sh, (int(x - sh.width/2), int(y - sh.height/2)))

def ladder(im, x0, y0, length, sway, sc=1.0):
    d = ImageDraw.Draw(im); col = (150, 110, 70); o = (20, 14, 12)
    x1 = x0 + sway
    for dx in (-26*sc, 26*sc):
        d.line([(x0 + dx, y0), (x1 + dx, y0 + length)], fill=o, width=int(10*sc)); d.line([(x0 + dx, y0), (x1 + dx, y0 + length)], fill=col, width=int(5*sc))
    n = max(1, int(length/(55*sc)))
    for i in range(1, n + 1):
        p = i/n; xx = x0 + sway*p; yy = y0 + length*p
        d.line([(xx - 26*sc, yy), (xx + 26*sc, yy)], fill=o, width=int(9*sc)); d.line([(xx - 24*sc, yy), (xx + 24*sc, yy)], fill=col, width=int(4*sc))

def wind_lines(im, t, n=24, seed=5, alpha=110, dirx=-1):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(n):
        y = r.uniform(80, 1500); sp = r.uniform(900, 1700); L = r.uniform(120, 340)
        x = (r.uniform(0, W + 600) + dirx*sp*t) % (W + 600) - 300
        d.line([(x, y), (x - dirx*L, y)], fill=(255, 255, 255, alpha), width=3)
    im.alpha_composite(lay)

def blue_eyes(im, cx, cy, a, sc=1.0):
    """two blue-flame glints behind the engine grille (Kuro tease)."""
    if a <= 0: return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for ex in (cx - 70*sc, cx + 70*sc):
        d.ellipse([ex - 50*sc, cy - 34*sc, ex + 50*sc, cy + 34*sc], fill=(60, 140, 255, int(200*a)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(20*sc)))
    d = ImageDraw.Draw(im)
    for s, ex in ((-1, cx - 70*sc), (1, cx + 70*sc)):
        pts = [(ex - 34*sc*s*-1 if False else ex - 34*sc, cy + 6*sc), (ex - 10*sc*s, cy - 16*sc), (ex + 34*sc, cy - 6*sc*s if False else cy - 2*sc), (ex + 6*sc*s, cy + 12*sc)]
        d.polygon(pts, fill=(int(150 + 90*a), int(200 + 50*a), 255))

def ren_leaper(im, x, y, sc, t, ang=0):
    """small full-figure Ren silhouette (from behind) reaching up, for the leap shot."""
    lay = Image.new("RGBA", (int(400*sc), int(520*sc)), (0, 0, 0, 0))
    ren_back_silhouette(lay, 200*sc, 470*sc, sc*1.4, t*8)
    d = ImageDraw.Draw(lay)
    # raised arm
    d.line([(200*sc + 40*sc, 470*sc - 190*sc), (200*sc + 70*sc, 470*sc - 330*sc)], fill=(20, 28, 56), width=int(24*sc))
    d.ellipse([200*sc + 52*sc, 470*sc - 360*sc, 200*sc + 92*sc, 470*sc - 320*sc], fill=SKIN, outline=(10, 10, 18), width=3)
    lay = lay.rotate(ang, Image.BICUBIC, expand=True)
    im.alpha_composite(lay, (int(x - lay.width/2), int(y - lay.height/2)))

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(CLOUDSKY, 1.0 + 0.05*lt, 650, 1100).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 8, 20, 255)), 0.45)
    im.alpha_composite(light_rays(t, (255, 200, 140), 540, -120, 50))
    a = ease(lt/0.8)
    kestrel(im, 540 + 200*(1 - a), 470, 0.95, t, 1.0)
    embers(im, t, 0.5)
    if lt > 0.5: glow_text(im, "SKYFORGE SAGA", 800, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.9:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.9)/0.4)*300
        d.rectangle([540 - w, 950, 540 + w, 956], fill=(90, 220, 210))
        text_center(d, "—  Ep %d  —" % EP, 980, 60, (255, 190, 110))
    if lt > 1.3: glow_text(im, TITLE, 1070, 96, (255, 255, 255), (60, 200, 190))
    return flash(im, max(0, 1 - lt/0.35))

def shot_arrive(t, lt):
    k = ease(lt/6)
    im = cam(EDGE, 1.1 + 0.06*k, 700 - 20*lt, 1100).convert("RGBA")
    # searchlight beam onto the island edge
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    ax, ay = 640, 760 - 220*k
    d.polygon([(ax + 160, ay + 110), (180, 1500), (560, 1500)], fill=(255, 230, 160, 55))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(22)))
    kestrel(im, ax, ay, 0.95 + 0.1*k, t, 1.0)
    # small Ren silhouette on the edge looking up, fog behind
    im.alpha_composite(violet_fog(t, 1250, 1600, 80, 11))
    ren_back_silhouette(im, 360, 1500, 0.9, t*6)
    wind_lines(im, t, 10, 3, 70)
    embers(im, t, 0.5)
    return shake(im, 2, t, 4)

def shot_lyra_intro(t, lt):
    k = ease(lt/6.8)
    im = cam(HULL, 1.05 + 0.04*k, 560 + 20*lt, 1050).convert("RGBA")
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("smirk" if lt > 0.8 else "calm", m, blink(t, 0.9)), 1.05 + 0.05*k, 500, 720)
    wind_lines(im, t, 22, 7, 110)
    # goggle glint
    if 0.4 < lt < 0.9:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g); p = (lt - 0.4)/0.5
        cx, cy = 390, 440; r = 90*math.sin(math.pi*p)
        gd.polygon([(cx - r, cy), (cx, cy - 8), (cx + r, cy), (cx, cy + 8)], fill=(255, 255, 255, 240))
        gd.polygon([(cx, cy - r), (cx + 8, cy), (cx, cy + r), (cx - 8, cy)], fill=(255, 255, 255, 240))
        im.alpha_composite(g)
    embers(im, t, 0.3)
    return im

def shot_ren_broke(t, lt):
    im = cam(EDGE, 1.25, 640 + 10*lt, 1000).convert("RGBA")
    im.alpha_composite(violet_fog(t, 900, 1500, 80, 13))
    m = speaking("REN", t)
    expr = "calm" if lt < 3.0 else "shocked"
    paste_bust(im, ren_bust(expr, m, blink(t, 0.4) and expr == "calm", int(t*6) % 8, False), 1.1, 560, 790)
    # he holds the glowing blade up, a little sheepishly
    hold = ease((lt - 2.6)/0.6)
    rot_paste(im, blade(1.0, 0.6 + 0.4*hold, 0.85), 30 - 20*hold, 220, 980 - 140*hold)
    ang = math.radians(30 - 20*hold)
    fist(im, 220 - 280*math.sin(ang)*-1 if False else 220 + 280*math.sin(ang), 980 - 140*hold + 280*math.cos(ang), 0.8)
    if hold > 0: sparks(im, t, 220 - 200*math.sin(ang), 980 - 140*hold - 300*math.cos(ang), 6, 0.3, 4, (170, 245, 255))
    wind_lines(im, t, 12, 9, 70)
    embers(im, t, 0.4, True)
    return im

def shot_lyra_deal(t, lt):
    k = ease(lt/6)
    im = cam(HULL, 1.25 + 0.08*k, 520, 900).convert("RGBA")
    m = speaking("LYRA", t)
    expr = "smirk" if lt < 3.6 else "calm"
    paste_bust(im, lyra_bust(expr, m, blink(t, 2.3)), 1.22 + 0.08*k, 560, 720)
    # rope ladder unrolls past her on the right when she yells
    if lt > 3.4:
        p = ease((lt - 3.4)/0.9)
        ladder(im, 860, 200, 1400*p, 40*math.sin(t*3)*p, 1.2)
    wind_lines(im, t, 26, 8, 120)
    embers(im, t, 0.3)
    return shake(im, 3 if 3.4 < lt < 4.2 else 0, t, 2)

def shot_leap(t, lt):
    k = ease(lt/6)
    im = cam(EDGE, 1.15, 640, 1150 + 60*k).convert("RGBA")
    # Kestrel pulling away up-right, ladder trailing
    sx, sy = 640 + 160*k, 420 - 120*k
    kestrel(im, sx, sy, 0.9, t, 1.0)
    lx, ly = sx - 40, sy + 150
    sway = -120 - 60*k + 30*math.sin(t*3)
    ladder(im, lx, ly, 520, sway, 1.0)
    # soldiers arriving at the cliff edge (left), too late
    for i in range(5):
        p = min(1, max(0, (lt - 0.3 - i*0.2)/2.2))
        soldier(im, -120 + 260*p + i*110, 1530 + (i % 2)*30, 0.42, t, 1.0, min(1, p*3), i + 20)
    im.alpha_composite(violet_fog(t, 1350, 1700, 90, 21))
    # Ren: run + jump (0-1.6), then clinging to the ladder bottom
    if lt < 1.0:
        ren_leaper(im, 520 + 120*lt, 1480 - 40*lt, 0.9, t, 0)
    elif lt < 1.7:
        p = (lt - 1.0)/0.7
        x = 640 + (lx + sway - 640)*p; y = 1440 + (ly + 520 + 100 - 1440)*p - 260*math.sin(math.pi*p)
        ren_leaper(im, x, y, 0.9, t, -15*p)
        im.alpha_composite(SPEED[int(t*15) % 4])
    else:
        ren_leaper(im, lx + sway + 10, ly + 520 + 100, 0.7, t, -10 + 6*math.sin(t*3))
    wind_lines(im, t, 18, 12, 100)
    embers(im, t, 0.7, True, 1.5)
    return shake(im, 10*max(0, 1 - abs(lt - 1.7)/0.4), t, 6)

def shot_mire(t, lt):
    im = cam(EDGE, 1.2, 520, 1050).convert("RGBA")
    # the Kestrel, small and far away
    kestrel(im, 820 - 30*lt, 330 - 10*lt, 0.32, t, 1.0)
    for i in range(4):
        soldier(im, 120 + i*280, 1500, 0.5, t, 1.0, 0.9, i + 30)
    im.alpha_composite(violet_fog(t, 1100, 1600, 100, 31))
    m = speaking("CAPTAIN MIRE", t)
    paste_bust(im, mire_bust(m, blink(t, 1.2)), 1.0 + 0.05*ease(lt/6), 480, 800)
    wind_lines(im, t, 14, 15, 80)
    embers(im, t, 0.3)
    return im

def shot_cockpit(t, lt):
    im = cam(COCKPIT, 1.05, 650, 1000).convert("RGBA")
    # rushing cloud streaks in the window
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(4)
    for i in range(12):
        x = (r.uniform(0, W + 600) - 900*t) % (W + 600) - 300; y = r.uniform(400, 1000)
        d.ellipse([x - 160, y - 30, x + 160, y + 30], fill=(255, 220, 190, 120))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("smirk", m, blink(t, 1.5)), 1.05, 540, 760)
    # ship's wheel in front of her
    d = ImageDraw.Draw(im); o = (14, 12, 22); cx, cy, R = 540, 1450, 230
    a0 = 0.25*math.sin(t*1.4)
    for k in range(8):
        a = a0 + k*math.pi/4
        d.line([(cx, cy), (cx + (R + 50)*math.cos(a), cy + (R + 50)*math.sin(a))], fill=o, width=26)
        d.line([(cx, cy), (cx + (R + 50)*math.cos(a), cy + (R + 50)*math.sin(a))], fill=(140, 92, 56), width=16)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=o, width=34); d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=(150, 100, 60), width=22)
    d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50], fill=BRASS, outline=o, width=5)
    embers(im, t, 0.2)
    return shake(im, 2, t, 8)

def shot_engine(t, lt):
    k = ease(lt/6)
    im = cam(ENGINE, 1.08 + 0.1*k, 480, 1050).convert("RGBA")
    # engine heat glow pulsing
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([380, 600, 1060, 1300], fill=(255, 140, 60, int(40 + 20*math.sin(t*6))))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    # glints in the grille appear after his line starts
    ga = ease((lt - 3.2)/0.8)
    blue_eyes(im, 700, 1000, ga, 1.0 + 0.1*k)
    m = speaking("REN", t)
    paste_bust(im, ren_bust("calm" if lt < 1.4 else "shocked", m, blink(t, 0.2) and lt < 1.4, int(t*6) % 8, True), 0.62, 250 + 20*k, 560)
    sparks(im, t, 760, 300, 8, 0.4, 17)
    return shake(im, 2 + 4*ga*abs(math.sin(t*20)), t, 12)

def shot_next(t, lt):
    im = shot_engine(t, 6.0)
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.72, lt/0.3*0.72))
    blue_eyes(im, 540, 470, 0.7 + 0.3*math.sin(t*3), 0.8)
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 700 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 820, 96, (255, 255, 255), (60, 140, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 990, 540 + 300*a, 996], fill=(120, 180, 255))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 1040, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1140, 50, (255, 220, 150), sw=6)
    return im

SHOT_FN = {"title": shot_title, "arrive": shot_arrive, "lyra_intro": shot_lyra_intro, "ren_broke": shot_ren_broke,
           "lyra_deal": shot_lyra_deal, "leap": shot_leap, "mire": shot_mire, "cockpit": shot_cockpit,
           "engine": shot_engine, "next": shot_next}

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

# ------------------------------------------------------------ audio (new flight score: E minor -> G major lift, 120 bpm)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(44)
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
    bpm = 120; beat = 60/bpm; bar = beat*4
    chords = [[52, 55, 59], [48, 52, 55], [43, 47, 50], [50, 54, 57]]  # Em C G D
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.7
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.5), (10, 0.6), (23, 0.7), (29.2, 1.0), (35.2, 0.75), (41.2, 0.8), (47, 0.45), (53, 1.0), (57.5, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.25, 0.5)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.03*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.4), t0, vol=0.06*inten(t0))
        t0 += bar; ci += 1
    # plucky arpeggio (adventure feel) except in the eerie engine shot
    t0, k = 0.0, 0
    while t0 < TOTAL:
        if not (47.0 <= t0 < 53.0):
            ch = chords[int(t0 // bar) % 4]; m = (ch + [ch[0] + 12])[[0, 1, 2, 3, 2, 1][k % 6]] + 12
            n = int(0.2*SR); add(saw(note(m), 0.2, 4)*np.exp(-16*tv(n)), t0, pan=0.4*(1 if k % 2 else -1), vol=0.03*speech_duck(t0))
        t0 += beat/2; k += 1
    # soaring lead motif when the Kestrel takes off (own melody)
    motif = [(64, 1), (67, 0.5), (71, 0.5), (76, 1.5), (74, 0.5), (71, 1), (72, 1), (74, 2)]
    tt = 29.3
    for m, b in motif:
        dur = b*beat; n = int(dur*SR)
        s = saw(note(m), dur, 8)*env(n, 0.04, 0.12)*(1 + 0.15*np.sin(2*np.pi*5*tv(n)))
        add(s, tt, pan=0.1, vol=0.04); tt += dur
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
        if 23.0 <= tb < 41.2:
            if b % 4 in (0, 2) or b % 8 == 7: add(KICK, tb, vol=0.45)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.16)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.08)
        elif 4.0 <= tb < 23.0 and b % 2 == 0:
            add(TAIKO, tb, vol=0.28)
        elif 41.2 <= tb < 47.0 and b % 4 == 0:
            add(KICK, tb, vol=0.3)
        b += 1
    # cut whooshes
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    # title hit
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # Kestrel engine hum (propeller flutter) under the airship shots
    for s, e, v in ((0.0, 17.0, 0.07), (23.0, 35.2, 0.08), (41.2, 53.0, 0.06)):
        dur = e - s; n = int(dur*SR); x = tv(n)
        eng = (saw(55, dur, 6)*(0.6 + 0.4*np.sign(np.sin(2*np.pi*16*x))) + 0.4*lp_noise(dur, 0.05, 0.05))*env(n, 0.8, 0.8)
        add(eng, s, pan=0.2, vol=v)
    # wind bed
    n = int(TOTAL*SR); add(lp_noise(TOTAL, 0.02, 0.02)*1.2, 0, vol=0.05)
    # ladder drop: rattle
    for i in range(8):
        nn = int(0.08*SR); add(rs.randn(nn)*np.exp(-50*tv(nn)), 26.4 + i*0.1, pan=0.5, vol=0.12)
    # leap: rising whoosh + catch thud
    add(whoosh(1.2, True)*1.5, 29.6, vol=0.4)
    n = int(1.2*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(60 + 80*np.exp(-20*x))/SR)*np.exp(-5*x), 30.9, vol=0.6)
    # Mire's spear slam
    n = int(1.5*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(50 + 80*np.exp(-20*x))/SR)*np.exp(-4*x), 35.25, vol=0.4)
    # engine shot: low growl (not engine-like) + heartbeat
    dur = 6.0; n = int(dur*SR); x = tv(n)
    growl = (saw(70, dur, 8)*(0.5 + 0.5*np.sin(2*np.pi*11*x)) + lp_noise(dur, 0.04, 0.04))*np.clip((x - 3.0)/1.0, 0, 1)*env(n, 0.0, 1.0)
    add(growl, 47.0, vol=0.12)
    for i in range(6):
        nn = int(0.3*SR); xx = tv(nn); add(np.sin(2*np.pi*50*xx)*np.exp(-12*xx), 47.2 + i*0.9, vol=0.35)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 53.0, vol=0.6)
    for i, m in enumerate([64, 71, 76, 79, 83]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 53.05, pan=-0.6 + 0.3*i, vol=0.05)
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
