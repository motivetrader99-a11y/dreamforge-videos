"""Shared art kit for SKYFORGE SAGA teen Shorts (original designs from teens.md).
Characters are drawn at 2x supersampling on a 900x1400 bust canvas and downscaled."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
SS = 2
BW, BH = 900, 1600
OUT = (14, 12, 22)

@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(6, int(sz)))

def P(pts): return [(x*SS, y*SS) for x, y in pts]
def B(box): return [v*SS for v in box]

def poly(d, pts, fill, ow=5, outline=OUT):
    d.polygon(P(pts), fill=fill, outline=outline if ow else None, width=ow*SS if ow else 0)

def ell(d, box, fill, ow=5, outline=OUT):
    d.ellipse(B(box), fill=fill, outline=outline if ow else None, width=ow*SS if ow else 0)

def new_layer(): return Image.new("RGBA", (BW*SS, BH*SS), (0, 0, 0, 0))

def finish(im): return im.resize((BW, BH), Image.LANCZOS)

# ---------------------------------------------------------------- REN ASAKA
SKIN, SKIN_SH = (255, 226, 204), (232, 180, 168)
HAIR, HAIR_HL = (24, 24, 36), (70, 80, 120)
COAT, COAT_SH, COAT_HL = (38, 58, 118), (24, 36, 82), (70, 96, 168)
SCARF, SCARF_SH = (214, 40, 52), (150, 24, 40)
IRIS, IRIS_D = (226, 146, 54), (140, 62, 26)

def scarf_tail(phase):
    a = math.sin(phase*2*math.pi); b = math.sin(phase*2*math.pi + 1.3)
    return [(340, 730), (230, 780+18*a), (120, 810+30*b), (40, 860+40*a), (70, 905+30*b),
            (170, 875+22*a), (270, 835+14*b), (350, 790)]

def head_shape():
    return ([300, 200, 600, 560],
            [(302, 410), (316, 535), (372, 624), (450, 666), (528, 624), (584, 535), (598, 410)])

@lru_cache(None)
def ren_bust(expr="calm", mouth=0, blink=False, phase=0, hilt=True):
    im = new_layer(); d = ImageDraw.Draw(im)
    # broken sword hilt over right shoulder (behind body)
    if hilt: _hilt(d)
    _ren_body(im, d, expr, mouth, blink, phase)
    return finish(im)

def _hilt(d):
    poly(d, [(630, 570), (668, 558), (700, 790), (662, 802)], (90, 70, 60))
    poly(d, [(600, 580), (708, 542), (716, 566), (608, 606)], (170, 150, 110))
    ell(d, [632, 518, 676, 562], (0, 200, 230))

def _ren_body(im, d, expr, mouth, blink, phase):
    # back hair mass
    cx, cy = 450, 400; pts = []
    rnd = random.Random(3)
    for i in range(23):
        a = math.radians(-25 + i*230/22)
        r = (300 if i % 2 == 0 else 225) + rnd.randint(-15, 15)
        pts.append((cx - r*math.cos(a), cy - r*math.sin(a)*0.95))
    pts = [(cx+150, 600), (cx+215, 660), (cx+205, 560), (cx+262, 600), (cx+250, 500)] + pts[::-1] + [(cx-250, 500), (cx-262, 600), (cx-205, 560), (cx-215, 660), (cx-150, 600)]
    poly(d, pts, HAIR)
    # body / coat
    poly(d, [(60, 1600), (100, 890), (240, 780), (660, 780), (800, 890), (840, 1600)], COAT)
    poly(d, [(560, 800), (660, 780), (800, 890), (840, 1600), (640, 1600)], COAT_SH, ow=0)
    poly(d, [(100, 890), (240, 780), (270, 800), (140, 920)], COAT_HL, ow=0)
    poly(d, [(370, 780), (530, 780), (450, 1010)], (52, 52, 64))
    d.line(P([(450, 1010), (450, 1600)]), fill=OUT, width=5*SS)
    for y in (1150, 1190):
        ell(d, [440, y, 462, y+22], (200, 170, 90), ow=3)
    # strap
    poly(d, [(250, 790), (300, 780), (760, 1600), (690, 1600)], (112, 72, 42))
    ell(d, [470, 1030, 530, 1090], (190, 160, 80), ow=4)
    # high collar
    poly(d, [(300, 790), (360, 690), (400, 790)], COAT_HL)
    poly(d, [(600, 790), (540, 690), (500, 790)], COAT)
    # neck
    poly(d, [(398, 520), (502, 520), (506, 730), (394, 730)], SKIN)
    poly(d, [(398, 530), (502, 530), (502, 610), (398, 580)], SKIN_SH, ow=0)
    # scarf wrap + tail
    poly(d, scarf_tail(phase), SCARF)
    poly(d, [(318, 690), (582, 690), (604, 780), (296, 780)], SCARF)
    poly(d, [(470, 692), (582, 690), (604, 780), (500, 780)], SCARF_SH, ow=0)
    for x in (360, 420, 540):
        d.line(P([(x, 700), (x-10, 770)]), fill=SCARF_SH, width=4*SS)
    # ears
    ell(d, [278, 440, 318, 520], SKIN); ell(d, [582, 440, 622, 520], SKIN)
    # head
    cran, jaw = head_shape()
    hm = Image.new("L", im.size, 0); hd = ImageDraw.Draw(hm)
    hd.ellipse(B(cran), fill=255); hd.polygon(P(jaw), fill=255)
    skin = Image.new("RGBA", im.size, SKIN + (255,))
    im.paste(skin, (0, 0), hm)
    sh = Image.new("L", im.size, 0); sd = ImageDraw.Draw(sh)
    sd.polygon(P([(540, 200), (620, 300), (620, 560), (528, 640), (450, 668), (560, 520), (575, 380)]), fill=255)
    sd.polygon(P([(290, 300), (610, 300), (610, 455), (560, 420), (520, 448), (470, 415), (420, 450), (370, 420), (330, 452), (290, 430)]), fill=255)
    sh = ImageChops.multiply(sh, hm)
    im.paste(Image.new("RGBA", im.size, SKIN_SH + (255,)), (0, 0), sh)
    # outline head
    d = ImageDraw.Draw(im)
    d.line(P(jaw), fill=OUT, width=5*SS, joint="curve")
    # blush (soft)
    if expr == "calm":
        for ex in (360, 540):
            ell(d, [ex-30, 560, ex+30, 580], (255, 170, 170), ow=0)
    # eyes
    for side, ex in ((-1, 370), (1, 530)):
        eye(im, ex, 478, side, expr, blink)
    d = ImageDraw.Draw(im)
    # nose
    d.line(P([(458, 545), (450, 572), (462, 574)]), fill=(190, 130, 120), width=4*SS)
    # mouth
    mouth_draw(d, expr, mouth)
    # bangs
    bangs = [(285, 250, 300, 470), (330, 240, 335, 455), (375, 240, 380, 420), (420, 235, 425, 395),
             (470, 235, 470, 405), (515, 240, 520, 425), (560, 245, 568, 450), (605, 255, 602, 475)]
    xs = [280, 315, 360, 405, 445, 495, 540, 585, 622]
    for i, (_, _, tx, ty) in enumerate(bangs):
        col = (236, 238, 248) if i == 2 else HAIR
        poly(d, [(xs[i]-6, 230), (xs[i+1]+6, 230), (tx + (8 if i < 4 else -8), ty)], col, ow=4)
    # top hair cap over cranium
    poly(d, [(286, 300), (300, 230), (360, 180), (450, 160), (540, 180), (600, 230), (614, 300), (600, 262), (450, 232), (300, 262)], HAIR, ow=4)
    # white streak continues up
    poly(d, [(360, 236), (400, 236), (420, 175), (380, 180)], (236, 238, 248), ow=4)
    # sheen
    poly(d, [(330, 210), (380, 192), (440, 186), (500, 190), (560, 205), (540, 214), (500, 204), (440, 200), (380, 206)], HAIR_HL, ow=0)
    # side locks
    poly(d, [(280, 300), (318, 330), (312, 560), (292, 610), (276, 480)], HAIR, ow=4)
    poly(d, [(620, 300), (582, 330), (588, 560), (608, 610), (624, 480)], HAIR, ow=4)
    # brows
    brows(d, expr)

def eye(im, ex, ey, side, expr, blink):
    d = ImageDraw.Draw(im)
    if blink:
        d.line(P([(ex-52, ey+8), (ex, ey+16), (ex+52, ey+8)]), fill=OUT, width=7*SS, joint="curve")
        return
    hgt = {"calm": 40, "shocked": 50, "determined": 32}[expr]
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
    m = Image.new("L", im.size, 0); md = ImageDraw.Draw(m)
    sclera = [(ex-54, ey), (ex-30, ey-hgt), (ex+30, ey-hgt-4*side), (ex+56, ey-4), (ex+30, ey+hgt*0.9), (ex-30, ey+hgt*0.9)]
    md.polygon(P(sclera), fill=255)
    ld.polygon(P(sclera), fill=(255, 255, 255))
    ir = 22 if expr == "shocked" else 32
    ld.ellipse(B([ex-ir, ey-44, ex+ir, ey+44]), fill=IRIS)
    ld.ellipse(B([ex-ir, ey-44, ex+ir, ey+4]), fill=IRIS_D)
    ld.ellipse(B([ex-ir*0.9, ey-10, ex+ir*0.9, ey+44]), fill=IRIS)
    ld.ellipse(B([ex-ir*0.45, ey-18, ex+ir*0.45, ey+18]), fill=(50, 20, 10))
    ld.ellipse(B([ex-ir*0.7, ey+14, ex+ir*0.7, ey+40]), fill=(250, 196, 110))
    ld.ellipse(B([ex-ir*0.85, ey-36, ex-ir*0.15, ey-12]), fill=(255, 255, 255))
    ld.ellipse(B([ex+ir*0.25, ey+16, ex+ir*0.55, ey+28]), fill=(255, 255, 255))
    if expr == "determined":
        ld.polygon(P([(ex-60, ey-60), (ex+60, ey-60), (ex+60, ey-hgt+14 + (10 if side < 0 else -10)*-1), (ex-60, ey-hgt+14 + (10 if side < 0 else -10))]), fill=SKIN_SH)
    im.paste(layer, (0, 0), ImageChops.multiply(m, layer.split()[3]))
    d = ImageDraw.Draw(im)
    # upper lash (thick) with outer flick
    o = ex + 64*side
    top = [(ex-54*side*-1 if False else ex - 58*side, ey+2), (ex - 30*side, ey-hgt-6), (ex + 30*side, ey-hgt-8), (o, ey-6), (o + 10*side, ey+4),
           (ex + 44*side, ey-hgt+6), (ex - 26*side, ey-hgt+4), (ex - 50*side, ey+6)]
    if expr == "determined":
        top = [(x, y + (12 if (x - ex)*side < 0 else 4)) for x, y in top]
    d.polygon(P(top), fill=OUT)
    d.line(P([(ex-30, ey+hgt*0.9+2), (ex+30, ey+hgt*0.9+2)]), fill=(120, 70, 70), width=3*SS)

def brows(d, expr):
    for side, ex in ((-1, 370), (1, 530)):
        if expr == "calm":
            pts = [(ex-44*side*-1 - 0, 0)]
            inner, outer = (ex - 40*side, 408), (ex + 46*side, 400)
        elif expr == "shocked":
            inner, outer = (ex - 40*side, 380), (ex + 46*side, 384)
        else:
            inner, outer = (ex - 40*side, 420), (ex + 46*side, 392)
        poly(d, [inner, outer, (outer[0], outer[1]+10), (inner[0], inner[1]+12)], (40, 30, 34), ow=0)

def mouth_draw(d, expr, mouth):
    mx, my = 450, 616
    if mouth == 0:
        if expr == "calm":
            d.line(P([(mx-26, my), (mx, my+5), (mx+26, my-2)]), fill=(110, 50, 50), width=4*SS)
        elif expr == "shocked":
            ell(d, [mx-12, my-8, mx+12, my+12], (110, 30, 40), ow=3)
        else:
            d.line(P([(mx-30, my+2), (mx+30, my-2)]), fill=(110, 50, 50), width=5*SS)
    else:
        w = {1: 20, 2: 30}[mouth] + (8 if expr == "shocked" else 0)
        h = {1: 14, 2: 28}[mouth] + (10 if expr == "shocked" else 0)
        if expr == "determined":
            poly(d, [(mx-w-6, my-h*0.3), (mx+w+6, my-h*0.4), (mx+w*0.6, my+h*0.7), (mx-w*0.6, my+h*0.7)], (110, 30, 40), ow=3)
            d.rectangle(B([mx-w+2, my-h*0.3, mx+w-2, my-h*0.3+6]), fill=(255, 255, 255))
        else:
            ell(d, [mx-w, my-h*0.6, mx+w, my+h], (110, 30, 40), ow=3)
            ell(d, [mx-w*0.6, my+h*0.2, mx+w*0.6, my+h*0.95], (230, 120, 130), ow=0)

# ---------------------------------------------------------------- HOLLOW KING
ARM, ARM_SH, ARM_HL = (66, 60, 92), (38, 34, 58), (128, 122, 162)

@lru_cache(None)
def hollow_king_base():
    im = new_layer(); d = ImageDraw.Draw(im)
    # cape
    poly(d, [(20, 1600), (80, 980), (250, 860), (650, 860), (820, 980), (880, 1600)], (34, 18, 50))
    # chest plate
    poly(d, [(230, 860), (670, 860), (700, 1600), (200, 1600)], ARM)
    poly(d, [(450, 860), (670, 860), (700, 1600), (450, 1600)], ARM_SH, ow=0)
    poly(d, [(450, 900), (560, 960), (530, 1140), (450, 1200), (370, 1140), (340, 960)], (52, 46, 74))
    ell(d, [418, 1000, 482, 1080], (200, 120, 255), ow=4)
    for y in (1240, 1320):
        d.line(P([(240, y), (450, y+40), (660, y)]), fill=OUT, width=5*SS)
    # pauldrons
    for s in (-1, 1):
        cx = 450 + s*250
        poly(d, [(cx - 170*s, 1000), (cx - 200*s, 900), (cx - 110*s, 820), (cx + 40*s, 800), (cx + 170*s, 860),
                 (cx + 150*s, 950), (cx + 60*s, 980)], ARM)
        poly(d, [(cx - 110*s, 820), (cx + 40*s, 800), (cx + 90*s, 690), (cx - 10*s, 770)], ARM_HL)  # spike
        d.line(P([(cx - 170*s, 960), (cx + 140*s, 900)]), fill=ARM_HL, width=6*SS)
    # gorget
    poly(d, [(340, 700), (560, 700), (600, 870), (300, 870)], ARM_SH)
    # helm
    poly(d, [(300, 420), (330, 290), (450, 230), (570, 290), (600, 420), (580, 640), (450, 720), (320, 640)], ARM)
    poly(d, [(450, 230), (570, 290), (600, 420), (580, 640), (450, 720)], ARM_SH, ow=0)
    d.line(P([(300, 420), (330, 290), (450, 230), (570, 290), (600, 420), (580, 640), (450, 720), (320, 640), (300, 420)]), fill=OUT, width=5*SS)
    d.line(P([(450, 232), (450, 360)]), fill=ARM_HL, width=5*SS)
    # face void
    poly(d, [(360, 400), (540, 400), (560, 520), (520, 640), (450, 676), (380, 640), (340, 520)], (8, 4, 14))
    # crown (empty, cracked; one spike broken)
    gold, gold_sh = (176, 156, 96), (120, 100, 60)
    poly(d, [(300, 300), (600, 300), (590, 350), (310, 350)], gold)
    spikes = [(320, 300, 300, 170), (380, 300, 375, 130), (450, 300, 450, 90), (520, 300, 522, 200), (580, 300, 600, 170)]
    for i, (x, y, tx, ty) in enumerate(spikes):
        if i == 3:  # broken spike: jagged top
            poly(d, [(x-28, y), (x+28, y), (x+24, 240), (x+6, 252), (x-4, 226), (x-20, 246)], gold)
        else:
            poly(d, [(x-28, y), (x+28, y), (tx, ty)], gold)
        poly(d, [(x, y), (x+26, y), (tx, ty+10)], gold_sh, ow=0)
    d.line(P([(440, 120), (455, 180), (438, 230), (458, 300), (446, 350)]), fill=OUT, width=6*SS)
    ell(d, [440, 316, 460, 336], (150, 140, 170), ow=3)
    return finish(im)

@lru_cache(None)
def hollow_king_glow(level):  # level 0..4
    g = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    k = 0.55 + 0.12*level
    d.ellipse([370, 430, 530, 650], fill=(150, 60, 230, int(200*k)))
    g = g.filter(ImageFilter.GaussianBlur(40))
    d = ImageDraw.Draw(g)
    for ex in (405, 495):
        d.polygon([(ex-34, 520), (ex+30, 508), (ex+34, 524), (ex-30, 534)], fill=(235, 200, 255, 255))
    core = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); cd = ImageDraw.Draw(core)
    for ex in (405, 495):
        cd.ellipse([ex-60, 480, ex+60, 560], fill=(200, 120, 255, int(160*k)))
    core = core.filter(ImageFilter.GaussianBlur(18))
    g.alpha_composite(core)
    return g

def hollow_king(level):
    im = hollow_king_base().copy()
    im.alpha_composite(hollow_king_glow(level))
    return im

# ---------------------------------------------------------------- SKY-SHARD
@lru_cache(None)
def shard(size=300):
    s = size; im = Image.new("RGBA", (s*2, s*2), (0, 0, 0, 0))
    g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([s*0.45, s*0.3, s*1.55, s*1.7], fill=(60, 230, 255, 150))
    g = g.filter(ImageFilter.GaussianBlur(s*0.18)); im.alpha_composite(g)
    d = ImageDraw.Draw(im); c = s
    body = [(c, c-s*0.62), (c+s*0.2, c-s*0.2), (c+s*0.16, c+s*0.45), (c, c+s*0.6), (c-s*0.18, c+s*0.42), (c-s*0.21, c-s*0.25)]
    d.polygon(body, fill=(120, 240, 255), outline=(20, 70, 110), width=max(2, s//60))
    d.polygon([(c, c-s*0.62), (c+s*0.2, c-s*0.2), (c+s*0.16, c+s*0.45), (c, c+s*0.6), (c+s*0.03, c-s*0.1)], fill=(60, 180, 230))
    d.polygon([(c-s*0.12, c-s*0.2), (c-s*0.04, c-s*0.45), (c-s*0.02, c+s*0.1), (c-s*0.1, c+s*0.25)], fill=(225, 255, 255))
    # small side crystal
    d.polygon([(c+s*0.18, c+s*0.2), (c+s*0.42, c-s*0.05), (c+s*0.38, c+s*0.32), (c+s*0.18, c+s*0.45)], fill=(90, 210, 245), outline=(20, 70, 110), width=max(2, s//80))
    return im

# ---------------------------------------------------------------- CAPTAIN MIRE
MIRE_ARM, MIRE_SH, MIRE_HL = (84, 92, 104), (52, 58, 70), (146, 156, 170)
MIRE_CLOAK, MIRE_CLOAK_SH = (128, 44, 36), (88, 28, 26)
MIRE_SKIN, MIRE_SKIN_SH = (222, 178, 146), (186, 136, 112)

def _mire_eye(d, ex, ey, side, blink):
    if blink:
        d.line(P([(ex-46, ey+4), (ex, ey+10), (ex+46, ey+2)]), fill=OUT, width=7*SS); return
    sclera = [(ex - 48*side, ey+6), (ex - 18*side, ey-20), (ex + 30*side, ey-24), (ex + 52*side, ey-10), (ex + 26*side, ey+14), (ex - 20*side, ey+16)]
    poly(d, sclera, (250, 248, 240), ow=0)
    ell(d, [ex-20, ey-24, ex+20, ey+16], (214, 170, 60), ow=0)
    ell(d, [ex-20, ey-24, ex+20, ey-6], (150, 100, 30), ow=0)
    ell(d, [ex-7, ey-12, ex+7, ey+6], (30, 16, 10), ow=0)
    ell(d, [ex-15, ey-20, ex-3, ey-9], (255, 255, 255), ow=0)
    # heavy angled upper lid
    poly(d, [(ex - 54*side, ey+6), (ex - 18*side, ey-26), (ex + 34*side, ey-32), (ex + 64*side, ey-14), (ex + 50*side, ey-10),
             (ex + 28*side, ey-22), (ex - 18*side, ey-16), (ex - 46*side, ey+8)], OUT, ow=0)
    d.line(P([(ex - 20*side, ey+18), (ex + 26*side, ey+16)]), fill=(120, 80, 70), width=3*SS)

@lru_cache(None)
def mire_bust(mouth=0, blink=False):
    im = new_layer(); d = ImageDraw.Draw(im)
    # double-bladed spear behind (shaft + both blade heads)
    poly(d, [(80, 1560), (110, 1580), (840, 170), (810, 150)], (60, 46, 40))
    for (bx, by, dx, dy) in ((826, 160, 1, -1), (95, 1570, -1, 1)):
        poly(d, [(bx - 34*dx, by - 10*dy), (bx + 10*dx, by + 30*dy), (bx + 90*dx, by - 170*dy*-1 if False else by + 30*dy - 0),
                 ], (0, 0, 0, 0), ow=0)
    top = [(790, 196), (850, 150), (900, 20), (880, 120), (870, 190), (826, 232)]
    poly(d, top, (196, 206, 218)); poly(d, [(850, 150), (900, 20), (872, 160)], (150, 160, 176), ow=0)
    poly(d, [(770, 220), (840, 250), (848, 236), (778, 204)], MIRE_CLOAK, ow=3)
    # cloak / shoulders
    poly(d, [(40, 1600), (90, 900), (250, 790), (650, 790), (810, 900), (860, 1600)], MIRE_CLOAK)
    poly(d, [(520, 790), (650, 790), (810, 900), (860, 1600), (600, 1600)], MIRE_CLOAK_SH, ow=0)
    # breastplate
    poly(d, [(250, 850), (650, 850), (690, 1600), (210, 1600)], MIRE_ARM)
    poly(d, [(450, 850), (650, 850), (690, 1600), (450, 1600)], MIRE_SH, ow=0)
    poly(d, [(450, 880), (600, 960), (560, 1200), (450, 1260), (340, 1200), (300, 960)], MIRE_HL)
    poly(d, [(450, 880), (600, 960), (560, 1200), (450, 1260)], MIRE_ARM, ow=0)
    d.line(P([(450, 880), (450, 1260)]), fill=OUT, width=4*SS)
    # battle scars on the armor (gouges)
    for a, b in (((330, 990), (430, 1120)), ((350, 1010), (440, 1140)), ((520, 1250), (640, 1180)), ((600, 1000), (560, 1060))):
        d.line(P([a, b]), fill=(30, 32, 40), width=6*SS); d.line(P([(a[0]+6, a[1]-6), (b[0]+6, b[1]-6)]), fill=(190, 200, 214), width=2*SS)
    ell(d, [420, 1290, 480, 1350], (170, 90, 255), ow=4)  # violet emblem
    # pauldrons with layered plates
    for s in (-1, 1):
        cx = 450 + s*260
        for k, yy in enumerate((860, 920, 980)):
            poly(d, [(cx - 150*s, yy + 40), (cx - 120*s, yy - 50), (cx + 60*s, yy - 70), (cx + 170*s, yy), (cx + 150*s, yy + 60)],
                 MIRE_ARM if k % 2 == 0 else MIRE_SH)
        d.line(P([(cx - 110*s, 840), (cx + 120*s, 820)]), fill=MIRE_HL, width=5*SS)
    # gorget
    poly(d, [(340, 680), (560, 680), (610, 860), (290, 860)], MIRE_SH)
    poly(d, [(340, 680), (450, 680), (450, 860), (290, 860)], MIRE_ARM, ow=0)
    d.line(P([(320, 770), (580, 770)]), fill=OUT, width=4*SS)
    # neck + head
    poly(d, [(400, 560), (500, 560), (504, 690), (396, 690)], MIRE_SKIN_SH)
    jaw = [(318, 420), (326, 540), (380, 630), (450, 662), (520, 630), (574, 540), (582, 420)]
    ell(d, [318, 250, 582, 560], MIRE_SKIN, ow=0); poly(d, jaw, MIRE_SKIN, ow=0)
    poly(d, [(520, 300), (590, 420), (574, 540), (520, 630), (470, 655), (548, 520), (556, 400)], MIRE_SKIN_SH, ow=0)
    d.line(P(jaw), fill=OUT, width=5*SS, joint="curve")
    d.line(P([(318, 420), (318, 360)]), fill=OUT, width=5*SS); d.line(P([(582, 420), (582, 360)]), fill=OUT, width=5*SS)
    # eyes, brows (stern), nose
    for side, ex in ((-1, 382), (1, 518)):
        _mire_eye(d, ex, 470, side, blink)
        poly(d, [(ex - 52*side, 410), (ex + 50*side, 432), (ex + 50*side, 446), (ex - 52*side, 426)], (60, 60, 70), ow=0)
    d.line(P([(454, 500), (446, 556), (460, 560)]), fill=(150, 100, 86), width=4*SS)
    # mouth
    mx, my = 450, 604
    if mouth == 0:
        d.line(P([(mx-34, my+4), (mx+30, my)]), fill=(100, 50, 46), width=5*SS)
    else:
        w, h = (22, 12) if mouth == 1 else (28, 24)
        poly(d, [(mx-w-6, my-h*0.3), (mx+w+4, my-h*0.4), (mx+w*0.6, my+h*0.7), (mx-w*0.6, my+h*0.7)], (96, 28, 34), ow=3)
        d.rectangle(B([mx-w+4, my-h*0.3, mx+w-4, my-h*0.3+6]), fill=(245, 245, 245))
    # helm: open face, swept-back horns, cheek guards
    poly(d, [(300, 420), (306, 310), (360, 236), (450, 210), (540, 236), (594, 310), (600, 420), (566, 380), (540, 318), (450, 300), (360, 318), (334, 380)], MIRE_ARM)
    poly(d, [(450, 210), (540, 236), (594, 310), (600, 420), (566, 380), (540, 318), (450, 300)], MIRE_SH, ow=0)
    d.line(P([(300, 420), (306, 310), (360, 236), (450, 210), (540, 236), (594, 310), (600, 420)]), fill=OUT, width=5*SS)
    poly(d, [(360, 318), (450, 300), (540, 318), (548, 342), (450, 326), (352, 342)], MIRE_HL, ow=3)  # brow band
    for s in (-1, 1):
        poly(d, [(450 + 150*s, 330), (450 + 158*s, 470), (450 + 120*s, 560), (450 + 136*s, 450), (450 + 128*s, 360)], MIRE_ARM, ow=4)
        poly(d, [(450 + 120*s, 270), (450 + 230*s, 200), (450 + 330*s, 90), (450 + 250*s, 230), (450 + 150*s, 310)], MIRE_HL, ow=4)
    # helm scar (deep diagonal gouge)
    d.line(P([(392, 240), (430, 310)]), fill=(24, 24, 32), width=7*SS)
    # ash-grey fringe peeking out
    for x in (366, 404, 440):
        poly(d, [(x-16, 340), (x+22, 340), (x+4, 392)], (170, 172, 180), ow=3)
    return finish(im)

# ---------------------------------------------------------------- REN'S BLADE
def blade_img(length_frac=1.0, broken=False, glow=1.0, scale=1.0):
    """vertical sword on a 260x1100 canvas, hilt at the bottom. broken=True draws the snapped half-blade.
    length_frac (0..1) grows the cyan shard-light blade beyond the break when not broken."""
    w, h = 260, 1100
    im = Image.new("RGBA", (w*SS, h*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = w/2; guard_y = 860; brk = 560; tip = 60
    if not broken and length_frac > 0:
        top = brk - (brk - tip)*length_frac
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.polygon(P([(cx-54, guard_y), (cx+54, guard_y), (cx+50, top+60), (cx, top-30), (cx-50, top+60)]), fill=(60, 220, 255, int(170*glow)))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(26*SS)))
        d = ImageDraw.Draw(im)
        # crystal half
        poly(d, [(cx-26, brk+8), (cx+26, brk-6), (cx+24, top+40), (cx, top), (cx-24, top+40)], (130, 240, 255), ow=4, outline=(20, 70, 110))
        poly(d, [(cx, brk), (cx+26, brk-6), (cx+24, top+40), (cx, top)], (70, 190, 236), ow=0)
        poly(d, [(cx-14, brk-10), (cx-6, brk-10), (cx-6, top+60), (cx-12, top+70)], (230, 255, 255), ow=0)
    # steel lower half
    poly(d, [(cx-28, guard_y), (cx+28, guard_y), (cx+26, brk-6), (cx+10, brk+14), (cx-2, brk-8), (cx-14, brk+10), (cx-26, brk+4)], (196, 204, 216), ow=4)
    poly(d, [(cx, guard_y), (cx+28, guard_y), (cx+26, brk-6), (cx+10, brk+14), (cx, brk)], (140, 150, 168), ow=0)
    d.line(P([(cx, guard_y-10), (cx, brk+20)]), fill=(110, 118, 134), width=3*SS)
    # crack lines glowing
    crack_col = (90, 230, 255) if not broken else (60, 60, 74)
    d.line(P([(cx-6, brk+10), (cx+6, brk+80), (cx-8, brk+150), (cx+4, brk+210)]), fill=crack_col, width=4*SS)
    d.line(P([(cx+6, brk+80), (cx+18, brk+120)]), fill=crack_col, width=3*SS)
    # guard with shard socket
    poly(d, [(cx-110, guard_y-10), (cx+110, guard_y-10), (cx+124, guard_y+18), (cx+90, guard_y+28), (cx-90, guard_y+28), (cx-124, guard_y+18)], (170, 140, 90), ow=4)
    ell(d, [cx-26, guard_y-20, cx+26, guard_y+34], (90, 230, 255) if not broken else (60, 70, 90), ow=4)
    # grip + pommel
    poly(d, [(cx-20, guard_y+28), (cx+20, guard_y+28), (cx+18, 1040), (cx-18, 1040)], (90, 60, 50), ow=4)
    for y in range(guard_y+44, 1040, 26):
        d.line(P([(cx-18, y), (cx+18, y+12)]), fill=(60, 40, 34), width=4*SS)
    ell(d, [cx-30, 1030, cx+30, 1090], (170, 140, 90), ow=4)
    out = im.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    return out

# ---------------------------------------------------------------- HOLLOW SOLDIER (Ep 3+)
SOL_ARM, SOL_SH, SOL_HL = (58, 54, 78), (34, 30, 50), (112, 106, 140)
SOL_SMOKE = (20, 10, 32)

@lru_cache(None)
def hollow_soldier(glow=1.0, phase=0):
    """full-figure armored shadow on a 420x820 canvas (feet = smoke at the bottom). phase 0..7 animates the smoke."""
    w, h = 420, 820
    im = Image.new("RGBA", (w*SS, h*SS), (0, 0, 0, 0))
    # violet aura
    g = Image.new("RGBA", im.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse(B([60, 120, 360, 760]), fill=(120, 50, 200, int(90*glow)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40*SS)))
    d = ImageDraw.Draw(im)
    a = phase/8*2*math.pi
    # smoky lower body (no legs)
    smoke = [(120, 470), (300, 470), (320, 600), (300 + 14*math.sin(a), 700), (260, 760 + 20*math.sin(a + 1)), (230, 720),
             (205, 800 + 14*math.sin(a + 2)), (180, 724), (150, 770 + 18*math.sin(a + 3)), (128, 690), (100 + 12*math.sin(a), 600)]
    poly(d, smoke, SOL_SMOKE, ow=4)
    for k in range(3):
        y = 560 + k*60
        d.line(P([(140, y), (210, y + 14*math.sin(a + k)), (280, y)]), fill=(60, 30, 90), width=4*SS)
    # shadow arms
    poly(d, [(92, 300), (60, 470), (78, 560), (112, 556), (128, 400)], SOL_SMOKE, ow=4)
    poly(d, [(328, 300), (370, 450), (352, 540), (318, 536), (296, 400)], SOL_SMOKE, ow=4)
    # shadow staff (violet crystal tip) in the right hand
    poly(d, [(330, 120), (344, 120), (348, 760), (334, 760)], (40, 30, 50), ow=3)
    poly(d, [(337, 40), (358, 90), (337, 140), (316, 90)], (190, 120, 255), ow=4)
    # breastplate
    poly(d, [(120, 260), (300, 260), (316, 480), (210, 520), (104, 480)], SOL_ARM)
    poly(d, [(210, 260), (300, 260), (316, 480), (210, 520)], SOL_SH, ow=0)
    d.line(P([(120, 260), (300, 260), (316, 480), (210, 520), (104, 480), (120, 260)]), fill=OUT, width=4*SS)
    d.line(P([(130, 360), (210, 390), (296, 360)]), fill=OUT, width=4*SS)
    d.line(P([(150, 300), (190, 310)]), fill=SOL_HL, width=4*SS)
    ell(d, [196, 410, 224, 438], (190, 120, 255), ow=3)
    # pauldrons
    for s in (-1, 1):
        cx = 210 + s*110
        poly(d, [(cx - 70*s, 300), (cx - 50*s, 240), (cx + 30*s, 226), (cx + 70*s, 260), (cx + 62*s, 320), (cx, 330)], SOL_ARM, ow=4)
        d.line(P([(cx - 40*s, 256), (cx + 40*s, 246)]), fill=SOL_HL, width=4*SS)
    # helm: tall bucket helm with a T-visor and a fin crest
    poly(d, [(206, 60), (222, 60), (240, 150), (188, 150)], SOL_HL, ow=4)  # fin
    poly(d, [(146, 140), (166, 100), (214, 86), (262, 100), (282, 140), (284, 250), (214, 272), (144, 250)], SOL_ARM)
    poly(d, [(214, 86), (262, 100), (282, 140), (284, 250), (214, 272)], SOL_SH, ow=0)
    d.line(P([(146, 140), (166, 100), (214, 86), (262, 100), (282, 140), (284, 250), (214, 272), (144, 250), (146, 140)]), fill=OUT, width=4*SS)
    # glowing T visor
    vg = Image.new("RGBA", im.size, (0, 0, 0, 0)); vd = ImageDraw.Draw(vg)
    vd.rectangle(B([160, 160, 268, 196]), fill=(190, 110, 255, int(220*glow))); vd.rectangle(B([200, 160, 228, 250]), fill=(190, 110, 255, int(220*glow)))
    im.alpha_composite(vg.filter(ImageFilter.GaussianBlur(10*SS)))
    d = ImageDraw.Draw(im)
    poly(d, [(166, 168), (262, 168), (262, 188), (226, 188), (226, 244), (202, 244), (202, 188), (166, 188)], (240, 210, 255), ow=0)
    return im.resize((w, h), Image.LANCZOS)

@lru_cache(None)
def soldier_helm(size=160):
    """a dropped, empty soldier helm (for when the shadow scatters)."""
    im = Image.new("RGBA", (300*SS, 260*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    def Q(pts): return [((x - 70)*SS, (y - 70)*SS) for x, y in pts]
    pts = [(146, 140), (166, 100), (214, 86), (262, 100), (282, 140), (284, 250), (214, 272), (144, 250)]
    d.polygon(Q(pts), fill=SOL_ARM, outline=OUT, width=4*SS)
    d.polygon(Q([(214, 86), (262, 100), (282, 140), (284, 250), (214, 272)]), fill=SOL_SH)
    d.polygon(Q([(206, 60), (222, 60), (240, 150), (188, 150)]), fill=SOL_HL, outline=OUT, width=4*SS)
    d.polygon(Q([(166, 168), (262, 168), (262, 188), (226, 188), (226, 244), (202, 244), (202, 188), (166, 188)]), fill=(16, 10, 24))
    im = im.resize((300, 260), Image.LANCZOS)
    return im.resize((int(300*size/160), int(260*size/160)), Image.LANCZOS)

# ---------------------------------------------------------------- AIRSHIP SILHOUETTE (original)
@lru_cache(None)
def airship(lit=1.0, prop=0):
    w, h = 900, 520
    im = Image.new("RGBA", (w*SS, h*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    dark, mid = (30, 34, 52), (52, 60, 84)
    # envelope
    poly(d, [(110, 150), (230, 70), (560, 50), (760, 100), (840, 170), (760, 240), (560, 280), (230, 270), (110, 200)], mid)
    poly(d, [(110, 190), (230, 270), (560, 280), (760, 240), (840, 170), (760, 200), (560, 230), (230, 220)], dark, ow=0)
    for x in (300, 430, 560, 680):
        d.line(P([(x, 62), (x - 6, 276)]), fill=(24, 26, 40), width=4*SS)
    # swept tail fins (wing-like)
    poly(d, [(150, 140), (30, 60), (70, 150), (20, 230), (150, 200)], (80, 50, 40))
    # rigging + gondola hull
    for x in (330, 470, 610):
        d.line(P([(x, 270), (x + 10, 350)]), fill=(20, 20, 30), width=3*SS)
    poly(d, [(250, 350), (700, 350), (740, 372), (690, 440), (300, 440), (240, 390)], (96, 60, 40))
    poly(d, [(300, 410), (690, 410), (690, 440), (300, 440)], (70, 44, 30), ow=0)
    d.line(P([(250, 350), (700, 350), (740, 372)]), fill=(200, 160, 90), width=4*SS)
    # windows
    for x in (340, 410, 480, 550, 620):
        ell(d, [x, 368, x + 34, 400], (int(80 + 175*lit), int(70 + 130*lit), int(50 + 40*lit)), ow=3)
    # propellers (side pods)
    for px in (200, 760):
        poly(d, [(px - 40, 330), (px + 40, 330), (px + 30, 370), (px - 30, 370)], (80, 84, 100), ow=4)
        ang = prop*math.pi/4
        for k in range(3):
            a2 = ang + k*2*math.pi/3
            poly(d, [(px, 350), (px + 70*math.cos(a2) - 10*math.sin(a2), 350 + 22*math.sin(a2)), (px + 70*math.cos(a2) + 10*math.sin(a2), 350 + 22*math.sin(a2) + 8)],
                 (150, 150, 170), ow=2)
    # bow lamp
    ell(d, [730, 356, 760, 386], (255, 230, 150), ow=3)
    return im.resize((w, h), Image.LANCZOS)
