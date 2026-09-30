import math, random, subprocess, os, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SR = 44100
OUT = "./count_the_stars_short.mp4"
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
WORDS = ["One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten"]
STAR_COLORS = [(255,205,60),(255,140,170),(120,210,255),(160,230,120),(200,160,255),
               (255,170,90),(255,230,100),(110,230,210),(255,120,120),(180,200,255)]
random.seed(7)

from functools import lru_cache
@lru_cache(None)
def font(sz): return ImageFont.truetype(FONT, max(4, sz))

# ---------- timeline ----------
INTRO, OUTRO = 5.0, 6.0
POP_GAP, PRE, POST = 0.42, 1.1, 1.4
segs, t = [], INTRO
for n in range(1, 11):
    dur = PRE + n * POP_GAP + POST
    segs.append((n, t, dur)); t += dur
TOTAL = t + OUTRO
NFR = int(TOTAL * FPS)

# ---------- art ----------
def star_poly(cx, cy, r, rot=0.0, inner=0.48):
    pts = []
    for i in range(10):
        a = rot - math.pi/2 + i*math.pi/5
        rr = r if i % 2 == 0 else r*inner
        pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a)))
    return pts

def make_star(r, color, face=True):
    s = int(r*2.6); im = Image.new("RGBA", (s, s), (0,0,0,0))
    glow = Image.new("RGBA", (s, s), (0,0,0,0))
    ImageDraw.Draw(glow).polygon(star_poly(s/2, s/2, r*1.05), fill=color+(120,))
    glow = glow.filter(ImageFilter.GaussianBlur(r*0.18))
    im.alpha_composite(glow)
    d = ImageDraw.Draw(im)
    d.polygon(star_poly(s/2, s/2+r*0.04, r), fill=tuple(max(0,c-45) for c in color))
    d.polygon(star_poly(s/2, s/2, r), fill=color)
    hl = Image.new("RGBA", (s, s), (0,0,0,0))
    ImageDraw.Draw(hl).ellipse([s/2-r*0.45, s/2-r*0.55, s/2-r*0.1, s/2-r*0.3], fill=(255,255,255,110))
    hl = hl.filter(ImageFilter.GaussianBlur(r*0.05)); im.alpha_composite(hl); d = ImageDraw.Draw(im)
    if face:
        e = r*0.09; cx, cy = s/2, s/2+r*0.05
        for dx in (-r*0.22, r*0.22):
            d.ellipse([cx+dx-e, cy-e*1.3, cx+dx+e, cy+e*1.3], fill=(60,40,70))
            d.ellipse([cx+dx-e*0.4, cy-e*1.0, cx+dx+e*0.2, cy-e*0.3], fill=(255,255,255))
        d.arc([cx-r*0.18, cy+r*0.02, cx+r*0.18, cy+r*0.28], 20, 160, fill=(60,40,70), width=max(2,int(r*0.05)))
        for dx in (-r*0.38, r*0.38):
            d.ellipse([cx+dx-r*0.09, cy+r*0.08, cx+dx+r*0.09, cy+r*0.2], fill=(255,120,150,130))
    return im

def background():
    bg = Image.new("RGB", (W, H))
    top, bot = np.array([40,30,110]), np.array([110,70,170])
    g = np.linspace(0,1,H)[:,None]
    arr = (top*(1-g) + bot*g).astype(np.uint8)
    bg = Image.fromarray(np.repeat(arr[:,None,:], W, axis=1).reshape(H,W,3))
    d = ImageDraw.Draw(bg)
    for _ in range(160):
        x, y, r = random.randint(0,W), random.randint(0,H-200), random.choice([1,1,2,2,3])
        d.ellipse([x-r,y-r,x+r,y+r], fill=(255,255,230))
    # moon
    m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
    md.ellipse([820,90,1000,270], fill=255); md.ellipse([870,75,1050,255], fill=0)
    bg.paste((255,245,200), mask=m); d = ImageDraw.Draw(bg)
    # hills
    d.ellipse([-500,1680,800,2300], fill=(70,150,120)); d.ellipse([300,1720,1600,2400], fill=(55,130,110))
    return bg.convert("RGBA")

BG = background()
SPRITES = [make_star(78, c) for c in STAR_COLORS]
HERO = make_star(170, (255,205,60))

def paste_scaled(canvas, sprite, cx, cy, scale, rot=0):
    if scale <= 0.02: return
    sz = max(2, int(sprite.width*scale))
    sp = sprite.resize((sz, sz), Image.BILINEAR)
    if rot: sp = sp.rotate(rot, resample=Image.BILINEAR)
    canvas.alpha_composite(sp, (int(cx-sz/2), int(cy-sz/2)))

def pop(x):  # 0..1 -> springy scale
    if x <= 0: return 0
    if x >= 1: return 1
    return 1 + math.sin(x*math.pi*1.5)*0.25*(1-x) if x > 0.35 else (x/0.35)*1.2

def text_center(d, txt, y, sz, fill, stroke=(40,25,80), sw=10):
    f = font(sz); w = d.textlength(txt, font=f)
    d.text(((W-w)/2, y), txt, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke)

def star_positions(n):
    rows = [3]*(n//3) + ([n%3] if n%3 else [])
    pos, y0 = [], 880
    for ri, cnt in enumerate(rows):
        gap = 290
        x0 = W/2 - gap*(cnt-1)/2
        for i in range(cnt): pos.append((x0+i*gap, y0+ri*250))
    return pos

# ---------- render ----------
proc = subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24",
    "-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","medium","-crf","20",
    "-pix_fmt","yuv420p","./_video_v.mp4"], stdin=subprocess.PIPE)

for fi in range(NFR):
    t = fi/FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    # twinkle overlay
    for k in range(12):
        x, y = (k*397)%W, 60+(k*211)%600
        a = (math.sin(t*3+k)+1)/2
        r = 3+4*a; d.polygon(star_poly(x,y,r*2), fill=(255,255,220,int(120+120*a)))
    if t < INTRO:
        s = pop(t/0.9); bob = math.sin(t*3)*15
        paste_scaled(im, HERO, W/2, 750+bob, s, math.sin(t*2)*6)
        if t > 1.0:
            text_center(d, "Count the Stars!", 1080, 120, (255,230,120))
        if t > 1.8:
            text_center(d, "Count 1 to 10 with Twinkle!", 1260, 58, (255,255,255), sw=6)
    elif t >= TOTAL-OUTRO:
        lt = t-(TOTAL-OUTRO); bob = math.sin(t*3)*15
        paste_scaled(im, HERO, W/2, 720+bob, pop(lt/0.9), math.sin(t*4)*10)
        if lt > 0.8: text_center(d, "Great counting!", 1060, 120, (255,230,120))
        if lt > 1.8: text_center(d, "You counted all 10 stars!", 1240, 60, (255,255,255), sw=6)
        if lt > 3.0: text_center(d, "Subscribe for more!", 1350, 56, (200,235,255), sw=5)
    else:
        for n, st, dur in segs:
            if st <= t < st+dur: break
        lt = t-st; col = STAR_COLORS[n-1]
        ns = pop(lt/0.6)
        if ns > 0:
            f = font(int(250*ns)); txt = str(n); w = d.textlength(txt, font=f)
            d.text(((W-w)/2, 200+(250-250*ns)/2), txt, font=f, fill=col, stroke_width=14, stroke_fill=(40,25,80))
        if lt > 0.4:
            text_center(d, WORDS[n-1], 500, 100, (255,255,255), sw=8)
        for i, (x, y) in enumerate(star_positions(n)):
            at = PRE + i*POP_GAP
            if lt >= at:
                bob = math.sin(t*3+i)*6
                paste_scaled(im, SPRITES[(n-1+i)%10], x, y+bob, pop((lt-at)/0.5))
                if lt - at < 0.9:  # running count bubble
                    cf = font(54); c = str(i+1); cw = d.textlength(c, font=cf)
                    a = int(255*(1-(lt-at)/0.9))
                    d.text((x-cw/2, y-190-(lt-at)*40), c, font=cf, fill=(255,255,255,a), stroke_width=5, stroke_fill=(40,25,80,a))
        # fade out/in edges
    proc.stdin.write(im.convert("RGB").tobytes())
proc.stdin.close(); proc.wait()

# ---------- audio ----------
N = int(TOTAL*SR); audio = np.zeros(N)
def tone(freq, dur, vol=0.2, shape="sine", decay=6):
    tt = np.arange(int(dur*SR))/SR
    w = np.sin(2*np.pi*freq*tt)
    if shape == "bell": w += 0.4*np.sin(2*np.pi*freq*2*tt) + 0.15*np.sin(2*np.pi*freq*3*tt)
    env = np.exp(-decay*tt) * np.minimum(1, tt*200)
    return vol*w*env
def add(sig, at):
    i = int(at*SR); j = min(N, i+len(sig)); audio[i:j] += sig[:j-i]

# gentle original background melody (C major pentatonic, music-box feel)
notes = {"C":523.25,"D":587.33,"E":659.25,"G":783.99,"A":880.0,"C2":1046.5}
tune = ["C","E","G","E","A","G","E","D","C","D","E","G","E","D","C","G"]
bass = [130.81, 174.61, 196.0, 130.81]
beat = 0.5; k = 0
while k*beat < TOTAL-1:
    add(tone(notes[tune[k%16]], 0.9, 0.05, "bell", 4), k*beat)
    if k % 4 == 0: add(tone(bass[(k//4)%4], 1.9, 0.07, "sine", 1.5), k*beat)
    k += 1
# sfx
add(tone(784, 0.6, 0.18, "bell"), 0.1); add(tone(1046, 0.8, 0.18, "bell"), 1.0)
scale = [523.25,587.33,659.25,698.46,783.99,880,987.77,1046.5,1174.66,1318.5]
for n, st, dur in segs:
    add(tone(392, 0.5, 0.15, "bell"), st+0.05); add(tone(523, 0.7, 0.15, "bell"), st+0.2)
    for i in range(n):
        add(tone(scale[i], 0.35, 0.22, "bell", 9), st+PRE+i*POP_GAP)
for i, f in enumerate([523.25,659.25,783.99,1046.5,1318.5]):
    add(tone(f, 1.2, 0.18, "bell", 3), TOTAL-OUTRO+0.1+i*0.15)
fade = np.ones(N); fl = int(1.5*SR); fade[-fl:] = np.linspace(1,0,fl)
audio = np.clip(audio*fade/ max(1e-9, np.abs(audio).max())*0.85, -1, 1)
with wave.open("./_audio_v.wav","wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((audio*32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg","-y","-loglevel","error","-i","./_video_v.mp4","-i","./_audio_v.wav",
    "-c:v","copy","-c:a","aac","-b:a","192k","-shortest",OUT], check=True)
print("done", round(TOTAL,1))
