"""SKYFORGE SAGA Ep 9: The First Memory  (no-voice build: music + sfx + timed captions).
The shard-blade pulls Ren into a golden memory of the unbroken sky-kingdom. A young king raises the great
shard and swears no island will fall - then the shard breaks the sky, his crown cracks, and he becomes the
Hollow King... who turns and SEES Ren inside the memory. Ren wakes in the drowned hall; Kuro steadies him,
Lyra spots a ship docking, and Captain Mire steps out of the mist. Reuses Ep 1-8 / Lore 2 helpers."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, embers, SPEED, cam, shake, flash, VIG, text_center, glow_text,
                                            paste_bust, ease, blink, light_rays, island, clouds, sky_cracks, KING_BG)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, energy_bolts
from make_teen_ep03_hollow_soldiers import violet_fog
from make_teen_ep05_the_fox_in_the_engine import paste_kuro, blue_embers, blue_fire_glow
from make_teen_lore02_the_shattered_skies_explained import KINGDOM, FRAGS, CRACKS, OLD_SKY, KX, KY
from make_teen_ep08_the_drowned_island import HALL, HALL_BLUR, dust, light_ring

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/09_the_first_memory.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 9, "The First Memory", "Mire Strikes"

SHOTS = [("title", 0.0, 4.0), ("kingdom", 4.0, 10.4), ("ren", 10.4, 15.2), ("king", 15.2, 21.8), ("shatter", 21.8, 28.0),
         ("crown", 28.0, 34.0), ("see", 34.0, 39.6), ("wake", 39.6, 45.0), ("lyra", 45.0, 50.0), ("mire", 50.0, 54.8),
         ("next", 54.8, 58.8)]
TOTAL = 58.8
BREAK_T = 24.2
LINES = [
    ("NARRATOR", "The shard dragged Ren into a memory... from before the sky ever broke.", 4.3, 10.1),
    ("REN", "Whoa. The islands are one piece. This is the old sky-kingdom!", 10.7, 14.9),
    ("THE KING", "With this shard, no island will ever fall again. I swear it.", 15.6, 21.4),
    ("NARRATOR", "But the shard was far too strong for one king to hold.", 22.1, 27.6),
    ("HOLLOW KING", "The sky broke. My crown broke. And I... became hollow.", 28.4, 33.7),
    ("HOLLOW KING", "Wait. Someone is watching. I see you, shard-bearer.", 34.3, 39.3),
    ("KURO", "Breathe, Ren. Memories in this place have teeth.", 40.0, 44.7),
    ("LYRA", "Uh, guys? Someone just docked right next to the Kestrel.", 45.3, 49.7),
    ("CAPTAIN MIRE", "There you are. Not even the deep can hide you from me.", 50.2, 54.6),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255),
          "HOLLOW KING": (190, 120, 255), "THE KING": (255, 206, 110), "CAPTAIN MIRE": (230, 110, 90)}
draw_caption, speaking = e1.draw_caption, e1.speaking
O = (14, 12, 22)
GOLD, GOLD_SH, GOLD_HL = (236, 196, 96), (176, 136, 60), (255, 236, 160)

# ------------------------------------------------------------ memory look: warm glowing frame edge + golden motes
def make_mem_edge():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W/2)/(W*0.62))**2 + ((y - H/2)/(H*0.6))**2)
    a = np.clip((d - 0.72)*1.6, 0, 0.75)
    lay = np.zeros((H, W, 4), np.uint8); lay[..., 0] = 255; lay[..., 1] = 214; lay[..., 2] = 150
    lay[..., 3] = (a*255).astype(np.uint8)
    return Image.fromarray(lay, "RGBA")
MEM_EDGE = make_mem_edge()

def motes(im, t, n=36, seed=3, col=(255, 226, 150)):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(n):
        x = (r.uniform(0, W) + 30*math.sin(t*0.5 + i)) % W; y = (r.uniform(0, H) - t*r.uniform(15, 45)) % H
        s = r.uniform(3, 7); a = int(110 + 90*math.sin(t*2.2 + i))
        d.ellipse([x - s, y - s, x + s, y + s], fill=col + (max(0, a),))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))

def memory_fx(im, t):
    im.alpha_composite(MEM_EDGE)
    motes(im, t)

# ------------------------------------------------------------ the young king, seen from behind (no face shown)
def make_king_back():
    im = new_layer(); d = ImageDraw.Draw(im)
    CAPE, CAPE_SH, SLEEVE = (40, 52, 128), (26, 32, 86), (58, 72, 156)
    HAIRK, HAIRK_HL = (54, 42, 78), (96, 84, 132)
    # raised arms in a V (drawn first so the cape shoulders overlap their base)
    for s in (-1, 1):
        sh_x, hx = 450 + s*250, 450 + s*175
        poly(d, [(sh_x - s*70, 860), (sh_x + s*40, 820), (hx + s*45, 300), (hx - s*35, 290)], SLEEVE)
        poly(d, [(sh_x + s*40, 820), (sh_x + s*5, 840), (hx + s*10, 296), (hx + s*45, 300)], CAPE_SH, ow=0)
        d.line(P([(hx - s*34, 330), (hx + s*46, 340)]), fill=GOLD, width=9*SS)  # gold cuff
        ell(d, [hx - 34, 236, hx + 34, 312], SKIN)
    # cape with broad shoulders
    poly(d, [(80, 1600), (110, 960), (180, 830), (330, 780), (570, 780), (720, 830), (790, 960), (820, 1600)], CAPE)
    poly(d, [(450, 780), (570, 780), (720, 830), (790, 960), (820, 1600), (450, 1600)], CAPE_SH, ow=0)
    d.line(P([(80, 1600), (110, 960), (180, 830), (330, 780), (570, 780), (720, 830), (790, 960), (820, 1600)]), fill=OUT, width=5*SS)
    for x0 in (260, 450, 640):  # cape folds
        d.line(P([(x0, 960), (x0 + (x0 - 450)*0.35, 1600)]), fill=(20, 24, 64), width=4*SS)
    d.line(P([(86, 1560), (814, 1560)]), fill=GOLD, width=10*SS)  # gold hem
    # gold mantle collar across the shoulders
    poly(d, [(180, 830), (330, 780), (570, 780), (720, 830), (640, 900), (450, 930), (260, 900)], (60, 74, 160))
    d.line(P([(190, 846), (330, 800), (570, 800), (710, 846)]), fill=GOLD, width=8*SS)
    # long hair down the back
    poly(d, [(350, 540), (550, 540), (590, 880), (510, 860), (450, 900), (390, 860), (310, 880)], HAIRK)
    ell(d, [345, 410, 555, 650], HAIRK)
    for x0 in (385, 425, 475, 515):  # hair strand highlights
        d.line(P([(x0, 480), (x0 + (x0 - 450)*0.3, 840)]), fill=HAIRK_HL, width=4*SS)
    # crown: same five-spike shape as the Hollow King's - but whole and shining
    poly(d, [(338, 440), (562, 440), (556, 492), (344, 492)], GOLD)
    spikes = [(358, 440, 342, 330), (404, 440, 400, 296), (450, 440, 450, 258), (496, 440, 500, 296), (542, 440, 558, 330)]
    for x, y, tx, ty in spikes:
        poly(d, [(x - 22, y), (x + 22, y), (tx, ty)], GOLD)
        poly(d, [(x, y), (x + 20, y), (tx, ty + 10)], GOLD_SH, ow=0)
    d.line(P([(346, 458), (554, 458)]), fill=GOLD_HL, width=4*SS)
    ell(d, [436, 448, 464, 476], (90, 220, 255), ow=3)
    return finish(im)
KING_BACK = make_king_back()

def make_balcony():
    im = OLD_SKY.copy()
    for cx, ty, w, dp, sd in ((170, 1180, 260, 160, 41), (900, 1120, 300, 190, 42), (560, 1300, 200, 120, 43)):
        island(im, cx, ty, w, dp, sd, houses=2, lit=False)
    d = ImageDraw.Draw(im)
    STONE, STONE_SH = (240, 230, 210), (196, 184, 166)
    d.rectangle([0, 1480, W, 1540], fill=STONE, outline=O, width=5)
    for x in range(20, W, 90):
        d.rounded_rectangle([x, 1540, x + 44, 1760], 12, fill=STONE, outline=O, width=4)
        d.rectangle([x + 26, 1544, x + 42, 1756], fill=STONE_SH)
    d.rectangle([0, 1760, W, H], fill=STONE_SH, outline=O, width=5)
    return im
BALCONY = make_balcony()

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(HALL, 1.15 + 0.05*lt, 650, 1300).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 8, 16, 255)), 0.5)
    dust(im, t, 50)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 700, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 850, 540 + w, 856], fill=(255, 190, 110))
        text_center(d, "—  Ep %d  —" % EP, 880, 60, (255, 190, 110))
    if lt > 1.2: glow_text(im, TITLE, 970, 96, (255, 255, 255), (255, 190, 90))
    if lt > 3.3: im = flash(im, (lt - 3.3)/0.7, (255, 236, 190))
    return flash(im, max(0, 1 - lt/0.35))

def kingdom_sprite(sc, crack=0.0):
    sp = KINGDOM
    if crack > 0:
        sp = KINGDOM.copy(); cr = CRACKS.copy()
        cr.putalpha(cr.split()[3].point(lambda v: int(v*crack))); sp.alpha_composite(cr)
    return sp.resize((int(sp.width*sc), int(sp.height*sc)), Image.BILINEAR)

def shot_kingdom(t, lt):
    k = ease(lt/6.4)
    im = OLD_SKY.copy()
    im.alpha_composite(light_rays(t, (255, 220, 150), 540, -150, 60))
    sc = 0.7 + 0.22*k
    im.alpha_composite(kingdom_sprite(sc), (int(540 - KX*sc), int(820 + 10*math.sin(t*1.2) - KY*sc)))
    # chain-bridge-free sky: tiny birds/airships gliding
    d = ImageDraw.Draw(im)
    for i in range(5):
        x = (120 + i*210 + t*40) % (W + 100) - 50; y = 300 + 60*math.sin(i*1.7)
        d.line([(x - 18, y), (x, y + 8), (x + 18, y)], fill=O, width=4)
    memory_fx(im, t)
    if lt < 0.5: im = flash(im, 1 - lt/0.5, (255, 236, 190))
    return im

def shot_ren(t, lt):
    k = ease(lt/4.8)
    bg = OLD_SKY.filter(ImageFilter.GaussianBlur(4)).copy() if not hasattr(shot_ren, "bg") else shot_ren.bg
    shot_ren.bg = bg
    im = bg.copy()
    s = kingdom_sprite(0.55)
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(3)), (int(780 - KX*0.55), int(1050 - KY*0.55)))
    im.alpha_composite(light_rays(t, (255, 220, 150), 900, -100, 50))
    m = speaking("REN", t)
    expr = "shocked" if lt < 2.4 else "calm"
    paste_bust(im, ren_bust(expr, m, blink(t, 0.3), int(t*4) % 8, True), 1.0 + 0.05*k, 500 - 20*k, 760)
    # warm rim light
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([520, 300, 1000, 1100], fill=(255, 210, 140, 50))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    memory_fx(im, t)
    return im

def shot_king(t, lt):
    k = ease(lt/6.6)
    im = cam(BALCONY, 1.08 + 0.06*k, 540, 1000 + 40*k).convert("RGBA")
    im.alpha_composite(light_rays(t, (255, 226, 160), 540, 500, int(50 + 40*k)))
    # the great shard rising above his hands
    rise = ease(lt/2.0)
    sx, sy = 540, 540 - 60*rise
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    rr = 220 + 40*math.sin(t*3)
    gd.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(120, 240, 255, int(110*rise)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(50)))
    paste_bust(im, KING_BACK, 0.82, 540, 900)
    sh = shard(150)
    im.alpha_composite(sh, (int(sx - sh.width/2), int(sy - sh.height/2 + 6*math.sin(t*2))))
    if lt > 2.0:
        for i in range(2):
            light_ring(im, sx, sy, ((lt*0.5 + i/2) % 1.0), (255, 236, 170))
    memory_fx(im, t)
    return im

def shot_shatter(t, lt):
    a = t - BREAK_T
    im = OLD_SKY.copy()
    ox, oy, sc = 540, 820 + 8*math.sin(t*1.2), 0.9
    if a < 0:
        im = Image.blend(im, Image.new("RGBA", im.size, (60, 30, 90, 255)), 0.25*ease(lt/2.4))
        c = ease(lt/2.4)
        im.alpha_composite(kingdom_sprite(sc, c), (int(ox - KX*sc), int(oy - KY*sc)))
        energy_bolts(im, t, ox, oy - 360, ox + 300*math.sin(t*4), oy - 600, 2, 3)
        memory_fx(im, t)
        return shake(im, 8*c, t, 2)
    p = ease(min(1, a/1.6)) + 0.25*max(0, a - 1.6)
    im = Image.blend(im, Image.new("RGBA", im.size, (40, 20, 70, 255)), min(0.55, a*0.45))
    sky_cracks(im, 9)
    for crop, cx, cy, dx, dy, rot in FRAGS:
        s = crop.resize((max(1, int(crop.width*sc)), max(1, int(crop.height*sc))), Image.BILINEAR)
        px = ox + (cx - KX)*sc + dx*420*p; py = oy + (cy - KY)*sc + dy*300*p + 120*p
        rot_paste(im, s, rot*p*2, px, py)
    sparks(im, t, ox, oy, 30, 1.4, 12, (150, 240, 255))
    r = random.Random(9)
    for kk in range(12):
        ang = r.uniform(0, 2*math.pi); spd = r.uniform(300, 700)
        x = ox + math.cos(ang)*spd*min(1.5, a); y = oy + math.sin(ang)*spd*min(1.5, a)*0.7 + 200*a*a
        sh = shard(26 + kk % 3*8); im.alpha_composite(sh, (int(x - sh.width/2), int(y - sh.height/2)))
    im.alpha_composite(SPEED[int(t*15) % 4])
    embers(im, t, 1.0, True, 2.0)
    memory_fx(im, t)
    im = shake(im, 22*max(0, 1 - a/0.9) + 3, t, 6)
    return flash(im, max(0, 1 - a/0.35))

def crown_crack_glow(im, sc, fx, fy, a):
    """violet light pouring out of the crack in the Hollow King's crown (crack line at bust 440..458, 120..350)."""
    if a <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    pts = [(440, 120), (455, 180), (438, 230), (458, 300), (446, 350)]
    pts = [(fx + (x - 450)*sc, fy + (y - 480)*sc) for x, y in pts]
    d.line(pts, fill=(210, 150, 255, int(255*a)), width=int(10*sc))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12*sc))); im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(3)))

def shot_crown(t, lt):
    k = ease(lt/6.0)
    im = cam(KING_BG, 1.1 + 0.06*k, 620, 1060).convert("RGBA")
    im.alpha_composite(violet_fog(t, 1250, 1650, 90, 31))
    m = speaking("HOLLOW KING", t)
    lvl = {1: 3, 2: 4}[m] if m else 2
    sc = 1.18 + 0.08*k
    paste_bust(im, hollow_king(lvl), sc, 540, 760)
    crown_crack_glow(im, sc, 540, 760, 0.6 + 0.4*math.sin(t*5))
    # gold flakes falling from the crown
    r = random.Random(77); d = ImageDraw.Draw(im)
    for i in range(14):
        x = 540 + r.uniform(-260, 260); y = (380 + r.uniform(0, 200) + lt*r.uniform(80, 200)) % 1500
        s = r.uniform(5, 10); d.polygon([(x, y - s), (x + s*0.7, y), (x, y + s), (x - s*0.7, y)], fill=GOLD, outline=O)
    embers(im, t, 0.4)
    if lt < 0.4: im = flash(im, 1 - lt/0.4, (190, 120, 255))
    return shake(im, 3 if m else 0, t, 4)

def glitch(im, amt, t):
    if amt <= 0: return im
    arr = np.array(im); r = random.Random(int(t*30))
    for i in range(int(4 + 10*amt)):
        y0 = r.randint(0, H - 80); hgt = r.randint(10, 80); dx = int(r.uniform(-60, 60)*amt)
        arr[y0:y0 + hgt] = np.roll(arr[y0:y0 + hgt], dx, axis=1)
    out = Image.fromarray(arr, im.mode)
    return Image.blend(out, Image.new(im.mode, im.size, (150, 70, 230, 255)), 0.15*amt)

def shot_see(t, lt):
    k = ease(lt/5.6)
    im = cam(KING_BG, 1.3 + 0.2*k, 620, 1000).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 2, 14, 255)), 0.4)
    m = speaking("HOLLOW KING", t)
    lvl = 4 if (m or lt > 3.0) else 2
    sc = 1.7 + 0.7*k
    # push in toward the face void, which sits just below the bust face centre
    paste_bust(im, hollow_king(lvl), sc, 540, 740 - 40*k)
    crown_crack_glow(im, sc, 540, 740 - 40*k, 0.8)
    if lt > 2.6:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        a = min(1, (lt - 2.6)/1.0)
        gd.ellipse([140, 300, 940, 1300], fill=(170, 80, 255, int(70*a)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(70)))
        im.alpha_composite(SPEED[int(t*15) % 4])
    embers(im, t, 0.5)
    im = glitch(im, max(0, (lt - 4.4)/1.0), t)
    if lt > 5.0: im = flash(im, (lt - 5.0)/0.6, (240, 230, 255))
    return shake(im, 2 + 6*max(0, lt - 3.0)/2.6, t, 9)

def shot_wake(t, lt):
    k = ease(lt/5.4)
    im = cam(HALL, 1.05 + 0.12*k, 650, 1300 - 100*k).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.3)
    blue_fire_glow(im, 540, 760, 380, 0.65)
    m = speaking("KURO", t)
    paste_kuro(im, kuro(m, blink(t, 1.2), int(t*10) % 8, "wide" if lt < 0.9 else "calm"), 1.2 + 0.05*k, 540, 760 + 8*math.sin(t*2.4))
    blue_embers(im, t, 540, 1000, 18, 15, 460)
    dust(im, t, 30, 16)
    if lt < 0.6: im = flash(im, 1 - lt/0.6, (240, 230, 255))
    return im

def shot_lyra(t, lt):
    k = ease(lt/5.0)
    im = cam(HALL_BLUR, 1.3 + 0.05*k, 650 + 60*k, 1500).convert("RGBA")
    # violet glow spilling in from the right (the other ship)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([700, 200, 1400, 1300], fill=(150, 70, 230, int(40 + 50*k)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(80)))
    dust(im, t, 30, 12)
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("shocked" if lt > 0.8 else "calm", m, blink(t, 0.9), True), 1.04 + 0.04*k, 520, 760)
    return im

def shot_mire(t, lt):
    k = ease(lt/4.8)
    im = cam(HALL_BLUR, 1.2 + 0.06*k, 650, 1250).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (10, 4, 18, 255)), 0.45)
    im.alpha_composite(violet_fog(t, 1050, 1600, 120, 41))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([140, 260, 940, 1300], fill=(160, 70, 230, 80))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(80)))
    m = speaking("CAPTAIN MIRE", t)
    # Mire strides out of the mist toward camera
    paste_bust(im, mire_bust(m, blink(t, 1.7)), 0.9 + 0.16*k, 520, 800 + 30*(1 - k))
    embers(im, t, 0.3)
    if lt < 0.4: im = shake(im, 10*(1 - lt/0.4), t)
    if 3.6 < lt < 3.8:  # spear glint
        d = ImageDraw.Draw(im)
        for i in range(8):
            a = i*math.pi/4; d.line([(860 + 30*math.cos(a), 320 + 30*math.sin(a)), (860 + 80*math.cos(a), 320 + 80*math.sin(a))], fill=(255, 255, 255), width=6)
    return im

def shot_next(t, lt):
    im = cam(KING_BG, 1.2, 620, 1060).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (8, 4, 14, 255)), 0.6)
    if lt < 0.4: im = flash(im, 1 - lt/0.4, (255, 220, 200))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 760, 110, (255, 255, 255), (230, 90, 70))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(230, 120, 90))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 970, 54, (230, 210, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1070, 50, (255, 220, 150), sw=6)
    return im

SHOT_FN = {"title": shot_title, "kingdom": shot_kingdom, "ren": shot_ren, "king": shot_king, "shatter": shot_shatter,
           "crown": shot_crown, "see": shot_see, "wake": shot_wake, "lyra": shot_lyra, "mire": shot_mire, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    if t - s < 0.08 and name in ("ren", "king", "lyra", "mire"):
        im = flash(im, 0.45)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio (A major memory -> A minor dread -> driving threat)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(99)
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
    def choir(m, dur):
        x = tv(int(dur*SR)); vib = 1 + 0.004*np.sin(2*np.pi*5.1*x)
        f = note(m)*vib; ph = 2*np.pi*np.cumsum(f)/SR
        return (np.sin(ph) + 0.45*np.sin(2*ph) + 0.25*np.sin(3*ph) + 0.6*np.sin(ph*1.003))*0.5
    def duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.6
        return 1.0
    def taiko():
        n = int(0.8*SR); x = tv(n); f = 62 + 46*np.exp(-12*x)
        return (np.sin(2*np.pi*np.cumsum(f)/SR) + 0.2*np.random.RandomState(4).randn(n)*np.exp(-30*x))*np.exp(-5*x)
    TAIKO = taiko()
    def harp(m, dur=1.6):
        n = int(dur*SR); x = tv(n)
        return (np.sin(2*np.pi*note(m)*x) + 0.3*np.sin(2*np.pi*note(m)*2*x) + 0.1*np.sin(2*np.pi*note(m)*3*x))*np.exp(-2.6*x)
    # --- memory section (4 - 22): warm A major pads A - F#m - D - E, choir + harp arps
    chords = [[45, 57, 61, 64], [42, 57, 61, 66], [38, 57, 62, 66], [40, 56, 59, 64]]
    t0, ci = 3.8, 0
    while t0 < 22.0:
        ch = chords[ci % 4]; dur = min(4.4, 22.6 - t0); n = int(dur*SR)
        for kk, m in enumerate(ch[1:]):
            add(choir(m, dur)*env(n, 0.9, 1.0), t0, pan=-0.5 + 0.5*kk, vol=0.035*duck(t0 + 1))
        add(sine(note(ch[0]), dur)*env(n, 0.5, 1.0), t0, vol=0.09)
        tt = t0
        for j in range(8):
            add(harp(ch[1 + j % 3] + 12*(j // 3 % 2)), tt, pan=-0.6 + 0.15*j, vol=0.04*duck(tt)); tt += 0.5
        t0 += 4.0; ci += 1
    # oath swell under the king (15.2-21.8)
    for m in (57, 61, 64, 69):
        n = int(6.4*SR); add((saw(note(m), 6.4, 6, 0.003) + saw(note(m), 6.4, 6, -0.003))*0.5*env(n, 2.5, 1.2), 15.4, pan=rs.uniform(-0.5, 0.5), vol=0.018)
    # --- shatter (21.8 - 28): tension cluster, riser, huge break at BREAK_T
    for m in (45, 46, 52):
        n = int(2.6*SR); x = tv(n)
        add(saw(note(m), 2.6, 6)*(0.7 + 0.3*np.sin(2*np.pi*9*x))*env(n, 0.3, 0.2), 21.7, pan=rs.uniform(-0.4, 0.4), vol=0.035)
    n = int(2.4*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(150 + 900*(x/2.4)**2)/SR)*(x/2.4)*0.6, 21.8, vol=0.08)
    add(whoosh(2.4, True)*(x/2.4), 21.8, vol=0.25)
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(40 + 80*np.exp(-6*x))/SR)*np.exp(-1.5*x) + 0.6*rs.randn(n)*np.exp(-5*x), BREAK_T, vol=0.6)
    for i in range(24):  # glassy shard tinkles
        nn = int(0.6*SR); xx = tv(nn); f = rs.uniform(1800, 4200)
        add(np.sin(2*np.pi*f*xx)*np.exp(-9*xx), BREAK_T + 0.1 + i*0.13 + rs.uniform(0, 0.08), pan=rs.uniform(-0.9, 0.9), vol=0.035)
    # --- Hollow King (28 - 39.6): A minor dread, low drone + heartbeat drums getting faster
    dread = [[33, 45, 48, 52], [29, 45, 48, 53], [31, 43, 50, 55]]
    t0 = 28.0
    for ci in range(3):
        ch = dread[ci]; dur = 4.2 if ci < 2 else 3.6; n = int(dur*SR)
        for kk, m in enumerate(ch[1:]):
            add((saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(n, 0.6, 0.8), t0, pan=-0.5 + 0.5*kk, vol=0.022*duck(t0 + 1))
        add(sine(note(ch[0]), dur)*env(n, 0.3, 0.8), t0, vol=0.12)
        t0 += dur
    tt = 28.2; step = 1.2
    while tt < 39.0:
        add(TAIKO, tt, vol=0.16); add(TAIKO, tt + 0.22, vol=0.09); tt += step; step = max(0.5, step*0.93)
    # "I see you" sting + glitch noise + whiteout
    for m in (57, 58, 63):
        n = int(2.0*SR); add(saw(note(m), 2.0, 5)*env(n, 0.02, 1.4), 37.4, pan=rs.uniform(-0.5, 0.5), vol=0.03)
    for i in range(16):
        nn = int(0.06*SR); add(rs.randn(nn)*np.exp(-30*tv(nn)), 38.4 + i*0.07, pan=rs.uniform(-0.8, 0.8), vol=0.12)
    n = int(1.4*SR); x = tv(n)
    add(whoosh(1.4, True)*(x/1.4), 38.2, vol=0.3)
    n = int(2.4*SR); x = tv(n)
    add(np.sin(2*np.pi*50*x)*np.exp(-2.2*x) + 0.4*whoosh(2.4, False)*np.exp(-2*x), 39.6, vol=0.5)
    # --- back in the hall (39.6 - 50): quiet E minor pad, water drips, music box
    for m in (52, 55, 59):
        n = int(10.6*SR); add(choir(m, 10.6)*env(n, 1.5, 2.0), 40.0, pan=rs.uniform(-0.5, 0.5), vol=0.025)
    add(sine(note(40), 10.4)*env(int(10.4*SR), 1.0, 1.5), 40.0, vol=0.08)
    for i in range(7):
        nn = int(0.3*SR); xx = tv(nn)
        add(np.sin(2*np.pi*(900 + 600*np.exp(-30*xx))*xx)*np.exp(-18*xx), 40.6 + i*1.4 + rs.uniform(0, 0.5), pan=rs.uniform(-0.8, 0.8), vol=0.035)
    # docking clunk off-screen during Lyra
    n = int(1.2*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(55 + 50*np.exp(-12*x))/SR)*np.exp(-4*x) + 0.4*rs.randn(n)*np.exp(-14*x), 45.1, pan=0.6, vol=0.32)
    add(np.sin(2*np.pi*np.cumsum(55 + 50*np.exp(-12*x))/SR)*np.exp(-4*x), 46.0, pan=0.6, vol=0.2)
    # --- Mire (50 - 54.8): driving drums, low brass stabs, then hit on NEXT
    tb = 50.0
    while tb < 54.6:
        add(TAIKO, tb, vol=0.22 if int((tb - 50)/0.4) % 2 == 0 else 0.12, pan=rs.uniform(-0.2, 0.2)); tb += 0.4
    for i, tb in enumerate((50.0, 51.6, 53.2)):
        n = int(0.9*SR)
        for m in (33, 45, 48):
            add(saw(note(m), 0.9, 7)*env(n, 0.01, 0.6), tb, vol=0.04)
    n = int(1.6*SR); x = tv(n)
    add(whoosh(1.6, True)*(x/1.6), 53.2, vol=0.3)
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 54.8, vol=0.6)
    for i, m in enumerate([45, 52, 57, 60, 64]):
        n = int(3.4*SR); add(saw(note(m), 3.4, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 54.85, pan=-0.6 + 0.3*i, vol=0.05)
    # shot whooshes, opening boom, ambient wind
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        if name not in ("shatter", "next", "wake"): add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.22)
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    add(whoosh(1.0, True), 3.2, vol=0.3)  # pulled into the memory
    add(lp_noise(TOTAL - 1, 0.015, 0.02)*1.4*env(int((TOTAL - 1)*SR), 2.0, 2.0), 0.5, vol=0.05)
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
