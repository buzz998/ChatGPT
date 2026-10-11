#!/bin/sh
# 一键成片：配音（需联网）→ 校对 → 音效点导出 → 配乐/混音 → 渲染 → 封装
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LIB=${LIB:-$(cd "$HERE/../.." && pwd)}
export LIB
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the library folder"; exit 1; }
cd "$LIB"
PY="$LIB/.venv/bin/python"
SIZE=1080x1920
if [ "${NO_VOICE:-0}" != 1 ]; then
  "$PY" core/tts/tts_zh.py "$HERE/lines.json" "$HERE/voice"
  "$PY" core/tts/asr_check.py "$HERE/lines.json" "$HERE/voice" --lang zh
fi
node core/render/events.mjs "$HERE" --size $SIZE
"$PY" "$HERE/mix.py"
"$PY" "$HERE/make_srt.py"
node core/render/video.mjs "$HERE" --fps 30 --workers 3 --size $SIZE --out "$HERE/out/video.mp4"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/sugar-case-file.mp4" 30 1
