"""Generate the home-screen / PWA PNG icons from the same pokeball artwork as
the inline SVG favicon in index.html. iOS home-screen web-clips need a real
PNG (apple-touch-icon); SVG favicons are ignored there.

Draws at 4x and downsamples (LANCZOS) for clean anti-aliasing. Coordinates are
the favicon's 0..100 viewBox, mapped into a padded square on a white ground
(iOS ignores alpha and squares the icon, so it's painted opaque with padding).
"""
from PIL import Image, ImageDraw
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RED, INK, WHITE = "#F0504A", "#39424B", "#ffffff"

def make(size, pad=0.09, bg=WHITE):
    ss = 4
    S = size * ss
    icon = Image.new("RGBA", (S, S), bg)
    content = S * (1 - 2 * pad)
    ox = oy = S * pad
    sc = content / 100.0
    def P(x, y): return (ox + x * sc, oy + y * sc)
    def bbox(cx, cy, r): return [*P(cx - r, cy - r), *P(cx + r, cy + r)]

    ball = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    b = ImageDraw.Draw(ball)
    b.ellipse(bbox(50, 50, 46), fill=WHITE)              # body
    b.chord(bbox(50, 50, 46), 180, 360, fill=RED)        # red top half
    x0, y0 = P(4, 44); x1, y1 = P(96, 56)
    b.rectangle([x0, y0, x1, y1], fill=INK)              # centre band
    b.ellipse(bbox(50, 50, 15), fill=WHITE)              # button rings
    b.ellipse(bbox(50, 50, 13), fill=INK)
    b.ellipse(bbox(50, 50, 8),  fill=WHITE)

    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse(bbox(50, 50, 46), fill=255)   # clip to the ball
    icon.paste(ball, (0, 0), mask)
    ImageDraw.Draw(icon).ellipse(bbox(50, 50, 46), outline=INK, width=max(1, round(6 * sc)))

    return icon.resize((size, size), Image.LANCZOS).convert("RGB")

def main():
    for name, size in [("apple-touch-icon.png", 180), ("icon-192.png", 192), ("icon-512.png", 512)]:
        make(size).save(ROOT / name)
        print("wrote", name, f"({size}x{size})")

if __name__ == "__main__":
    main()
