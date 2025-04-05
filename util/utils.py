#!/usr/bin/env python3

import os
import sys

import requests

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps


def custom_print(string, output=False):
    if output:
        sys.stdout.write("\r" + " " * 50 + "\r")
        print(string, sep=" ", end="\r", flush=True)


def shorten_string(text, length):
    if len(text) > length:
        return text[:length] + "..."

    return text


def generate_new_token():
    client_id = os.environ["TRACKARD_SPOTIFY_CLIENT_ID"]
    client_secret = os.environ["TRACKARD_SPOTIFY_SECRET_ID"]

    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=10,
    ).json()

    new_token = resp["access_token"]
    os.environ["TRACKARD_SPOTIFY_TOKEN"] = new_token

    return new_token


def get_token():
    try:
        token = os.environ["TRACKARD_SPOTIFY_TOKEN"]

    except KeyError:
        token = generate_new_token()

    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(
        "https://api.spotify.com/v1/search?q=home+resonance&type=track",
        headers=headers,
        timeout=10,
    )

    if resp.status_code != 200:
        return generate_new_token()

    return token


def add_text(image, text, position, color, output, font_file, max_len):
    img = Image.open(image)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_file, 48)

    draw.text(position, shorten_string(text, max_len), font=font, fill=color)

    img.save(output)


def add_blur(image, output, radius=50):
    img = Image.open(image)
    blurred_image = img.filter(ImageFilter.GaussianBlur(radius))

    blurred_image.save(output)


def change_brightness(image, value, output):
    brightness_value_filter = ImageEnhance.Brightness(Image.open(image))
    brightness_value_output = brightness_value_filter.enhance(value)

    brightness_value_output.save(output)


def create_container(output, width, height, color):
    image = Image.new("RGB", (width, height), color)

    image.save(output)


def make_transparent(
    image_path, color_to_make_transparent, transparency_percentage, output_path
):
    img = Image.open(image_path).convert("RGBA")
    alpha_value = int(255 * (1 - transparency_percentage / 100))
    datas = img.getdata()
    new_data = []

    for item in datas:
        if item[:3] == color_to_make_transparent:
            new_data.append(
                (item[0], item[1], item[2], alpha_value)
            )

        else:
            new_data.append(item)

    img.putdata(new_data)
    img.save(output_path)


def get_track_data(query):
    url = "https://api.spotify.com/v1/search"
    params = {"q": query, "type": "track", "limit": 1}
    headers = {"Authorization": f"Bearer {get_token()}"}

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if data["tracks"]["items"]:
        return data["tracks"]["items"][0]


def formatted_artists(artists_data):
    artists = []

    for artist in artists_data:
        artists.append(artist["name"])

    if len(artists) >= 2:
        artists[-1] = f"& {artists[-1]}"
        artists_string = ", ".join(artists)

        if len(artists) == 2:
            artists_string = artists_string.replace(",", "")

        artists_string = artists_string.replace(", &", " &")

    else:
        artists_string = artists[0]

    return artists_string


def get_cover(images):
    highest_quality_image = max(images, key=lambda x: x["height"] * x["width"])

    with open("temp/input.jpg", "wb") as cover_img:
        try:
            cover_img.write(
                requests.get(highest_quality_image["url"], timeout=10).content
            )

            img = Image.open("temp/input.jpg")

            if img.size != (640, 640):
                img = img.resize((640, 640))

            img.save("temp/input-converted.png")

        except Exception as e:
            sys.exit(f"Couldnt download cover: {e}")


def create_background(image_path, output_path, width=1080, height=1920):
    img = Image.open(image_path)
    original_width, original_height = img.size

    target_aspect_ratio = width / height

    if original_width / original_height > target_aspect_ratio:
        new_width = int(original_height * target_aspect_ratio)
        new_height = original_height

    else:
        new_width = original_width
        new_height = int(original_width / target_aspect_ratio)

    left = (original_width - new_width) // 2
    top = (original_height - new_height) // 2
    right = left + new_width
    bottom = top + new_height

    cropped_img = img.crop((left, top, right, bottom))
    resized_img = cropped_img.resize((width, height), Image.LANCZOS)

    resized_img.save(output_path)


def overlay_on_top(
    background_path,
    overlay_path,
    position: tuple[int],
    # overlay_size: tuple[int],
    output,
):
    background = Image.open(background_path)

    overlay = Image.open(overlay_path)
    # overlay = overlay.resize(overlay_size)

    background.paste(overlay, position, overlay)
    background.save(output)


def round_corners(image_path, output_filename, radius=30, resolution=4):
    with Image.open(image_path) as im:
        im = im.convert("RGBA")

        hi_res_size = (im.size[0] * resolution, im.size[1] * resolution)
        hi_res_radius = radius * resolution

        mask = Image.new("L", hi_res_size, 0)
        draw = ImageDraw.Draw(mask)

        left, top, right, bottom = 0, 0, hi_res_size[0], hi_res_size[1]
        draw.rounded_rectangle([left, top, right, bottom], hi_res_radius, fill=255)

        mask = mask.resize(im.size, Image.Resampling.LANCZOS)
        output = Image.new("RGBA", im.size)

        output.paste(im, (0, 0), mask)
        output.save(output_filename, format="PNG")


def safe_filename(text):
    valid_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    filename = "".join(c if c in valid_chars else "_" for c in text)

    return filename.strip().replace(" ", "_").replace("__", "_")
