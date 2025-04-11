#!/usr/bin/env python3

import os
import sys
import glob

from util import utils


def main(
    search_query=None,
    track_id=None,
    output=True,
    cover_brightness=1.10,
    cover_blur_radius=30,
    cover_round_radius=30,
    container_transparency=30,
    container_round_radius=45,
    text_length_limit_title=28,
    text_length_limit_artist=28,
    text_length_limit_album=28,
):

    if search_query:
        track_data = utils.get_track_data(search_query)
        
    else:
        track_data = utils.get_track_data_by_id(track_id)
    
    artists_name = utils.formatted_artists(track_data["artists"])
    track_name = track_data["name"]
    album_name = track_data["album"]["name"]

    safe_track_name = utils.safe_filename(track_name)
    safe_artist_name = utils.safe_filename(artists_name)
    
    filename = f"{safe_track_name}_{safe_artist_name}.png"

    # download cover
    utils.custom_print("[ 1/13]               downloading cover...", output)
    utils.get_cover(track_data["album"]["images"])

    # round its corners
    utils.custom_print("[ 2/13]                  rounding cover...", output)
    utils.round_corners("temp/input-converted.png", "temp/input-rounded.png", radius=cover_round_radius)

    # change brightness (will be used for the background)
    utils.custom_print("[ 3/13]       changing cover brightness...", output)
    utils.change_brightness(
        "temp/input-converted.png", cover_brightness, "temp/dark-input.png"
    )

    # then blur it
    utils.custom_print("[ 4/13]                  blurring cover...", output)
    utils.add_blur(
        "temp/dark-input.png", "temp/dark-blur-input.png", radius=cover_blur_radius
    )

    # and now upscale and zoom into it. this will be the background of the image card
    utils.custom_print("[ 5/13]    create background from cover...", output)
    utils.create_background("temp/dark-blur-input.png", "temp/background.png")

    # now we create the container
    utils.custom_print("[ 6/13]              creating container...", output)
    utils.create_container(
        "temp/container.png", 740, 960, (25, 25, 25)
    )

    # and we make it transparent
    utils.custom_print("[ 7/13]    making container transparent...", output)
    utils.make_transparent(
        "temp/container.png", (25, 25, 25), container_transparency, "temp/container-transparent.png"
    )

    # blur the container
    utils.custom_print("[ 8/13]              blurring container...", output)
    utils.add_blur("temp/container-transparent.png", "temp/container-blur.png")

    # round its corners
    utils.custom_print("[ 9/13]              rounding container...", output)
    utils.round_corners(
        "temp/container-blur.png",
        "temp/container-rounded.png",
        radius=container_round_radius,
    )

    # now we add the tracks cover image to the container
    utils.custom_print("[10/13]       adding cover to container...", output)
    utils.overlay_on_top(
        "temp/container-rounded.png",
        "temp/input-rounded.png",
        (50, 50),
        "temp/container-cover.png",
    )

    # now we add the artist name, track title and album name (color: 158, 158, 158)
    utils.custom_print("[11/13]        adding text to container...", output)
    utils.add_text(
        "temp/container-cover.png",
        track_name,
        (50, 720),
        (255, 255, 255),
        "temp/container-title.png",
        "util/SF-Pro-Display-Semibold.otf",
        text_length_limit_title,
    )
    utils.add_text(
        "temp/container-title.png",
        artists_name,
        (50, 780),
        (255, 255, 255),
        "temp/container-artist.png",
        "util/SF-Pro-Display-Semibold.otf",
        text_length_limit_artist,
    )
    utils.add_text(
        "temp/container-artist.png",
        album_name,
        (50, 860),
        (158, 158, 158),
        "temp/container-album.png",
        "util/SF-Pro-Display-Semibold.otf",
        text_length_limit_album,
    )

    # then we paste that container to the background
    utils.custom_print("[12/13] pasting container to background...", output)
    utils.overlay_on_top(
        "temp/background.png", "temp/container-album.png", (170, 490), filename
    )

    # clean up temp files
    utils.custom_print("[13/13]               cleaning temp dir...", output)
    sys.stdout.write("\r" + " " * 50 + "\r")

    for file in glob.glob("temp/*.**g"):
        os.remove(file)

    if output:
        print("all done")

    else:
        return filename


if __name__ == "__main__":
    main(sys.argv[1])
