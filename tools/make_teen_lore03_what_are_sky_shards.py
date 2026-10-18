"""SKYFORGE SAGA Lore #3: What Are Sky-Shards?  (no-voice build: music + sfx + timed captions).
Magic-system Short. New shots: a turning hero shard with facet callouts, a Kestrel engine sliver, the three
shard rules board, a shard size chart, Mire on the hunt. Reuses Ep 1-9 / Lore 1-2 helpers. New score (E minor, 90 bpm)."""
import math, random, subprocess, os, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from teen_art import *
import make_teen_ep01_the_shard_falls as e1
from make_teen_ep01_the_shard_falls import (grad, embers, SPEED, cam, shake, flash, VIG, light_rays, text_center,
                                            glow_text, paste_bust, ease, blink, KING_BG, KING_DOT, EMBERS, WIDE, sky_cracks)
from make_teen_ep02_the_cracked_blade import rot_paste, sparks, energy_bolts, blade
from make_teen_ep03_hollow_soldiers import violet_fog
from make_teen_ep04_lyras_airship import COCKPIT, ENGINE, wind_lines
from make_teen_ep05_the_fox_in_the_engine import BRIDGE, paste_kuro, blue_embers, blue_fire_glow
from make_teen_lore01_who_is_ren_asaka import panel, callout, pulse_rings, SCAN, FILE_BG, FORGE_DARK
from make_teen_ep08_the_drowned_island import HALL, HALL_BLUR, dust

FPS, SR = 30, 44100
OUTFILE = sys.argv[1] if len(sys.argv) > 1 else "teen/lore03_what_are_sky_shards.mp4"
TMP = os.environ.get("TMPDIR_EP", "/tmp")
TITLE, NEXT, NEXT_EP = "What Are Sky-Shards?", "Mire Strikes", 10

SHOTS = [("title", 0.0, 4.0), ("hero", 4.0, 10.6), ("lyra", 10.6, 16.6), ("ren", 16.6, 22.6), ("rules", 22.6, 30.0),
         ("kuro", 30.0, 35.6), ("king", 35.6, 41.0), ("mire", 41.0, 46.0), ("hook", 46.0, 52.6), ("next", 52.6, 56.6)]
TOTAL = 56.6
LINES = [
    ("NARRATOR", "Sky-shards: crystals of pure sky-magic, left behind when the old kingdom shattered.", 4.3, 10.3),
    ("LYRA", "One shard can keep an airship flying for a year. The Kestrel runs on a sliver.", 10.9, 16.3),
    ("REN", "Mine fused with my broken sword. Now it glows, it hums... and sometimes it ignores me.", 16.9, 22.3),
    ("NARRATOR", "Rule one: a shard chooses its bearer. Rule two: bigger shard, bigger power.", 22.9, 26.6),
    ("NARRATOR", "Rule three... a shard remembers everything.", 26.8, 29.7),
    ("KURO", "A shard is not a tool. It is a memory with a heartbeat.", 30.3, 35.3),
    ("HOLLOW KING", "Every shard was mine once. I am only taking back what fell.", 35.9, 40.7),
    ("CAPTAIN MIRE", "The King wants them all. And I always deliver.", 41.3, 45.7),
    ("NARRATOR", "And right now, Mire is coming for Ren's. Who keeps it... and who loses it?", 46.3, 52.3),
]
e1.LINES = LINES
e1.TAG = {"NARRATOR": (190, 220, 235), "REN": (240, 80, 80), "LYRA": (90, 220, 210), "KURO": (110, 170, 255),
          "HOLLOW KING": (190, 120, 255), "CAPTAIN MIRE": (235, 120, 90)}
draw_caption, speaking = e1.draw_caption, e1.speaking
O = (14, 12, 22)

# ------------------------------------------------------------ backgrounds
def make_void():
    im = Image.fromarray(grad(W, H, [(0, (4, 10, 26)), (0.45, (10, 40, 70)), (0.7, (6, 24, 48)), (1, (2, 6, 16))])).convert("RGBA")
    d = ImageDraw.Draw(im); r = random.Random(31)
    for _ in range(160):
        x, y, s = r.uniform(0, W), r.uniform(0, H), r.choice([1, 2, 2, 3])
        d.ellipse([x - s, y - s, x + s, y + s], fill=(170, 230, 255))
    return im
VOID = make_void()

def facet_rings(im, t, cx, cy, R, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for k in range(3):
        rr = R + k*70; rot = t*(0.4 + 0.25*k)*(1 if k % 2 else -1)
        pts = [(cx + rr*math.cos(rot + i*math.pi/3), cy + rr*0.92*math.sin(rot + i*math.pi/3)) for i in range(6)]
        d.polygon(pts, outline=(110, 230, 255, int((150 - 35*k)*a)), width=4)
        for x, y in pts: d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(200, 250, 255, int(220*a)))
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(4))); im.alpha_composite(lay)

def shard_icon(size, col=(120, 240, 255)):
    s = shard(size)
    if col != (120, 240, 255):
        arr = np.array(s).astype(np.float32)
        tint = np.array(col, np.float32)/np.array((120, 240, 255), np.float32)
        arr[..., :3] = np.clip(arr[..., :3]*tint, 0, 255)
        s = Image.fromarray(arr.astype(np.uint8))
    return s

# ------------------------------------------------------------ shots
def shot_title(t, lt):
    im = VOID.copy()
    im.alpha_composite(light_rays(t, (110, 220, 255), 540, -120, 55))
    sh = shard(int(70 + 30*ease(lt/3))); im.alpha_composite(sh, (540 - sh.width//2, 520 - sh.height//2 + int(8*math.sin(t*2))))
    embers(im, t, 0.6, True)
    if lt > 0.4: glow_text(im, "SKYFORGE SAGA", 760, 112, (235, 250, 255), (40, 180, 255))
    if lt > 0.8:
        d = ImageDraw.Draw(im); w = min(1, (lt - 0.8)/0.4)*300
        d.rectangle([540 - w, 900, 540 + w, 906], fill=(90, 220, 255))
        text_center(d, "—  LORE #3  —", 930, 60, (255, 190, 110))
    if lt > 1.2:
        glow_text(im, "What Are", 1020, 92, (255, 255, 255), (60, 160, 255))
        glow_text(im, "Sky-Shards?", 1130, 100, (255, 255, 255), (60, 160, 255))
    return flash(im, max(0, 1 - lt/0.35))

def shot_hero(t, lt):
    k = ease(lt/6.6)
    im = VOID.copy()
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([140, 340, 940, 1260], fill=(60, 210, 255, 90))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(110)))
    cx, cy = 540, 760 + 14*math.sin(t*1.8)
    facet_rings(im, t, cx, cy, 300, ease(lt/1.2))
    sz = int(250 + 40*k)
    sh = shard(sz)
    # "turning" illusion: squash horizontally with a slow sine
    sq = 0.72 + 0.28*abs(math.cos(t*0.9))
    sh = sh.resize((max(2, int(sh.width*sq)), sh.height), Image.BILINEAR)
    im.alpha_composite(sh, (int(cx - sh.width/2), int(cy - sh.height/2)))
    # glint sweep
    gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gx = -300 + ((lt*500) % 1500)
    gd.polygon([(gx, cy - 260), (gx + 60, cy - 260), (gx - 60, cy + 260), (gx - 120, cy + 260)], fill=(255, 255, 255, 70))
    mask = sh.split()[3]; m2 = Image.new("L", (W, H), 0); m2.paste(mask, (int(cx - sh.width/2), int(cy - sh.height/2)))
    gl.putalpha(Image.composite(gl.split()[3], Image.new("L", (W, H), 0), m2)); im.alpha_composite(gl)
    callout(im, (cx - 20, cy - 60), (300, 200), "CORE", "living sky-magic", (lt - 1.2)/1.4)
    callout(im, (cx + 80, cy + 60), (760, 330), "FACETS", "store power", (lt - 2.8)/1.4, (255, 200, 120))
    embers(im, t, 0.7, True, 1.2)
    return shake(im, 1.5, t, 2)

def engine_vial(im, t, cx, cy, a):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle([cx - 70, cy - 120, cx + 70, cy + 120], 30, fill=(20, 40, 60, int(220*a)), outline=(200, 160, 90, int(255*a)), width=8)
    for yy in (cy - 120, cy + 120):
        d.rounded_rectangle([cx - 90, yy - 18, cx + 90, yy + 18], 10, fill=(170, 120, 60, int(255*a)), outline=O + (int(255*a),), width=4)
    im.alpha_composite(lay)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([cx - 120, cy - 120, cx + 120, cy + 120], fill=(90, 230, 255, int((120 + 60*math.sin(t*5))*a)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40)))
    sh = shard(34); sh.putalpha(sh.split()[3].point(lambda v: int(v*a)))
    im.alpha_composite(sh, (cx - sh.width//2, int(cy - sh.height//2 + 6*math.sin(t*3))))

def shot_lyra(t, lt):
    k = ease(lt/6)
    im = cam(COCKPIT, 1.05 + 0.03*k, 650, 1000).convert("RGBA")
    wind_lines(im, t, 14, 7, 80)
    m = speaking("LYRA", t)
    paste_bust(im, lyra_bust("smirk" if lt < 3.4 else "calm", m, blink(t, 0.6)), 1.0, 470, 780)
    if lt > 2.6:
        a = ease((lt - 2.6)/0.5)
        panel(im, [650, 240 - int(20*(1 - a)), 930, 700 - int(20*(1 - a))], (255, 190, 110), int(200*a))
        engine_vial(im, t, 790, 450 - int(20*(1 - a)), a)
        d = ImageDraw.Draw(im)
        d.text((680, 600 - 20*(1 - a)), "FUEL: 1 SLIVER", font=font(30), fill=(255, 190, 110))
        d.text((680, 640 - 20*(1 - a)), "range: 1 year", font=font(26), fill=(200, 235, 255))
    return shake(im, 2, t, 4)

def shot_ren(t, lt):
    im = FORGE_DARK.copy()
    im.alpha_composite(SPEED[int(t*12) % 4])
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([0, 300, 700, 1400], fill=(80, 220, 255, int(70 + 30*math.sin(t*4))))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(120)))
    m = speaking("REN", t)
    ignore = lt > 3.9   # "...ignores me" -> blade glow cuts out
    expr = "smirk" if lt < 1.8 else ("determined" if not ignore else "shocked")
    paste_bust(im, ren_bust(expr, m, blink(t, 0.4) and expr != "shocked", int(t*10) % 8, False), 1.0 + 0.05*ease(lt/6), 600, 980)
    glow = 0.25 if (ignore and int(lt*8) % 3) else (0.85 + 0.15*math.sin(t*6))
    rot_paste(im, blade(1.0, round(glow, 1), 0.9), -14, 230, 1060)
    if not ignore:
        energy_bolts(im, t, 230, 1300, 260, 820, 2, 1)
        sparks(im, t, 230, 900, 10, 0.5, 9, (170, 245, 255))
    else:
        d = ImageDraw.Draw(im)
        d.text((100, 420), "...?", font=font(110), fill=(255, 255, 255), stroke_width=8, stroke_fill=(8, 8, 16))
    embers(im, t, 0.6, True, 1.4)
    return shake(im, 4 if 3.9 < lt < 4.2 else 0, t, 2)

RULES = [("1", "A shard CHOOSES", "its bearer", 0.3), ("2", "Bigger shard =", "bigger power", 2.0), ("3", "A shard", "REMEMBERS", 4.3)]
def shot_rules(t, lt):
    im = FILE_BG.copy(); im.alpha_composite(SCAN)
    panel(im, [90, 150, 930, 1090], (90, 220, 255), 200)
    d = ImageDraw.Draw(im)
    text_center(d, "THE SHARD RULES", 190, 66, (255, 255, 255), sw=6)
    d.rectangle([260, 278, 820, 284], fill=(90, 220, 255))
    for i, (n, a1, a2, at) in enumerate(RULES):
        p = ease((lt - at)/0.45)
        if p <= 0: continue
        y = 320 + i*270; x = 140 - int(80*(1 - p))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.ellipse([x, y + 20, x + 130, y + 150], fill=(10, 30, 50, int(255*p)), outline=(120, 235, 255, int(255*p)), width=6)
        im.alpha_composite(lay)
        d = ImageDraw.Draw(im)
        d.text((x + 65 - font(80).getlength(n)/2, y + 30), n, font=font(80), fill=(255, 210, 120))
        d.text((x + 170, y + 30), a1, font=font(54), fill=(255, 255, 255), stroke_width=5, stroke_fill=(8, 8, 16))
        d.text((x + 170, y + 100), a2, font=font(54), fill=(120, 235, 255), stroke_width=5, stroke_fill=(8, 8, 16))
        # little visual for each rule (inside the panel, left of the right edge)
        if i == 1:
            for j, s in enumerate((34, 54, 80)):
                sh = shard(s); im.alpha_composite(sh, (int(660 + j*95 - sh.width/2), int(y + 200 - sh.height/2)))
    if lt > 4.6:  # rule 3: memory ripple
        pulse_rings(im, t, 820, 930, 2, (255, 210, 140))
    embers(im, t, 0.35, True)
    return im

def shot_kuro(t, lt):
    k = ease(lt/5.6)
    im = cam(HALL_BLUR, 1.25 + 0.05*k, 650, 1300).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (6, 10, 30, 255)), 0.35)
    blue_fire_glow(im, 540, 700, 380, 0.6)
    m = speaking("KURO", t)
    eyes = "calm" if lt < 2.6 else "narrow"
    paste_kuro(im, kuro(m, blink(t, 1.2) and eyes == "calm", int(t*10) % 8, eyes), 1.15 + 0.08*k, 540, 680 + 8*math.sin(t*2))
    # heartbeat: a small shard pulsing in front
    beat = max(0, math.sin(t*2*math.pi*1.1))**8
    sh = shard(int(40 + 14*beat)); im.alpha_composite(sh, (540 - sh.width//2, 1150 - sh.height//2))
    if lt > 2.6: pulse_rings(im, t, 540, 1150, 2, (110, 200, 255))
    blue_embers(im, t, 540, 900, 22, 15, 480)
    dust(im, t, 24, 19)
    return im

def shot_king(t, lt):
    im = cam(KING_BG, 1.12 - 0.05*ease(lt/5.4), 620, 1060).convert("RGBA")
    m = speaking("HOLLOW KING", t)
    lvl = {1: 2, 2: 4}[m] if m else int(1 + 0.8*math.sin(t*2))
    # shards being pulled toward him from all sides
    for i in range(7):
        ph = (lt*0.35 + i/7) % 1
        a = i*2*math.pi/7 + 0.3
        rr = 620*(1 - ph) + 200
        x = 540 + rr*math.cos(a); y = 560 + rr*0.8*math.sin(a)
        sh = shard(22 + i % 3*6); im.alpha_composite(sh, (int(x - sh.width/2), int(y - sh.height/2)))
    paste_bust(im, hollow_king(max(0, min(4, lvl))), 1.22 + 0.06*ease(lt/5.4), 540, 720)
    for x0, y0, sp, ph, r, cy in EMBERS[:26]:
        yy = (y0 - sp*0.6*t) % (H + 100) - 50; xx = x0 + 30*math.sin(t + ph)
        im.alpha_composite(KING_DOT, (int(xx - 12), int(yy - 12)))
    if 3.0 < lt < 3.15: im = flash(im, 0.35, (150, 90, 220))
    return shake(im, 3 if lt > 3.0 else 0, t)

def shot_mire(t, lt):
    k = ease(lt/5)
    im = cam(BRIDGE, 1.25 + 0.05*k, 650, 1100).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (24, 8, 20, 255)), 0.45)
    im.alpha_composite(violet_fog(t, 1050, 1600, 110, 43))
    wind_lines(im, t, 12, 11, 90)
    m = speaking("CAPTAIN MIRE", t)
    paste_bust(im, mire_bust(m, blink(t, 1.7)), 0.95 + 0.12*k, 520, 800)
    # tracker hologram: Ren's shard signal
    a = ease((lt - 1.0)/0.5)
    if a > 0:
        panel(im, [610, 180, 930, 470], (235, 120, 90), int(190*a))
        pulse_rings(im, t, 770, 320, 2, (255, 150, 110))
        d = ImageDraw.Draw(im); d.ellipse([755, 305, 785, 335], fill=(255, 220, 200))
        d.text((640, 410), "TARGET: REN", font=font(30), fill=(255, 190, 160))
    embers(im, t, 0.3)
    if 3.4 < lt < 3.6:
        d = ImageDraw.Draw(im)
        for i in range(8):
            q = i*math.pi/4; d.line([(250 + 26*math.cos(q), 420 + 26*math.sin(q)), (250 + 70*math.cos(q), 420 + 70*math.sin(q))], fill=(255, 255, 255), width=6)
    return shake(im, 2, t, 6)

def shot_hook(t, lt):
    k = ease(lt/6.6)
    im = cam(HALL, 1.1 + 0.15*k, 650, 1250).convert("RGBA")
    im = Image.blend(im, Image.new("RGBA", im.size, (8, 6, 22, 255)), 0.4)
    # cyan shard light (Ren) vs creeping violet (Mire)
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.ellipse([140, 500, 700, 1200], fill=(70, 220, 255, 110))
    gd.ellipse([600 - 300*k, 300, 1400, 1500], fill=(160, 70, 230, int(60 + 70*k)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(90)))
    im.alpha_composite(violet_fog(t, 1000, 1600, int(80 + 60*k), 47))
    rot_paste(im, blade(1.0, round(0.7 + 0.3*math.sin(t*5), 1), 0.75), -30, 400, 880)
    # Mire's silhouette shadow sliding in from the right
    sil = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sil)
    sx = 1180 - 300*k
    sd.ellipse([sx - 70, 420, sx + 70, 560], fill=(10, 4, 16, 230))
    sd.polygon([(sx - 150, 1500), (sx - 110, 570), (sx + 110, 570), (sx + 150, 1500)], fill=(10, 4, 16, 230))
    sd.line([(sx - 200, 300), (sx - 120, 1400)], fill=(10, 4, 16, 230), width=16)
    im.alpha_composite(sil.filter(ImageFilter.GaussianBlur(3)))
    sparks(im, t, 400, 880, 10, 0.5, 33, (160, 240, 255))
    embers(im, t, 0.6, True)
    if lt > 3.2: im.alpha_composite(SPEED[int(t*15) % 4])
    return shake(im, 2 + 4*max(0, lt - 3.2)/3.4, t, 5)

def shot_next(t, lt):
    im = VOID.copy()
    im = Image.blend(im, Image.new("RGBA", im.size, (4, 6, 16, 255)), 0.3)
    if lt < 0.4: im = flash(im, 1 - lt/0.4, (255, 220, 200))
    if lt > 0.15:
        a = ease((lt - 0.15)/0.3); d = ImageDraw.Draw(im)
        text_center(d, "NEXT:", 640 - int(40*(1 - a)), 80, (255, 170, 80))
        glow_text(im, "Ep %d: %s" % (NEXT_EP, NEXT), 760, 96, (255, 255, 255), (230, 90, 70))
        d = ImageDraw.Draw(im)
        d.rectangle([540 - 300*a, 920, 540 + 300*a, 926], fill=(230, 120, 90))
        if lt > 0.9: text_center(d, "SKYFORGE SAGA", 960, 54, (200, 230, 255), sw=6)
        if lt > 1.5: text_center(d, "Follow so you don't miss it!", 1060, 50, (255, 220, 150), sw=6)
    embers(im, t, 0.5, True)
    return im

SHOT_FN = {"title": shot_title, "hero": shot_hero, "lyra": shot_lyra, "ren": shot_ren, "rules": shot_rules,
           "kuro": shot_kuro, "king": shot_king, "mire": shot_mire, "hook": shot_hook, "next": shot_next}

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

# ------------------------------------------------------------ audio (new score: E minor, 90 bpm)
def build_audio(path):
    N = int(TOTAL*SR); L = np.zeros(N); R = np.zeros(N)
    rs = np.random.RandomState(73)
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
    bpm = 90; beat = 60/bpm; bar = beat*4
    chords = [[52, 55, 59], [48, 52, 55], [43, 47, 50], [50, 54, 57]]  # Em C G D
    def speech_duck(t):
        for _, _, s, e in LINES:
            if s - 0.2 <= t < e + 0.2: return 0.66
        return 1.0
    def inten(t):
        pts = [(0, 0.6), (4, 0.55), (10.6, 0.6), (16.6, 0.75), (22.6, 0.6), (30, 0.5), (35.6, 0.8), (41, 0.9), (46, 0.8),
               (49, 1.0), (52.6, 1.0), (56.6, 0.6)]
        return np.interp(t, [p[0] for p in pts], [p[1] for p in pts])
    t0, ci = 0.0, 0
    while t0 < TOTAL:
        ch = chords[ci % 4]; dur = bar + 0.3
        for k, m in enumerate(ch + [ch[0] + 12]):
            s = (saw(note(m), dur, 6, 0.004) + saw(note(m), dur, 6, -0.004))*0.5*env(int(dur*SR), 0.4, 0.6)
            add(s, t0, pan=-0.45 + 0.3*k, vol=0.03*inten(t0)*speech_duck(t0 + 1))
        add(saw(note(ch[0] - 12), dur, 4)*env(int(dur*SR), 0.03, 0.4), t0, vol=0.05*inten(t0))
        n = int(dur*SR); x = tv(n); vib = 1 + 0.004*np.sin(2*np.pi*5*x)
        add(sum(np.sin(2*np.pi*note(m + 12)*x*vib) for m in ch)/3*env(n, 0.8, 0.8), t0, vol=0.022*speech_duck(t0 + 1))
        t0 += bar; ci += 1
    # crystal arpeggio (bell-like) under the explainer parts
    t0, k = 4.0, 0
    while t0 < 35.6:
        ch = chords[int(t0 // bar) % 4]; m = [ch[0] + 24, ch[1] + 24, ch[2] + 24, ch[1] + 36, ch[2] + 24, ch[1] + 24, ch[0] + 36, ch[2] + 24][k % 8]
        n = int(0.9*SR); x = tv(n)
        add((np.sin(2*np.pi*note(m)*x) + 0.4*np.sin(2*np.pi*note(m)*3.01*x)*np.exp(-9*x))*np.exp(-4.5*x), t0, pan=0.45*(1 if k % 2 else -1), vol=0.035*speech_duck(t0))
        t0 += beat/2; k += 1
    # lead motif over villains (own melody)
    motif = [(64, 1), (67, 0.5), (71, 0.5), (72, 1), (71, 0.5), (67, 0.5), (66, 1.5), (64, 2.5)]
    tt = 41.0
    for m, b in motif:
        dur = b*beat; n = int(dur*SR)
        add(saw(note(m), dur, 8)*env(n, 0.04, 0.12)*(1 + 0.15*np.sin(2*np.pi*5*tv(n))), tt, pan=0.1, vol=0.03); tt += dur
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
        if 41.0 <= tb < 52.6:
            if b % 4 in (0, 2) or b % 8 == 7: add(KICK, tb, vol=0.5)
            if b % 4 in (1, 3): add(SNARE, tb, vol=0.16)
            add(SNARE[:1800]*0.5, tb + beat/2, pan=-0.4, vol=0.07)
        elif 35.6 <= tb < 41.0 and b % 2 == 0:
            add(TAIKO, tb, vol=0.45)
        elif 10.6 <= tb < 30.0 and b % 2 == 0:
            add(KICK, tb, vol=0.2)
        b += 1
    WH = whoosh()
    for name, s, e in SHOTS[1:]:
        add(WH, s - 0.3, pan=rs.uniform(-0.5, 0.5), vol=0.3)
    def blip(f=1400):
        n = int(0.09*SR); x = tv(n); return np.sin(2*np.pi*f*x)*np.exp(-30*x)
    for at, f in ((4.0 + 1.3, 1300), (4.0 + 2.9, 1000), (10.6 + 2.7, 1200), (22.6 + 0.3, 900), (22.6 + 2.0, 1100), (22.6 + 4.3, 1300), (41.0 + 1.0, 800)):
        add(blip(f), at, vol=0.12)
    # title hit + shimmer
    n = int(2.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-2.5*x) + 0.4*rs.randn(n)*np.exp(-12*x), 0.05, vol=0.55)
    n = int(3.0*SR); x = tv(n)
    add(sum(np.sin(2*np.pi*fq*x)*np.exp(-(1 + i*0.3)*x) for i, fq in enumerate((1318.5, 1975.5, 2637.0)))/3, 0.1, vol=0.07)
    # blade hum for Ren, glitch-out on "ignores me"
    n = int(3.9*SR); x = tv(n)
    add((np.sin(2*np.pi*110*x) + 0.5*np.sin(2*np.pi*220.7*x))*env(n, 0.3, 0.1), 16.6, vol=0.05)
    add(TAIKO, 16.6 + 3.9, vol=0.3)
    # Kuro heartbeat
    for i in range(6):
        tb = 30.0 + i/1.1
        add(KICK[:int(0.25*SR)], tb + 0.12, vol=0.3); add(KICK[:int(0.25*SR)], tb + 0.32, vol=0.2)
    # Hollow King drone + hit
    n = int(5.4*SR); x = tv(n)
    add((saw(note(40), 5.4, 5) + 0.5*np.sin(2*np.pi*note(47)*x*(1 + 0.003*np.sin(2*np.pi*5*x))))*env(n, 0.8, 1.0), 35.6, vol=0.08)
    n = int(2.0*SR); x = tv(n)
    add(np.sin(2*np.pi*np.cumsum(40 + 50*np.exp(-6*x))/SR)*np.exp(-2*x), 38.6, vol=0.5)
    # Mire spear glint
    n = int(1.0*SR); x = tv(n)
    add(sum(np.sin(2*np.pi*fq*x) for fq in (2400, 3600))*np.exp(-5*x)/2, 41.0 + 3.4, vol=0.08)
    # hook riser into NEXT
    dur = 6.4; n = int(dur*SR); f = np.linspace(150, 1100, n)
    add((np.sin(2*np.pi*np.cumsum(f)/SR)*0.2 + whoosh(dur, True)*0.5)*np.linspace(0.05, 1, n)**2, 46.2, vol=0.3)
    n = int(3.5*SR); x = tv(n)
    add(np.sin(2*np.pi*55*x)*np.exp(-1.6*x) + 0.5*whoosh(3.5, False)*np.exp(-2*x), 52.6, vol=0.6)
    for i, m in enumerate([64, 71, 76, 79, 83]):
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
