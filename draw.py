"""VELDARA - Valley of the Floating Lanterns.

A vintage travel poster for a place that does not exist, drawn
procedurally with PIL: dusk sky, layered mountains and mist, a river
valley full of glowing paper lanterns, a stone bridge, a small town
with lit windows on both banks, and a low moon. Fully deterministic
(fixed seed) - two runs produce byte-identical output.
"""

import math
import os
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

W = H = 1024
SEED = 20261121

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

CREAM = (245, 233, 208)
GOLD = (255, 179, 71)


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(w, h, stops):
    """stops: list of (position 0..1, rgb). Returns RGB image."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    ys = np.linspace(0.0, 1.0, h)
    for y in range(h):
        t = ys[y]
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                f = 0.0 if p1 == p0 else (t - p0) / (p1 - p0)
                arr[y, :, :] = lerp_color(c0, c1, f)
                break
        else:
            arr[y, :, :] = stops[-1][1]
    return Image.fromarray(arr, "RGB")


def ridge_points(rng, base_y, amp, x0=0, x1=W, step=16):
    pts = []
    phase = rng.uniform(0, 6.28)
    for x in range(x0, x1 + 1, step):
        y = base_y - amp * (
            0.55 * math.sin(x * 0.006 + phase)
            + 0.30 * math.sin(x * 0.017 + phase * 2.1)
            + 0.15 * rng.uniform(-0.4, 0.4)
        )
        pts.append((x, y))
    return pts


def draw_text_spaced(draw, cx, y, text, font, fill, spacing, shadow=None):
    """Draw centred text with manual letter spacing."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2.0
    for ch, wd in zip(text, widths):
        if shadow is not None:
            draw.text((x + 2, y + 3), ch, font=font, fill=shadow)
        draw.text((x, y), ch, font=font, fill=fill)
        x += wd + spacing
    return total


def render():
    rng = random.Random(SEED)
    np_rng = np.random.default_rng(SEED)

    # ---------- sky ----------
    sky = vertical_gradient(W, H, [
        (0.00, (14, 20, 44)),
        (0.30, (34, 48, 88)),
        (0.48, (86, 76, 104)),
        (0.56, (196, 122, 82)),
        (0.62, (232, 164, 92)),
        (1.00, (24, 34, 58)),
    ])
    base = sky.convert("RGB")
    draw = ImageDraw.Draw(base, "RGBA")
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gdraw = ImageDraw.Draw(glow)

    # stars in the upper sky
    for _ in range(170):
        x = rng.uniform(0, W)
        y = rng.uniform(0, 330)
        r = rng.uniform(0.6, 1.8)
        a = rng.randint(90, 210)
        draw.ellipse([x - r, y - r, x + r, y + r],
                     fill=(235, 238, 255, a))

    # low moon, upper right corner, clear of the title, with halo
    mx, my, mr = 935, 78, 24
    gdraw.ellipse([mx - mr * 3, my - mr * 3, mx + mr * 3, my + mr * 3],
                  fill=(90, 80, 50))
    draw.ellipse([mx - mr, my - mr, mx + mr, my + mr],
                 fill=(250, 238, 210, 255))
    draw.ellipse([mx - mr + 9, my - mr + 7, mx - mr + 22, my - mr + 20],
                 fill=(238, 222, 190, 255))

    # ---------- mountains (back to front) ----------
    for base_y, amp, color in [
        (560, 150, (52, 64, 100)),
        (575, 110, (40, 50, 82)),
        (590, 70, (28, 36, 64)),
    ]:
        pts = ridge_points(rng, base_y, amp)
        pts = [(0, H)] + pts + [(W, H)]
        draw.polygon(pts, fill=color + (255,))

    # mist bands between the ridges
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(mist)
    for cy, cw, ch, alpha in [
        (470, 900, 26, 34), (520, 760, 30, 40), (545, 620, 22, 30),
    ]:
        mdraw.ellipse([W / 2 - cw / 2, cy - ch, W / 2 + cw / 2, cy + ch],
                      fill=(210, 205, 225, alpha))
    mist = mist.filter(ImageFilter.GaussianBlur(18))
    base = Image.alpha_composite(base.convert("RGBA"), mist)
    draw = ImageDraw.Draw(base, "RGBA")

    # ---------- river ----------
    river = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(river)
    rgrad = vertical_gradient(700, 470, [
        (0.0, (52, 74, 96)),
        (0.5, (36, 56, 82)),
        (1.0, (20, 32, 54)),
    ])
    rmask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(rmask)
    md.polygon([(430, 560), (594, 560), (880, H), (144, H)], fill=255)
    # paste the gradient, then keep it only inside the river polygon
    river = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    river.paste(rgrad, (162, 560))
    river.putalpha(Image.composite(
        Image.new("L", (W, H), 255), Image.new("L", (W, H), 0), rmask))
    base = Image.alpha_composite(base, river)
    draw = ImageDraw.Draw(base, "RGBA")

    # warm horizon light reflected on the river head
    refl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(refl)
    rd.polygon([(470, 560), (554, 560), (640, 760), (384, 760)],
               fill=(232, 164, 92, 70))
    refl = refl.filter(ImageFilter.GaussianBlur(24))
    base = Image.alpha_composite(base, refl)
    draw = ImageDraw.Draw(base, "RGBA")

    # ---------- banks + town ----------
    bank = (18, 26, 44)
    draw.polygon([(0, 560), (430, 560), (144, H), (0, H)], fill=bank + (255,))
    draw.polygon([(594, 560), (W, 560), (W, H), (880, H)], fill=bank + (255,))

    def house(x, y, w, h, lit):
        draw.polygon([(x, y), (x + w / 2, y - h * 0.45), (x + w, y),
                      (x + w, y + h), (x, y + h)], fill=(14, 20, 36, 255))
        for _ in range(lit):
            wx = rng.uniform(x + 5, x + w - 12)
            wy = rng.uniform(y + 6, y + h - 12)
            draw.rectangle([wx, wy, wx + 6, wy + 8],
                           fill=(255, 210, 122, 255))
            gdraw.rectangle([wx - 4, wy - 4, wx + 10, wy + 12],
                            fill=(60, 42, 12))

    for _ in range(9):
        house(rng.uniform(20, 330), rng.uniform(600, 850),
              rng.uniform(42, 66), rng.uniform(30, 52), rng.randint(1, 3))
    for _ in range(9):
        house(rng.uniform(680, 950), rng.uniform(600, 850),
              rng.uniform(42, 66), rng.uniform(30, 52), rng.randint(1, 3))

    # ---------- stone bridge ----------
    # deck band across the river, arch curving down to the water below it,
    # lamp posts standing on the deck.
    bx0, bx1, by = 315, 709, 700
    draw.arc([bx0 + 25, by - 60, bx1 - 25, by + 100], start=0, end=180,
             fill=(30, 40, 62, 255), width=18)
    draw.rectangle([bx0, by, bx1, by + 14], fill=(36, 46, 68, 255))
    draw.line([bx0, by, bx1, by], fill=(78, 90, 118, 255), width=3)
    for fx in range(bx0 + 14, bx1 - 10, 46):
        draw.line([fx, by - 24, fx, by], fill=(30, 40, 62, 255), width=5)
        draw.ellipse([fx - 5, by - 32, fx + 5, by - 22],
                     fill=(255, 200, 110, 255))
        gdraw.ellipse([fx - 14, by - 41, fx + 14, by - 13], fill=(70, 46, 10))

    # ---------- lanterns on the river ----------
    lanterns = []
    for _ in range(150):
        t = rng.uniform(0, 1)
        y = 580 + t * 420
        half = 82 + (y - 560) / 464 * 368
        x = 512 + rng.uniform(-half, half)
        s = 5 + t * 15 + rng.uniform(-2, 2)
        lanterns.append((x, y, s))
    lanterns.sort(key=lambda l: l[1])

    # reflections first (soft vertical streaks under each lantern)
    streak = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(streak)
    for x, y, s in lanterns:
        ln = 18 + s * 3.2
        sd.line([x, y + s, x, y + s + ln], fill=(255, 150, 70, 110),
                width=max(2, int(s * 0.7)))
    streak = streak.filter(ImageFilter.GaussianBlur(3))
    base = Image.alpha_composite(base, streak)
    draw = ImageDraw.Draw(base, "RGBA")

    for x, y, s in lanterns:
        gdraw.ellipse([x - s * 2.4, y - s * 2.4, x + s * 2.4, y + s * 2.4],
                      fill=(96, 58, 14))
        draw.ellipse([x - s, y - s * 0.82, x + s, y + s * 0.82],
                     fill=(255, 166, 66, 255))
        draw.ellipse([x - s * 0.55, y - s * 0.55, x + s * 0.55, y + s * 0.55],
                     fill=(255, 214, 130, 255))
        draw.line([x - s * 0.7, y - s * 0.82, x + s * 0.7, y - s * 0.82],
                  fill=(120, 60, 20, 255), width=2)
        draw.line([x - s * 0.7, y + s * 0.82, x + s * 0.7, y + s * 0.82],
                  fill=(120, 60, 20, 255), width=2)

    # a few sky lanterns rising
    for _ in range(10):
        x = rng.uniform(80, 940)
        y = rng.uniform(240, 480)
        s = rng.uniform(4, 7)
        gdraw.ellipse([x - s * 3, y - s * 3, x + s * 3, y + s * 3],
                      fill=(80, 48, 10))
        draw.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8],
                     fill=(255, 180, 90, 255))

    # ---------- foreground banks ----------
    draw.polygon([(0, 900), (260, 860), (330, H), (0, H)], fill=(12, 18, 34, 255))
    draw.polygon([(W, 900), (764, 860), (694, H), (W, H)], fill=(12, 18, 34, 255))
    for (x, y, s) in [(120, 950, 26), (905, 955, 28), (60, 990, 18),
                      (970, 995, 16)]:
        gdraw.ellipse([x - s * 2.4, y - s * 2.4, x + s * 2.4, y + s * 2.4],
                      fill=(96, 58, 14))
        draw.ellipse([x - s, y - s * 0.82, x + s, y + s * 0.82],
                     fill=(255, 166, 66, 255))
        draw.ellipse([x - s * 0.55, y - s * 0.55, x + s * 0.55, y + s * 0.55],
                     fill=(255, 214, 130, 255))

    # ---------- bloom: screen the blurred glow layer on top ----------
    glow = glow.filter(ImageFilter.GaussianBlur(14))
    base = ImageChops.screen(base.convert("RGB"), glow)
    draw = ImageDraw.Draw(base, "RGBA")

    # ---------- type ----------
    title_font = ImageFont.truetype(os.path.join(FONTS, "DejaVuSerif-Bold.ttf"), 116)
    sub_font = ImageFont.truetype(os.path.join(FONTS, "DejaVuSans.ttf"), 26)
    tag_font = ImageFont.truetype(os.path.join(FONTS, "DejaVuSans.ttf"), 20)

    draw_text_spaced(draw, W / 2, 52, "VELDARA", title_font, CREAM, 22,
                     shadow=(10, 14, 30, 255))
    draw_text_spaced(draw, W / 2, 196, "VALLEY OF THE FLOATING LANTERNS",
                     sub_font, (240, 224, 192), 9)
    # rules flanking the subtitle
    tw = draw.textlength("VALLEY OF THE FLOATING LANTERNS", font=sub_font) \
        + 9 * (len("VALLEY OF THE FLOATING LANTERNS") - 1)
    draw.line([W / 2 - tw / 2 - 130, 210, W / 2 - tw / 2 - 16, 210],
              fill=CREAM + (200,), width=2)
    draw.line([W / 2 + tw / 2 + 16, 210, W / 2 + tw / 2 + 130, 210],
              fill=CREAM + (200,), width=2)
    draw_text_spaced(draw, W / 2, 946, "WHERE THE RIVER CARRIES THE LIGHT",
                     tag_font, (235, 220, 190), 7)

    # ---------- frame ----------
    draw.rectangle([26, 26, W - 26, H - 26], outline=CREAM + (235,), width=3)
    draw.rectangle([34, 34, W - 34, H - 34], outline=CREAM + (110,), width=1)

    # ---------- grain + vignette ----------
    # keep the grain light: heavy grain blows the PNG past the 1 MiB gate
    arr = np.asarray(base.convert("RGB")).astype(np.int16)
    noise = np_rng.normal(0, 3.0, arr.shape[:2])[..., None]
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.25, -H * 0.25, W * 1.25, H * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(img, Image.blend(img, black, 0.22), vig)
    return img


if __name__ == "__main__":
    import sys

    out = render()
    out.save(sys.argv[1] if len(sys.argv) > 1 else "entry.png",
             optimize=True)
