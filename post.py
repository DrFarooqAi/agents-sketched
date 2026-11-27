"""Records one book page as a colourful social post: looping GIF + 4:5 MP4 + 9:16 MP4.

Usage:  python post.py <page_index> <loop_seconds> <name>
        python post.py all            (records every chapter's chosen page)
Output: ..\\clips\\posts\\
"""
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
OUT = HERE.parent / "clips" / "posts"
FPS = 12

# chapter -> (page index, animation loop length in seconds, file name)
CHAPTERS = [
    (3, 8.4, "01-chatbot-workflow-or-agent"), (9, 14.1, "02-the-agent-loop"), (15, 10.0, "03-how-tool-calls-work"),
    (21, 8.4, "04-send-back-less"), (25, 10.5, "05-context-rot"), (30, 17.5, "06-write-the-plan-down"),
    (35, 13.6, "07-draft-check-fix"), (40, 13.5, "08-the-model-forgets"), (45, 11.0, "09-crash-and-resume"),
    (51, 12.5, "10-the-router"), (55, 10.5, "11-boss-and-workers"), (61, 11.0, "12-handoffs"),
    (66, 10.0, "13-a2a-task"), (71, 22.0, "14-framework-map"), (75, 10.0, "15-message-list"), (80, 10.4, "16-approval-gate"),
    (86, 9.0, "17-pass-every-time"),
    (91, 8.0, "18-trace-every-run"),
    (95, 14.0, "19-claims-agent"),
    (102, 9.6, "20-lethal-trifecta"),
    (105, 9.6, "21-why-agents-get-expensive"),
    (112, 14.4, "22-failure-slot-machine"),
]


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def make(idx: int, loop: float, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fr = OUT / f"_fr_{name}"
    shutil.rmtree(fr, ignore_errors=True)
    fr.mkdir()
    n = round(loop * FPS)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
        pg.goto((HERE / "index.html").as_uri() + f"?clip={idx}&post=1&loop={loop}")
        pg.wait_for_function("window.__clip && window.__clip.ready")
        pg.evaluate("document.fonts.ready.then(() => 1)")
        pg.wait_for_timeout(1500)
        for i in range(n):
            pg.evaluate(f"window.__clip.setTime({i / FPS:.4f})")
            pg.locator("#post").screenshot(path=str(fr / f"{i:04d}.png"))
        b.close()
    src = str(fr / "%04d.png")
    dur = 2 * n / FPS  # videos play the loop twice
    ff("-framerate", str(FPS), "-i", src, "-vf",
       "scale=720:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=200:stats_mode=diff[p];"
       "[b][p]paletteuse=dither=none:diff_mode=rectangle", "-loop", "0", str(OUT / f"{name}.gif"))
    ff("-framerate", str(FPS), "-i", src, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
       f"[0:v]loop=1:{n}:0,fps=30,format=yuv420p[v]", "-map", "[v]", "-map", "1:a", "-t", f"{dur:.2f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
       str(OUT / f"{name}_4x5.mp4"))
    ff("-framerate", str(FPS), "-i", src, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-filter_complex",
       f"[0:v]loop=1:{n}:0,split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
       "boxblur=40:2,eq=brightness=0.04[bg];[b]scale=1080:1350:flags=lanczos[fg];[bg][fg]overlay=0:285,fps=30,format=yuv420p[v]",
       "-map", "[v]", "-map", "1:a", "-t", f"{dur:.2f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
       "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(OUT / f"{name}_9x16.mp4"))
    shutil.rmtree(fr, ignore_errors=True)
    sizes = [(OUT / f).stat().st_size / 1e6 for f in (f"{name}.gif", f"{name}_4x5.mp4", f"{name}_9x16.mp4")]
    print(f"{name}: gif {sizes[0]:.1f} MB, 4x5 {sizes[1]:.1f} MB, 9x16 {sizes[2]:.1f} MB", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "all":
        for idx, loop, name in CHAPTERS:
            make(idx, loop, name)
    else:
        make(int(sys.argv[1]), float(sys.argv[2]), sys.argv[3])
