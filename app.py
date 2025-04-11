import os
import hmac
import base64
import hashlib
import subprocess

from io import BytesIO

import pylistenbrainz
import requests

import trackard

from util import utils

from PIL import Image
from flask import Flask, request, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

pylistenbrainz_client = pylistenbrainz.ListenBrainz()

BASE_URL = "https://ws.audioscrobbler.com/2.0"
API_KEY = os.environ.get("TRACKARD_LASTFM_TOKEN")
TRACKARD_MODE = os.environ.get("TRACKARD_MODE")
APP_SECRET_TOKEN = os.environ.get("APP_SECRET_TOKEN")  

if TRACKARD_MODE == "debug":
    print("[TRACKARD] DEBUG = True")
    app.config["DEBUG"] = True
    
    print("[TRACKARD] TEMPLATES_AUTO_RELOAD = True")
    app.config["TEMPLATES_AUTO_RELOAD"] = True


def lastfm_client(username):
    resp = requests.get(
        f"{BASE_URL}/?api_key={API_KEY}&method=User.getrecenttracks&user={username}&format=json&limit=1"
    )
    data = resp.json()

    artist = data["recenttracks"]["track"][0]["artist"]["#text"]
    title = data["recenttracks"]["track"][0]["name"]
    nowplaying = data["recenttracks"]["track"][0].get("@attr")

    return f"{title} {artist}"


def listenbrainz_client(username):
    data = pylistenbrainz_client.get_playing_now(username=username) or pylistenbrainz_client.get_listens(username=username)[0]

    artist = data.artist_name
    title = data.track_name

    return f"{title} {artist}"


def verify_signature(secret_token, signature_header, payload_body):
    if not signature_header:
        return False
        
    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if hmac.compare_digest(expected_signature, signature_header):
        return True

    else:
        return False


@app.route("/autod", methods=["POST"])
def autod():
    signature = request.headers.get("X-Hub-Signature-256")
    payload = request.get_data()

    if verify_signature(APP_SECRET_TOKEN, signature, payload):
        subprocess.Popen([os.path.abspath("auto-deploy.sh")])

        return "", 200

    else:
        return "", 403


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/examples")
def examples():
    return render_template("examples.html")


@app.route("/diff")
def diff():
    return render_template("diff.html")


@app.route("/get")
def get_image():
    username = request.args["username"]
    service = request.args["service"]
    s_query = request.args["track_title_artist"]
    spotify_track_id = request.args["spotify_track_id"]

    filename = None
    search_query = None

    if username:
        if service == "listenbrainz":
            search_query = listenbrainz_client(username)

        else:
            search_query = lastfm_client(username)

    elif s_query:
        search_query = s_query

    filename = trackard.main(
        search_query,
        spotify_track_id,
        False,
        float(request.args["cover_brightness"]),
        int(request.args["cover_blur_radius"]),
        int(request.args["cover_round_radius"]),
        int(request.args["container_transparency"]),
        int(request.args["container_round_radius"]),
        int(request.args["text_length_limit_title"]),
        int(request.args["text_length_limit_artist"]),
        int(request.args["text_length_limit_album"]),
    )

    img_data = BytesIO()
    img = Image.open(filename)
    img.save(img_data, format="PNG")
    img_data.seek(0)

    img_base64 = base64.b64encode(img_data.getvalue()).decode()

    try:
        os.remove(filename)

    except OSError:
        pass

    return render_template("get.html", img_base64=img_base64)
