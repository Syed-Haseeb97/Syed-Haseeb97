from pathlib import Path
import io
import re

import cairosvg
from PIL import Image, ImageDraw, ImageFont

source = Path("assets/plasma-header.svg").read_text(encoding="utf-8")
# Strip SVG SMIL animations so the original artwork renders consistently in CI.
source = re.sub(r"<animate(?:Transform)?\b[^>]*/>", "", source)
# Leave the name area empty; the GIF frames will draw the type-on effect there.
source, count = re.subn(
    r'<text x="66" y="159"[^>]*aria-label="Haseeb">.*?</text>',
    "",
    source,
    count=1,
    flags=re.S,
)
if count != 1:
    raise RuntimeError("Could not find the Haseeb name element in assets/plasma-header.svg")
source = re.sub(r'<rect x="66" y="91"[^>]*>.*?</rect>', "", source, count=1, flags=re.S)

png = cairosvg.svg2png(bytestring=source.encode("utf-8"), output_width=1200, output_height=360)
base = Image.open(io.BytesIO(png)).convert("RGB")
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font = ImageFont.truetype(font_path, 78)
chars = list("HASEEB.")
frames = []

def draw_frame(visible_count, cursor_on=True):
    frame = base.copy()
    draw = ImageDraw.Draw(frame)
    x = 66.0
    baseline = 159
    for index, char in enumerate(chars[:visible_count]):
        color = "#67e8f9" if char == "." else "#f8fafc"
        draw.text((round(x), baseline), char, font=font, fill=color, anchor="ls", stroke_width=0)
        x += draw.textlength(char, font=font) - 3
    if cursor_on:
        draw.rounded_rectangle((round(x + 1), 91, round(x + 6), 169), radius=1, fill="#67e8f9")
    return frame

# Type on, pause, erase, and pause before repeating.
for n in range(1, len(chars) + 1):
    for _ in range(4):
        frames.append(draw_frame(n, True))
for i in range(12):
    frames.append(draw_frame(len(chars), i % 4 != 3))
for n in range(len(chars) - 1, -1, -1):
    for _ in range(2):
        frames.append(draw_frame(n, True))
for i in range(6):
    frames.append(draw_frame(0, i % 3 != 2))

# Quantize to a shared palette for a compact, looping README GIF.
palette_frames = []
for frame in frames:
    palette_frames.append(frame.quantize(colors=128, method=Image.Quantize.MEDIANCUT))
out = Path("assets/plasma-header.gif")
palette_frames[0].save(
    out,
    save_all=True,
    append_images=palette_frames[1:],
    duration=90,
    loop=0,
    optimize=True,
    disposal=2,
)
print(f"Generated {out} ({out.stat().st_size} bytes, {len(frames)} frames)")
