import os
from PIL import Image, ImageDraw

OUTPUT = "temp_images"


def generate_images(scenes):

    os.makedirs(OUTPUT, exist_ok=True)

    image_files = []

    for i, scene in enumerate(scenes):

        img = Image.new("RGB", (1080, 1920), (100, 180, 255))

        d = ImageDraw.Draw(img)

        d.text((100, 900), scene.text, fill=(0, 0, 0))

        path = f"{OUTPUT}/scene_{i}.png"

        img.save(path)

        image_files.append(path)

    return image_files
