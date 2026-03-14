"""
image_generator.py — Cartoon image generation for Kids Cartoon Maker.

PRIMARY:  Pollinations.ai — 100% free, no API key, no sign-up, no rate limits.
          Just sends an HTTP GET request and receives a cartoon image back.
          https://pollinations.ai

FALLBACK: Procedurally generated colorful PIL cartoon scenes.
          Works with zero internet connection.

Nothing here costs money. Nothing requires registration. Ever.
"""

import os
import io
import time
import random
import urllib.parse
import requests
from PIL import Image, ImageDraw
from typing import Optional


# ─────────────────────────────────────────────
# POLLINATIONS.AI  —  FREE, NO KEY NEEDED
# ─────────────────────────────────────────────
# Pollinations.ai is a completely free, open-access AI image generation
# service. No account, no API key, no credit card — ever.
# Docs: https://pollinations.ai

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

STYLE_SUFFIX = (
    ", cute cartoon illustration for children, bright vibrant colors, "
    "simple clean shapes, friendly characters, whimsical, no text, "
    "safe for kids, flat cartoon style, digital art"
)

POLLINATIONS_PARAMS = {
    "width":  768,
    "height": 512,
    "seed":   42,
    "model":  "flux",      # Best free model on Pollinations
    "nologo": "true",
    "safe":   "true",      # Safe content filter on
}


def generate_image_pollinations(prompt: str, output_path: str, scene_index: int = 0) -> bool:
    """
    Generate a cartoon image via Pollinations.ai.
    Completely free — no API key, no account, no cost.

    Args:
        prompt:       Scene description for image generation
        output_path:  Where to save the PNG image
        scene_index:  Used to vary the seed so each scene looks different

    Returns:
        True on success, False on failure (fallback will be used)
    """
    full_prompt = prompt + STYLE_SUFFIX
    encoded     = urllib.parse.quote(full_prompt)
    url         = POLLINATIONS_URL.format(prompt=encoded)

    params = dict(POLLINATIONS_PARAMS)
    params["seed"] = 42 + scene_index * 7   # Different seed per scene

    try:
        print(f"    🌐 Calling Pollinations.ai (free, no key needed)...")
        response = requests.get(url, params=params, timeout=60)

        if response.status_code == 200 and len(response.content) > 1000:
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            img = img.resize((768, 512), Image.LANCZOS)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, "PNG")
            return True
        else:
            print(f"    ⚠️  Pollinations returned status {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("    ⚠️  Pollinations timed out — using fallback art")
        return False
    except Exception as e:
        print(f"    ⚠️  Pollinations error: {e} — using fallback art")
        return False


# ─────────────────────────────────────────────
# PROCEDURAL PIL FALLBACK  —  ZERO DEPENDENCIES
# ─────────────────────────────────────────────

PALETTES = [
    ["#FFD700", "#87CEEB", "#90EE90", "#FF69B4", "#FFA07A"],  # Sunny meadow
    ["#6495ED", "#DDA0DD", "#98FB98", "#F0E68C", "#FF6347"],  # Rainbow
    ["#191970", "#4169E1", "#9370DB", "#C0C0C0", "#FFD700"],  # Night sky
    ["#228B22", "#32CD32", "#ADFF2F", "#FFD700", "#FF8C00"],  # Forest
    ["#87CEEB", "#FFFFFF", "#FFD700", "#FF69B4", "#98FB98"],  # Daytime
]


def _draw_cloud(draw, x, y, size, color):
    for dx, dy, r in [(0,0,size),(size,0,int(size*.8)),(-size,0,int(size*.8)),
                      (size//2,-size//2,int(size*.7)),(-size//2,-size//2,int(size*.7))]:
        draw.ellipse([x+dx-r, y+dy-r, x+dx+r, y+dy+r], fill=color)


def _draw_star(draw, cx, cy, size, color):
    import math
    pts = []
    for i in range(10):
        angle = math.pi / 5 * i - math.pi / 2
        r = size if i % 2 == 0 else size * 0.4
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(pts, fill=color)


def _draw_sun(draw, cx, cy, size, color):
    import math
    draw.ellipse([cx-size, cy-size, cx+size, cy+size], fill=color)
    for i in range(8):
        a = math.pi / 4 * i
        draw.line([cx + size*1.1*math.cos(a), cy + size*1.1*math.sin(a),
                   cx + size*1.6*math.cos(a), cy + size*1.6*math.sin(a)],
                  fill=color, width=max(3, size//8))


def _draw_tree(draw, x, y, h, colors):
    tw = max(8, h // 6)
    draw.rectangle([x-tw//2, y-h//3, x+tw//2, y], fill="#8B4513")
    for scale, offset in [(1.0, 0), (0.75, h//4), (0.55, h//2)]:
        draw.polygon([
            (x, y - h//3 - offset - int(h//3*scale)),
            (x - int(h//3*scale), y - h//3 - offset),
            (x + int(h//3*scale), y - h//3 - offset),
        ], fill=colors[1])


def generate_fallback_image(scene_description: str, output_path: str, index: int = 0) -> str:
    """
    Generate a colorful procedural cartoon scene using PIL only.
    Works with no internet, no API, no dependencies beyond Pillow.
    """
    W, H = 768, 512
    palette = PALETTES[index % len(PALETTES)]
    img = Image.new("RGB", (W, H), palette[1])
    draw = ImageDraw.Draw(img)

    # Sky gradient
    for i in range(H // 2):
        t = i / (H // 2)
        r = int(135 + t * 50); g = int(206 + t * 30); b = int(235 - t * 20)
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    # Ground
    for i in range(H // 2, H):
        t = (i - H // 2) / (H // 2)
        r = int(60 + t * 40); g = int(179 - t * 20); b = 60
        draw.line([(0, i), (W, i)], fill=(r, g, b))

    # Night sky variant
    if index % 3 == 2:
        for y in range(H // 2):
            t = y / (H // 2)
            draw.line([(0, y), (W, y)], fill=(int(20+t*10), int(20+t*10), int(60+t*20)))
        for _ in range(40):
            sx = random.randint(0, W); sy = random.randint(0, H//2-20)
            r = random.randint(2, 5)
            draw.ellipse([sx-r, sy-r, sx+r, sy+r], fill="white")
        _draw_star(draw, W-120, 80, 40, "#FFD700")
    else:
        _draw_sun(draw, 100, 80, 55, "#FFD700")

    # Clouds
    for cx in [200, 450, 650]:
        _draw_cloud(draw, cx, random.randint(40, 130), random.randint(30, 50), "white")

    # Trees
    for tx in [50, 180, W-80, W-200]:
        _draw_tree(draw, tx, H-30, random.randint(120, 180), palette)

    # Central cartoon character
    cx, cy = W // 2, H // 2 + 40
    body_color = ["#FF69B4","#FFD700","#87CEEB","#FF6347","#DDA0DD"][index % 5]
    draw.ellipse([cx-30, cy-10, cx+30, cy+80], fill=body_color)
    draw.ellipse([cx-40, cy-80, cx+40, cy],    fill="#FFDAB9")
    for ex in [cx-15, cx+15]:
        draw.ellipse([ex-8, cy-60, ex+8, cy-44], fill="white")
        draw.ellipse([ex-5, cy-57, ex+5, cy-47], fill="#333333")
    draw.arc([cx-20, cy-50, cx+20, cy-30], start=0, end=180, fill="#CC5500", width=3)
    draw.line([cx-30, cy+20, cx-70, cy+50], fill=body_color, width=10)
    draw.line([cx+30, cy+20, cx+70, cy+50], fill=body_color, width=10)
    draw.line([cx-15, cy+80, cx-25, cy+130], fill=body_color, width=12)
    draw.line([cx+15, cy+80, cx+25, cy+130], fill=body_color, width=12)

    # Sparkles
    for _ in range(8):
        _draw_star(draw, random.randint(0,W), random.randint(0,H//3), 10, palette[0])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def generate_scene_images(
    scenes: list,
    output_dir: str,
    use_ai: bool = True,
) -> list:
    """
    Generate cartoon images for all scenes.

    Tries Pollinations.ai (free, no key) first.
    Falls back to procedural PIL art if offline or on error.

    Args:
        scenes:     List of RhymeScene objects
        output_dir: Directory to save images
        use_ai:     Set False to always use procedural art (faster, offline)

    Returns:
        List of image file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    image_files = []

    for i, scene in enumerate(scenes):
        output_path = os.path.join(output_dir, f"scene_{i:03d}.png")
        print(f"  🖼️  Generating image for scene {i+1}/{len(scenes)}")

        success = False
        if use_ai:
            success = generate_image_pollinations(scene.scene_description, output_path, i)

        if not success:
            if use_ai:
                print(f"    🎨 Using procedural fallback art")
            generate_fallback_image(scene.scene_description, output_path, i)

        image_files.append(output_path)
        time.sleep(0.5)   # Small pause to be polite to Pollinations servers

    return image_files
