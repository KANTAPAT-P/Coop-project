# -*- coding: utf-8 -*-
"""ส่งออกเฉพาะผัง SVG จากหน้า Artifact เป็นไฟล์ PNG สำหรับวางในรายงาน

## วิธีที่ใช้และเหตุผล

เครื่องนี้ไม่มี cairosvg, Inkscape หรือ ImageMagick แต่มี Chrome
ซึ่งเป็นตัวแสดงผล SVG ที่ตรงกับที่เห็นในเบราว์เซอร์ที่สุด จึงสร้างหน้า
HTML ชั่วคราวที่มีเฉพาะผัง แล้วให้ Chrome โหมดไม่มีหน้าจอถ่ายภาพออกมา

**บังคับธีมสว่างด้วย `data-theme="light"`** เพราะไฟล์จะไปวางบนกระดาษสีขาว
ถ้าปล่อยตามธีมของระบบแล้วเครื่องตั้งเป็นธีมมืด จะได้รูปพื้นดำ

**คูณความละเอียดสองเท่า** เพื่อให้ตัวอักษรคมเมื่อพิมพ์ ขนาดที่ได้คือ
1,880 x 3,150 จุด ซึ่งที่ความกว้าง 16 ซม. บนกระดาษคิดเป็นราว 298 dpi

รัน:
    python export_png.py <ไฟล์ html> <ไฟล์ png ที่ต้องการ>
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(sys.argv[1])
OUT = Path(sys.argv[2])
SCALE = 2

BROWSERS = [
    Path(r"C:/Program Files/Google/Chrome/Application/chrome.exe"),
    Path(r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
]
browser = next((b for b in BROWSERS if b.is_file()), None)
if browser is None:
    raise SystemExit("ไม่พบ Chrome หรือ Edge สำหรับแสดงผล SVG")

html = SRC.read_text(encoding="utf-8")

style = re.search(r"<style>(.*?)</style>", html, re.S)
svg = re.search(r"(<svg class=\"dg\".*?</svg>)", html, re.S)
fonts = re.search(r'(<link rel="stylesheet" href="https://fonts\.[^"]+">)', html)
assert style and svg, "ไม่พบ <style> หรือ <svg> ในไฟล์ต้นทาง"

vb = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg.group(1))
W, H = int(vb.group(1)), int(vb.group(2))

# ตัด min-width ของผังออก เพราะหน้าสำหรับส่งออกกว้างเท่าผังพอดีอยู่แล้ว
page = f"""<!doctype html>
<html lang="th" data-theme="light">
<head>
<meta charset="utf-8">
{fonts.group(1) if fonts else ""}
<style>
{style.group(1)}
html, body {{ margin: 0; padding: 0; background: #ffffff; }}
.dg {{ display: block; min-width: 0; width: {W}px; height: {H}px; }}
</style>
</head>
<body>
{svg.group(1)}
</body>
</html>
"""

tmp = Path(tempfile.mkdtemp(prefix="pdm-export-"))
try:
    page_file = tmp / "diagram.html"
    page_file.write_text(page, encoding="utf-8")
    shot = tmp / "shot.png"

    cmd = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--default-background-color=FFFFFFFF",
        f"--force-device-scale-factor={SCALE}",
        f"--window-size={W},{H}",
        "--virtual-time-budget=6000",
        f"--screenshot={shot}",
        f"--user-data-dir={tmp / 'profile'}",
        page_file.as_uri(),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not shot.is_file():
        raise SystemExit(f"ถ่ายภาพไม่สำเร็จ\n{r.stdout}\n{r.stderr}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(shot, OUT)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

try:
    from PIL import Image
    with Image.open(OUT) as im:
        w, h = im.size
        # ตรวจว่าไม่ใช่ภาพเปล่า โดยนับจำนวนสีที่ต่างกัน
        colors = im.convert("RGB").getcolors(maxcolors=100_000)
        n_colors = len(colors) if colors else 100_000
    print(f"ขนาดภาพ {w:,} x {h:,} จุด  ({w / SCALE:.0f} x {h / SCALE:.0f} หน่วย SVG)")
    print(f"จำนวนสีที่ต่างกัน {n_colors:,}")
    if n_colors < 5:
        print("⚠️ ภาพแทบไม่มีสีต่างกันเลย -> น่าจะว่างเปล่า")
    print(f"ที่ความกว้าง 16 ซม. บนกระดาษ = {w / (16 / 2.54):.0f} dpi")
except ImportError:
    print("ไม่มี Pillow จึงข้ามการตรวจภาพ")

print(f"เขียนลง {OUT}")
print(f"ขนาดไฟล์ {OUT.stat().st_size / 1024:,.0f} kB")
