"""Capture SMIL-animated SVGs to compact GIFs for GitHub README."""
from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageSequence
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

BANNERS = [
    ("banner-a.svg", "banner-a.gif"),
    ("banner-b.svg", "banner-b.gif"),
    ("banner-c.svg", "banner-c.gif"),
]

WIDTH = 1000
HEIGHT = 280
FPS = 6
DURATION_S = 2.0
COLORS = 64


def capture_frames(svg_path: Path) -> list[Image.Image]:
    svg = svg_path.read_text(encoding="utf-8")
    if 'width="1500"' in svg:
        svg = svg.replace('width="1500"', f'width="{WIDTH}"', 1)
        svg = svg.replace('height="420"', f'height="{HEIGHT}"', 1)

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  html, body {{ margin: 0; padding: 0; background: #050A0F; overflow: hidden; width: {WIDTH}px; height: {HEIGHT}px; }}
  svg {{ display: block; width: {WIDTH}px; height: {HEIGHT}px; }}
</style></head>
<body>{svg}</body></html>"""

    frames: list[Image.Image] = []
    frame_count = int(DURATION_S * FPS)
    delay_ms = int(1000 / FPS)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(350)
        for _ in range(frame_count):
            png = page.screenshot(type="png", clip={"x": 0, "y": 0, "width": WIDTH, "height": HEIGHT})
            frames.append(Image.open(io.BytesIO(png)).convert("RGB"))
            page.wait_for_timeout(delay_ms)
        browser.close()
    return frames


def save_gif(frames: list[Image.Image], out_path: Path) -> None:
    # Build a shared palette from a representative frame for smaller files
    base = frames[0].quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT)
    palette = base.getpalette()
    converted = []
    for frame in frames:
        q = frame.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT)
        # Remap onto first palette when possible
        converted.append(frame.quantize(palette=base, dither=Image.Dither.FLOYDSTEINBERG))

    converted[0].save(
        out_path,
        save_all=True,
        append_images=converted[1:],
        duration=int(1000 / FPS),
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Wrote {out_path.name} ({out_path.stat().st_size / 1024:.0f} KB, {len(frames)} frames)")


def main() -> None:
    for svg_name, gif_name in BANNERS:
        print(f"Capturing {svg_name}...")
        frames = capture_frames(ASSETS / svg_name)
        save_gif(frames, ASSETS / gif_name)

    banner_gif = ASSETS / "banner.gif"
    banner_gif.write_bytes((ASSETS / "banner-a.gif").read_bytes())
    print(f"Wrote {banner_gif.name}")


if __name__ == "__main__":
    main()
