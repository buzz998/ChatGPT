# 糖的案卷 · Sugar Case File

抖音竖屏短片（1080×1920，30 fps，93.5 秒），复古半调案卷风格，主题“给奶茶里的糖立案：它对身体做了什么”。
用 [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) 的工具链纯代码制作。

## 当前状态

- `sugar-case-file.mp4`：画面 + 字幕 + 原创配乐 + 音效，**尚未配音**（−14 LUFS）。
- 配音未完成原因：制作时的云端环境网络策略拦截了 `speech.platform.bing.com`（edge-tts 晓晓语音）和 `huggingface.co`（Whisper 校对模型）。
- 台词已备好：`lines.json`（37 句，`zh-CN-XiaoxiaoNeural`，语速 +0%，数字已转汉字读法）。

## 补配音、出最终成片

在能访问上面两个域名的环境里：

```sh
git clone https://github.com/lemomo-ai/lemo-opuscar && cd lemo-opuscar
sh plugin/skills/lemo-opuscar/scripts/setup.sh deps voice
sh tools/fetch.sh instruments salamander && sh tools/fetch.sh instruments vcsl && sh tools/fetch.sh instruments vsco2ce
cp -r <本文件夹> films/sugar-case-file
sh films/sugar-case-file/build.sh        # 配音 → 校对 → 配乐/混音（自动闪避）→ 渲染 → 封装
```

注意：字幕和画面时间按估算语速排布（总长 93.5 秒）。配音生成后若某句实测比字幕窗口长，需要把 `index.html` 里的 `TL`/`CAPS` 相应后移再跑 `build.sh`（`mix.py`、`make_srt.py` 都从这两张表读时间）。

## 文件

| 文件 | 说明 |
|---|---|
| `index.html` | 整片画面（`render(t)`），时间轴 `TL`、字幕 `CAPS` 都在开头 |
| `mix.py` | 原创配乐（D 小调 92 BPM）+ 音效 + 混音 + 母带 |
| `lines.json` | 配音台词 |
| `build.sh` | 一键成片 |
| `TREATMENT.md` | 创作方案（结构、分镜表、cue map、音效表） |
| `storyboard.jpg` | 分镜 |
| `sugar-case-file.srt` | 字幕 |
| `CREDITS` | 第三方素材与授权（乐器采样、字体、语音引擎） |
