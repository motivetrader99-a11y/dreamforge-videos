"""SKYFORGE SAGA Ep 8: The Drowned Island  (no-voice build: music + sfx + timed captions).
The Kestrel limps down onto the ruined island beneath the Cloud Sea. A rune door opens for Ren's
shard-blade, Kuro names the old sky-kingdom, and a mural shows a king holding a shard - wearing a
cracked crown. The blade blazes: the shard is about to show Ren a memory. Reuses Ep 1-7 helpers."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, embers, SPEED, cam, shake, flash, VIG, text_center, glow_text,
                                            paste_bust, ease, blink, light_rays)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, energy_bolts, blade
from make_teen_ep05_the_fox_in_the_engine import paste_kuro, blue_embers, blue_fire_glow
from make_teen_ep07_into_the_cloud_sea import BELOW, shard_lights, ship_sprite, torn_sails, smoke_trail

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/08_the_drowned_island.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
EP, TITLE, NEXT = 8, "The Drowned Island", "The First Memory"

SHOTS = [("title", 0.0, 4.0), ("land", 4.0, 10.2), ("lyra", 10.2, 15.2), ("ren_door", 15.2, 22.6), ("kuro", 22.6, 28.2),
         ("mural", 28.2, 34.4), ("crown", 34.4, 40.4), ("glow", 40.4, 46.0), ("hook", 46.0, 51.4), ("next", 51.4, 55.8)]
TOTAL = 55.8
GLOW_T = 40.4
LINES = [
    ("NARRATOR", "Beneath the Cloud Sea lies a kingdom the sky forgot... and its lights are still on.", 4.3, 9.9),
    ("LYRA", "The Kestrel's patched enough to land. Barely. Nobody touch anything.", 10.4, 15.0),
    ("REN", "Uh... too late. It opened the second my blade got close.", 18.6, 22.4),
    ("KURO", "These halls belonged to the old sky-kingdom. Walk softly here.", 22.9, 27.9),
    ("LYRA", "Look at this mural. A king... holding a shard just like yours.", 28.6, 34.1),
    ("REN", "Wait. Why is the king's crown... cracked?", 35.6, 40.1),
    ("NARRATOR", "Then the shard-blade began to burn brighter than ever before.", 40.8, 45.6),
    ("REN", "Kuro... the shard is showing me something!", 46.3, 51.1),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255)}
draw_caption, speaking = e1.draw_caption, e1.speaking
O = (14, 12, 22)
STONE, STONE_D, STONE_HL = (40, 70, 84), (20, 40, 52), (78, 118, 132)
RUNE = (110, 240, 255)

# ------------------------------------------------------------ backgrounds
def make_hall():
    """interior of the drowned hall: broken pillars, collapsed roof letting cloud-light in, mist on the floor."""
    w, h = 1300, 2400
    im = Image.fromarray(grad(w, h, [(0, (90, 120, 140)), (0.12, (30, 60, 78)), (0.5, (12, 32, 46)), (1, (4, 14, 22))])).convert("RGBA")
    d = ImageDraw.Draw(im); r = random.Random(81)
    # back wall blocks
    for y in range(260, 1900, 90):
        off = 0 if (y // 90) % 2 else 70
        for x in range(-140 + off, w, 140):
            c = r.randint(-6, 6)
            d.rectangle([x + 3, y + 3, x + 137, y + 87], fill=(22 + c, 46 + c, 60 + c), outline=(12, 26, 36), width=3)
    # broken roof opening (cloud underside)
    d.polygon([(260, 0), (1040, 0), (980, 160), (820, 120), (700, 240), (560, 140), (420, 210), (300, 120)], fill=(150, 175, 195))
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.polygon([(330, 160), (980, 160), (1180, 2000), (120, 2000)], fill=(150, 230, 255, 30))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im)
    # pillars (some broken)
    for px, top, broken in ((90, 180, False), (360, 520, True), (940, 420, True), (1210, 160, False)):
        d.rectangle([px - 70, top, px + 70, 2100], fill=STONE, outline=O, width=6)
        d.rectangle([px - 70, top, px - 36, 2100], fill=STONE_HL)
        d.rectangle([px + 40, top, px + 70, 2100], fill=STONE_D)
        for y in range(top + 120, 2100, 220): d.line([(px - 70, y), (px + 70, y)], fill=O, width=4)
        if broken:
            d.polygon([(px - 70, top), (px - 30, top - 60), (px + 10, top - 20), (px + 50, top - 80), (px + 70, top)], fill=STONE, outline=O)
            # glowing rune band
            d.rectangle([px - 60, top + 300, px + 60, top + 330], fill=(40, 150, 170))
        else:
            d.rectangle([px - 90, top - 40, px + 90, top], fill=STONE_HL, outline=O, width=5)
    # rubble
    for i in range(30):
        x = r.uniform(0, w); y = r.uniform(1960, 2150); s = r.uniform(20, 70)
        d.polygon([(x - s, y), (x - s*0.4, y - s*0.8), (x + s*0.6, y - s*0.6), (x + s, y)], fill=STONE_D, outline=O)
    # mist on the floor
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for i in range(26):
        x = r.uniform(-100, w + 100); y = r.uniform(1900, 2350)
        ld.ellipse([x - 300, y - 60, x + 300, y + 60], fill=(120, 190, 210, 60))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(24)))
    return im.convert("RGB")
HALL = make_hall()
HALL_BLUR = HALL.filter(ImageFilter.GaussianBlur(5))

def make_door_bg():
    """great stone arch with a dark doorway; the rune ring and door leaves are drawn per frame."""
    im = cam(HALL_BLUR, 1.0, 650, 1200).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 12, 20, 255)), 0.35)
    d = ImageDraw.Draw(im)
    d.rectangle([150, 120, 930, 1700], fill=STONE, outline=O, width=8)
    d.rectangle([150, 120, 210, 1700], fill=STONE_HL)
    d.rectangle([870, 120, 930, 1700], fill=STONE_D)
    d.pieslice([230, 160, 850, 780], 180, 360, fill=(6, 16, 24), outline=O, width=6)
    d.rectangle([230, 470, 850, 1700], fill=(6, 16, 24), outline=O, width=6)
    for y in range(180, 1700, 160):
        d.line([(150, y), (230, y)], fill=O, width=4); d.line([(850, y), (930, y)], fill=O, width=4)
    return im
DOOR_BG = make_door_bg()

def make_mural():
    """long carved stone mural (2200x1400): floating islands, people raising hands, a king holding a shard high.
    The king's crown has a single crack (the clue). Drawn as flat carved relief, no faces."""
    w, h = 2200, 1400
    im = Image.new("RGBA", (w, h), (58, 92, 104, 255)); d = ImageDraw.Draw(im); r = random.Random(88)
    for i in range(1800):  # stone grain
        x, y = r.uniform(0, w), r.uniform(0, h); c = r.randint(-14, 14)
        d.point((x, y), fill=(58 + c, 92 + c, 104 + c))
    d.rectangle([20, 20, w - 20, h - 20], outline=(30, 54, 64), width=16)
    d.rectangle([50, 50, w - 50, h - 50], outline=(96, 140, 150), width=6)
    CARVE, CARVE_D, CARVE_HL = (88, 128, 138), (34, 58, 68), (140, 186, 192)
    def relief(pts, fill=CARVE):
        d.polygon([(x + 6, y + 8) for x, y in pts], fill=CARVE_D)
        d.polygon(pts, fill=fill, outline=(28, 50, 60))
    # floating islands across the top
    for cx, cy, s in ((260, 260, 1.0), (620, 200, 0.7), (1600, 210, 0.8), (1950, 300, 1.0)):
        relief([(cx - 140*s, cy), (cx + 140*s, cy), (cx + 70*s, cy + 90*s), (cx, cy + 150*s), (cx - 80*s, cy + 80*s)])
        relief([(cx - 40*s, cy), (cx - 40*s, cy - 70*s), (cx, cy - 100*s), (cx + 40*s, cy - 70*s), (cx + 40*s, cy)], CARVE_HL)
    # people (simple robed shapes) raising arms toward the king
    for i, x in enumerate((260, 420, 580, 1620, 1780, 1940)):
        y = 1180; f = 1 if x < 1100 else -1
        relief([(x - 50, y), (x + 50, y), (x + 34, y - 210), (x - 34, y - 210)])
        d.ellipse([x - 34, y - 290, x + 34, y - 222], fill=CARVE, outline=(28, 50, 60), width=4)
        relief([(x + 20*f, y - 190), (x + 90*f, y - 330), (x + 110*f, y - 316), (x + 44*f, y - 180)])
    # the king, centre: tall robe, arms up holding a shard; crown on the head
    kx = 1100
    relief([(kx - 160, 1220), (kx + 160, 1220), (kx + 90, 640), (kx - 90, 640)])
    relief([(kx - 100, 650), (kx + 100, 650), (kx + 70, 560), (kx - 70, 560)], CARVE_HL)
    d.ellipse([kx - 64, 430, kx + 64, 566], fill=CARVE, outline=(28, 50, 60), width=5)
    relief([(kx - 80, 620), (kx - 170, 400), (kx - 140, 390), (kx - 50, 600)])
    relief([(kx + 80, 620), (kx + 170, 400), (kx + 140, 390), (kx + 50, 600)])
    # crown: 5 points
    crown = [(kx - 74, 450), (kx - 80, 360), (kx - 46, 405), (kx - 20, 340), (kx, 395), (kx + 20, 340), (kx + 46, 405), (kx + 80, 360), (kx + 74, 450)]
    relief(crown, (170, 160, 110))
    # the crack (dark carved line straight down the crown)
    d.line([(kx + 4, 338), (kx - 10, 372), (kx + 12, 404), (kx - 4, 450)], fill=(20, 18, 30), width=9)
    # the carved shard above the king's hands (painted cyan)
    sx, sy = kx, 300
    d.polygon([(sx, sy - 120), (sx + 56, sy), (sx, sy + 90), (sx - 56, sy)], fill=(90, 220, 240), outline=(28, 50, 60), width=5)
    d.polygon([(sx, sy - 120), (sx + 56, sy), (sx, sy)], fill=(160, 245, 255))
    for k in range(10):  # carved rays
        a = math.radians(-90 + (k - 4.5)*18); d.line([(sx + 110*math.cos(a), sy + 110*math.sin(a)),
                                                      (sx + 230*math.cos(a), sy + 230*math.sin(a))], fill=CARVE_HL, width=8)
    # rune border along the bottom
    for x in range(120, w - 120, 70):
        d.line([(x, 1290), (x + 24, 1250), (x + 40, 1290)], fill=(60, 170, 190), width=6)
    return im
MURAL = make_mural()
CROWN_XY = (1100, 395)

# ------------------------------------------------------------ helpers
def rune_ring(im, cx, cy, R, lit, t, col=RUNE):
    """12 rune glyphs around a ring; `lit` (0..1) lights them clockwise."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=col + (int(60 + 160*lit),), width=6)
    for k in range(12):
        a = -math.pi/2 + k*math.pi/6
        x, y = cx + R*math.cos(a), cy + R*math.sin(a)
        on = lit*12 > k
        c = col + (255,) if on else (60, 90, 100, 200)
        g = k % 3
        if g == 0: pts = [(x - 16, y + 18), (x, y - 20), (x + 16, y + 18)]
        elif g == 1: pts = [(x - 16, y - 16), (x + 16, y - 16), (x - 16, y + 16), (x + 16, y + 16)]
        else: pts = [(x, y - 20), (x, y + 20), (x - 14, y + 4), (x + 14, y + 4)]
        d.line(pts, fill=c, width=6)
    if lit > 0:
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(10)))
    im.alpha_composite(lay)

def door_leaves(im, openp, t):
    """two stone leaves inside the doorway (x 230..850, y 160..1700) sliding apart, cyan light behind."""
    gap = 310*ease(openp)
    if openp > 0:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.rectangle([540 - gap - 30, 300, 540 + gap + 30, 1700], fill=(140, 240, 255, int(220*min(1, openp*2))))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im)
    lx1 = 540 - gap; rx0 = 540 + gap
    if lx1 > 236:
        d.rectangle([236, 470, lx1, 1696], fill=(30, 56, 68), outline=O, width=6)
    if rx0 < 844:
        d.rectangle([rx0, 470, 844, 1696], fill=(30, 56, 68), outline=O, width=6)
    if gap < 4:
        d.pieslice([236, 166, 844, 774], 180, 360, fill=(30, 56, 68), outline=O, width=6)
        d.line([(540, 170), (540, 1696)], fill=(110, 240, 255) if t > 1.8 else O, width=5)

def light_ring(im, cx, cy, p, col=(150, 240, 255)):
    R = 60 + 900*p
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=col + (int(255*(1 - p)),), width=int(10 + 20*(1 - p)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(6))); im.alpha_composite(lay)

def dust(im, t, n=40, seed=8, col=(170, 240, 255)):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); r = random.Random(seed)
    for i in range(n):
        x = (r.uniform(0, W) + 20*math.sin(t*0.7 + i)) % W; y = (r.uniform(0, H) - t*r.uniform(10, 40)) % H
        s = r.uniform(2, 5); a = int(120 + 100*math.sin(t*2 + i))
        d.ellipse([x - s, y - s, x + s, y + s], fill=col + (max(0, a),))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(1)))

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = cam(HALL, 1.15 + 0.05*lt, 650, 1300).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 8, 16, 255)), 0.5)
    dust(im, t, 50)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 700, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 850, 540 + w, 856], fill=(255, 150, 90))
        text_center(d, "—  Ep %d  —" % EP, 880, 60, (255, 190, 110))
    if lt > 1.2: glow_text(im, TITLE, 970, 92, (255, 255, 255), (60, 220, 255))
    return flash(im, max(0, 1 - lt/0.35))

def shot_land(t, lt):
    k = ease(lt/6.2)
    im = cam(BELOW, 1.25 + 0.25*k, 650, 1450 + 250*k).convert("RGBA")
    shard_lights(im, t, 0.7, 200)
    # tower windows flicker on
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for i, (gx, gy) in enumerate(((250, 1240), (430, 1170), (650, 1210), (850, 1140))):
        a = 0.6 + 0.4*math.sin(t*3 + i)
        gd.ellipse([gx - 22, gy - 22, gx + 22, gy + 22], fill=(110, 240, 255, int(200*a)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)))
    # the Kestrel descending toward a landing ledge
    x, y = 820 - 260*k, 280 + 620*k + 10*math.sin(lt*1.6)
    sc = 0.36 + 0.22*k
    smoke_trail(im, x + 90, y - 50, t*0.5, 7, 0.6, -1.0, 21)
    ang = 8 - 6*k
    rot_paste(im, ship_sprite(round(sc, 2), t), ang, x, y)
    torn_sails(im, x, y, sc, t*0.5, ang)
    im.alpha_composite(light_rays(t, (120, 230, 255), 540, -300, 30))
    embers(im, t, 0.25, True, 0.4)
    return im

def shot_lyra(t, lt):
    k = ease(lt/5.0)
    im = cam(HALL_BLUR, 1.3 + 0.05*k, 650 - 60*k, 1500).convert("RGBA")
    dust(im, t, 30, 12)
    m = speaking("LYRA", t)
    expr = "calm" if lt < 2.6 else "smirk"
    paste_bust(im, lyra_bust(expr, m, blink(t, 0.9), False), 1.04 + 0.04*k, 540, 760)
    return im

def shot_ren_door(t, lt):
    im = DOOR_BG.copy()
    lit = min(1, max(0, (lt - 0.3)/1.8))
    openp = min(1, max(0, (lt - 2.3)/1.2))
    door_leaves(im, openp, lt)
    rune_ring(im, 540, 480, 230, lit, t)
    if openp > 0: dust(im, t, 60, 14, (200, 250, 255))
    if 2.2 < lt < 3.6:   # grinding dust puffs from the floor
        sparks(im, t, 540, 1680, 14, 0.5, 31, (150, 200, 210))
    # Ren in the foreground, lower, looking back sheepishly
    m = speaking("REN", t)
    expr = "shocked" if lt < 3.4 else "calm"
    paste_bust(im, ren_bust(expr, m, blink(t, 0.4), int(t*4) % 8, True), 0.92, 540, 990)
    # his hilt glowing in answer to the runes
    if lit > 0:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        hx, hy = 540 + (654 - 450)*0.92, 990 + (540 - 480)*0.92
        rr = 26 + 20*lit + 6*math.sin(t*8)
        gd.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], fill=(90, 240, 255, 170))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(12)))
    return shake(im, 5 if 2.3 < lt < 3.5 else 0, t, 3)

def shot_kuro(t, lt):
    k = ease(lt/5.6)
    im = cam(HALL, 1.05 + 0.12*k, 650, 1300 - 100*k).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.3)
    blue_fire_glow(im, 540, 760, 380, 0.65)
    m = speaking("KURO", t)
    paste_kuro(im, kuro(m, blink(t, 1.2), int(t*10) % 8, "calm"), 1.2 + 0.05*k, 540, 760 + 8*math.sin(t*2.4))
    blue_embers(im, t, 540, 1000, 18, 15, 460)
    dust(im, t, 30, 16)
    return im

def shot_mural(t, lt):
    k = ease(lt/6.2)
    # pan across the mural from the left islands to the king
    view = cam(MURAL_SRC, 1.65, 640 + 460*k, 1050).convert("RGBA")
    # shard-blade light sweeping over the carving
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gx = 200 + 700*k
    gd.ellipse([gx - 340, 300, gx + 340, 1100], fill=(120, 230, 255, 60))
    view.alpha_composite(g.filter(ImageFilter.GaussianBlur(60)))
    dust(view, t, 30, 18)
    m = speaking("LYRA", t)
    paste_bust(view, lyra_bust("calm" if lt < 3.5 else "shocked", m, blink(t, 2.0), False), 0.8, 300, 1050)
    return view

def make_mural_src():
    src = Image.new("RGBA", (2200, 2600), (8, 20, 30, 255))
    d = ImageDraw.Draw(src)
    for y in range(0, 2600, 120):  # wall blocks above/below the mural
        off = 0 if (y // 120) % 2 else 90
        for x in range(-180 + off, 2200, 180):
            d.rectangle([x + 3, y + 3, x + 177, y + 117], fill=(20, 42, 54), outline=(10, 22, 30), width=4)
    src.alpha_composite(MURAL, (0, 380))
    return src
MURAL_SRC = make_mural_src()

def shot_crown(t, lt):
    k = ease(lt/6.0)
    # tight push-in on the cracked crown; the crack glows violet
    cx, cy = CROWN_XY[0], CROWN_XY[1] + 380
    im = cam(MURAL_SRC, 3.0 + 0.5*k, cx, cy + 150).convert("RGBA")
    pulse = 0.55 + 0.45*math.sin(t*4)
    if lt > 0.6:
        a = min(1, (lt - 0.6)/0.8)*pulse
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.ellipse([340, 120, 740, 620], fill=(170, 90, 255, int(110*a)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(50)))
    if lt < 1.4:
        return shake(im, 0, t)
    # Ren reacts in front (lower)
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 8, 20, 255)), 0.15)
    m = speaking("REN", t)
    paste_bust(im, ren_bust("shocked" if lt < 3.6 else "determined", m, blink(t, 0.7), int(t*4) % 8, True), 0.95, 540, 1120)
    if 1.4 <= lt < 1.6:
        d = ImageDraw.Draw(im)
        for i in range(12):
            a = i*math.pi/6; d.line([(540 + 360*math.cos(a), 960 + 360*math.sin(a)), (540 + 460*math.cos(a), 960 + 460*math.sin(a))], fill=(255, 255, 255), width=8)
    return im

def shot_glow(t, lt):
    p = ease(lt/5.6)
    im = cam(HALL_BLUR, 1.4 + 0.1*p, 650, 1200).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (2, 6, 14, 255)), 0.55)
    im.alpha_composite(light_rays(t, (110, 240, 255), 540, 760, int(30 + 60*p)))
    blue_fire_glow(im, 540, 760, 520, 0.4 + 0.6*p)
    if lt > 0.8: im.alpha_composite(SPEED[int(t*15) % 4])
    # blade held upright, rising and glowing harder
    bl = blade(1.0, round(min(1, 0.4 + 0.6*p), 1), 1.0)
    rot_paste(im, bl, 3*math.sin(t*6)*p, 540, 860 - 40*p)
    energy_bolts(im, t, 540, 330, 540 + 260*math.sin(t*3), 120, 2, 5)
    energy_bolts(im, t, 540, 330, 540 - 260*math.cos(t*2.6), 140, 2, 9)
    for i in range(3):
        q = ((lt*0.7 + i/3) % 1.0)
        light_ring(im, 540, 640, q)
    embers(im, t, 0.5, True, 1.4)
    if lt > 4.8: im = flash(im, (lt - 4.8)/0.8*0.7, (190, 250, 255))
    return shake(im, 2 + 8*p, t, 7)

def shot_hook(t, lt):
    k = ease(lt/5.4)
    im = cam(HALL_BLUR, 1.6, 650, 1150).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (2, 10, 22, 255)), 0.45)
    blue_fire_glow(im, 540, 780, 560, 0.7 + 0.2*math.sin(t*5))
    im.alpha_composite(light_rays(t, (120, 240, 255), 540, 1700, 40))
    m = speaking("REN", t)
    paste_bust(im, ren_bust("determined", m, blink(t, 0.2), int(t*5) % 8, True), 1.06 + 0.12*k, 540, 780)
    # cyan rim light on his face
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([340, 540, 740, 1060], fill=(110, 230, 255, 40))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    # small violet crown silhouette forming in the light (the memory begins)
    if lt > 3.4:
        a = min(1, (lt - 3.4)/0.8)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        cx, cy = 540, 230
        pts = [(cx - 110, cy + 60), (cx - 120, cy - 70), (cx - 70, cy - 5), (cx - 30, cy - 100), (cx, cy - 20), (cx + 30, cy - 100),
               (cx + 70, cy - 5), (cx + 120, cy - 70), (cx + 110, cy + 60)]
        d.polygon(pts, fill=(170, 100, 255, int(170*a)))
        d.line([(cx + 6, cy - 100), (cx - 14, cy - 40), (cx + 12, cy + 10), (cx - 4, cy + 60)], fill=(20, 10, 40, int(255*a)), width=8)
        im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(16))); im.alpha_composite(lay)
    embers(im, t, 0.5, True, 0.8)
    if lt > 4.8: im = flash(im, (lt - 4.8)/0.6, (235, 250, 255))
    return shake(im, 2, t, 15)

def shot_next(t, lt):
    im = cam(MURAL_SRC, 1.6, 1100, 860).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), min(0.74, 0.74*lt/0.3 if lt < 0.3 else 0.74))
    if lt < 0.4: im = flash(im, 1 - lt/0.4, (235, 250, 255))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, NEXT, 760, 100, (255, 255, 255), (170, 100, 255))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(120, 200, 255))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA — Ep %d" % (EP + 1), 970, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1070, 50, (255, 220, 150), sw=6)
    return im

SHOT_FN = {"title": shot_title, "land": shot_land, "lyra": shot_lyra, "ren_door": shot_ren_door, "kuro": shot_kuro,
           "mural": shot_mural, "crown": shot_crown, "glow": shot_glow, "hook": shot_hook, "next": shot_next}

def frame(t):
    for name, s, e in SHOTS:
        if s <= t < e: break
    im = SHOT_FN[name](t, t - s)
    if im.mode != "RGBA": im = im.convert("RGBA")
    im.alpha_composite(VIG)
    if t - s < 0.08 and name not in ("title", "next", "land"):
        im = flash(im, 0.45)
    if name not in ("title", "next"): draw_caption(im, t)
    return im.convert("RGB")

# ------------------------------------------------------------ audio (E minor, mysterious ruins -> rising awe)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(88)
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
    def choir(m, dur):   # soft "aah" pad: detuned sines with slow vibrato + formant-ish 2nd/3rd harmonics
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
    # --- part A (4 - GLOW_T): slow mysterious pads Em - C - Am - B, 4.5 s each, choir on top
    chords = [[40, 52, 55, 59], [36, 52, 55, 60], [45, 52, 57, 60], [47, 51, 54, 59]]
    t0, ci = 3.6, 0
    while t0 < GLOW_T:
        ch = chords[ci % 4]; dur = min(4.9, GLOW_T + 0.6 - t0)
        n = int(dur*SR)
        for k, m in enumerate(ch[1:]):
            add(choir(m, dur)*env(n, 1.2, 1.2), t0, pan=-0.5 + 0.5*k, vol=0.03*duck(t0 + 1))
        add(sine(note(ch[0]), dur)*env(n, 0.6, 1.0), t0, vol=0.09)
        t0 += 4.5; ci += 1
    # music-box-like arpeggio in the ruins
    r2 = np.random.RandomState(6); tt = 4.2; arp = [64, 67, 71, 74, 76, 79]
    while tt < GLOW_T - 0.5:
        m = arp[r2.randint(len(arp))]; n = int(1.4*SR); x = tv(n)
        add((np.sin(2*np.pi*note(m)*x) + 0.25*np.sin(2*np.pi*note(m)*4*x))*np.exp(-3.5*x), tt, pan=r2.uniform(-0.7, 0.7), vol=0.03*duck(tt))
        tt += r2.choice([0.5, 0.75, 0.75, 1.0])
    # distant heartbeat drum, slowly getting closer
    tt = 22.6
    while tt < GLOW_T:
        add(TAIKO, tt, vol=0.08 + 0.12*(tt - 22.6)/(GLOW_T - 22.6)); tt += 1.5 if tt < 34 else 0.75
    # --- door opening at 17.5: rune chimes + stone grind + boom
    for i in range(12):
        n = int(0.9*SR); x = tv(n)
        add(np.sin(2*np.pi*note(76 + (i % 6)*2)*x)*np.exp(-4*x), 15.5 + i*0.15, pan=-0.6 + 0.1*i, vol=0.05)
    n = int(1.4*SR); x = tv(n)
    add((lp_noise(1.4, 0.05, 0.03)*4 + 0.3*saw(46, 1.4, 6)*(1 + 0.5*np.sin(2*np.pi*11*x)))*env(n, 0.1, 0.4), 17.5, vol=0.22)
    n = int(2.0*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(45 + 70*np.exp(-8*x))/SR)*np.exp(-2.2*x), 18.7, vol=0.45)
    # Kestrel landing thud + creak
    n = int(1.2*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(50 + 60*np.exp(-12*x))/SR)*np.exp(-4*x) + 0.4*rs.randn(n)*np.exp(-14*x), 9.6, vol=0.35)
    # crown reveal sting (violet): low cluster + tremolo
    for m in (40, 41, 47):
        n = int(3.0*SR); x = tv(n)
        add(saw(note(m), 3.0, 6)*(0.7 + 0.3*np.sin(2*np.pi*7*x))*env(n, 0.05, 1.5), 35.0, pan=rs.uniform(-0.4, 0.4), vol=0.03)
    # --- part B (glow): riser into big E-major-ish swell, driving drums
    dur = 5.0; n = int(dur*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(120 + 800*(x/dur)**2)/SR)*(x/dur)*0.6, GLOW_T + 0.4, vol=0.08)
    add(whoosh(5.0, True)*(x/dur), GLOW_T + 0.4, vol=0.25)
    swell = [[40, 52, 56, 59, 64], [36, 52, 55, 60, 64], [38, 50, 54, 57, 62], [47, 51, 54, 59, 63]]
    t0 = GLOW_T
    for ci in range(3):
        ch = swell[ci % 4]; d_ = 3.6 if ci < 2 else 4.4; n = int(d_*SR)
        for k, m in enumerate(ch):
            s = (saw(note(m), d_, 6, 0.004) + saw(note(m), d_, 6, -0.004))*0.5*env(n, 0.3, 0.6)
            add(s, t0, pan=-0.5 + 0.25*k, vol=0.022*duck(t0 + 1))
        add(choir(ch[-1] + 12, d_)*env(n, 0.5, 0.8), t0, vol=0.02)
        t0 += d_
    beat = 0.5; tb = GLOW_T
    while tb < 51.2:
        add(TAIKO, tb, vol=0.22 if int((tb - GLOW_T)/beat) % 2 == 0 else 0.12, pan=rs.uniform(-0.2, 0.2)); tb += beat
    # energy crackle
    for i in range(30):
        n = int(0.05*SR); add(rs.randn(n)*np.exp(-60*tv(n)), GLOW_T + 0.8 + i*0.17, pan=rs.uniform(-0.7, 0.7), vol=0.08)
    # whiteout impact at 51.4
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 51.4, vol=0.6)
    for i, m in enumerate([52, 59, 64, 67, 71]):
        n = int(3.2*SR); add(saw(note(m), 3.2, 5)*np.exp(-1.0*tv(n))*env(n, 0.02, 0.5), 51.45, pan=-0.6 + 0.3*i, vol=0.05)
    # shot whooshes, opening boom, ambient wind
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        if name not in ("glow", "next"): add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.22)
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    add(lp_noise(TOTAL - 1, 0.015, 0.02)*1.4*env(int((TOTAL - 1)*SR), 2.0, 2.0), 0.5, vol=0.05)
    # water drips in the hall
    for i in range(14):
        n = int(0.3*SR); x = tv(n)
        add(np.sin(2*np.pi*(900 + 600*np.exp(-30*x))*x)*np.exp(-18*x), 10.5 + i*2.1 + rs.uniform(0, 0.8), pan=rs.uniform(-0.8, 0.8), vol=0.035)
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
