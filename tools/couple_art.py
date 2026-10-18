"""Shared art kit for CHIKU & GOLA Shorts (original designs from couple.md).
Characters are drawn at 2x supersampling on a 520x720 logical canvas (returned at 2x so close-ups stay crisp).
Reuse + extend this file every episode so Chiku and Gola always look the same."""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
SS = 2
CW, CH = 520, 720          # logical character canvas; feet touch y=690
OUT = (74, 46, 58)          # warm plum outline

# palettes
C_FUR, C_FUR_SH, C_EAR_IN = (255, 251, 243), (238, 228, 218), (255, 196, 204)
C_BOW, C_BOW_SH = (150, 226, 196), (96, 186, 156)
C_EYE, C_EYE_D, C_EYE_L = (150, 92, 52), (72, 40, 26), (214, 160, 108)
BLUSH = (255, 140, 128)
G_OR, G_OR_SH, G_STRIPE, G_BELLY = (255, 172, 92), (236, 140, 64), (206, 104, 40), (255, 228, 190)
G_SCARF, G_SCARF_SH = (255, 212, 58), (226, 172, 30)
G_EYE, G_EYE_D, G_EYE_L = (118, 196, 96), (40, 104, 48), (190, 236, 150)
PINK = (255, 150, 170)


@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(6, int(sz)))

def P(pts): return [(x*SS, y*SS) for x, y in pts]
def B(box): return [v*SS for v in box]

def ell(d, box, fill, ow=0, outline=OUT):
    d.ellipse(B(box), fill=fill, outline=outline if ow else None, width=int(ow*SS))

def poly(d, pts, fill, ow=0, outline=OUT):
    d.polygon(P(pts), fill=fill, outline=outline if ow else None, width=int(ow*SS))

def line(d, pts, w=4, col=OUT):
    d.line(P(pts), fill=col, width=int(w*SS), joint="curve")
    for x, y in (pts[0], pts[-1]):
        r = w*SS/2; d.ellipse([x*SS-r, y*SS-r, x*SS+r, y*SS+r], fill=col)

def arc(d, box, a0, a1, w=4, col=OUT):
    d.arc(B(box), a0, a1, fill=col, width=int(w*SS))

def bez(p0, p1, p2, n=24):
    return [((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t*t*p2[0], (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t*t*p2[1])
            for t in np.linspace(0, 1, n)]

def tube(center, w0, w1):
    """polygon around a centre polyline, width tapering w0->w1 (round-ish ends)."""
    left, right = [], []
    n = len(center)
    for i, (x, y) in enumerate(center):
        a = center[max(0, i-1)]; b = center[min(n-1, i+1)]
        dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy) or 1
        nx, ny = -dy/L, dx/L
        w = (w0 + (w1-w0)*i/(n-1))/2
        left.append((x+nx*w, y+ny*w)); right.append((x-nx*w, y-ny*w))
    return left + right[::-1]

def rot_ellipse(cx, cy, rx, ry, ang, n=40):
    a = math.radians(ang)
    return [(cx + rx*math.cos(t)*math.cos(a) - ry*math.sin(t)*math.sin(a),
             cy + rx*math.cos(t)*math.sin(a) + ry*math.sin(t)*math.cos(a)) for t in np.linspace(0, 2*math.pi, n, endpoint=False)]

def heart_pts(cx, cy, s, n=48):
    pts = []
    for t in np.linspace(0, 2*math.pi, n, endpoint=False):
        x = 16*math.sin(t)**3
        y = 13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t)
        pts.append((cx + x*s/32, cy - y*s/32))
    return pts

def new_layer(): return Image.new("RGBA", (CW*SS, CH*SS), (0, 0, 0, 0))

def outline_under(im, px=9):
    """thick clean outer silhouette outline (blur+threshold dilation)."""
    a = im.split()[3]
    k = px*SS
    big = a.filter(ImageFilter.GaussianBlur(k*0.55)).point(lambda v: 255 if v > 18 else 0)
    big = big.filter(ImageFilter.GaussianBlur(1.2))
    base = Image.new("RGBA", im.size, OUT + (0,)); base.putalpha(big)
    base.alpha_composite(im)
    return base


# ------------------------------------------------------------------ eyes (shared)
def big_eye(im, cx, cy, rx, ry, iris, dark, light, mode, side, lidcol, look=(0, 0)):
    d = ImageDraw.Draw(im)
    if mode == "happy":       # ^ ^
        arc(d, [cx-rx, cy-ry*0.35, cx+rx, cy+ry*1.15], 200, 340, 7); return
    if mode == "blink":
        arc(d, [cx-rx, cy-ry*0.9, cx+rx, cy+ry*0.5], 20, 160, 7); return
    if mode == "closed_sad":
        arc(d, [cx-rx, cy-ry*0.2, cx+rx, cy+ry*1.2], 200, 340, 6)
        line(d, [(cx-rx*0.6*side, cy+ry*0.55), (cx-rx*0.9*side, cy+ry*0.95)], 4, (120, 190, 255)); return
    if mode == "wide": rx, ry = rx*1.12, ry*1.14
    pad = 20
    ox, oy = int((cx-rx-pad)*SS), int((cy-ry-pad)*SS)
    L = Image.new("RGBA", (int((2*rx+2*pad)*SS), int((2*ry+2*pad)*SS)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(L)
    def lb(box): return [(box[0]-cx+rx+pad)*SS, (box[1]-cy+ry+pad)*SS, (box[2]-cx+rx+pad)*SS, (box[3]-cy+ry+pad)*SS]
    def lp(pts): return [((x-cx+rx+pad)*SS, (y-cy+ry+pad)*SS) for x, y in pts]
    lx, ly = look
    if mode == "heart":
        ld.polygon(lp(heart_pts(cx, cy+4, rx*2.3)), fill=(255, 92, 128), outline=OUT, width=4*SS)
        ld.ellipse(lb([cx-rx*0.55, cy-ry*0.45, cx-rx*0.1, cy-ry*0.05]), fill=(255, 255, 255))
        im.alpha_composite(L, (ox, oy)); return
    ld.ellipse(lb([cx-rx, cy-ry, cx+rx, cy+ry]), fill=dark)
    ld.ellipse(lb([cx-rx*0.86+lx, cy-ry*0.3+ly, cx+rx*0.86+lx, cy+ry*0.98]), fill=iris)
    ld.ellipse(lb([cx-rx*0.55+lx, cy+ry*0.35+ly, cx+rx*0.55+lx, cy+ry*0.9]), fill=light)
    pr = 0.34 if mode == "wide" else 0.5
    ld.ellipse(lb([cx-rx*pr+lx, cy-ry*pr*0.9+ly, cx+rx*pr+lx, cy+ry*pr*1.1+ly]), fill=dark)
    # two white highlights (+ sparkle)
    h1 = 0.42 if mode != "wide" else 0.48
    ld.ellipse(lb([cx-rx*0.62+lx, cy-ry*0.72+ly, cx-rx*0.62+rx*h1*1.3+lx, cy-ry*0.72+ry*h1*1.1+ly]), fill=(255, 255, 255))
    ld.ellipse(lb([cx+rx*0.22+lx, cy+ry*0.28+ly, cx+rx*0.5+lx, cy+ry*0.52+ly]), fill=(255, 255, 255))
    if mode == "wide":
        ld.ellipse(lb([cx+rx*0.25, cy-ry*0.55, cx+rx*0.45, cy-ry*0.35]), fill=(255, 255, 255))
        ld.arc(lb([cx-rx*0.8, cy-ry*0.2, cx+rx*0.8, cy+ry*0.95]), 30, 150, fill=(200, 235, 255), width=4*SS)
    # lids
    if mode == "half":
        ld.rectangle(lb([cx-rx-pad, cy-ry-pad, cx+rx+pad, cy-ry*0.05]), fill=lidcol)
    elif mode == "angry":
        ld.polygon(lp([(cx-rx-pad, cy-ry-pad), (cx+rx+pad, cy-ry-pad), (cx+(rx+pad)*side, cy-ry*0.55), (cx-(rx+pad)*side, cy-ry*0.05)]), fill=lidcol)
    elif mode == "sad":
        ld.polygon(lp([(cx-rx-pad, cy-ry-pad), (cx+rx+pad, cy-ry-pad), (cx+(rx+pad)*side, cy-ry*0.1), (cx-(rx+pad)*side, cy-ry*0.6)]), fill=lidcol)
        ld.arc(lb([cx-rx*0.75, cy, cx+rx*0.75, cy+ry*0.95]), 20, 160, fill=(190, 230, 255), width=5*SS)
    m = Image.new("L", L.size, 0); ImageDraw.Draw(m).ellipse(lb([cx-rx, cy-ry, cx+rx, cy+ry]), fill=255)
    L.putalpha(ImageChops.multiply(m, L.split()[3]))
    im.alpha_composite(L, (ox, oy))
    d = ImageDraw.Draw(im)
    if mode == "half":
        d.chord(B([cx-rx, cy-ry, cx+rx, cy+ry]), 0, 180, outline=OUT, width=4*SS)
        line(d, [(cx-rx-3, cy-ry*0.05), (cx+rx+3, cy-ry*0.05)], 7)
    else:
        d.ellipse(B([cx-rx, cy-ry, cx+rx, cy+ry]), outline=OUT, width=4*SS)
        if mode == "angry":
            line(d, [(cx-(rx+4)*side, cy-ry*0.05), (cx+(rx+4)*side, cy-ry*0.55)], 7)
        elif mode == "sad":
            line(d, [(cx-(rx+4)*side, cy-ry*0.6), (cx+(rx+4)*side, cy-ry*0.1)], 7)
        else:  # top lash
            arc(d, [cx-rx-1, cy-ry-1, cx+rx+1, cy+ry+1], 200, 340, 7)
            line(d, [(cx+rx*0.86*side, cy-ry*0.55), (cx+(rx+14)*side, cy-ry*0.82)], 5)


def open_mouth(d, mx, my, w, h):
    ell(d, [mx-w, my-h*0.4, mx+w, my+h], (120, 40, 58), ow=4)
    ell(d, [mx-w*0.6, my+h*0.25, mx+w*0.6, my+h*0.92], (255, 128, 140))


# ------------------------------------------------------------------ CHIKU (bunny)
CHIKU_EYES = {"happy": "open", "shocked": "wide", "angry": "angry", "pout": "angry", "sad": "sad",
              "love": "heart", "joy": "happy", "sulk": "closed_sad", "sparkle": "wide"}

@lru_cache(None)
def chiku(expr="happy", mouth=0, blink=False, arms="down"):
    im = new_layer(); d = ImageDraw.Draw(im)
    # tail puff (behind)
    ell(d, [338, 585, 392, 638], C_FUR)
    # upright ear
    poly(d, rot_ellipse(188, 150, 40, 118, -8), C_FUR)
    poly(d, rot_ellipse(190, 160, 20, 90, -8), C_EAR_IN)
    # floppy ear (rises then flops outward/down)
    ctr = bez((305, 250), (360, 95), (470, 270), 30)
    poly(d, tube(ctr, 70, 58), C_FUR)
    poly(d, tube(bez((312, 240), (360, 115), (458, 262), 30)[3:-3], 30, 24), C_EAR_IN)
    # arms behind (up pose)
    if arms == "up":
        poly(d, rot_ellipse(128, 400, 30, 52, 35), C_FUR); poly(d, rot_ellipse(392, 400, 30, 52, -35), C_FUR)
    # body
    ell(d, [158, 440, 362, 664], C_FUR)
    ell(d, [196, 500, 324, 652], (255, 246, 236))
    # feet
    for fx in (210, 310):
        ell(d, [fx-48, 632, fx+48, 692], C_FUR)
    im = outline_under(im, 9); d = ImageDraw.Draw(im)
    # inner lines: body over-lines, feet
    for fx in (210, 310):
        ell(d, [fx-48, 632, fx+48, 692], C_FUR, ow=4)
        for k in (-18, 0, 18): ell(d, [fx+k-7, 652, fx+k+7, 666], C_EAR_IN)
    # ear inner separation lines
    poly(d, rot_ellipse(190, 160, 20, 90, -8), C_EAR_IN, ow=3)
    # head (cheeks puff when pouting)
    head = Image.new("RGBA", im.size, (0, 0, 0, 0)); hd = ImageDraw.Draw(head)
    ell(hd, [86, 215, 434, 495], C_FUR)
    if expr == "pout":
        ell(hd, [70, 350, 176, 472], C_FUR); ell(hd, [344, 350, 450, 472], C_FUR)
    head = outline_under(head, 5)
    im.alpha_composite(head); d = ImageDraw.Draw(im)
    # ear base re-drawn over head top (ears attach behind; small fur tuft)
    poly(d, [(230, 222), (250, 200), (262, 226), (280, 204), (292, 230)], C_FUR)
    arc(d, [228, 196, 262, 236], 200, 330, 4); arc(d, [258, 198, 294, 238], 200, 340, 4)
    # mint bow on floppy ear
    bx, by = 392, 168
    poly(d, [(bx, by), (bx-58, by-40), (bx-50, by+30)], C_BOW, ow=5)
    poly(d, [(bx, by), (bx+52, by-48), (bx+60, by+22)], C_BOW, ow=5)
    poly(d, [(bx-6, by+4), (bx-42, by-24), (bx-38, by+14)], C_BOW_SH)
    poly(d, [(bx+6, by+2), (bx+42, by-30), (bx+46, by+10)], C_BOW_SH)
    ell(d, [bx-18, by-18, bx+18, by+18], C_BOW, ow=5)
    ell(d, [bx-8, by-12, bx, by-4], (230, 255, 245))
    # arms front-of-body poses
    if arms == "down":
        poly(d, rot_ellipse(170, 530, 26, 46, 18), C_FUR, ow=5); poly(d, rot_ellipse(350, 530, 26, 46, -18), C_FUR, ow=5)
    elif arms == "front":
        ell(d, [204, 486, 262, 540], C_FUR, ow=5); ell(d, [258, 486, 316, 540], C_FUR, ow=5)
    elif arms == "cross":
        poly(d, rot_ellipse(232, 520, 62, 24, -12), C_FUR, ow=5); poly(d, rot_ellipse(288, 528, 62, 24, 12), C_FUR, ow=5)
    elif arms == "up":
        pass
    # face
    e = "blink" if (blink and CHIKU_EYES.get(expr, "open") in ("open", "wide", "angry", "sad")) else CHIKU_EYES.get(expr, "open")
    for side, ex in ((-1, 196), (1, 324)):
        big_eye(im, ex, 352, 46, 56, C_EYE, C_EYE_D, C_EYE_L, e, side, C_FUR)
    d = ImageDraw.Draw(im)
    if expr == "sparkle":
        for side, ex in ((-1, 196), (1, 324)):
            star(d, ex+22*side, 316, 14, (255, 255, 255))
    # blush
    bl = 1.35 if expr in ("pout", "love", "angry") else 1.0
    for bx2 in (150, 370):
        ell(d, [bx2-30*bl, 418-14*bl, bx2+30*bl, 418+14*bl], BLUSH)
    if expr in ("pout", "love"):
        for bx2 in (150, 370):
            for k in (-14, 0, 14): line(d, [(bx2+k-4, 410), (bx2+k+4, 426)], 3, (230, 90, 90))
    # brows
    if expr in ("angry", "pout"):
        line(d, [(158, 282), (226, 300)], 7); line(d, [(362, 282), (294, 300)], 7)
    elif expr in ("sad", "sulk"):
        line(d, [(160, 298), (222, 280)], 6); line(d, [(360, 298), (298, 280)], 6)
    # nose
    poly(d, [(250, 400), (270, 400), (260, 412)], PINK, ow=3)
    # mouth
    mx, my = 260, 428
    if mouth:
        open_mouth(d, mx, my+4, 15 + 6*mouth, 12 + 10*mouth)
    elif expr in ("happy", "love", "sparkle"):
        arc(d, [mx-22, my-14, mx, my+8], 0, 170, 4); arc(d, [mx, my-14, mx+22, my+8], 10, 180, 4)
    elif expr == "joy":
        poly(d, [(mx-24, my-4), (mx+24, my-4), (mx+16, my+18), (mx-16, my+18)], (120, 40, 58), ow=4)
        ell(d, [mx-12, my+6, mx+12, my+18], (255, 128, 140))
    elif expr == "shocked":
        ell(d, [mx-10, my-4, mx+10, my+18], (120, 40, 58), ow=4)
    elif expr == "pout":
        line(d, [(mx-16, my+6), (mx-8, my), (mx, my+6), (mx+8, my), (mx+16, my+6)], 4)
    else:  # angry / sad / sulk
        arc(d, [mx-18, my+2, mx+18, my+24], 200, 340, 4)
    return im


# ------------------------------------------------------------------ GOLA (kitten)
GOLA_EYES = {"sleepy": "half", "happy": "happy", "panic": "wide", "shocked": "wide", "guilty": "half",
             "love": "heart", "sad": "sad", "open": "open", "sparkle": "wide"}

@lru_cache(None)
def gola(expr="sleepy", mouth=0, blink=False, arms="down", crumbs=False, cheeks=False):
    im = new_layer(); d = ImageDraw.Draw(im)
    # tail (behind body)
    tc = bez((340, 640), (470, 640), (440, 470), 30)
    poly(d, tube(tc, 40, 34), G_OR)
    poly(d, tube(tc[-7:], 34, 30), G_STRIPE)
    # ears
    for s in (-1, 1):
        cx = 260
        poly(d, [(cx+s*150, 300), (cx+s*128, 172), (cx+s*42, 236)], G_OR)
    if arms == "up":
        poly(d, rot_ellipse(110, 420, 32, 50, 35), G_OR); poly(d, rot_ellipse(410, 420, 32, 50, -35), G_OR)
    # body
    ell(d, [124, 430, 396, 672], G_OR)
    for fx in (205, 315):
        ell(d, [fx-50, 630, fx+50, 694], G_BELLY)
    im = outline_under(im, 9); d = ImageDraw.Draw(im)
    for s in (-1, 1):
        cx = 260
        poly(d, [(cx+s*136, 284), (cx+s*124, 196), (cx+s*66, 240)], PINK)
    for x in (430, 440):
        pass
    ell(d, [186, 488, 334, 656], G_BELLY)
    ell(d, [124, 430, 396, 672], None, ow=0)
    for fx in (205, 315):
        ell(d, [fx-50, 630, fx+50, 694], G_BELLY, ow=4)
        for k in (-18, 0, 18): line(d, [(fx+k, 640), (fx+k, 654)], 3)
    # head
    head = Image.new("RGBA", im.size, (0, 0, 0, 0)); hd = ImageDraw.Draw(head)
    ell(hd, [68, 200, 452, 500], G_OR)
    if cheeks:
        ell(hd, [70, 360, 190, 480], G_OR); ell(hd, [330, 360, 450, 480], G_OR)
    # cheek fluff tufts
    poly(hd, [(78, 380), (44, 404), (84, 420), (52, 446), (98, 450)], G_OR)
    poly(hd, [(442, 380), (476, 404), (436, 420), (468, 446), (422, 450)], G_OR)
    ell(hd, [150, 380, 370, 496], G_BELLY)  # muzzle/chin
    head = outline_under(head, 5)
    im.alpha_composite(head); d = ImageDraw.Draw(im)
    # three darker head stripes
    for sx, ln in ((220, 52), (260, 66), (300, 52)):
        poly(d, [(sx-17, 206), (sx+17, 206), (sx+5, 206+ln), (sx-5, 206+ln)], G_STRIPE)
    poly(d, [(74, 320), (118, 330), (76, 342)], G_STRIPE); poly(d, [(446, 320), (402, 330), (444, 342)], G_STRIPE)
    # neckerchief
    poly(d, [(176, 486), (344, 486), (282, 566), (260, 586), (238, 566)], G_SCARF, ow=5)
    poly(d, [(262, 492), (344, 486), (282, 566)], G_SCARF_SH)
    poly(d, [(176, 486), (344, 486), (282, 566), (260, 586), (238, 566)], None, ow=5)
    ell(d, [244, 476, 276, 504], G_SCARF, ow=4)
    # arms
    if arms == "down":
        poly(d, rot_ellipse(150, 560, 30, 46, 14), G_OR, ow=5); poly(d, rot_ellipse(370, 560, 30, 46, -14), G_OR, ow=5)
    elif arms == "front":
        ell(d, [196, 540, 258, 598], G_OR, ow=5); ell(d, [262, 540, 324, 598], G_OR, ow=5)
    elif arms == "hold":   # holding something high in front (plate goes on top)
        ell(d, [150, 470, 212, 530], G_OR, ow=5); ell(d, [308, 470, 370, 530], G_OR, ow=5)
    # eyes
    e = GOLA_EYES.get(expr, "half")
    if blink and e in ("half", "open", "wide", "sad"): e = "blink"
    look = (-10, 2) if expr == "guilty" else (0, 0)
    for side, ex in ((-1, 188), (1, 332)):
        big_eye(im, ex, 352, 44, 50, G_EYE, G_EYE_D, G_EYE_L, e, side, G_OR, look)
    d = ImageDraw.Draw(im)
    if expr == "sparkle":
        for side, ex in ((-1, 188), (1, 332)): star(d, ex+20*side, 318, 13, (255, 255, 255))
    for bx2 in (140, 380):
        ell(d, [bx2-28, 410, bx2+28, 434], (255, 130, 110) if expr in ("love", "happy") else (255, 150, 120))
    if expr in ("panic", "sad", "guilty"):
        line(d, [(150, 290), (214, 278)], 6); line(d, [(370, 290), (306, 278)], 6)
    # nose + mouth
    poly(d, [(248, 398), (272, 398), (260, 412)], PINK, ow=3)
    mx, my = 260, 420
    if mouth:
        open_mouth(d, mx, my+4, 16 + 6*mouth, 12 + 10*mouth)
    elif cheeks:
        line(d, [(mx-10, my+8), (mx+10, my+8)], 4)
    elif expr == "panic":
        line(d, [(mx-30, my+12), (mx-18, my+4), (mx-6, my+12), (mx+6, my+4), (mx+18, my+12), (mx+30, my+4)], 4)
    elif expr in ("sad", "guilty"):
        arc(d, [mx-16, my+4, mx+16, my+24], 200, 340, 4)
    else:  # cat "w" mouth
        line(d, [(260, 412), (260, my)], 3)
        arc(d, [mx-24, my-12, mx, my+10], 0, 170, 4); arc(d, [mx, my-12, mx+24, my+10], 10, 180, 4)
    # whiskers
    for s in (-1, 1):
        for k, dy in enumerate((-10, 6, 22)):
            line(d, [(260+s*104, 412+dy), (260+s*170, 404+dy*1.6)], 3)
    if crumbs:
        for (cx, cy, r) in ((226, 444, 7), (296, 450, 6), (312, 434, 5), (240, 462, 5)):
            ell(d, [cx-r, cy-r, cx+r, cy+r], (246, 222, 168), ow=2.5)
    return im


# ------------------------------------------------------------------ props + fx
def star(d, x, y, s, col=(255, 248, 200), ow=0):
    pts = []
    for i in range(8):
        r = s if i % 2 == 0 else s*0.32
        a = i*math.pi/4 - math.pi/2
        pts.append((x + r*math.cos(a), y + r*math.sin(a)))
    poly(d, pts, col, ow=ow)

def heart(d, x, y, s, col=(255, 96, 132), ow=4):
    poly(d, heart_pts(x, y, s), col, ow=ow)
    ell(d, [x-s*0.32, y-s*0.28, x-s*0.12, y-s*0.1], (255, 220, 228))

def dumpling(d, x, y, s=1.0, face=True):
    """cream pleated dumpling, centre-bottom at x,y (logical px)."""
    w, h = 90*s, 66*s
    poly(d, [(x-w, y)] + [(x + w*math.cos(t), y - h*math.sin(t)) for t in np.linspace(math.pi, 0, 24)] + [(x+w, y)], (255, 244, 218), ow=4.5)
    poly(d, [(x-w*0.3, y-h*0.95), (x, y-h*1.32), (x+w*0.3, y-h*0.95)], (255, 244, 218), ow=4.5)
    for k in (-0.45, -0.15, 0.15, 0.45):
        arc(d, [x+w*k-16*s, y-h*1.05, x+w*k+16*s, y-h*0.55], 200, 340, 3.5)
    ell(d, [x-w*0.95, y-10*s, x+w*0.95, y+8*s], (240, 214, 170))
    line(d, [(x-w, y), (x+w, y)], 4.5)
    if face:
        ell(d, [x-30*s, y-30*s, x-20*s, y-18*s], OUT); ell(d, [x+20*s, y-30*s, x+30*s, y-18*s], OUT)
        arc(d, [x-8*s, y-26*s, x+8*s, y-14*s], 20, 160, 3)
        ell(d, [x-50*s, y-22*s, x-34*s, y-14*s], (255, 170, 160)); ell(d, [x+34*s, y-22*s, x+50*s, y-14*s], (255, 170, 160))

def plate(d, x, y, s=1.0):
    ell(d, [x-150*s, y-30*s, x+150*s, y+30*s], (255, 255, 255), ow=5)
    ell(d, [x-118*s, y-20*s, x+118*s, y+20*s], (220, 236, 250), ow=0)
    arc(d, [x-150*s, y-30*s, x+150*s, y+30*s], 0, 180, 9, (130, 180, 230))

def steam(d, x, y, t, s=1.0, col=(255, 255, 255)):
    for k in (-1, 0, 1):
        ph = t*2.2 + k*1.3
        pts = [(x + k*36*s + 10*s*math.sin(ph + j*0.9), y - j*16*s - (t*30 % 16)) for j in range(6)]
        line(d, pts, 5*s, col)

def sweat(d, x, y, s=1.0):
    poly(d, [(x, y-34*s)] + [(x + 18*s*math.cos(t), y + 18*s*math.sin(t)) for t in np.linspace(-0.4, math.pi+0.4, 16)], (150, 210, 255), ow=4)
    ell(d, [x-8*s, y-4*s, x-2*s, y+6*s], (240, 250, 255))

def anger_mark(d, x, y, s=1.0, col=(240, 60, 80)):
    for a in (45, 135, 225, 315):
        r = math.radians(a)
        cx, cy = x + 22*s*math.cos(r), y + 22*s*math.sin(r)
        arc(d, [cx-18*s, cy-18*s, cx+18*s, cy+18*s], a+90, a+270, 7*s, col)

def puff_cloud(d, x, y, s=1.0, col=(255, 255, 255)):
    for (dx, dy, r) in ((-40, 10, 34), (0, -10, 42), (42, 8, 34), (-14, 26, 30), (20, 28, 30)):
        ell(d, [x+dx*s-r*s, y+dy*s-r*s, x+dx*s+r*s, y+dy*s+r*s], col, ow=5)
    for (dx, dy, r) in ((-40, 10, 30), (0, -10, 38), (42, 8, 30), (-14, 26, 26), (20, 28, 26)):
        ell(d, [x+dx*s-r*s, y+dy*s-r*s, x+dx*s+r*s, y+dy*s+r*s], col)

def rain_cloud(d, x, y, t, s=1.0):
    for k in range(7):
        ph = (t*2.6 + k*0.37) % 1.0
        rx = x - 80*s + k*27*s
        ry = y + 30*s + ph*170*s
        line(d, [(rx, ry), (rx-5*s, ry+24*s)], 5*s, (120, 170, 235))
    for (dx, dy, r) in ((-70, 10, 44), (-20, -18, 58), (40, -8, 52), (86, 14, 38), (0, 24, 44)):
        ell(d, [x+dx*s-r*s, y+dy*s-r*s, x+dx*s+r*s, y+dy*s+r*s], (150, 158, 186), ow=5)
    for (dx, dy, r) in ((-70, 10, 40), (-20, -18, 54), (40, -8, 48), (86, 14, 34), (0, 24, 40)):
        ell(d, [x+dx*s-r*s, y+dy*s-r*s, x+dx*s+r*s, y+dy*s+r*s], (150, 158, 186))
    ell(d, [x-50*s, y-50*s, x-10*s, y-30*s], (182, 190, 214))


# ------------------------------------------------------------------ backgrounds
def treehouse_kitchen(tint=None):
    """cosy wooden treehouse interior, 1080x1920 (floor line ~y=1240)."""
    im = Image.new("RGBA", (W*SS, H*SS), (255, 226, 190, 255)); d = ImageDraw.Draw(im)
    for i in range(0, W, 120):
        col = (250, 214, 172) if (i//120) % 2 == 0 else (244, 204, 160)
        d.rectangle(B([i, 0, i+120, 1240]), fill=col)
        line(d, [(i, 0), (i, 1240)], 3, (214, 168, 122))
        for k in range(3):
            yy = (i*7 + k*420) % 1180 + 30
            arc(d, [i+40, yy, i+80, yy+24], 0, 360, 2.5, (220, 176, 130))
    # round window with sky + leaves
    ell(d, [130, 300, 530, 700], (186, 226, 255), ow=12, outline=(176, 120, 76))
    ell(d, [190, 340, 330, 420], (255, 255, 255)); ell(d, [270, 330, 420, 410], (255, 255, 255))
    for k, (lx, ly) in enumerate(((180, 560), (240, 610), (310, 600), (380, 640), (450, 590))):
        poly(d, rot_ellipse(lx, ly, 40, 20, -30 + k*18), (130, 206, 120), ow=4)
    line(d, [(130, 500), (530, 500)], 10, (176, 120, 76)); line(d, [(330, 300), (330, 700)], 10, (176, 120, 76))
    # shelf with jars
    d.rectangle(B([620, 520, 960, 548]), fill=(196, 140, 92), outline=OUT, width=4*SS)
    for k, (jc, lid) in enumerate((((255, 200, 210), (240, 120, 150)), ((200, 236, 210), (100, 180, 140)), ((255, 236, 170), (230, 170, 60)))):
        x0 = 650 + k*104
        d.rounded_rectangle(B([x0, 410, x0+78, 520]), 18*SS, fill=jc, outline=OUT, width=4*SS)
        d.rectangle(B([x0+6, 396, x0+72, 420]), fill=lid, outline=OUT, width=4*SS)
    # string lights
    pts = bez((0, 150), (540, 300), (1080, 150), 30)
    line(d, pts, 3, (120, 90, 70))
    for k in range(2, 28, 3):
        x, y = pts[k]
        col = [(255, 210, 120), (255, 160, 190), (170, 230, 210)][k % 3]
        ell(d, [x-14, y, x+14, y+30], col, ow=3)
    # floor
    d.rectangle(B([0, 1240, W, H]), fill=(206, 150, 102))
    for y in range(1240, H, 70):
        line(d, [(0, y), (W, y)], 3, (178, 124, 82))
    line(d, [(0, 1240), (W, 1240)], 6, (150, 100, 66))
    # rug
    ell(d, [140, 1290, 940, 1480], (255, 190, 200), ow=5)
    ell(d, [200, 1312, 880, 1458], (255, 214, 220))
    im = im.resize((W, H), Image.LANCZOS)
    if tint:
        ov = Image.new("RGBA", (W, H), tint); im = Image.alpha_composite(im, ov)
    return im

def table_layer():
    """little round wooden table (front prop), logical 1080x1920 layer, top surface at y~1010."""
    im = Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    poly(d, [(520, 1030), (560, 1030), (580, 1250), (500, 1250)], (176, 120, 76), ow=5)
    ell(d, [450, 1230, 630, 1270], (176, 120, 76), ow=5)
    ell(d, [330, 980, 750, 1060], (196, 140, 92), ow=6)
    ell(d, [350, 978, 730, 1040], (214, 160, 108))
    return im.resize((W, H), Image.LANCZOS)

def soft_sky(top, bot):
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None, :]*(1-a) + np.array(bot)[None, None, :]*a).repeat(W, 1)
    return Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")

def burst_bg(c1, c2, n=18, rot=0.0):
    im = Image.new("RGBA", (W, H), c1 + (255,)); d = ImageDraw.Draw(im)
    cx, cy = 540, 900
    for i in range(n):
        a0 = rot + i*2*math.pi/n; a1 = a0 + math.pi/n
        d.polygon([(cx, cy), (cx + 2600*math.cos(a0), cy + 2600*math.sin(a0)), (cx + 2600*math.cos(a1), cy + 2600*math.sin(a1))], fill=c2)
    return im


# ------------------------------------------------------------------ compositing helpers
def paste_char(frame, img, cx, feet_y, scale=1.0, sx=1.0, sy=1.0, flip=False, rot=0.0):
    """paste a 2x character image so its feet centre lands at (cx, feet_y) in frame coords."""
    w = max(2, int(CW*scale*sx)); h = max(2, int(CH*scale*sy))
    im = img.transpose(Image.FLIP_LEFT_RIGHT) if flip else img
    im = im.resize((w, h), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
        blit(frame, im, int(cx - im.width/2), int(feet_y - h*690/CH - (im.height-h)/2))
        return
    x = int(cx - w/2); y = int(feet_y - h*690/CH)
    blit(frame, im, x, y)

def blit(frame, im, x, y):
    """alpha_composite that tolerates negative / off-frame positions."""
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(frame.width, x + im.width), min(frame.height, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    frame.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def squash(t, freq=2.0, amt=0.04):
    s = math.sin(t*freq*2*math.pi)
    return 1 + amt*s, 1 - amt*s

def fx_layer():
    return Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0))

def fx_done(L): return L.resize((W, H), Image.LANCZOS)
