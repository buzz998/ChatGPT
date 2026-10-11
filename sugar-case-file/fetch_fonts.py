"""按 index.html 用到的字符子集化下载 Google Fonts（OFL）→ fonts/ + fonts.css"""
import re, urllib.request, urllib.parse, pathlib
here = pathlib.Path(__file__).parent
src = (here / 'index.html').read_text('utf-8')
chars = ''.join(sorted(set(src) - set('\n\r\t'))) + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
chars = ''.join(sorted(set(chars)))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
fams = ['Noto+Serif+SC:wght@900', 'Noto+Sans+SC:wght@900', 'ZCOOL+KuaiLe', 'Bagel+Fat+One', 'JetBrains+Mono:wght@800']
(here / 'fonts').mkdir(exist_ok=True)
out = ''; n = 0
for f in fams:
    url = f'https://fonts.googleapis.com/css2?family={f}&display=block&text=' + urllib.parse.quote(chars)
    css = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA})).read().decode()
    for u in sorted(set(re.findall(r'url\((https://[^)]+)\)', css))):
        name = f'f{n}.woff2'; n += 1
        (here / 'fonts' / name).write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': UA})).read())
        css = css.replace(u, 'fonts/' + name)
    out += css; print(f, 'ok')
(here / 'fonts.css').write_text(out, 'utf-8')
