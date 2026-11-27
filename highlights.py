"""Builds the 'AI Agents, Sketched' highlights video: intro card, 5 animated chapter posts, closing card.

Usage:  python highlights.py
Output: ..\\clips\\highlights\\ (highlights_4x5.mp4, highlights_9x16.mp4)
"""
import shutil
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE.parent / "clips" / "highlights"
FPS = 24
FADE = 0.5
# (kind, page/card, loop seconds, start, duration)
SEGMENTS = [
    ("card", "intro", 0, 0.0, 5.0),
    ("post", 9, 14.1, 0.0, 7.0),      # ch2 the agent loop
    ("post", 51, 12.5, 4.4, 5.2),     # ch10 router: refill + urgent message
    ("post", 102, 9.6, 0.0, 8.8),     # ch20 lethal trifecta
    ("post", 86, 9.0, 0.0, 7.0),      # ch17 pass every time
    ("post", 117, 9.0, 0.0, 7.0),     # ch23 launch checklist
    ("card", "outro", 0, 0.0, 5.0),
]


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def record():
    OUT.mkdir(parents=True, exist_ok=True)
    clips = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        for i, (kind, what, loop, start, dur) in enumerate(SEGMENTS):
            fr = OUT / f"_seg{i}"
            shutil.rmtree(fr, ignore_errors=True)
            fr.mkdir()
            if kind == "card":
                pg.goto((HERE / "highlight-cards.html").as_uri() + f"?card={what}")
                pg.wait_for_function("window.__ready")
                setter, sel = "window.__setT", "#stage"
            else:
                pg.goto((HERE / "index.html").as_uri() + f"?clip={what}&post=1&loop={loop}")
                pg.wait_for_function("window.__clip && window.__clip.ready")
                setter, sel = "window.__clip.setTime", "#post"
            pg.evaluate("document.fonts.ready.then(() => 1)")
            pg.wait_for_timeout(1200)
            if start:
                for k in range(int(start * FPS)):
                    pg.evaluate(f"{setter}({k / FPS:.4f})")
            for k in range(round(dur * FPS)):
                pg.evaluate(f"{setter}({start + k / FPS:.4f})")
                pg.locator(sel).screenshot(path=str(fr / f"{k:04d}.png"))
            mp4 = OUT / f"_seg{i}.mp4"
            ff("-framerate", str(FPS), "-i", str(fr / "%04d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
               "-pix_fmt", "yuv420p", str(mp4))
            shutil.rmtree(fr, ignore_errors=True)
            clips.append((mp4, dur))
            print(f"segment {i} done ({dur}s)", flush=True)
        b.close()
    return clips


def join(clips):
    args, chain, total, last = [], [], clips[0][1], "[0:v]"
    for mp4, _ in clips:
        args += ["-i", str(mp4)]
    for i in range(1, len(clips)):
        off = total - FADE
        out = f"[v{i}]"
        chain.append(f"{last}[{i}:v]xfade=transition=slideleft:duration={FADE}:offset={off:.3f}{out}")
        last, total = out, total + clips[i][1] - FADE
    n = len(clips)
    base = OUT / "_joined.mp4"
    ff(*args, "-filter_complex", ";".join(chain), "-map", last, "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
       "-pix_fmt", "yuv420p", "-r", "30", str(base))
    ff("-i", str(base), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-map", "0:v", "-map", "1:a", "-shortest",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(OUT / "highlights_4x5.mp4"))
    ff("-i", str(base), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
       "[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:2,eq=brightness=0.04[bg];"
       "[b]scale=1080:1350[fg];[bg][fg]overlay=0:285,format=yuv420p[v]", "-map", "[v]", "-map", "1:a", "-shortest",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
       str(OUT / "highlights_9x16.mp4"))
    for mp4, _ in clips:
        mp4.unlink(missing_ok=True)
    base.unlink(missing_ok=True)
    print(f"done: {total:.1f} s", flush=True)


if __name__ == "__main__":
    join(record())
