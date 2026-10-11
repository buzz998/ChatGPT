"""分镜总览：storyboard/index.html（用真实渲染帧）→ storyboard.jpg"""
import re, urllib.request, urllib.parse, pathlib, html
here = pathlib.Path(__file__).parent
SHOTS = [
 (1.2, '01', '0.0–1.7s', '中景·锁定→印章震屏', '证物袋落下，闪光，“立案”红章砸下', '立案。嫌疑人：糖。'),
 (3.0, '02', '1.7–3.6s', '中景·闪光→慢推', '嫌疑人照：方糖站在克数身高尺前，被闪光吓一跳', '藏身地点：你手里这杯全糖奶茶。'),
 (7.9, '03', '3.6–8.6s', '中景·推→横移', '杯身透视出 8 块方糖，逐块跳出；巨大半调“30+g”', '一大杯大约30多克，差不多8块方糖。'),
 (14.0, '04', '8.6–15.0s', '全景·横摇→硬切静默', '天平：4g 一滴血 vs 30g 方糖砸下，秤盘翻倒，“？”', '而你全身血液里的糖……身体怎么收场？'),
 (20.5, '05', '15.0–21.8s', '网点擦除·跟拍曲线', '罪状一：大号“1”；血糖曲线猛冲，胰腺拉警报派出胰岛素信使', '罪状一：累垮胰岛素……'),
 (24.5, '06', '21.8–26.8s', '中景·慢推到门', '信使敲门越敲越没劲，细胞挂“已读不回”→ 胰岛素抵抗', '天天这样，细胞对胰岛素越来越不理睬'),
 (29.8, '07', '26.8–31.6s', '纸张滑入·快速变焦进网点', '研究卡：每天多一份含糖饮料 → 2型糖尿病风险 约↑18%', '2型糖尿病风险约高18%。'),
 (39.5, '08', '31.6–41.6s', '中景·慢推', '罪状二：果糖箱被搬进肝脏仓库，油滴堆满，肝脏胀大 → 脂肪肝', '把肝脏变成脂肪仓库……'),
 (47.5, '09', '41.6–50.2s', '剖面·网点放大', '罪状三：方糖粘在胶原弹簧上，弹簧变硬，表皮起皱 + “糖化终产物”', '多余的糖粘在胶原蛋白上……'),
 (54.5, '10', '50.2–55.8s', '特写·硬切加速', '罪状四：细菌吃糖吐酸泡，牙齿被网点蛀空，“咔嚓”', '嘴里的细菌吃糖、吐酸……'),
 (61.5, '11', '55.8–63.0s', '锁定·节拍脉冲', '罪状五：腰带扣一格格外移；热量表爆表，饱腹感表几乎不动', '而喝下去的热量，偏偏最不顶饱。'),
 (64.6, '12', '63.0–65.2s', '★标志镜头·大拉远', '人体证据板全貌：五张证物照，红线全部连回那杯奶茶（呼吸）', '（无口播，音乐留白）'),
 (70.5, '13', '65.2–72.8s', '推进→网点放大', '伪装：“不另外加糖”标签被涂黑条盖住再撕开 → 检测单 ≈4g/100g', '它最狡猾的是伪装……'),
 (84.0, '14', '72.8–84.2s', '锁定→慢推→印章', '宣判：膳食指南尺子，50g 红线 / 25g 绿线，奶茶糖量柱越线；静默后“越线”章', '一杯全糖奶茶，就已经越过了这条线。'),
 (88.0, '15', '84.2–89.8s', '文件夹滑入→拉远', '便签“别天天喝”“别喝全糖”；“结案”章，案卷推进满是奶茶案卷的抽屉', '不是一口都不能喝……结案。'),
 (91.5, '16', '89.8–93.5s', '锁定', '片尾卡', '关注我，复杂的事讲清楚。'),
]
cards = ''
for t, n, tm, cam, desc, line in SHOTS:
    cards += f'''<div class="c"><img src="../stills/sb/t_{t}.jpg"><div class="m"><b>#{n}</b><span>{tm}</span></div>
<div class="cam">{html.escape(cam)}</div><div class="d">{html.escape(desc)}</div><div class="l">“{html.escape(line)}”</div></div>'''
page = f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="sb.css"><style>
body{{margin:0;background:#1C2340;color:#F1E4C6;font-family:'Noto Sans SC';width:2000px}}
h1{{margin:0;padding:36px 40px 6px;font-size:52px;font-weight:900;color:#F5C518}}
.sub{{padding:0 40px 24px;font-size:24px;font-weight:500;line-height:1.6}}
.g{{display:grid;grid-template-columns:repeat(8,1fr);gap:18px;padding:0 40px 40px}}
.c{{background:#F1E4C6;color:#1C2340;border-radius:8px;overflow:hidden}}
.c img{{width:100%;display:block}}
.m{{display:flex;justify-content:space-between;padding:8px 10px 0;font-size:22px;font-weight:900}} .m span{{font-size:17px;font-weight:500}}
.cam{{padding:2px 10px;font-size:16px;font-weight:900;color:#C8834A}}
.d{{padding:2px 10px;font-size:16px;font-weight:500;line-height:1.35;min-height:88px}}
.l{{padding:4px 10px 10px;font-size:15px;font-weight:500;color:#D8352A;line-height:1.35}}
</style></head><body><h1>糖的案卷 · 分镜（复古半调案卷 · 9:16 · 30fps）</h1>
<div class="sub">一杯全糖奶茶被当作证物立案，嫌疑人“糖”被逐条宣读五宗罪、揭穿伪装，按膳食指南判定“越线”，最后温和结案。<br>
时间按估算语速排布，配音完成后按实测时长重排；字幕卡顶边在 y=1290（下三分之一上沿），底部 1460 以下只留纸面网点，给抖音标题区。<br>
配乐：D 小调 92BPM 原创悬疑侦探（钢琴低音固定音型 + 拨弦 + 马林巴拨音 + 合成鼓 + 钟表滴答），只借《夜的第七章》的氛围。</div>
<div class="g">{cards}</div></body></html>'''
(here / 'index.html').write_text(page, 'utf-8')
chars = ''.join(sorted(set(page)))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
url = 'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@500;900&display=block&text=' + urllib.parse.quote(chars)
css = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA})).read().decode()
for i, u in enumerate(sorted(set(re.findall(r'url\((https://[^)]+)\)', css)))):
    (here / f'sb{i}.woff2').write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA})).read())
    css = css.replace(u, f'sb{i}.woff2')
(here / 'sb.css').write_text(css, 'utf-8')
