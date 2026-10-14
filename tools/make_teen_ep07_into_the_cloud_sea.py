"""SKYFORGE SAGA Ep 7: Into the Cloud Sea  (no-voice build: music + sfx + timed captions).
The Kestrel, its lift-sails torn by Mire's hooks, falls through the Cloud Sea and finds a hidden
dark sky below, lit by thousands of drifting shards. Reuses Ep 1-6 helpers; new falling / plunge /
under-cloud backgrounds and a new descending, mysterious score."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, embers, SPEED, cam, shake, flash,
                                            VIG, text_center, glow_text, paste_bust, ease, blink, light_rays)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks
from make_teen_ep03_hollow_soldiers import violet_fog, CLOUDSKY
from make_teen_ep04_lyras_airship import COCKPIT, wind_lines
from make_teen_ep05_the_fox_in_the_engine import paste_kuro, blue_embers, blue_fire_glow

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/07_into_the_cloud_sea.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 7, "Into the Cloud Sea", "The Drowned Island"

SHOTS = [("title", 0.0, 4.0), ("fall", 4.0, 10.0), ("lyra", 10.0, 15.2), ("ren", 15.2, 19.6), ("lyra2", 19.6, 24.4),
         ("kuro", 24.4, 29.4), ("plunge", 29.4, 35.0), ("below", 35.0, 41.0), ("ren_wonder", 41.0, 46.4),
         ("lyra_hook", 46.4, 51.6), ("next", 51.6, 56.0)]
TOTAL = 56.0
SPLASH_T = 33.0   # moment the Kestrel punches through the cloud sea
LINES = [
    ("NARRATOR", "No one who falls into the Cloud Sea comes back up. At least... that's what the stories say.", 4.3, 9.7),
    ("LYRA", "Mire's hooks shredded the lift-sails! We're going down!", 10.4, 14.8),
    ("REN", "Then pull UP! You're the pilot!", 15.5, 19.2),
    ("LYRA", "I AM pulling up. The sky just isn't listening!", 19.9, 24.0),
    ("KURO", "Stop fighting the fall. The clouds will catch us.", 24.8, 29.0),
    ("REN", "Kuro, if you're wrong about this...", 29.7, 32.6),
    ("NARRATOR", "Beneath the clouds, the sky was dark and silent... and full of light.", 35.4, 40.6),
    ("REN", "Those aren't stars. They're shards. Thousands of them.", 41.4, 46.0),
    ("LYRA", "And that island down there... it isn't on any map.", 46.8, 51.2),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255)}
draw_caption, speaking = e1.draw_caption, e1.speaking
O = (14, 12, 22)

# ------------------------------------------------------------ backgrounds
def make_storm_sky():
    """above the cloud sea at dusk, camera looking down-ish: cloud tops fill the lower 2/3."""
    w, h = 1300, 2600
    im = Image.fromarray(grad(w, h, [(0, (12, 18, 44)), (0.2, (60, 50, 104)), (0.32, (220, 120, 92)), (0.4, (250, 176, 112)),
                                     (0.55, (190, 130, 120)), (1, (70, 62, 100))])).convert("RGBA")
    stars(im, 60, 400, 701)
    island(im, 220, 560, 220, 200, 702, houses=1); island(im, 1080, 640, 180, 170, 703)
    clouds(im, 900, 2600, 704, tint=(255, 190, 150)); clouds(im, 1400, 2600, 705, tint=(255, 170, 140))
    return im.convert("RGB")
STORM = make_storm_sky()

def make_below():
    """under the cloud sea: cloud ceiling at the top, deep teal void, shard 'stars', ruined island far below."""
    w, h = 1300, 2400
    im = Image.fromarray(grad(w, h, [(0, (150, 170, 190)), (0.1, (60, 90, 120)), (0.3, (14, 46, 66)), (0.65, (6, 26, 40)),
                                     (1, (2, 10, 20))])).convert("RGBA")
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(711)
    # underside of the cloud sea (bumpy ceiling)
    for i in range(60):
        x = r.uniform(-100, w + 100); y = r.uniform(-60, 260); rx = r.uniform(120, 260); ry = r.uniform(50, 110)
        c = r.randint(150, 200)
        d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(c - 30, c - 10, c + 10, 235))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    # god-ray shafts through holes in the ceiling
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x0 in (260, 640, 980):
        d.polygon([(x0 - 40, 200), (x0 + 40, 200), (x0 + 220, 2000), (x0 - 140, 2000)], fill=(150, 230, 255, 26))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
    # the drowned island, far below: dark mass with broken towers
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx, ty = 650, 1840
    d.polygon([(cx - 520, ty), (cx + 520, ty), (cx + 360, ty + 160), (cx + 120, ty + 420), (cx - 160, ty + 380), (cx - 400, ty + 180)],
              fill=(10, 30, 42, 255))
    for bx, bh, bw in ((-300, 260, 50), (-170, 420, 70), (-40, 330, 60), (90, 520, 80), (230, 300, 56), (350, 380, 60)):
        x = cx + bx
        d.polygon([(x - bw/2, ty + 4), (x - bw/2, ty - bh), (x - bw/4, ty - bh - 30), (x + bw/4, ty - bh + 10), (x + bw/2, ty - bh + 40),
                   (x + bw/2, ty + 4)], fill=(12, 36, 50, 255))
        for k in range(3):
            wy = ty - bh + 60 + k*70
            if wy < ty - 20: d.rectangle([x - 8, wy, x + 8, wy + 22], fill=(70, 200, 220, 160))
    im.alpha_composite(lay)
    # mist band over the ruins
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for i in range(20):
        x = r.uniform(0, w); y = r.uniform(1780, 2050)
        d.ellipse([x - 240, y - 40, x + 240, y + 40], fill=(90, 160, 180, 50))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(20)))
    return im.convert("RGB")
BELOW = make_below()

SHARDS = [(random.Random(800 + i).uniform(0, W), random.Random(900 + i).uniform(80, 1450), random.Random(1000 + i).uniform(2, 9),
           random.Random(1100 + i).uniform(0, 6.28)) for i in range(140)]
def shard_lights(im, t, amt=1.0, drift=0.0):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for x, y, s, ph in SHARDS[:int(len(SHARDS)*amt)]:
        yy = (y - 18*t*s/5 + drift) % 1500 + 60
        tw = 0.55 + 0.45*math.sin(t*2.2 + ph)
        r = s*(0.8 + 0.4*tw)
        d.polygon([(x, yy - r*1.8), (x + r, yy), (x, yy + r*1.8), (x - r, yy)], fill=(170, 250, 255, int(230*tw)))
    glow = lay.filter(ImageFilter.GaussianBlur(7))
    im.alpha_composite(glow); im.alpha_composite(glow); im.alpha_composite(lay)

def smoke_trail(im, x, y, t, n=10, dx=1.0, dy=-1.0, seed=3):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(n):
        p = ((i/n) + t*0.9) % 1.0
        rr = 30 + 120*p
        px = x + dx*420*p + r.uniform(-30, 30); py = y + dy*420*p + r.uniform(-30, 30)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(70, 66, 80, int(150*(1 - p))))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12)))

SHIP = {}
def ship_sprite(sc, t, lit=1.0):
    key = (round(sc, 2), int(t*20) % 8, lit)
    if key not in SHIP:
        if len(SHIP) > 64: SHIP.clear()
        sh = airship(lit, int(t*20) % 8)
        SHIP[key] = sh.resize((max(1, int(900*sc)), max(1, int(520*sc))), Image.BILINEAR)
    return SHIP[key]

def torn_sails(im, x, y, sc, t, ang):
    """ragged sail strips flapping above the ship (the damage from Mire's hooks)."""
    d = ImageDraw.Draw(im)
    for k, off in enumerate((-120, -10, 100)):
        bx, by = x + off*sc, y - 180*sc
        f = math.sin(t*16 + k*1.7)
        pts = [(bx - 20*sc, by), (bx + 20*sc, by), (bx + (30 + 30*f)*sc, by - 130*sc), (bx + (10 + 50*f)*sc, by - 170*sc),
               (bx + (-10 + 20*f)*sc, by - 110*sc)]
        c, s_ = math.cos(math.radians(-ang)), math.sin(math.radians(-ang))
        rp = [(x + (px - x)*c - (py - y)*s_, y + (px - x)*s_ + (py - y)*c) for px, py in pts]
        d.polygon(rp, fill=(226, 214, 190), outline=O)

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(BELOW, 1.1 + 0.05*lt, 650, 1300).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 8, 16, 255)), 0.45)
    shard_lights(im, t, 0.6)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 700, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 850, 540 + w, 856], fill=(255, 150, 90))
        text_center(d, "—  Ep %d  —" % EP, 880, 60, (255, 190, 110))
    if lt > 1.2: glow_text(im, TITLE, 970, 92, (255, 255, 255), (255, 110, 60))
    return flash(im, max(0, 1 - lt/0.35))

def shot_fall(t, lt):
    k = ease(lt/6.0)
    # camera chases the ship down: pan from sky to the cloud tops
    im = cam(STORM, 1.0 + 0.15*k, 650, 900 + 900*k).convert("RGBA")
    x, y = 560 + 40*math.sin(lt*1.3), 760 + 60*math.sin(lt*0.9)
    ang = -18 + 8*math.sin(lt*2.0)
    smoke_trail(im, x + 150, y - 40, t, 12, 0.6, -1.0)
    sh = ship_sprite(0.78, t)
    rot_paste(im, sh, ang, x, y)
    torn_sails(im, x, y, 0.78, t, ang)
    sparks(im, t, x + 160, y - 60, 8, 0.4, 3, (255, 210, 140))
    # upward speed streaks (we're falling)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(32)
    for i in range(26):
        sx = r.uniform(0, W); sp = r.uniform(900, 1600); L = r.uniform(140, 360)
        sy = (r.uniform(0, H + 600) - sp*t) % (H + 600) - 300
        d.line([(sx, sy), (sx, sy + L)], fill=(255, 255, 255, 120), width=3)
    im.alpha_composite(lay)
    embers(im, t, 0.3)
    return shake(im, 4, t, 3)

def shot_lyra(t, lt):
    im = cam(COCKPIT, 1.08, 650 + 30*math.sin(t*3), 1000).convert("RGBA")
    im = rot_paste_bg(im, 6*math.sin(t*2.2))
    a = 0.5 + 0.5*math.sin(t*9)
    im.alpha_composite(Image.new("RGBA", (W, H), (255, 30, 40, int(55*a))))
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("shocked", m, blink(t, 0.9), lt > 1.0), 1.02, 540, 760)
    sparks(im, t, 900, 420, 8, 0.4, 5, (255, 200, 120))
    return shake(im, 6 + (12*(1 - lt/0.4) if lt < 0.4 else 0), t, 4)

def rot_paste_bg(im, ang):
    """tilt the whole background (ship lurching) without black corners: rotate an over-scaled copy."""
    big = im.resize((int(W*1.15), int(H*1.15)), Image.BILINEAR).rotate(ang, Image.BILINEAR)
    return big.crop(((big.width - W)//2, (big.height - H)//2, (big.width - W)//2 + W, (big.height - H)//2 + H))

def deck_bg(t, k, tilt):
    im = cam(STORM, 1.25 + 0.06*k, 650, 1500 + 120*k).convert("RGBA")
    im = rot_paste_bg(im, tilt)
    # railing of the Kestrel's deck in the foreground
    d = ImageDraw.Draw(im)
    for x in range(-40, W + 80, 150):
        d.rectangle([x, 1380, x + 22, 1700], fill=(104, 72, 50), outline=O, width=4)
    d.rectangle([-20, 1360, W + 20, 1400], fill=(128, 90, 60), outline=O, width=5)
    return im

def shot_ren(t, lt):
    k = ease(lt/4.4)
    im = deck_bg(t, k, 8*math.sin(t*1.8))
    wind_lines(im, t, 18, 8, 100, dirx=1)
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked", m, False, int(t*8) % 8, True), 1.12, 540, 760)
    embers(im, t, 0.3)
    if lt < 0.6:
        d = ImageDraw.Draw(im)
        for i in range(10):
            a = i*math.pi/5; d.line([(540 + 330*math.cos(a), 600 + 330*math.sin(a)), (540 + 420*math.cos(a), 600 + 420*math.sin(a))], fill=(255, 255, 255), width=8)
    return shake(im, 6, t, 5)

def shot_lyra2(t, lt):
    k = ease(lt/4.8)
    im = cam(COCKPIT, 1.15 + 0.08*k, 650, 1000).convert("RGBA")
    im = rot_paste_bg(im, -7*math.sin(t*2.0))
    a = 0.5 + 0.5*math.sin(t*9)
    im.alpha_composite(Image.new("RGBA", (W, H), (255, 30, 40, int(40*a))))
    im.alpha_composite(SPEED[int(t*15) % 4])
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("smirk" if lt > 2.6 else "calm", m, blink(t, 2.1), False), 1.08 + 0.05*k, 540, 770)
    return shake(im, 5, t, 6)

def shot_kuro(t, lt):
    k = ease(lt/5.0)
    im = deck_bg(t, k, 4*math.sin(t*1.5))
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.35)
    blue_fire_glow(im, 540, 700, 380, 0.7)
    m = speaking("KURO", t)
    paste_kuro(im, kuro(m, blink(t, 1.2), int(t*10) % 8, "calm"), 1.25 + 0.06*k, 540, 640 + 8*math.sin(t*3))
    blue_embers(im, t, 540, 900, 22, 15, 480)
    wind_lines(im, t, 10, 9, 70, dirx=1)
    return shake(im, 2, t, 9)

def shot_plunge(t, lt):
    # wide: the Kestrel dives nose-first into the cloud sea; whiteout at SPLASH_T; lightning inside
    p = lt/(SPLASH_T - 29.4)
    im = cam(STORM, 1.0 + 0.25*ease(min(1, p)), 650, 1700).convert("RGBA")
    if t < SPLASH_T:
        x, y = 540 + 30*math.sin(lt), 520 + 760*ease(p)
        sc = 0.55 + 0.25*p
        smoke_trail(im, x + 60, y - 160, t, 10, 0.2, -1.0, 7)
        rot_paste(im, ship_sprite(sc, t), -48, x, y)
        # cloud surface in front that the ship sinks into
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(41)
        for i in range(18):
            cx = r.uniform(-100, W + 100); cy = 1240 + r.uniform(0, 400)
            d.ellipse([cx - 260, cy - 90, cx + 260, cy + 90], fill=(255, 205, 170, 245))
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(8)))
        if p > 0.7:
            wh = Image.new("RGBA", (W, H), (255, 235, 220, int(255*min(1, (p - 0.7)/0.3)**2)))
            im.alpha_composite(wh)
        return shake(im, 3 + 8*p, t, 10)
    # inside the cloud: grey-white churn, lightning flicker, falling streaks
    q = t - SPLASH_T
    im = Image.new("RGBA", (W, H), (200, 196, 206, 255))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(52)
    for i in range(30):
        cx = r.uniform(-100, W + 100); cy = (r.uniform(0, H + 600) - 1600*q) % (H + 600) - 300
        g = r.randint(120, 230)
        d.ellipse([cx - 280, cy - 120, cx + 280, cy + 120], fill=(g, g, g + 12, 200))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18)))
    if 0.5 < q < 0.62 or 1.1 < q < 1.18:
        im = flash(im, 0.6, (200, 230, 255))
        d = ImageDraw.Draw(im); x = 300; y = 0; rr = random.Random(int(q*10))
        while y < 1100:
            nx, ny = x + rr.uniform(-70, 70), y + rr.uniform(60, 120)
            d.line([(x, y), (nx, ny)], fill=(255, 255, 255), width=6); x, y = nx, ny
    im.alpha_composite(SPEED[int(t*15) % 4])
    # fade to dark at end -> cut below
    im = Image.blend(im, Image.new("RGBA", (W, H), (6, 20, 32, 255)), min(1, max(0, (q - 1.4)/0.6)))
    return shake(im, 12*max(0, 1 - q/1.0) + 3, t, 11)

def shot_below(t, lt):
    k = ease(lt/6.0)
    im = cam(BELOW, 1.0 + 0.1*k, 650, 800 + 500*k).convert("RGBA")
    shard_lights(im, t, 1.0)
    # the Kestrel gliding level, small, sails in tatters, lanterns lit
    x, y = 300 + 420*k, 560 + 140*k + 14*math.sin(lt*1.4)
    smoke_trail(im, x - 180, y - 30, t*0.4, 8, -1.0, -0.3, 12)
    rot_paste(im, ship_sprite(0.42, t), 6 + 3*math.sin(lt), x, y)
    im.alpha_composite(light_rays(t, (120, 230, 255), 540, -300, 34))
    # a single distant violet glint in the ruins (mystery)
    if lt > 3.6:
        a = min(1, (lt - 3.6)/0.6)*(0.6 + 0.4*math.sin(t*5))
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gx, gy = 700, 1330 - 20*k
        gd.ellipse([gx - 40, gy - 40, gx + 40, gy + 40], fill=(190, 110, 255, int(200*a)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(14)))
    if lt < 0.8: im = flash(im, 0.5*(1 - lt/0.8), (180, 240, 255))
    return im

def shot_ren_wonder(t, lt):
    k = ease(lt/5.4)
    im = cam(BELOW, 1.3 + 0.08*k, 650, 1000 - 120*k).convert("RGBA")
    shard_lights(im, t, 0.8, 300)
    blue_fire_glow(im, 540, 640, 460, 0.45 + 0.15*math.sin(t*2))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("calm" if lt < 3.0 else "determined", m, blink(t, 0.3), int(t*3) % 8, True), 1.08 + 0.06*k, 540, 770)
    # the shard-blade hilt glows brighter, reacting to the shards
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    hx, hy = 540 + (654 - 450)*(1.08 + 0.06*k), 770 + (540 - 480)*(1.08 + 0.06*k)
    rr = 30 + 14*k + 6*math.sin(t*7)
    gd.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], fill=(90, 240, 255, 150))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    embers(im, t, 0.35, True, 0.5)
    return im

def shot_lyra_hook(t, lt):
    k = ease(lt/5.2)
    # Lyra in the foreground, pointing look; ruined island pulls into view behind her
    im = cam(BELOW, 1.15 + 0.2*k, 650, 1500 + 250*k).convert("RGBA")
    shard_lights(im, t, 0.6, 600)
    if lt > 2.4:   # lights blink on, one by one, in the drowned towers
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for i, (gx, gy) in enumerate(((240, 1250), (420, 1180), (640, 1220), (860, 1150))):
            if lt > 2.4 + i*0.35:
                gd.ellipse([gx - 26, gy - 26, gx + 26, gy + 26], fill=(110, 240, 255, 230))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10))); im.alpha_composite(g.filter(ImageFilter.GaussianBlur(3)))
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("calm" if lt < 2.2 else "shocked", m, blink(t, 1.6), False), 0.78, 330, 560)
    return shake(im, 1 + (6 if 2.4 < lt < 2.7 else 0), t, 15)

def shot_next(t, lt):
    im = shot_lyra_hook(t, 5.2)
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

SHOT_FN = {"title": shot_title, "fall": shot_fall, "lyra": shot_lyra, "ren": shot_ren, "lyra2": shot_lyra2, "kuro": shot_kuro,
           "plunge": shot_plunge, "below": shot_below, "ren_wonder": shot_ren_wonder, "lyra_hook": shot_lyra_hook, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    if t - s < 0.08 and name not in ("title", "next", "below"):
        im = flash(im, 0.45)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio (D minor, 120 bpm falling score -> ambient awe below)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(77)
    def tv(n): return np.arange(n)/SR
    def add(sig, at, pan=0.0, vol=1.0):
        i = int(at*SR); j = min(N, i + len(sig))
        if j <= i or i < 0: return
        L[i:j] += sig[:j-i]*vol*(1 - pan)*0.5; R[i:j] += sig[:j-i]*vol*(1 + pan)*0.5
    def saw(f, dur, nh=7, det=0.0):
        t = tv(int(dur*SR)); s = np.zeros_like(t)
        for h in range(1, nh+1): s += np.sin(2*np.pi*f*h*t*(1 + det))/h
        return s
    def sine(f, dur): return np.sin(2*np.pi*f*tv(int(dur*SR)))
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
    def duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.6
        return 1.0
    bpm = 120; beat = 60/bpm; bar = beat*4
    # --- part A (0 - SPLASH_T): urgent falling strings, Dm Bb F C with descending bass
    chordsA = [[50, 53, 57], [46, 50, 53], [45, 48, 53], [48, 52, 55]]
    t0, ci = 0.0, 0
    while t0 < SPLASH_T:
        ch = chordsA[ci % 4]; dur = min(bar + 0.3, SPLASH_T + 0.5 - t0)
        for k, m in enumerate(ch):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.2, 0.4)
            add(s, t0, pan=-0.4 + 0.4*k, vol=0.022*duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.3), t0, vol=0.05)
        t0 += bar; ci += 1
    # descending 8th-note ostinato (the fall)
    t0, k = 4.0, 0
    while t0 < SPLASH_T - 0.2:
        ch = chordsA[int(t0 // bar) % 4]; seq = [ch[2] + 12, ch[1] + 12, ch[0] + 12, ch[2]]
        m = seq[k % 4]; dur = beat/2; n = int(dur*SR)
        add(saw(note(m), dur, 6)*env(n, 0.005, 0.08), t0, pan=0.35*(1 if k % 2 else -1), vol=0.024*duck(t0))
        t0 += beat/2; k += 1
    def kick():
        n = int(0.4*SR); x = tv(n); f = 48 + 110*np.exp(-30*x)
        return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-8*x)
    def taiko():
        n = int(0.8*SR); x = tv(n); f = 62 + 46*np.exp(-12*x)
        return (np.sin(2*np.pi*np.cumsum(f)/SR) + 0.2*np.random.RandomState(4).randn(n)*np.exp(-30*x))*np.exp(-5*x)
    def snare():
        n = int(0.22*SR); x = tv(n)
        return (np.random.RandomState(3).randn(n)*0.6 + 0.4*np.sin(2*np.pi*190*x))*np.exp(-17*x)
    KICK, TAIKO, SNARE = kick(), taiko(), snare()
    b = 0
    while b*beat < SPLASH_T - 0.3:
        tb = b*beat
        if tb >= 4.0:
            if b % 2 == 0: add(TAIKO, tb, vol=0.24)
            if b % 4 == 3: add(TAIKO, tb + beat/2, pan=0.3, vol=0.16)
            if tb >= 24.4 and b % 2 == 1: add(SNARE, tb, vol=0.12)
        b += 1
    # snare roll + riser into the plunge
    for i in range(int(3.0/(beat/4))):
        tt = 29.6 + i*beat/4
        if tt < SPLASH_T: add(SNARE[:3000], tt, pan=rs.uniform(-0.3, 0.3), vol=0.05 + 0.12*(tt - 29.6)/3.4)
    dur = 3.4; n = int(dur*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(150 + 700*(x/dur)**2)/SR)*(x/dur)*0.6, SPLASH_T - dur, vol=0.08)
    # --- impact into the clouds
    n = int(2.0*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(50 + 90*np.exp(-10*x))/SR)*np.exp(-2.5*x) + 0.6*rs.randn(n)*np.exp(-6*x), SPLASH_T, vol=0.6)
    add(lp_noise(2.0, 0.3, 0.02)*env(int(2.0*SR), 0.01, 1.2)*2.5, SPLASH_T, vol=0.25)
    # thunder inside the cloud
    for tt in (SPLASH_T + 0.5, SPLASH_T + 1.1):
        n = int(1.6*SR); x = tv(n)
        add((lp_noise(1.6, 0.08, 0.01)*3 + 0.3*np.sin(2*np.pi*40*x))*np.exp(-2.2*x), tt, pan=rs.uniform(-0.5, 0.5), vol=0.25)
    # --- part B (below): slow awe pad, Dm(add9) -> Bbmaj7 -> Gm -> A, celesta-like shimmer
    chordsB = [[50, 57, 62, 64], [46, 53, 57, 62], [43, 50, 55, 58], [45, 52, 57, 61]]
    t0, ci = 35.0, 0
    while t0 < TOTAL:
        ch = chordsB[ci % 4]; dur = 4.2
        for k, m in enumerate(ch):
            s = (saw(note(m), dur, 4, 0.003) + saw(note(m), dur, 4, -0.003))*0.5*env(int(dur*SR), 1.0, 1.2)
            add(s, t0, pan=-0.5 + 0.33*k, vol=0.017*duck(t0 + 1))
        add(sine(note(ch[0] - 12), dur)*env(int(dur*SR), 0.5, 1.0), t0, vol=0.08)
        t0 += 4.0; ci += 1
    r2 = np.random.RandomState(5)
    tt = 35.2
    scale = [74, 76, 77, 79, 81, 84, 86]
    while tt < TOTAL - 2:
        m = scale[r2.randint(len(scale))]; n = int(1.6*SR); x = tv(n)
        s = (np.sin(2*np.pi*note(m)*x) + 0.3*np.sin(2*np.pi*note(m)*3*x))*np.exp(-3*x)
        add(s, tt, pan=r2.uniform(-0.7, 0.7), vol=0.035)
        tt += r2.choice([0.25, 0.5, 0.5, 0.75])
    # soft heartbeat taiko under the hook
    for i in range(6):
        add(TAIKO, 46.4 + i*0.9, vol=0.12 + 0.03*i)
    # shot whooshes
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        if name not in ("below",): add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    # opening low boom
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # constant falling wind until the plunge, gentle wind below
    add(lp_noise(SPLASH_T + 2 - 4, 0.06, 0.12)*1.6*env(int((SPLASH_T + 2 - 4)*SR), 1.0, 1.5), 4.0, vol=0.09)
    add(lp_noise(TOTAL - 35, 0.02, 0.02)*1.2*env(int((TOTAL - 35)*SR), 2.0, 2.0), 35.0, vol=0.05)
    # cockpit alarm
    for i in range(16):
        if 10.0 + i*0.55 > 24.4: break
        n = int(0.18*SR); x = tv(n); add(np.sign(np.sin(2*np.pi*880*x))*env(n, 0.005, 0.03), 10.1 + i*0.55, vol=0.028)
    # flapping sail cloth / creaks
    for i in range(14):
        n = int(0.1*SR); x = tv(n)
        add(rs.randn(n)*np.exp(-40*x), 4.2 + i*0.4, pan=rs.uniform(-0.6, 0.6), vol=0.12)
    for tt in (11.0, 16.2, 21.3, 26.5):
        n = int(0.7*SR); x = tv(n)
        add(saw(rs.uniform(90, 140), 0.7, 5)*np.exp(-4*x)*(1 + 0.3*np.sin(2*np.pi*14*x)), tt, pan=rs.uniform(-0.5, 0.5), vol=0.06)
    # tower lights blinking on
    for i in range(4):
        n = int(0.8*SR); x = tv(n)
        add(np.sin(2*np.pi*note(81 + 3*i)*x)*np.exp(-5*x), 46.4 + 2.4 + i*0.35, pan=-0.6 + 0.4*i, vol=0.06)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 51.6, vol=0.6)
    for i, m in enumerate([62, 69, 74, 77, 81]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 51.65, pan=-0.6 + 0.3*i, vol=0.05)
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
