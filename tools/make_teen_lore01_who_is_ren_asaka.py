"""SKYFORGE SAGA Lore: Who is Ren Asaka?  (no-voice build: music + sfx + timed captions).
Character-profile Short. Reuses the Ep 1-3 effect/caption helpers; new shots, profile UI, callouts and a new score."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, stars, clouds, island, chain, embers, SPEED, cam, shake, flash,
                                            VIG, light_rays, text_center, glow_text, paste_bust, ease, blink, KING_BG, KING_DOT,
                                            EMBERS, WIDE, WIDE_BLUR, ren_back_silhouette, make_wide)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, energy_bolts, blade, fist, BLADE_BROKEN

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/lore01_who_is_ren_asaka.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
TITLE, NEXT, NEXT_EP = "Who is Ren Asaka?", "Lyra's Airship", 4

SHOTS = [("title", 0.0, 4.0), ("profile", 4.0, 11.0), ("goats", 11.0, 17.0), ("streak", 17.0, 23.0), ("scarf", 23.0, 28.2),
         ("blade", 28.2, 34.2), ("stats", 34.2, 41.0), ("king", 41.0, 46.0), ("wake", 46.0, 52.0), ("next", 52.0, 55.5)]
TOTAL = 55.5
FUSE_T = 30.9
LINES = [
    ("NARRATOR", "Ren Asaka. Sixteen. Born on a tiny island at the very edge of the Shattered Skies.", 4.4, 10.7),
    ("REN", "Tiny? Excuse me. We have three goats. And a LOT of wind.", 11.3, 16.6),
    ("NARRATOR", "That white streak in his hair? He's had it since he was a baby. Nobody knows why.", 17.4, 22.7),
    ("REN", "The scarf was my mom's. Nobody touches the scarf.", 23.4, 27.9),
    ("NARRATOR", "His blade was broken for years. Then a sky-shard fell... and chose it.", 28.5, 33.9),
    ("REN", "Stubborn? Reckless? Okay, fine. But I never leave anyone behind.", 34.6, 40.6),
    ("HOLLOW KING", "Loyal hearts are the easiest to break, boy.", 41.4, 45.7),
    ("NARRATOR", "But the shard knows something about Ren... and it's starting to wake up.", 46.4, 51.7),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "HOLLOW KING": (190, 120, 255)}
draw_caption, speaking = e1.draw_caption, e1.speaking

# ------------------------------------------------------------ helpers
def bust_pt(bx, by, scale, fx, fy):
    """screen position of a point given in bust coords, for a bust placed with paste_bust(.., scale, fx, fy)."""
    return fx + (bx - 450)*scale, fy + (by - 480)*scale

def panel(im, box, col=(90, 220, 255), alpha=200):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, 22, fill=(8, 14, 30, alpha), outline=col + (255,), width=4)
    # corner brackets
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(cx + 8*sx, cy + 50*sy), (cx + 8*sx, cy + 8*sy), (cx + 50*sx, cy + 8*sy)], fill=(230, 255, 255, 255), width=6)
    im.alpha_composite(lay)

def callout(im, target, label_xy, title, sub, p, col=(120, 235, 255)):
    """animated pointer line from target to a label box; p 0..1."""
    if p <= 0: return
    tx, ty = target; lx, ly = label_xy
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    q = min(1, p*2)
    ex, ey = tx + (lx - tx)*q, ty + (ly - ty)*q
    d.line([(tx, ty), (ex, ey)], fill=col + (255,), width=6)
    r = 16 + 6*math.sin(p*20)
    d.ellipse([tx - r, ty - r, tx + r, ty + r], outline=col + (255,), width=5)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6))); im.alpha_composite(lay)
    if p > 0.5:
        a = ease((p - 0.5)/0.3)
        f1, f2 = font(54), font(38)
        w = max(f1.getlength(title), f2.getlength(sub)) + 50
        x0 = min(max(lx - w/2, 60), 920 - w)
        box = Image.new("RGBA", im.size, (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        bd.rounded_rectangle([x0, ly - 10, x0 + w, ly + 130], 18, fill=(8, 14, 30, int(215*a)), outline=col + (int(255*a),), width=4)
        bd.text((x0 + 25, ly), title, font=f1, fill=(255, 255, 255, int(255*a)), stroke_width=5, stroke_fill=(8, 8, 16, int(255*a)))
        bd.text((x0 + 25, ly + 72), sub, font=f2, fill=col + (int(255*a),))
        im.alpha_composite(box)

def wind_streaks(im, t, n=14, seed=4, alpha=120):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(n):
        y = r.uniform(150, 1500); sp = r.uniform(900, 1600); ln = r.uniform(120, 320)
        x = W + 200 - ((t*sp + r.uniform(0, 3000)) % (W + 600))
        d.line([(x, y), (x + ln, y - ln*0.12)], fill=(255, 255, 255, alpha), width=4)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))

def goat(im, x, y, sc, t, seed=0, flip=False):
    lay = Image.new("RGBA", (int(220*sc) + 20, int(200*sc) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); o = (14, 12, 22)
    s = sc; bob = 3*math.sin(t*6 + seed)
    for lx in (50, 80, 140, 170):
        d.rectangle([lx*s, 120*s, (lx + 14)*s, 180*s], fill=(60, 50, 50), outline=o, width=2)
    d.ellipse([30*s, 60*s + bob, 190*s, 140*s + bob], fill=(246, 244, 236), outline=o, width=4)
    d.ellipse([150*s, 30*s + bob, 215*s, 90*s + bob], fill=(246, 244, 236), outline=o, width=4)
    d.polygon([(165*s, 36*s + bob), (150*s, 6*s + bob), (176*s, 32*s + bob)], fill=(170, 150, 110), outline=o)
    d.polygon([(190*s, 34*s + bob), (198*s, 4*s + bob), (202*s, 36*s + bob)], fill=(170, 150, 110), outline=o)
    d.ellipse([186*s, 52*s + bob, 196*s, 62*s + bob], fill=o)
    d.polygon([(190*s, 86*s + bob), (198*s, 112*s + bob), (204*s, 84*s + bob)], fill=(200, 196, 186))
    if flip: lay = lay.transpose(Image.FLIP_LEFT_RIGHT)
    im.alpha_composite(lay, (int(x - lay.width/2), int(y - lay.height)))

def stat_bar(im, y, label, val, p, col):
    d = ImageDraw.Draw(im)
    d.text((150, y), label, font=font(44), fill=(255, 255, 255), stroke_width=5, stroke_fill=(8, 8, 16))
    x0, x1 = 150, 880
    d.rounded_rectangle([x0, y + 64, x1, y + 96], 14, fill=(20, 26, 46), outline=(8, 8, 16), width=3)
    v = val*ease(p)
    if v > 1:
        d.rounded_rectangle([x0 + 3, y + 67, x0 + 3 + (x1 - x0 - 6)*v/100, y + 93], 12, fill=col)
    num = "%d" % round(v)
    f = font(46); d.text((x1 - f.getlength(num), y - 2), num, font=f, fill=col, stroke_width=5, stroke_fill=(8, 8, 16))

def eye_glow(im, scale, fx, fy, a):
    if a <= 0: return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for bx in (370, 530):
        x, y = bust_pt(bx, 478, scale, fx, fy); r = 40*scale
        d.ellipse([x - r, y - r, x + r, y + r], fill=(90, 235, 255, int(230*a)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(18*scale)))
    d = ImageDraw.Draw(lay)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(5*scale)))

def pulse_rings(im, t, cx, cy, n=3, col=(120, 240, 255)):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(n):
        p = ((t*0.7 + k/n) % 1.0); r = 80 + 700*p
        d.ellipse([cx - r, cy - r*0.9, cx + r, cy + r*0.9], outline=col + (int(200*(1 - p)),), width=10)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6)))

def scanlines():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for y in range(0, H, 6): d.line([(0, y), (W, y)], fill=(120, 220, 255, 14))
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(120, 220, 255, 10))
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(120, 220, 255, 10))
    return lay
SCAN = scanlines()

# ------------------------------------------------------------ backgrounds
def make_dusk():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (20, 40, 80)), (0.35, (60, 110, 150)), (0.58, (240, 150, 100)), (0.7, (255, 190, 120)), (1, (90, 70, 110))])).convert("RGBA")
    clouds(im, 1350, 2200, 61, tint=(255, 190, 150))
    island(im, 1100, 900, 160, 140, 63); island(im, 180, 1050, 120, 110, 64)
    island(im, 640, 1250, 520, 380, 65, houses=3, lit=False)
    return im.convert("RGB")
DUSK = make_dusk()
DUSK_BLUR = DUSK.filter(ImageFilter.GaussianBlur(3))

def make_file_bg():
    im = Image.fromarray(grad(W, H, [(0, (6, 18, 40)), (0.5, (14, 56, 88)), (1, (6, 14, 30))])).convert("RGBA")
    stars(im, 140, 1900, 71)
    return im
FILE_BG = make_file_bg()

def make_forge_dark():
    im = Image.fromarray(grad(W, H, [(0, (4, 8, 20)), (0.55, (16, 36, 64)), (1, (4, 8, 18))])).convert("RGBA")
    return im
FORGE_DARK = make_forge_dark()

NIGHT_BG = WIDE.filter(ImageFilter.GaussianBlur(5))

def make_cloudsky():
    w, h = 1300, 2200
    im = Image.fromarray(grad(w, h, [(0, (8, 16, 40)), (0.35, (30, 60, 100)), (0.6, (200, 110, 90)), (0.72, (240, 160, 100)), (1, (70, 60, 100))])).convert("RGBA")
    stars(im, 120, 800, 81); clouds(im, 1250, 2200, 82, tint=(255, 180, 140))
    return im.convert("RGB")
CLOUDSKY = make_cloudsky()

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(NIGHT_BG, 1.0 + 0.05*lt, 540, 1000).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 8, 20, 255)), 0.45)
    im.alpha_composite(light_rays(t, (110, 220, 255), 540, -120, 60))
    # Ren from behind on a cliff edge, scarf whipping
    d = ImageDraw.Draw(im)
    d.polygon([(0, 1500), (420, 1440), (760, 1470), (1080, 1520), (1080, 1920), (0, 1920)], fill=(16, 16, 28))
    ren_back_silhouette(im, 540, 1460, 2.1, t*7)
    rot_paste(im, blade(1.0, 0.8 + 0.2*math.sin(t*4), 0.45), 160, 640, 1330)
    embers(im, t, 0.6, True)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 760, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 910, 540 + w, 916], fill=(90, 220, 255))
        text_center(d, "—  LORE  —", 940, 60, (255, 190, 110))
    if lt > 1.2: glow_text(im, TITLE, 1030, 92, (255, 255, 255), (220, 60, 70))
    return flash(im, max(0, 1 - lt/0.35))

def shot_profile(t, lt):
    im = FILE_BG.copy()
    im.alpha_composite(SCAN)
    im.alpha_composite(light_rays(t, (120, 220, 255), 900, -200, 35))
    # Ren slides in from the left
    k = ease(lt/0.8)
    sc = 0.95; fx = -300 + 840*k; fy = 900
    m = speaking("REN", t)
    paste_bust(im, ren_bust("calm", 0, blink(t), int(t*5) % 8, False), sc, fx, fy)
    rot_paste(im, blade(1.0, 0.6 + 0.2*math.sin(t*3), 0.75), 22, fx + 330, fy + 140)
    # profile card on top
    if lt > 0.5:
        a = ease((lt - 0.5)/0.4)
        panel(im, [110, 170 - 30*(1 - a), 920, 600 - 30*(1 - a)], alpha=int(200*a))
        d = ImageDraw.Draw(im); y0 = 200 - 30*(1 - a)
        d.text((150, y0), "CHARACTER FILE  #01", font=font(38), fill=(120, 235, 255))
        rows = [("NAME", "REN ASAKA"), ("AGE", "16"), ("HOME", "Edge-of-sky island"), ("WEAPON", "Cracked shard-blade")]
        for i, (kk, vv) in enumerate(rows):
            if lt > 0.9 + 0.5*i:
                yy = y0 + 70 + i*78
                d.text((150, yy), kk, font=font(40), fill=(255, 190, 110), stroke_width=4, stroke_fill=(8, 8, 16))
                d.text((360, yy - 2), vv, font=font(44), fill=(255, 255, 255), stroke_width=5, stroke_fill=(8, 8, 16))
    embers(im, t, 0.4, True)
    return im

def shot_goats(t, lt):
    im = cam(DUSK, 1.08 + 0.04*ease(lt/6), 640 - 12*lt, 1130).convert("RGBA")
    im.alpha_composite(light_rays(t, (255, 190, 110), 950, -150, 45))
    # three goats on the island ridge, one keeps chewing
    for i, (x, sc, fl) in enumerate(((210, 0.55, False), (330, 0.5, True), (880, 0.6, True))):
        goat(im, x - 8*lt, 1215 + (i % 2)*12, sc, t, i, fl)
    m = speaking("REN", t)
    expr = "calm" if lt < 3.2 else "determined"
    sc = 1.08
    paste_bust(im, ren_bust(expr, m, blink(t, 0.9), int(t*14) % 8, False), sc, 560, 800)
    wind_streaks(im, t, 16, 5, 140)
    embers(im, t, 0.5)
    return shake(im, 2, t, 5) if lt > 3.2 else im

def shot_streak(t, lt):
    k = ease(lt/6)
    im = cam(NIGHT_BG, 1.25, 600, 900).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 20, 40, 255)), 0.3)
    sc = 1.55 + 0.25*k; fx, fy = 590 + 40*k, 900 + 60*k
    paste_bust(im, ren_bust("calm", 0, blink(t, 1.3), int(t*5) % 8, False), sc, fx, fy)
    # shimmer on the streak
    sx, sy = bust_pt(385, 230, sc, fx, fy)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    r = 70 + 20*math.sin(t*5)
    d.ellipse([sx - r, sy - r*1.6, sx + r, sy + r*1.6], fill=(150, 240, 255, 90))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(30)))
    for i in range(6):
        a = t*2 + i; px = sx + 70*math.cos(a); py = sy + 110*math.sin(a*1.3)
        d2 = ImageDraw.Draw(im); d2.ellipse([px - 5, py - 5, px + 5, py + 5], fill=(220, 255, 255))
    callout(im, (sx, sy), (520, 190), "WHITE STREAK", "origin: UNKNOWN", (lt - 0.6)/1.6)
    embers(im, t, 0.3, True)
    return im

def shot_scarf(t, lt):
    im = cam(DUSK_BLUR, 1.2, 760 - 20*lt, 1000).convert("RGBA")
    im.alpha_composite(light_rays(t, (255, 170, 90), 200, -200, 55))
    m = speaking("REN", t)
    sc = 1.2 + 0.05*ease(lt/5); fx, fy = 520, 700
    paste_bust(im, ren_bust("determined", m, blink(t, 2.2), int(t*16) % 8, False), sc, fx, fy)
    tx, ty = bust_pt(150, 840, sc, fx, fy)
    callout(im, (max(150, tx), ty), (360, 140), "RED SCARF", "do NOT touch", (lt - 0.8)/1.4, (255, 120, 120))
    wind_streaks(im, t, 12, 9, 120)
    embers(im, t, 0.7, False, 1.4)
    return im

def shot_blade(t, lt):
    a = t - FUSE_T
    k = ease(lt/6)
    im = FORGE_DARK.copy()
    if a > 0: im.alpha_composite(SPEED[int(t*15) % 4])
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([140, 300, 940, 1300], fill=(80, 220, 255, int(40 + (150 if a > 0 else 0)*min(1, max(0, a)))))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
    if a < 0:
        # broken blade lying still, slowly turning in the dark
        rot_paste(im, BLADE_BROKEN, 12 - 6*lt, 540, 820)
        p = ease((lt - 0.4)/(FUSE_T - 28.2 - 0.4))
        sh = shard(int(150 - 60*p)); sx, sy = 760 - 220*p, 120 + 900*p
        # falling streak
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).line([(sx + 160, sy - 500), (sx, sy)], fill=(140, 240, 255, 160), width=26)
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(14)))
        im.alpha_composite(sh, (int(sx - sh.width/2), int(sy - sh.height/2)))
        return shake(im, 2 + 4*p, t, 3)
    frac = ease(a/1.8)
    rot_paste(im, blade(frac, 0.8 + 0.2*math.sin(t*6), 1.0) if frac > 0.02 else BLADE_BROKEN, 12*(1 - frac), 540, 820 - 30*frac)
    energy_bolts(im, t, 540, 1250, 540, 1250 - 950*frac, 3, 1)
    sparks(im, t, 540, 1230, 18, 0.6, 21, (170, 245, 255))
    im.alpha_composite(light_rays(t, (150, 240, 255), 540, 900, 60*max(0, 1 - a/2.5)))
    embers(im, t, 1.0, True, 2.2)
    im = shake(im, 18*max(0, 1 - a/0.8) + 2, t, 7)
    return flash(im, max(0, 1 - a/0.4))

def shot_stats(t, lt):
    im = Image.fromarray(grad(W, H, [(0, (40, 14, 30)), (0.5, (110, 40, 50)), (1, (20, 10, 24))])).convert("RGBA")
    im.alpha_composite(SPEED[int(t*12) % 4])
    m = speaking("REN", t)
    sc = 1.0 + 0.06*ease(lt/6.8); fx, fy = 560, 1000
    expr = "calm" if lt < 2.2 else "determined"
    paste_bust(im, ren_bust(expr, m, blink(t, 0.4) and expr == "calm", int(t*10) % 8, False), sc, fx, fy)
    rot_paste(im, blade(1.0, 0.85 + 0.15*math.sin(t*5), 0.9), -14, 220, 1050)
    fist(im, 220 - 300*math.sin(math.radians(14)), 1050 + 300*math.cos(math.radians(14)), 0.8)
    panel(im, [110, 150, 920, 640], (255, 140, 120), 190)
    stats = [("STUBBORN", 99, (255, 150, 90)), ("RECKLESS", 97, (255, 110, 110)), ("LOYAL", 100, (120, 235, 255)), ("PATIENCE", 4, (200, 200, 210))]
    for i, (lb, v, c) in enumerate(stats):
        stat_bar(im, 175 + i*112, lb, v, (lt - 0.3 - 0.45*i)/0.8, c)
    if 3.6 < lt:
        d = ImageDraw.Draw(im)
        # LOYAL bar flashes
        if int(lt*6) % 2 == 0: d.rounded_rectangle([140, 175 + 2*112 + 56, 890, 175 + 2*112 + 104], 18, outline=(230, 255, 255), width=4)
    embers(im, t, 0.8, False, 1.6)
    return shake(im, 3 if 2.2 < lt < 2.6 else 0, t, 2)

def shot_king(t, lt):
    im = cam(KING_BG, 1.12 - 0.05*ease(lt/5), 620, 1060).convert("RGBA")
    m = speaking("HOLLOW KING", t)
    lvl = {1: 2, 2: 4}[m] if m else int(1 + 0.8*math.sin(t*2))
    paste_bust(im, hollow_king(max(0, min(4, lvl))), 1.25 + 0.06*ease(lt/5), 540, 720)
    # a tiny red scarf scrap drifting past him
    x = 900 - 160*lt; y = 1150 + 60*math.sin(lt*2)
    d = ImageDraw.Draw(im); d.polygon([(x, y), (x + 60, y - 14), (x + 90, y + 6), (x + 30, y + 22)], fill=SCARF, outline=(14, 12, 22))
    for i, (x0, y0, sp, ph, r, cy) in enumerate(EMBERS[:30]):
        yy = (y0 - sp*0.6*t) % (H + 100) - 50; xx = x0 + 30*math.sin(t + ph)
        im.alpha_composite(KING_DOT, (int(xx - 12), int(yy - 12)))
    if 2.2 < lt < 2.35: im = flash(im, 0.3, (150, 90, 220))
    return shake(im, 3 if m == 2 else 0, t)

def shot_wake(t, lt):
    k = ease(lt/6)
    im = Image.fromarray(grad(W, H, [(0, (4, 14, 30)), (0.5, (16, 70, 100)), (1, (4, 12, 24))])).convert("RGBA")
    if lt > 2.8: im.alpha_composite(SPEED[int(t*15) % 4])
    pulse_rings(im, t, 540, 1050)
    sc = 1.25 + 0.35*k; fx, fy = 540, 820 + 40*k
    opened = lt > 2.8
    paste_bust(im, ren_bust("shocked" if opened else "calm", 0, not opened, int(t*8) % 8, False), sc, fx, fy)
    if opened: eye_glow(im, sc, fx, fy, min(1, (lt - 2.8)/0.4)*(0.75 + 0.25*math.sin(t*9)))
    # cyan up-light
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([100, 1100, 1000, 2200], fill=(120, 240, 255, int(60 + 120*k)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(100)))
    sh = shard(110); im.alpha_composite(sh, (int(170 - sh.width/2), int(330 - sh.height/2 + 20*math.sin(t*2))))
    if opened:
        energy_bolts(im, t, 80, 1500, 300, 1000, 1, 3); energy_bolts(im, t, 1000, 1500, 780, 1050, 1, 5)
    embers(im, t, 0.9, True, 2.0)
    im = shake(im, (10*max(0, 1 - (lt - 2.8)/0.5) + 3) if opened else 0, t, 4)
    return flash(im, max(0, 1 - (lt - 2.8)/0.3)) if 2.8 <= lt < 3.1 else im

def shot_next(t, lt):
    im = cam(CLOUDSKY, 1.08, 650, 1150).convert("RGBA")
    sh = airship(1.0, int(t*20) % 8).resize((760, 439), Image.BILINEAR)
    im.alpha_composite(sh, (int(540 - 380 + 30*lt), int(1250 - 220 - 20*lt)))
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.62, lt/0.3*0.62))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, "Ep %d: %s" % (NEXT_EP, NEXT), 760, 96, (255, 255, 255), (255, 140, 60))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(255, 170, 90))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA", 960, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1060, 50, (255, 220, 150), sw=6)
    embers(im, t, 0.5, True)
    return im

SHOT_FN = {"title": shot_title, "profile": shot_profile, "goats": shot_goats, "streak": shot_streak, "scarf": shot_scarf,
           "blade": shot_blade, "stats": shot_stats, "king": shot_king, "wake": shot_wake, "next": shot_next}

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

# ------------------------------------------------------------ audio (new mystery-hero score: E minor, 92 bpm)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(51)
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
    bpm = 92; beat = 60/bpm; bar = beat*4
    chords = [[52, 55, 59], [48, 52, 55], [43, 47, 50], [50, 54, 57]]  # Em C G D
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.7
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.5), (11, 0.6), (17, 0.45), (23, 0.6), (28.2, 0.7), (31, 1.0), (34, 0.85), (41, 0.55), (46, 0.6), (49, 1.0), (52, 1.0), (55.5, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.005) + saw(note(m), dur, 6, -0.005))*0.5*env(int(dur*SR), 0.4, 0.5)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.03*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.4), t0, vol=0.055*inten(t0))
        t0 += bar; ci += 1
    # music-box arpeggio (own pattern) through the profile parts
    t0, k = 4.0, 0
    while t0 < 28.0:
        ch = chords[int(t0 // bar) % 4]; m = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 24, ch[0] + 36, ch[2] + 24][k % 6]
        n = int(0.9*SR); x = tv(n)
        add((np.sin(2*np.pi*note(m)*x) + 0.25*np.sin(2*np.pi*note(m)*3.01*x)*np.exp(-8*x))*np.exp(-4*x), t0, pan=0.35*(1 if k % 2 else -1), vol=0.035*speech_duck(t0))
        t0 += beat/2; k += 1
    # heroic lead after the fusion (own melody)
    motif = [(64, 1), (67, 0.5), (71, 0.5), (76, 1.5), (74, 0.5), (71, 1), (72, 1), (71, 2)]
    tt = 31.0
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
        if 31.0 <= tb < 41.0 or 49.0 <= tb < 52.0:
            if b % 4 in (0, 2) or b % 8 == 7: add(KICK, tb, vol=0.5)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.17)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.08)
        elif 11.0 <= tb < 17.0 or 23.0 <= tb < 28.0:
            if b % 2 == 0: add(KICK, tb, vol=0.25)
        elif 41.0 <= tb < 46.0 and b % 4 == 0:
            add(TAIKO, tb, vol=0.5)
        elif 46.0 <= tb < 49.0:
            add(TAIKO, tb, vol=0.25 + 0.1*(tb - 46))
        b += 1
    # cut whooshes
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    # UI blips for profile rows, callouts and stat bars
    def blip(f=1400):
        n = int(0.09*SR); x = tv(n); return np.sin(2*np.pi*f*x)*np.exp(-30*x)
    for i in range(4): add(blip(1200 + 150*i), 4.0 + 0.9 + 0.5*i, vol=0.12)
    add(blip(900), 4.5, vol=0.12)
    add(blip(1500), 17.0 + 0.6 + 0.8, vol=0.12); add(blip(1300), 23.0 + 0.8 + 0.7, vol=0.12)
    for i in range(4): add(blip(1000 + 200*i), 34.2 + 0.3 + 0.45*i, vol=0.12)
    # goat bleat (synth, playful)
    n = int(0.5*SR); x = tv(n)
    bleat = saw(380, 0.5, 5)*(1 + 0.6*np.sin(2*np.pi*22*x))*env(n, 0.03, 0.2)
    add(bleat, 14.0, pan=-0.5, vol=0.05)
    # wind gusts
    add(lp_noise(6.0, 0.05, 0.12)*env(int(6*SR), 0.5, 1.0), 11.0, pan=0.3, vol=0.08)
    add(lp_noise(5.2, 0.05, 0.12)*env(int(5.2*SR), 0.5, 1.0), 23.0, pan=-0.3, vol=0.07)
    # title hit
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    # shard falling: rising whine to the fusion
    dur = FUSE_T - 28.6; n = int(dur*SR)
    f = np.linspace(300, 1600, n); amp = np.linspace(0.05, 1, n)**2
    add((np.sin(2*np.pi*np.cumsum(f)/SR)*0.22 + whoosh(dur, True)*0.5)*amp, 28.6, vol=0.28)
    # fusion impact + crystal ring
    n = int(3.5*SR); x = tv(n); f = 40 + 60*np.exp(-6*x)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-1.4*x) + 0.6*whoosh(3.5, False)*np.exp(-1.2*x), FUSE_T, vol=0.85)
    n = int(5.0*SR); x = tv(n)
    add(sum(np.sin(2*np.pi*fq*x) for fq in (659.3, 987.8, 1318.5))*np.exp(-0.6*x)/3, FUSE_T + 0.05, vol=0.06)
    # Hollow King drone
    n = int(5.0*SR); x = tv(n)
    add((saw(note(40), 5.0, 5) + 0.5*np.sin(2*np.pi*note(47)*x*(1 + 0.003*np.sin(2*np.pi*5*x))))*env(n, 0.8, 1.0), 41.0, vol=0.08)
    # heartbeat build before the eyes open
    for i in range(4):
        add(KICK*0.7, 46.3 + i*0.6, vol=0.35); add(KICK*0.5, 46.5 + i*0.6, vol=0.25)
    dur = 2.6; n = int(dur*SR); f = np.linspace(200, 1200, n)
    add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.linspace(0, 1, n)**2*0.2, 46.2, vol=0.3)
    n = int(3.0*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(45 + 70*np.exp(-6*x))/SR)*np.exp(-1.5*x) + 0.5*whoosh(3.0, False)*np.exp(-1.5*x), 48.8, vol=0.7)
    # NEXT hit
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 52.0, vol=0.6)
    for i, m in enumerate([64, 71, 76, 79, 83]):
        n = int(3.0*SR); add(saw(note(m), 3.0, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 52.05, pan=-0.6 + 0.3*i, vol=0.05)
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
