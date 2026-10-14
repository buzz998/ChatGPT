import math, random, subprocess, re, wave, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from script import SCENES

W, H, FPS, SR = 1920, 1080, 30, 24000
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
_fc = {}
def F(s):
    if s not in _fc: _fc[s] = ImageFont.truetype(FONT, s)
    return _fc[s]

ACC = {"intro": (120, 170, 255), "steam": (255, 138, 61), "electric": (255, 210, 63),
       "info": (61, 214, 255), "ai": (170, 110, 255), "timeline": (120, 170, 255),
       "criteria": (170, 110, 255), "apps": (61, 214, 255), "impact": (255, 110, 90),
       "advice": (90, 220, 150), "outro": (170, 110, 255)}

# ---------------- audio ----------------
def decode(p):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", p, "-f", "s16le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768

HEAD, GAP, TAIL = 0.6, 0.35, 0.9
timeline = []   # per scene: dict(start, dur, lines=[(t0,t1,text)])
voice = []
t = 0.0
for i, (kind, title, lines) in enumerate(SCENES):
    sc = {"kind": kind, "title": title, "start": t, "lines": []}
    local = HEAD
    chunks = [np.zeros(int(HEAD * SR), np.float32)]
    for j, text in enumerate(lines):
        a = decode(f"aud/{i:02d}_{j:02d}.mp3")
        d = len(a) / SR
        sc["lines"].append((local, local + d, text))
        chunks += [a, np.zeros(int(GAP * SR), np.float32)]
        local += d + GAP
    chunks.append(np.zeros(int(TAIL * SR), np.float32))
    local += TAIL
    seg = np.concatenate(chunks)
    sc["dur"] = len(seg) / SR
    voice.append(seg)
    timeline.append(sc)
    t += sc["dur"]
TOTAL = t
voice = np.concatenate(voice)

# soft synth pad: Am - F - C - G
n = len(voice); tt = np.arange(n) / SR
chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
bar = 6.0
music = np.zeros(n, np.float32)
for k in range(int(TOTAL / bar) + 1):
    s, e = int(k * bar * SR), min(n, int((k + 1) * bar * SR + 1.5 * SR))
    if s >= n: break
    x = tt[s:e] - k * bar
    env = np.minimum(1, x / 1.5) * np.clip((bar + 1.5 - x) / 1.5, 0, 1)
    for f in chords[k % 4]:
        music[s:e] += (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * f * 2 * x + 1)) * env
    music[s:e] += 0.6 * np.sin(2 * np.pi * chords[k % 4][0] / 2 * x) * env
music *= 0.025 * np.minimum(1, tt / 3) * np.minimum(1, (TOTAL - tt) / 3)
mix = np.clip(voice * 0.95 + music, -1, 1)
with wave.open("mix.wav", "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("total seconds", round(TOTAL, 1))

# ---------------- helpers ----------------
def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def lerp(a, b, x): return tuple(int(a[i] + (b[i] - a[i]) * x) for i in range(len(a)))

def text_layer(s, size, color=(255, 255, 255), stroke=0):
    f = F(size)
    b = f.getbbox(s, stroke_width=stroke)
    im = Image.new("RGBA", (b[2] - b[0] + 8, b[3] - b[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - b[0], 4 - b[1]), s, font=f, fill=color + (255,),
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
    return im

_tl = {}
def T(s, size, color=(255, 255, 255)):
    k = (s, size, color)
    if k not in _tl: _tl[k] = text_layer(s, size, color)
    return _tl[k]

def paste(img, layer, x, y, a=1.0, anchor="lt"):
    if a <= 0.01: return
    if anchor == "mm": x, y = x - layer.width // 2, y - layer.height // 2
    elif anchor == "mt": x = x - layer.width // 2
    if a < 0.99:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    img.paste(layer, (int(x), int(y)), layer)

def glow(r, color):
    g = np.linspace(-1, 1, 2 * r)
    d = np.sqrt(g[None, :] ** 2 + g[:, None] ** 2)
    al = np.clip(1 - d, 0, 1) ** 2.2 * 255
    im = np.zeros((2 * r, 2 * r, 4), np.uint8)
    im[..., :3] = color; im[..., 3] = al.astype(np.uint8)
    return Image.fromarray(im, "RGBA")
_gl = {}
def G(r, color):
    k = (r, color)
    if k not in _gl: _gl[k] = glow(r, color)
    return _gl[k]

# background
yy, xx = np.mgrid[0:H, 0:W]
vig = np.clip(1 - ((xx - W / 2) ** 2 / (W * 0.75) ** 2 + (yy - H / 2) ** 2 / (H * 0.85) ** 2), 0.25, 1)
bgarr = np.zeros((H, W, 3), np.float32)
bgarr[..., 0] = 10 + 8 * yy / H; bgarr[..., 1] = 14 + 6 * yy / H; bgarr[..., 2] = 30 + 14 * yy / H
bgarr *= vig[..., None]
grid = ((xx % 80 == 0) | (yy % 80 == 0))
bgarr[grid] += 9
BG = Image.fromarray(np.clip(bgarr, 0, 255).astype(np.uint8), "RGB")

random.seed(7)
PARTS = [(random.random() * W, random.random() * H, random.uniform(8, 30), random.uniform(1, 3), random.random() * 6.28)
         for _ in range(90)]

def particles(d, T_, color):
    for x, y, sp, r, ph in PARTS:
        px = (x + T_ * sp) % W
        py = (y - T_ * sp * 0.4 + 10 * math.sin(T_ * 0.5 + ph)) % H
        b = 0.35 + 0.35 * math.sin(T_ * 1.3 + ph)
        c = lerp((20, 26, 48), color, b * 0.6)
        d.ellipse([px - r, py - r, px + r, py + r], fill=c)

# ---------------- icons ----------------
def gear(d, cx, cy, r, teeth, ang, color, hole=(14, 20, 38)):
    pts = []
    for k in range(teeth * 4):
        a = ang + k * 2 * math.pi / (teeth * 4)
        rr = r if (k % 4) in (1, 2) else r * 0.8
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color)
    d.ellipse([cx - r * .35, cy - r * .35, cx + r * .35, cy + r * .35], fill=hole)

def scene_steam(img, d, t, sc, acc):
    cx, cy = 1350, 520
    paste(img, G(380, acc), cx - 380, cy - 380, 0.25)
    gear(d, cx, cy, 200, 12, t * 0.6, acc)
    gear(d, cx + 300, cy - 150, 120, 8, -t * 1.0 + 0.2, lerp(acc, (255, 255, 255), .25))
    gear(d, cx - 230, cy + 250, 100, 7, -t * 1.2, lerp(acc, (60, 40, 30), .3))
    # steam puffs
    for k in range(7):
        ph = (t * 0.35 + k / 7) % 1
        x = cx + 330 + 40 * math.sin(ph * 6 + k); y = cy - 300 - ph * 300
        r = 20 + 60 * ph
        paste(img, G(int(r), (220, 220, 230)), x - r, y - r, (1 - ph) * 0.5)

def scene_electric(img, d, t, sc, acc):
    cx, cy = 1350, 480
    flick = 0.75 + 0.25 * math.sin(t * 9) * math.sin(t * 3.3)
    paste(img, G(400, acc), cx - 400, cy - 400, 0.35 * flick)
    d.ellipse([cx - 150, cy - 170, cx + 150, cy + 130], fill=lerp((60, 50, 20), acc, flick))
    d.rectangle([cx - 70, cy + 110, cx + 70, cy + 210], fill=(150, 150, 165))
    for k in range(4):
        d.line([cx - 70, cy + 130 + k * 22, cx + 70, cy + 130 + k * 22], fill=(90, 90, 105), width=6)
    d.line([cx - 40, cy + 40, cx - 20, cy - 60, cx, cy + 20, cx + 20, cy - 60, cx + 40, cy + 40],
           fill=(255, 255, 230), width=7)
    # assembly line
    y0 = 860
    d.rectangle([900, y0, 1820, y0 + 14], fill=(70, 80, 110))
    for k in range(6):
        x = 900 + ((t * 120 + k * 160) % 920)
        d.rounded_rectangle([x - 50, y0 - 50, x + 50, y0 - 6], 10, fill=lerp(acc, (40, 40, 60), .35))
        d.ellipse([x - 40, y0 - 18, x - 16, y0 + 6], fill=(30, 30, 40))
        d.ellipse([x + 16, y0 - 18, x + 40, y0 + 6], fill=(30, 30, 40))

def scene_info(img, d, t, sc, acc):
    cx, cy = 1350, 520
    paste(img, G(360, acc), cx - 360, cy - 360, 0.22)
    traces = []
    for k in range(6):
        o = -150 + k * 60
        traces += [((cx + o, cy - 150), (cx + o, cy - 380)), ((cx + o, cy + 150), (cx + o, cy + 380)),
                   ((cx - 150, cy + o), (cx - 420, cy + o)), ((cx + 150, cy + o), (cx + 420, cy + o))]
    for a, b in traces:
        d.line([a, b], fill=lerp((30, 40, 70), acc, .35), width=4)
        d.ellipse([b[0] - 9, b[1] - 9, b[0] + 9, b[1] + 9], outline=acc, width=3)
    for idx, (a, b) in enumerate(traces):
        p = (t * 0.6 + idx * 0.137) % 1
        x, y = b[0] + (a[0] - b[0]) * p, b[1] + (a[1] - b[1]) * p
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(230, 250, 255))
    d.rounded_rectangle([cx - 170, cy - 170, cx + 170, cy + 170], 24, fill=(22, 34, 58), outline=acc, width=5)
    paste(img, T("CPU", 90, acc), cx, cy, 1, "mm")
    for k in range(10):
        s = "".join(random.Random(int(t * 4) * 31 + k).choice("01") for _ in range(10))
        paste(img, T(s, 26, lerp(acc, (14, 20, 38), .5)), 900 + (k % 2) * 760, 150 + k * 75, .5)

NET = None
def scene_ai(img, d, t, sc, acc, cx=1350, cy=520, scale=1.0, alpha=1.0):
    global NET
    layers = [4, 6, 6, 3]
    pos = [[(cx + (li - 1.5) * 220 * scale, cy + (ni - (n - 1) / 2) * 110 * scale) for ni in range(n)]
           for li, n in enumerate(layers)]
    paste(img, G(int(420 * scale), acc), cx - 420 * scale, cy - 420 * scale, 0.25 * alpha)
    edges = [(a, b) for li in range(3) for a in pos[li] for b in pos[li + 1]]
    for a, b in edges:
        d.line([a, b], fill=lerp((20, 26, 48), acc, .3 * alpha), width=2)
    rnd = random.Random(3)
    for k, (a, b) in enumerate(edges):
        if rnd.random() > 0.35: continue
        p = (t * 0.7 + rnd.random()) % 1
        x, y = a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p
        d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=lerp((20, 26, 48), (255, 255, 255), alpha))
    for li, col in enumerate(pos):
        for ni, (x, y) in enumerate(col):
            pulse = 0.5 + 0.5 * math.sin(t * 3 - li * 1.2 + ni)
            r = 22 * scale
            d.ellipse([x - r, y - r, x + r, y + r], fill=lerp((20, 26, 48), lerp(acc, (255, 255, 255), pulse * .4), alpha))

def era_left(img, d, t, sc, num, years, tags, acc):
    a = ease(t / 0.8)
    paste(img, T(num, 300, lerp((14, 20, 38), acc, .55)), 140 - (1 - a) * 80, 130, a)
    paste(img, T(sc["title"], 84), 150, 470, ease((t - .3) / .8))
    paste(img, T(years, 44, acc), 154, 590, ease((t - .6) / .8))
    for k, tag in enumerate(tags):
        ap = ease((t - 1.2 - k * .5) / .6)
        x = 154 + k * 190
        if ap > 0:
            d.rounded_rectangle([x, 680, x + 170, 744], 32, outline=lerp((14, 20, 38), acc, ap), width=3)
            paste(img, T(tag, 34), x + 85, 712, ap, "mm")

def scene_intro(img, d, t, sc, acc):
    split = sc["lines"][2][0]
    if t < split:
        a = ease(t / 1.2) * (1 - ease((t - split + .8) / .8))
        gear(d, W // 2, 470, 260, 14, t * .3, lerp((14, 20, 38), (255, 138, 61), .35 * a))
        paste(img, T("1769", 240, lerp((14, 20, 38), (255, 200, 150), a)), W // 2, 470, 1, "mm")
        paste(img, T("蒸汽机 · 一个时代的开端", 46, (220, 220, 230)), W // 2, 650, a * ease((t - 1) / 1), "mt")
    else:
        u = t - split
        scene_ai(img, d, t, sc, acc, W // 2, 470, 1.1, ease(u / 1.5) * 0.22)
        paste(img, T("AI", 260, (255, 255, 255)), W // 2, 400, ease(u / 1.0), "mm")
        paste(img, T("第四次工业革命", 110, acc), W // 2, 600, ease((u - .6) / 1.0), "mt")

def scene_timeline(img, d, t, sc, acc):
    y = 560; xs = [300, 740, 1180, 1620]
    eras = [("1760s", "蒸汽", ACC["steam"]), ("1870s", "电力", ACC["electric"]),
            ("1950s", "信息", ACC["info"]), ("2020s", "智能", ACC["ai"])]
    p = ease(t / 4)
    d.line([200, y, 200 + (1720 - 200) * p, y], fill=(90, 110, 160), width=6)
    for k, (x, (yr, nm, c)) in enumerate(zip(xs, eras)):
        a = ease((t - k * 0.9) / 0.6)
        if a <= 0: continue
        r = 30 + (14 * (0.5 + 0.5 * math.sin(t * 4)) if k == 3 else 0)
        paste(img, G(110, c), x - 110, y - 110, .4 * a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=lerp((14, 20, 38), c, a))
        paste(img, T(yr, 52, c), x, y - 150, a, "mt")
        paste(img, T(nm, 64), x, y + 70, a, "mt")
    # interval shrinking labels
    gaps = ["≈110年", "≈80年", "≈70年"]
    s3 = sc["lines"][1][0]
    for k in range(3):
        a = ease((t - s3 - k * .4) / .6)
        paste(img, T(gaps[k], 40, (180, 190, 220)), (xs[k] + xs[k + 1]) / 2, y - 60, a, "mt")
    s4 = sc["lines"][2][0]
    a = ease((t - s4) / .8)
    paste(img, T("间隔在缩短 · 影响在扩大", 56, acc), W // 2, 830, a, "mt")

def title_top(img, sc, t, acc):
    a = ease(t / .8)
    paste(img, T(sc["title"], 76), W // 2, 110 - (1 - a) * 30, a, "mt")
    d = ImageDraw.Draw(img)
    w = 160 * a
    d.rectangle([W / 2 - w, 215, W / 2 + w, 221], fill=acc)

def cards(img, d, t, sc, acc, items, start_line=1):
    n = len(items); cw = 480; gap = 60
    x0 = (W - (n * cw + (n - 1) * gap)) // 2
    for k, (big, head, sub) in enumerate(items):
        st = sc["lines"][min(start_line + k, len(sc["lines"]) - 1)][0] if start_line is not None else 0.5 + k * 0.4
        a = ease((t - st) / .7)
        if a <= 0: continue
        x = x0 + k * (cw + gap); y = 320 + (1 - a) * 60
        d.rounded_rectangle([x, y, x + cw, y + 480], 28, fill=lerp((10, 14, 30), (26, 34, 64), a),
                            outline=lerp((10, 14, 30), acc, a), width=3)
        paste(img, T(big, 120, acc), x + cw / 2, y + 50, a, "mt")
        paste(img, T(head, 56), x + cw / 2, y + 220, a, "mt")
        for j, s in enumerate(sub.split("\n")):
            paste(img, T(s, 34, (180, 190, 220)), x + cw / 2, y + 320 + j * 50, a, "mt")

def scene_criteria(img, d, t, sc, acc):
    title_top(img, sc, t, acc)
    cards(img, d, t, sc, acc, [("01", "通用技术", "像电力一样\n渗透每个行业"),
                               ("02", "成本骤降", "几天的工作\n变成几分钟"),
                               ("03", "重塑分工", "人与机器的边界\n被重新划定")])

def scene_apps(img, d, t, sc, acc):
    title_top(img, sc, t, acc)
    items = [("🧬", "生命科学", "AlphaFold\n2亿+蛋白质结构", 1), ("</>", "软件开发", "AI 参与\n编写代码", 2),
             ("⚙", "智能制造", "质检·调度", 3), ("✚", "医疗", "辅助诊断", 3), ("✎", "教育", "个性化辅导", 3),
             ("☎", "客服", "7×24 小时", 3)]
    cw, ch = 520, 300
    for k, (ic, head, sub, li) in enumerate(items):
        st = sc["lines"][li][0] + (k - 2) * 0.35 * (li == 3)
        a = ease((t - st) / .6)
        if a <= 0: continue
        x = 160 + (k % 3) * (cw + 40); y = 290 + (k // 3) * (ch + 40) + (1 - a) * 40
        d.rounded_rectangle([x, y, x + cw, y + ch], 24, fill=lerp((10, 14, 30), (24, 34, 60), a),
                            outline=lerp((10, 14, 30), acc, a * .8), width=3)
        if ic == "🧬":
            for j in range(14):  # tiny helix
                yy_ = y + 60 + j * 14; ph = t * 2 + j * .6
                x1 = x + 90 + 40 * math.sin(ph); x2 = x + 90 - 40 * math.sin(ph)
                d.line([x1, yy_, x2, yy_], fill=lerp((10, 14, 30), (120, 140, 190), a), width=2)
                d.ellipse([x1 - 6, yy_ - 6, x1 + 6, yy_ + 6], fill=lerp((10, 14, 30), acc, a))
                d.ellipse([x2 - 6, yy_ - 6, x2 + 6, yy_ + 6], fill=lerp((10, 14, 30), (255, 150, 200), a))
        elif ic == "⚙":
            gear(d, x + 90, y + ch / 2, 55, 9, t * .8, lerp((10, 14, 30), acc, a), hole=(24, 34, 60))
        elif ic == "✚":
            c = lerp((10, 14, 30), acc, a); mx, my = x + 90, y + ch / 2
            d.rectangle([mx - 16, my - 50, mx + 16, my + 50], fill=c); d.rectangle([mx - 50, my - 16, mx + 50, my + 16], fill=c)
        elif ic == "✎":
            c = lerp((10, 14, 30), acc, a); mx, my = x + 90, y + ch / 2
            d.polygon([(mx - 60, my - 40), (mx - 4, my - 28), (mx - 4, my + 46), (mx - 60, my + 34)], outline=c, width=5)
            d.polygon([(mx + 60, my - 40), (mx + 4, my - 28), (mx + 4, my + 46), (mx + 60, my + 34)], outline=c, width=5)
        else:
            paste(img, T(ic, 90, acc), x + 90, y + ch / 2, a, "mm")
        paste(img, T(head, 52), x + 190, y + 70, a)
        for j, s in enumerate(sub.split("\n")):
            paste(img, T(s, 34, (180, 190, 220)), x + 190, y + 150 + j * 48, a)

def scene_impact(img, d, t, sc, acc):
    title_top(img, sc, t, acc)
    base = 860; x0 = 260
    s2 = sc["lines"][1][0]; s3 = sc["lines"][2][0]; s4 = sc["lines"][3][0]
    # Luddite gear cracked
    a = ease((t - s2) / .6) * (1 - ease((t - s3 + .3) / .6))
    if a > 0:
        gear(d, W // 2, 560, 200, 12, 0.1, lerp((14, 20, 38), (150, 120, 100), a))
        d.line([W // 2 - 80, 380, W // 2 + 10, 560, W // 2 - 30, 620, W // 2 + 60, 760], fill=(14, 20, 38), width=14)
        paste(img, T("卢德运动 · 1811", 50, lerp((14, 20, 38), acc, a)), W // 2, 800, a, "mt")
    b = ease((t - s3) / .8)
    if b > 0:
        for k in range(8):
            h1 = 300 * (1 - 0.7 * ease((t - s3 - k * .1) / 1.5)) * (0.6 + 0.4 * ((k * 37) % 7) / 7)
            x = x0 + k * 80
            d.rectangle([x, base - h1, x + 56, base], fill=lerp((14, 20, 38), (120, 130, 160), b))
        for k in range(8):
            h2 = 360 * ease((t - s3 - .5 - k * .12) / 1.5) * (0.5 + 0.5 * ((k * 53) % 9) / 9)
            x = 1040 + k * 80
            d.rectangle([x, base - h2, x + 56, base], fill=lerp((14, 20, 38), ACC["advice"], b))
        paste(img, T("消失的岗位", 46, (180, 190, 220)), x0 + 300, base + 30, b, "mt")
        paste(img, T("新职业", 46, ACC["advice"]), 1340, base + 30, b, "mt")
    c = ease((t - s4) / .6)
    if c > 0:
        paste(img, T("这一次，更快", 80, acc), W // 2, 300, c, "mt")

def scene_advice(img, d, t, sc, acc):
    title_top(img, sc, t, acc)
    items = ["学会与 AI 协作", "提出好问题", "守住判断力与创造力", "终身学习"]
    for k, s in enumerate(items):
        st = sc["lines"][k + 1][0]
        a = ease((t - st) / .6)
        if a <= 0: continue
        y = 320 + k * 140; x = 560 - (1 - a) * 60
        d.rounded_rectangle([x, y, x + 84, y + 84], 18, outline=lerp((14, 20, 38), acc, a), width=5)
        ck = ease((t - st - .4) / .4)
        if ck > 0:
            d.line([x + 18, y + 44, x + 36, y + 64, x + 36 + 34 * ck, y + 64 - 44 * ck], fill=acc, width=9)
        paste(img, T(s, 62), x + 130, y + 8, a)

def scene_outro(img, d, t, sc, acc):
    s2 = sc["lines"][1][0]
    a = ease(t / 1) * (1 - ease((t - s2 + .5) / .6))
    paste(img, T("拒绝改变，才会被淘汰", 90, (230, 230, 240)), W // 2, 420, a, "mt")
    u = t - s2
    if u > 0:
        # train of light
        for k in range(30):
            x = (u * 900 - k * 70)
            if -50 < x < W + 50:
                d.rounded_rectangle([x, 640, x + 56, 676], 8, fill=lerp((14, 20, 38), acc, max(0, 1 - k / 30)))
        d.line([0, 690, W, 690], fill=(60, 70, 110), width=4)
        paste(img, T("AI · 第四次工业革命", 110), W // 2, 360, ease(u / 1), "mt")
        s3 = sc["lines"][2][0]
        paste(img, T("你准备好了吗？", 72, acc), W // 2, 780, ease((t - s3) / .8), "mt")

DRAW = {"intro": scene_intro, "steam": None, "electric": None, "info": None, "ai": None,
        "timeline": scene_timeline, "criteria": scene_criteria, "apps": scene_apps,
        "impact": scene_impact, "advice": scene_advice, "outro": scene_outro}
ERA = {"steam": ("01", "1760s — 1840s", ["蒸汽机", "纺织", "铁路"], scene_steam),
       "electric": ("02", "1870s — 1910s", ["电力", "内燃机", "流水线"], scene_electric),
       "info": ("03", "1950s — 2010s", ["计算机", "互联网", "手机"], scene_info),
       "ai": ("04", "2020s —", ["大模型", "机器人", "AI 科学"], scene_ai)}

# subtitles: split long lines at punctuation, time by char count
SUBS = []
for sc in timeline:
    for t0, t1, text in sc["lines"]:
        parts = [p for p in re.split(r"(?<=[，。？；])", text) if p.strip()]
        merged = []
        for p in parts:
            if merged and len(merged[-1]) + len(p) <= 20: merged[-1] += p
            else: merged.append(p)
        tot = sum(len(p) for p in merged); c = t0
        for p in merged:
            dd = (t1 - t0) * len(p) / tot
            SUBS.append((sc["start"] + c, sc["start"] + c + dd, p.rstrip("，。；")))
            c += dd

_sl = {}
def sub_layer(s):
    if s not in _sl: _sl[s] = text_layer(s, 50, (255, 255, 255), stroke=3)
    return _sl[s]

def frame(T_):
    img = BG.copy(); d = ImageDraw.Draw(img)
    sc = next(s for s in timeline if s["start"] <= T_ < s["start"] + s["dur"]) if T_ < TOTAL else timeline[-1]
    t = T_ - sc["start"]; acc = ACC[sc["kind"]]
    particles(d, T_, acc)
    k = sc["kind"]
    if k in ERA:
        num, yrs, tags, fn = ERA[k]
        fn(img, d, t, sc, acc)
        era_left(img, d, t, sc, num, yrs, tags, acc)
    else:
        DRAW[k](img, d, t, sc, acc)
    # progress bar
    d.rectangle([0, H - 6, W * T_ / TOTAL, H], fill=acc)
    for s0, s1, s in SUBS:
        if s0 <= T_ < s1:
            L = sub_layer(s)
            paste(img, L, W // 2, 960, 1, "mt"); break
    # fade between scenes
    f = min(1, t / .4, (sc["dur"] - t) / .4)
    if f < 1:
        img = Image.blend(Image.new("RGB", (W, H)), img, max(0, f))
    return img

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for sc in timeline:
            frame(sc["start"] + sc["dur"] * 0.8).save(f"prev_{sc['kind']}.jpg", quality=80)
        sys.exit()
    nfr = int(TOTAL * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-i", "mix.wav", "-c:v", "libx264", "-preset", "medium",
                          "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                          "-shortest", "-movflags", "+faststart", "out.mp4"], stdin=subprocess.PIPE)
    for i in range(nfr):
        p.stdin.write(frame(i / FPS).tobytes())
        if i % 300 == 0: print(f"{i}/{nfr}", flush=True)
    p.stdin.close(); p.wait()
