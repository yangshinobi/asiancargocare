#!/usr/bin/env python3
"""
build_og.py — composes the Asian Cargocare OG share card.

Output:  public/og-cover.png  (1200x630, sRGB)
         public/og-cover-square.png  (1200x1200, X-card fallback)

Brand tokens from src/index.css:
  --brand-orange: #E57025 / #ff8e53
  --brand-forest:  #12441f
  --brand-blue:    #2fa2d9
"""
from __future__ import annotations
import io
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# brand tokens (mirroring ecologitex.com)
ORANGE = (229, 112, 37)      # #E57025 — cargo orange (primary)
ORANGE_LIGHT = (255, 142, 83)  # #ff8e53
FOREST = (18, 68, 31)        # #12441f
WHITE = (255, 255, 255)
INK = (15, 23, 42)
SLATE_900 = (15, 23, 42)

# macOS system fonts
FONT_HELV = "/System/Library/Fonts/Helvetica.ttc"
FONT_HELV_NEUE = "/System/Library/Fonts/HelveticaNeue.ttc"
FONT_MENLO = "/System/Library/Fonts/Menlo.ttc"
FONT_AVENIR = "/System/Library/Fonts/Avenir.ttc"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size=size)
    except OSError:
        return ImageFont.load_default()


def fetch(url: str) -> Image.Image:
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "asiancargocare-og-builder/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def cover_crop(img, w, h):
    src_w, src_h = img.size
    target_ratio = w / h
    src_ratio = src_w / src_h
    if src_ratio > target_ratio:
        new_w = int(src_h * target_ratio)
        x0 = (src_w - new_w) // 2
        img = img.crop((x0, 0, x0 + new_w, src_h))
    else:
        new_h = int(src_w / target_ratio)
        y0 = (src_h - new_h) // 2
        img = img.crop((0, y0, src_w, y0 + new_h))
    return img.resize((w, h), Image.LANCZOS)


def add_dark_gradient(img, bottom_alpha: int = 215):
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    for y in range(0, h, 2):
        t = y / h
        a = int(min(bottom_alpha, max(0, t * bottom_alpha)))
        for x in range(0, w, 4):
            px[x, y] = (8, 20, 12, a)
    overlay = overlay.resize((w, h), Image.BILINEAR)
    img = img.convert("RGBA")
    return Image.alpha_composite(img, overlay).convert("RGB")


def add_wordmark_plate(img, x, y, w, h):
    plate = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rectangle((x, y, x + w, y + h), fill=(8, 20, 12, 140))
    plate = plate.filter(ImageFilter.GaussianBlur(radius=20))
    return Image.alpha_composite(img.convert("RGBA"), plate).convert("RGB")


def draw_card_1200x630(bg, out):
    w, h = 1200, 630
    base = cover_crop(bg, w, h)
    base = add_dark_gradient(base, bottom_alpha=215)
    f_brand_huge = font(FONT_HELV_NEUE, 100)
    f_tagline = font(FONT_HELV, 36)
    f_micro = font(FONT_MENLO, 17)
    f_brand_sm = font(FONT_HELV, 22)
    pad = 60
    base = add_wordmark_plate(base, 0, 0, w, 200)
    d = ImageDraw.Draw(base)
    # wordmark
    d.text((pad + 2, pad + 2), "Asian Cargocare", font=f_brand_huge, fill=(0, 0, 0))
    d.text((pad, pad), "Asian Cargocare", font=f_brand_huge, fill=ORANGE_LIGHT)
    # tagline
    tagline1 = "Air-freight forwarding, ocean consolidation,"
    tagline2 = "and customs-cleared lanes from India to the world."
    bbox1 = d.textbbox((0, 0), tagline1, font=f_tagline)
    bbox2 = d.textbbox((0, 0), tagline2, font=f_tagline)
    tw1, th1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]
    tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    cx = w // 2
    cy = h // 2 + 20
    d.text((cx - tw1 // 2 + 2, cy - th1 - 8 + 2), tagline1, font=f_tagline, fill=(0, 0, 0))
    d.text((cx - tw1 // 2, cy - th1 - 8), tagline1, font=f_tagline, fill=WHITE)
    d.text((cx - tw2 // 2 + 2, cy + 8 + 2), tagline2, font=f_tagline, fill=(0, 0, 0))
    d.text((cx - tw2 // 2, cy + 8), tagline2, font=f_tagline, fill=WHITE)
    # micro tags
    tags = "Since 1986  ·  Reactivation workstream active  ·  Q3 2026"
    d.text((pad + 2, h - pad - 28 + 2), tags, font=f_micro, fill=(0, 0, 0))
    d.text((pad, h - pad - 28), tags, font=f_micro, fill=ORANGE_LIGHT)
    # url
    url_text = "asiancargocare.com"
    bu = d.textbbox((0, 0), url_text, font=f_brand_sm)
    uw, uh = bu[2] - bu[0], bu[3] - bu[1]
    d.text((w - pad - uw + 2, h - pad - uh + 0), url_text, font=f_brand_sm, fill=(0, 0, 0))
    d.text((w - pad - uw, h - pad - uh - 2), url_text, font=f_brand_sm, fill=ORANGE_LIGHT)
    # rule
    d.rectangle((pad, h - pad - 60, w - pad, h - pad - 58), fill=ORANGE_LIGHT)
    base.save(out, "PNG", optimize=True)
    print(f"  wrote {out}  ({out.stat().st_size:,} bytes)")


def draw_card_1200x1200(bg, out):
    w = h = 1200
    base = cover_crop(bg, w, h)
    base = add_dark_gradient(base, bottom_alpha=225)
    f_brand_huge = font(FONT_HELV_NEUE, 130)
    f_tagline = font(FONT_HELV, 44)
    f_micro = font(FONT_MENLO, 20)
    f_brand_sm = font(FONT_HELV, 28)
    pad = 80
    base = add_wordmark_plate(base, 0, 0, w, 280)
    d = ImageDraw.Draw(base)
    d.text((pad + 2, pad + 2), "Asian Cargocare", font=f_brand_huge, fill=(0, 0, 0))
    d.text((pad, pad), "Asian Cargocare", font=f_brand_huge, fill=ORANGE_LIGHT)
    lines = [
        "Air-freight forwarding,",
        "ocean consolidation,",
        "and customs-cleared lanes",
        "from India to the world.",
    ]
    cy = h // 2
    for i, line in enumerate(lines):
        bb = d.textbbox((0, 0), line, font=f_tagline)
        lw, lh = bb[2] - bb[0], bb[3] - bb[1]
        d.text((w // 2 - lw // 2 + 2, cy - 130 + i * 60 + 2), line, font=f_tagline, fill=(0, 0, 0))
        d.text((w // 2 - lw // 2, cy - 130 + i * 60), line, font=f_tagline, fill=WHITE)
    tags = "Since 1986  ·  Reactivation workstream active  ·  Q3 2026"
    d.text((pad + 2, h - pad - 36 + 2), tags, font=f_micro, fill=(0, 0, 0))
    d.text((pad, h - pad - 36), tags, font=f_micro, fill=ORANGE_LIGHT)
    url_text = "asiancargocare.com"
    bu = d.textbbox((0, 0), url_text, font=f_brand_sm)
    uw, uh = bu[2] - bu[0], bu[3] - bu[1]
    d.text((w - pad - uw + 2, h - pad - uh + 0), url_text, font=f_brand_sm, fill=(0, 0, 0))
    d.text((w - pad - uw, h - pad - uh - 4), url_text, font=f_brand_sm, fill=ORANGE_LIGHT)
    d.rectangle((pad, h - pad - 80, w - pad, h - pad - 78), fill=ORANGE_LIGHT)
    base.save(out, "PNG", optimize=True)
    print(f"  wrote {out}  ({out.stat().st_size:,} bytes)")


def main():
    repo = Path(__file__).resolve().parent.parent
    public = repo / "public"
    public.mkdir(parents=True, exist_ok=True)
    # Use the freight / port / logistics shots from the same Cloudinary pool
    bg_url_candidates = [
        "https://res.cloudinary.com/dhyaqzbv0/image/upload/v1758953170/terminal1_vsbtmk.jpg",
        "https://res.cloudinary.com/dhyaqzbv0/image/upload/v1758953172/terminal2_srzs7c.jpg",
        "https://res.cloudinary.com/dhyaqzbv0/image/upload/v1750756544/aircargo_fbyte1.jpg",
        "https://res.cloudinary.com/dhyaqzbv0/image/upload/v1740756546/conatainers_oarreu.jpg",
        "https://res.cloudinary.com/dhyaqzbv0/image/upload/v1758955490/6_iaiupu.jpg",
    ]
    bg = None
    last_err = None
    for url in bg_url_candidates:
        try:
            print(f"  fetching {url}")
            bg = fetch(url)
            print(f"  got {bg.size}")
            break
        except Exception as e:
            print(f"  failed: {e}", file=sys.stderr)
            last_err = e
    if bg is None:
        print(f"  could not fetch any background: {last_err}", file=sys.stderr)
        return 1
    print("Building 1200x630 OG card…")
    draw_card_1200x630(bg, public / "og-cover.png")
    print("Building 1200x1200 square card…")
    draw_card_1200x1200(bg, public / "og-cover-square.png")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
