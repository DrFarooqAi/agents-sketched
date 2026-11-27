"""Records one book page as MP4 (1920x1080, for LinkedIn) and GIF.

Usage:  python record.py <page_index> <seconds> <name>
Example: python record.py 3 9.4 ch1-chatbot-workflow-agent
Pages count from 0 (0 = cover). Output goes to ..\\clips\\
"""
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE.parent / "clips"
FPS = 25


def record(idx: int, secs: float, name: str) -> None:
    OUT.mkdir(exist_ok=True)
    frames = OUT / f"_frames_{name}"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 760}, device_scale_factor=1.5)
        page.goto((HERE / "index.html").as_uri() + f"?clip={idx}")
        page.wait_for_function("window.__clip && window.__clip.ready")
        page.evaluate("document.fonts.ready.then(() => true)")
        page.wait_for_timeout(1200)
        box = page.evaluate(
            """() => {
                const a = document.querySelector('.page.on').getBoundingClientRect();
                const b = document.querySelector('.clip-foot').getBoundingClientRect();
                return {x: a.left - 14, y: Math.max(0, a.top - 14), width: a.width + 30, height: (b.bottom - a.top) + 20};
            }"""
        )
        need = int(box["y"] + box["height"] + 10)
        if need > 760:
            page.set_viewport_size({"width": 1280, "height": need})
        n = int(secs * FPS)
        for i in range(n):
            page.evaluate(f"window.__clip.setTime({i / FPS:.4f})")
            page.screenshot(path=str(frames / f"{i:05d}.png"), clip=box)
        browser.close()

    src = str(frames / "%05d.png")
    mp4 = OUT / f"{name}.mp4"
    gif = OUT / f"{name}.gif"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", src,
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,"
               "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xe9edf1,format=yuv420p",
        "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", str(mp4),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", src,
        "-vf", "fps=12,scale=900:-1:flags=lanczos,split[a][b];"
               "[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
        str(gif),
    ], check=True)
    shutil.rmtree(frames, ignore_errors=True)
    print(f"{name}: {mp4.stat().st_size / 1e6:.1f} MB mp4, {gif.stat().st_size / 1e6:.1f} MB gif")


if __name__ == "__main__":
    record(int(sys.argv[1]), float(sys.argv[2]), sys.argv[3])
