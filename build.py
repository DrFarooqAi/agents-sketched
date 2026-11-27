"""Builds index.html (the GitHub Pages website) from agents-sketched.html (the book source).
Run:  python build.py
"""
from pathlib import Path

here = Path(__file__).parent
src = (here / "agents-sketched.html").read_text(encoding="utf-8")

# Everything before the top bar is head material (title, fonts, styles).
cut = src.index('<header class="bar">')
head_part, body_part = src[:cut], src[cut:]

DESC = "AI Agents, Sketched: a practical way to make AI agents, by Dr. Muhammad Farooq. Moving sketches and real hospital cases."

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{DESC}">
<meta name="author" content="Dr. Muhammad Farooq">
<meta property="og:title" content="AI Agents, Sketched">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="book">
<style>body{{margin:0}} img{{max-width:100%}} [hidden]{{display:none!important}}</style>
{head_part.strip()}
</head>
<body>
{body_part.strip()}
</body>
</html>
"""
(here / "index.html").write_text(page, encoding="utf-8")
print("index.html built:", len(page), "chars")
