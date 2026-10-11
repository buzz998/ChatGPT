"""字幕：index.html 的 CAPS → sugar-case-file.srt"""
import os, re, json, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.environ.get('LIB') or os.path.abspath(os.path.join(HERE, '..', '..'))
src = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
caps = re.findall(r"\[\s*([\d.]+),\s*([\d.]+),\s*'([^']*)'", re.search(r'const CAPS = \[(.*?)\n\];', src, re.S).group(1))
cues = [{'t0': float(a), 't1': float(b), 'text': s} for a, b, s in caps]
p = os.path.join(HERE, 'out', 'cues.json'); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(cues, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
subprocess.run([sys.executable, os.path.join(LIB, 'core/render/srt.py'), p, os.path.join(HERE, 'sugar-case-file.srt')], check=True)
