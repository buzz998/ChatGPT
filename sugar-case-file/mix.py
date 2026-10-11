"""《糖的案卷》配乐 + 音效 + 混音。
原创悬疑侦探配乐（D 小调，92 BPM）：钢琴低音固定音型 + 低音提琴拨奏 + 马林巴/羽管键琴主题 + 合成底鼓/拍手/踩镲 + 钟表滴答。
只借《夜的第七章》式的悬疑氛围，旋律、和声进行、节奏型均为原创。

时间轴与音效点全部来自 index.html（TL、CAPS）和 events.json（events.mjs 导出），改画面时间后重跑即可。
用法（库根目录）：.venv/bin/python films/sugar-case-file/mix.py
输出：out/music.wav  out/sfx.wav  out/mix.wav（有 voice/ 时含人声并对音乐做闪避）
"""
import json, os, re, sys
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.environ.get('LIB') or os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, limit, compress, noise, t_, env_exp, bp, lp, hp, norm, whoosh, click, clack, thump, ding, pop, creak, rumble

S.seed(11)
rng = np.random.default_rng(5)

# ---------------- 读时间轴 ----------------
src = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
TL = {k: float(v) for k, v in re.findall(r'(\w+):\s*([\d.]+)', re.search(r'const TL = window\.TL = \{(.*?)\};', src, re.S).group(1))}
CAPS = [(float(a), float(b), s) for a, b, s in re.findall(r"\[\s*([\d.]+),\s*([\d.]+),\s*'([^']*)'", re.search(r'const CAPS = \[(.*?)\n\];', src, re.S).group(1))]
EVJ = json.load(open(os.path.join(HERE, 'events.json')))
DUR = float(EVJ['dur']); EV = EVJ['ev']
N = int((DUR + 0.5) * SR)

BPM = 92; BEAT = 60 / BPM; BAR = 4 * BEAT; E8 = BEAT / 2; E16 = BEAT / 4

def buf(): return np.zeros((N, 2), np.float32)

# ---------------- 合成小件 ----------------
def kick(v=1.0):
    d = .45; tt = t_(d); f = 48 + 90 * np.exp(-tt / .035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(d, .16)
    x += hp(noise(d), 3000) * env_exp(d, .004) * .25
    return norm(np.tanh(x * 1.6)) * v

def tick(v=1.0, hi=True):
    d = .04; tt = t_(d); f = 3200 if hi else 2400
    return norm(np.sin(2 * np.pi * f * tt) * env_exp(d, .004) + hp(noise(d), 4000) * env_exp(d, .002) * .6) * v

def snap(v=1.0):
    d = .08; tt = t_(d)
    return norm(bp(noise(d), 1800, 5200) * env_exp(d, .009) + np.sin(2 * np.pi * 1450 * tt) * env_exp(d, .01) * .4) * v

def sqbass(midi, dur, v=1.0):
    f = 440 * 2 ** ((midi - 69) / 12); tt = t_(dur + .05)
    x = np.sign(np.sin(2 * np.pi * f * tt)) * .55 + np.sin(2 * np.pi * f * tt) * .8 + np.sin(4 * np.pi * f * tt) * .25
    e = np.minimum(1, tt / .004) * np.exp(-tt / (dur * .9)); e[-int(.05 * SR):] *= np.linspace(1, 0, int(.05 * SR))
    return lp(x * e, 1400) * v

def riser(d=.6, v=1.0):
    n = noise(d); tt = t_(d); out = np.zeros_like(n)
    for i in range(0, len(n), 480):
        hi = min(len(n), i + 480); f = 300 + 5000 * (i / len(n)) ** 2
        out[i:hi] = bp(n[max(0, i - 2000):hi], f * .8, f * 1.25)[-(hi - i):]
    return norm(out * (tt / d) ** 1.5) * v

# ---------------- 音效 ----------------
def stamp(big=False):
    d = .9; tt = t_(d)
    boom = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-tt / .12) + 38) / SR) * env_exp(d, .22)
    x = boom.copy()
    c = lp(clack(.75, 1.0), 5000); x[:len(c)] += c * .7
    x += lp(noise(d), 900) * env_exp(d, .05) * .6
    if big:
        cr = hp(noise(d), 1500) * (rng.random(len(tt)) > .985) * env_exp(d, .25) * 2.5
        x += lp(cr, 7000)
    return norm(np.tanh(x * 1.3))

def shutter():
    a = click(1.4, .9); b = click(.9, .7); out = np.zeros(int(.16 * SR)); out[:len(a)] += a; s = int(.07 * SR); out[s:s + len(b)] += b[:len(out) - s]
    return norm(out + hp(noise(.16), 2000) * env_exp(.16, .03) * .3)

def crinkle(d=.4):
    x = hp(noise(d), 2500) * (rng.random(int(d * SR)) > .97) * 3
    return norm(lp(x, 9000) * np.sin(np.pi * t_(d) / d))

def paper(d=.35):
    return norm(bp(noise(d), 1500, 6000) * np.sin(np.pi * t_(d) / d) ** 1.5)

def beep(f=1000, d=.12):
    tt = t_(d); x = np.sign(np.sin(2 * np.pi * f * tt)) * .5; x[-200:] *= np.linspace(1, 0, 200); return lp(x, 4000)

def alarm():
    out = np.zeros(int(.9 * SR))
    for k in range(4):
        b = beep(880 if k % 2 == 0 else 660, .2); s = int(k * .22 * SR); out[s:s + len(b)] += b
    return out

def boing():
    d = .5; tt = t_(d); f = 220 + 140 * np.sin(2 * np.pi * 9 * tt) * np.exp(-tt / .2)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(d, .18))

def squelch():
    d = .25; tt = t_(d); f = 300 - 200 * tt / d
    return norm(lp(noise(d), 900) * env_exp(d, .07) + np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(d, .06) * .6)

def munch():
    d = .14; return norm(bp(noise(d), 800, 4000) * (rng.random(int(d * SR)) > .9) * env_exp(d, .05) * 3)

def crack():
    c = clack(1.3, 1.0); x = np.zeros(int(.25 * SR)); x[:len(c)] += c; x += hp(noise(.25), 3000) * env_exp(.25, .02) * .7
    return norm(x)

def deflate():
    d = .9; tt = t_(d); f = 500 * np.exp(-tt / .4) + 90
    return norm(bp(noise(d), 300, 2000) * .4 * env_exp(d, .4) + np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * .25 * env_exp(d, .5))

def twang():
    return S.note('contrabass_pizz', 'D2', 1.2, vel=.9)

def tape():
    d = .3; return norm(hp(noise(d), 1200) * (rng.random(int(d * SR)) > .6) * np.linspace(1, .3, int(d * SR)))

def printer():
    d = .9; tt = t_(d); return norm(bp(noise(d), 600, 2500) * (np.sin(2 * np.pi * 14 * tt) > 0) * .8)

def gavel():
    c = clack(.55, 1.0); x = thump(1.0, 85); x[:len(c)] += c * 1.2; return norm(x)

def drawer():
    d = .8; x = lp(rumble(d), 400) * .8; t = thump(1.0, 60); s = int(.55 * SR); x[s:s + len(t)] += t[:len(x) - s] * 1.0; return norm(x)

SFX = buf()
for e in EV:
    t, ty = e['t'], e['type']
    if ty == 'stamp': add(SFX, stamp(e.get('big')), t - .02, .7)
    elif ty == 'stampSmall': add(SFX, stamp(False), t, .55)
    elif ty == 'shutter': add(SFX, shutter(), t, .55)
    elif ty == 'whoosh': add(SFX, whoosh(.4), t, .4)
    elif ty == 'wipe': add(SFX, whoosh(.44), t - .22, .3, .2)
    elif ty == 'bag': add(SFX, crinkle(.45), t - .1, .35)
    elif ty == 'plop': add(SFX, pop(.9), t, .4)
    elif ty == 'pop': add(SFX, pop(.9), t, .3, .3 * (e.get('n', 0) % 3 - 1))
    elif ty == 'scan': add(SFX, riser(.5), t, .2)
    elif ty == 'boom': add(SFX, thump(1.0, 55), t, .7)
    elif ty == 'ding': add(SFX, ding(.8), t, .16, -.4 + e.get('n', 0) * .1)
    elif ty == 'slam': add(SFX, thump(1.0, 70), t, .8); add(SFX, clack(1.0, 1.0), t, .5)
    elif ty == 'creak': add(SFX, creak(1.0), t, .3)
    elif ty == 'hit': add(SFX, thump(1.0, 60), t, .65)
    elif ty == 'riser': add(SFX, riser(.6), t, .22)
    elif ty == 'alarm': add(SFX, alarm(), t, .18, .4)
    elif ty == 'knock': add(SFX, clack(.5, 1.0), t, .45, -.3)
    elif ty == 'buzzer': add(SFX, beep(150, .45), t, .25)
    elif ty == 'paper': add(SFX, paper(.4), t, .35)
    elif ty == 'beep': add(SFX, beep(1150, .14), t, .12, .5)
    elif ty == 'boing': add(SFX, boing(), t, .35)
    elif ty == 'sticky': add(SFX, squelch(), t, .35, -.5 + e.get('n', 0) * .2)
    elif ty == 'munch': add(SFX, munch(), t, .4, .3 * ((e.get('n', 0) % 3) - 1))
    elif ty == 'crack': add(SFX, crack(), t, .45)
    elif ty == 'click': add(SFX, click(.8, 1.0), t, .5)
    elif ty == 'deflate': add(SFX, deflate(), t, .25)
    elif ty == 'pin': add(SFX, click(1.2, .9), t, .35, -.4 + e.get('n', 0) * .2)
    elif ty == 'twang': add(SFX, twang(), t, .6)
    elif ty == 'tape': add(SFX, tape(), t, .4)
    elif ty == 'printer': add(SFX, printer(), t, .2)
    elif ty == 'gavel': add(SFX, lp(gavel(), 5000), t, .6)
    elif ty == 'line': add(SFX, whoosh(.3), t, .25)
    elif ty == 'drawer': add(SFX, drawer(), t, .6)

# ---------------- 配乐 ----------------
M = buf(); notes = []
def nt(t, inst, p, d, v, pan=0.0, gain=1.0): notes.append((t, inst, p, d, v, pan, gain))
def win(a, b, step, t0=0.0):
    k = np.ceil((a - t0) / step - 1e-9); out = []
    while t0 + k * step < b - 1e-6: out.append(t0 + k * step); k += 1
    return out

# 和声：Dm – Bb – Gm – A（每小节一和弦，A 为和声小调属和弦）
CH = [('D', [50, 53, 57], 38), ('Bb', [46, 50, 53], 34), ('G', [43, 46, 50], 31), ('A', [45, 49, 52], 33)]
# 原创主题（每 4 小节一轮；8 分音符格，None=休止）
THEME = [
    [69, None, 74, 76, 77, None, 76, 74],
    [77, None, None, 74, 70, None, 69, None],
    [67, None, 70, 74, 79, None, 77, 76],
    [76, None, 73, None, 69, None, None, None],
]
G0 = TL['c1']
def bar_of(t): return int(np.floor((t - G0) / BAR + 1e-9))

# A. 立案：低音钢琴 + 钟摆（印章前空出来）
nt(0.0, 'piano', 'D1', 1.6, .85, 0, .6); nt(0.0, 'piano', 'D2', 1.6, .7, 0, .8); nt(0.0, 'piano', 'A3', 1.6, .5, .2, .5)
nt(0.0, 'timpani', 'D3', 0.7, .5, 0, .6)
for t in win(1.0, TL['blood'], BEAT): add(M, tick(1, int((t - 1.0) / BEAT) % 2 == 0), t, .12, .5)

# B. 嫌疑人 / 藏身：拨弦潜行 + 响指
for t in win(TL['mug'], TL['c1'] - .4, E8, TL['mug']):
    i = int(round((t - TL['mug']) / E8)); b = i // 8
    root = [38, 38, 34, 33][b % 4]
    pat = [0, None, 12, 7, None, 3, 7, None][i % 8]
    if pat is not None and t < TL['blood'] + 4.0: nt(t, 'cellos_pizz', root + 12 + pat if pat != 0 else root + 12, .3, .55, -.2)
    if i % 8 == 0: nt(t, 'contrabass_pizz', root, .6, .7, 0)
for t in win(TL['mug'] + BEAT, TL['blood'] + 5.6, 2 * BEAT, TL['mug']): add(M, snap(), t, .28, .35)
# 羽管键琴：藏身地点处一句
for k, p in enumerate([62, 65, 69, 68, 69, 74]):
    nt(TL['hide'] + 0.4 + k * E8, 'harpsichord', p, .4, .6, .3, .7)
for k, p in enumerate([74, 72, 70, 69]):
    nt(TL['hide'] + 2.6 + k * E8, 'harpsichord', p, .4, .55, .3, .6)
# C. 血液对比：震音弦乐渐强 → 静默
nt(TL['blood'] + 2.8, 'violins_trem', 'D5', 3.2, .35, .2, .55); nt(TL['blood'] + 2.8, 'violins_trem', 'Eb5', 3.2, .3, -.2, .45)
nt(TL['blood'] + 2.8, 'cellos', 'D2', 3.2, .4, 0, .6)

# D. 五宗罪：完整律动
GE = TL['board']
for t in win(G0, GE, E8, G0):
    i = int(round((t - G0) / E8)); bi = i // 8; pos = i % 8
    name, tri, bass = CH[bi % 4]
    # 钢琴固定音型（低中音区分解和弦）
    arp = [tri[0], tri[1], tri[2], tri[1] + 12, tri[2], tri[1], tri[0] + 12, tri[2]]
    nt(t, 'piano', arp[pos] + 12, E8 * 1.6, .42 + (.08 if pos == 0 else 0), -.25, .8)
    # 方波低音 + 拨奏低音
    if pos in (0, 3, 4, 6): add(M, sqbass(bass + 12, E8 * .9, 1.0), t, .07, 0)
    if pos == 0: nt(t, 'contrabass_pizz', bass, .8, .75, 0, .8)
    # 鼓
    if pos in (0, 4) or (pos == 7 and bi % 2): add(M, kick(), t, .3)
    if pos in (2, 6): nt(t, 'claps', 'solo', None, .65, .15, .7)
    late = t >= TL['c4']
    nt(t, 'hihat', 'closed', None, .55 if pos % 2 == 0 else .4, .35, .55)
    if late: nt(t + E16, 'hihat', 'closed', None, .35, .35, .35)
    # 主题：马林巴（第二轮起羽管键琴低八度叠奏）
    mel = THEME[bi % 4][pos]
    if mel is not None and bi >= 1:
        nt(t, 'marimba', mel, E8 * 1.8, .7, .25, 1.1)
        if bi >= 5: nt(t, 'harpsichord', mel, E8 * 1.8, .55, -.35, .6)
# 每条罪状开头：军鼓滚奏 + 重音
for k in ('c1', 'c2', 'c3', 'c4', 'c5'):
    t = TL[k]
    nt(t - .55, 'snare2', 'roll', .5, .45, 0, .45)
    nt(t, 'timpani', 'D3', 1.0, .85, 0, .8); nt(t, 'bass_drum', None, None, .8, 0, .6)
    nt(t, 'piano', 'D2', 1.4, .8, 0, .5)

# E. 证据板：长音 + 滴答（呼吸）
nt(TL['board'], 'violins', 'A4', 2.4, .35, .2, .45); nt(TL['board'], 'violins', 'D5', 2.4, .3, -.2, .4)
nt(TL['board'], 'cellos', 'D2', 2.4, .4, 0, .55)
for t in win(TL['board'], TL['disguise'], BEAT, TL['board']): add(M, tick(1, True), t, .12, .5)

# F. 伪装：只剩低音 + 响指 + 稀疏羽管键琴
for t in win(TL['disguise'], TL['verdict'] - .3, E8, TL['disguise']):
    i = int(round((t - TL['disguise']) / E8)); pos = i % 8; b = i // 8
    root = [38, 34, 31, 33][b % 4]
    if pos in (0, 3, 6): nt(t, 'contrabass_pizz', root, .5, .7, 0, .85)
    if pos in (2, 6): add(M, snap(), t, .3, .35)
    if pos == 4 and b % 2 == 0: nt(t, 'harpsichord', root + 36, .5, .5, .3, .5)

# G. 宣判：定音鼓四分脉冲 → 震音渐强 → 静默 → 印章 → 一小节律动
ST = next(e['t'] for e in EV if e['type'] == 'stamp' and e.get('verdict'))
nt(TL['verdict'], 'timpani', 'D3', 1.2, .9, 0, .9)
for t in win(TL['verdict'] + BEAT, ST - 1.2, BEAT, TL['verdict']):
    nt(t, 'timpani', 'A2' if int((t - TL['verdict']) / BEAT) % 4 == 3 else 'D3', .6, .45, 0, .55)
    nt(t, 'piano', 'D2', BEAT, .4, -.2, .5)
nt(ST - 3.0, 'violins_trem', 'A4', 2.4, .5, .2, .6); nt(ST - 3.0, 'violins_trem', 'C#5', 2.4, .5, -.2, .55)
nt(ST - 3.0, 'cellos', 'A2', 2.4, .55, 0, .7)
nt(ST - 1.1, 'snare2', 'roll', .55, .5, 0, .5)
# ST-0.6 .. ST 静默
nt(ST, 'timpani', 'D3', 1.5, 1.0, 0, 1.0); nt(ST, 'bass_drum', None, None, 1.0, 0, .8)
nt(ST, 'piano', 'D1', 2.0, .9, 0, .9); nt(ST, 'piano', 'D2', 2.0, .8, 0, .7); nt(ST, 'piano', 'A2', 2.0, .7, 0, .6)
for t in win(ST + BEAT, TL['close'] + 1.2, E8, ST):
    i = int(round((t - ST) / E8)); pos = i % 8
    if pos in (0, 4): add(M, kick(), t, .3)
    nt(t, 'hihat', 'closed', None, .45, .35, .45)
    if pos in (2, 6): nt(t, 'claps', 'solo', None, .5, .15, .35)

# H. 结案：马林巴主题放慢 + 音乐盒
for k, p in enumerate([69, 74, 76, 77, 76, 74, 73, 74]):
    nt(TL['close'] + .6 + k * BEAT * .75, 'marimba', p, BEAT, .5, .2, .6)
CS = next(e['t'] for e in EV if e['type'] == 'stamp' and e.get('close'))
nt(CS, 'piano', 'D1', 2.0, .75, 0, .7); nt(CS, 'timpani', 'D3', 1.2, .7, 0, .6)
for k, p in enumerate([86, 89, 93, 98]): nt(CS + .5 + k * .18, 'glockenspiel', p, 1.5, .45, .3, .5)
# I. 片尾：音乐盒尾句 + 最后一记低音
for k, p in enumerate([81, 86, 88, 89, 88, 86]): nt(TL['end'] + .2 + k * .3, 'glockenspiel', p, 1.4, .4, -.2 + k * .08, .45)
nt(TL['end'] + 2.2, 'piano', 'D1', 2.0, .6, 0, .6); nt(TL['end'] + 2.2, 'piano', 'D3', 2.0, .4, 0, .4)

print('rendering', len(notes), 'notes …')
SC = S.render(notes, dur=N / SR, master=False)
M[:len(SC)] += SC[:N]
M = S.room(M, size=.35, mix=.14)
# 印章前的静默：硬性清空
for a, b in [(TL['blood'] + 6.2, TL['c1'] - .02), (ST - .6, ST - .02)]:
    i0, i1 = int(a * SR), int(b * SR); M[i0:i1] = 0
    f = int(.08 * SR); M[i0 - f:i0] *= np.linspace(1, 0, f)[:, None]
fo = int(.6 * SR); e = int(DUR * SR); M[e - fo:e] *= np.linspace(1, 0, fo)[:, None]; M[e:] = 0

# 低频平衡：大于 -3 dB 的 20–120 Hz 收一点
def band_db(x, lo, hi): return 10 * np.log10(np.mean(bp(x.mean(1), lo, hi) ** 2) + 1e-12)
lo_db, mid_db = band_db(M, 20, 120), band_db(M, 120, 8000)
if lo_db - mid_db > -3:
    g = 10 ** ((-3 - (lo_db - mid_db)) / 20); low = np.stack([lp(M[:, 0], 120), lp(M[:, 1], 120)], 1); M = M - low + low * g
print(f'music low/mid balance: {lo_db - mid_db:+.1f} dB')

os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'music.wav'), M, SR)
sf.write(os.path.join(HERE, 'out', 'sfx.wav'), SFX, SR)

# ---------------- 人声（若有）----------------
VO = buf(); has_voice = False
vdir = os.path.join(HERE, 'voice')
if os.path.exists(os.path.join(vdir, 'dur.json')):
    lines = json.load(open(os.path.join(HERE, 'lines.json'), encoding='utf-8'))
    for ln in lines:
        w = os.path.join(vdir, f"{ln['id']}.wav")
        if not os.path.exists(w): continue
        x, sr = sf.read(w, dtype='float32')
        if x.ndim > 1: x = x.mean(1)
        if sr != SR:
            import soxr; x = soxr.resample(x, sr, SR)
        add(VO, compress(x / (np.abs(x).max() + 1e-9) * .8, thr=.2, ratio=3), ln['t'], .5, 0)
    has_voice = True

def rms(x): return np.sqrt(np.mean(x ** 2) + 1e-12)
if has_voice:
    # 音乐闪避：人声包络 → 约 -9 dB
    env = np.abs(VO.mean(1)); from scipy.ndimage import maximum_filter1d, uniform_filter1d
    env = uniform_filter1d(maximum_filter1d(env, int(.25 * SR)), int(.12 * SR)); duck = 1 - .65 * np.clip(env / .05, 0, 1)
    M = M * duck[:, None]
    vr = rms(VO[np.abs(VO.mean(1)) > 1e-4]); mr = rms(M[np.abs(M.mean(1)) > 1e-4])
    M *= (vr / mr) * 10 ** (-10 / 20)
else:
    M *= .9
MIX = M * 1.0 + SFX * .9 + VO
# 母带：先把整体电平推到约 -15 dBFS RMS，再限幅到 -2 dBFS，让 mux 的 loudnorm 不再把峰值推过 -1.2 dB
act = np.abs(MIX.mean(1)) > 1e-3
MIX = np.stack([lp(MIX[:, 0], 16000), lp(MIX[:, 1], 16000)], 1).astype(np.float32)
MIX *= 10 ** (-16 / 20) / rms(MIX[act])
import soxr
for c in range(2): MIX[:, c] = limit(np.tanh(MIX[:, c] * 1.05) / 1.05, .79)
# 真峰值限幅：4 倍过采样后再限一次
up = soxr.resample(MIX, SR, SR * 4)
for c in range(2): up[:, c] = limit(up[:, c], .72, look=.002)
MIX = soxr.resample(up, SR * 4, SR)[:len(MIX)].astype(np.float32)
for c in range(2): MIX[:, c] = limit(MIX[:, c], .72)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), MIX, SR)
print('voice' if has_voice else 'NO VOICE (music + sfx only)', '→ out/mix.wav', f'{len(MIX) / SR:.1f}s')

used = sorted({n[1] for n in notes if isinstance(n[1], str)})
open(os.path.join(HERE, 'out', 'instruments.txt'), 'w').write('\n'.join(S.credits(used)))
