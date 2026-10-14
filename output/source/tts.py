import asyncio, ssl, os, json, subprocess
import edge_tts.communicate as C
C._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
import edge_tts
from script import SCENES
os.makedirs("aud", exist_ok=True)
async def one(i, j, text):
    p = f"aud/{i:02d}_{j:02d}.mp3"
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        for k in range(4):
            try:
                await edge_tts.Communicate(text, "zh-CN-YunxiNeural", rate="+4%").save(p); break
            except Exception as e:
                print("retry", p, e); await asyncio.sleep(2)
async def main():
    for i, (_, _, lines) in enumerate(SCENES):
        await asyncio.gather(*[one(i, j, t) for j, t in enumerate(lines)])
asyncio.run(main())
