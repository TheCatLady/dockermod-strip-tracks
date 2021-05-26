#!/usr/bin/env python3

from iso_639_codes import translate
import json
import logging
import os
import requests
import subprocess
import sys
import time
import untangle

def refresh_arr():
    if SERVER_TYPE == "radarr":
        payload = {"name": "RefreshMovie", "movieIds": [MOVIE_ID]}
    elif SERVER_TYPE == "sonarr":
        payload = {"name": "RefreshSeries", "seriesId": SERIES_ID}

    params = {"apikey": API_KEY}
    req = requests.post(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/command", params=params, json=payload)

    try:
        req.raise_for_status()
        response = req.json()

        if "id" in response:
            COMMAND_ID = response["id"]

            while True:
                time.sleep(5)
                params = {"apikey": API_KEY}
                req = requests.get(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/command/{COMMAND_ID}", params=params)

                try:
                    req.raise_for_status()
                    response = req.json()

                    if response["status"].lower() == "completed":
                        break
                except Exception as e:
                    log.error(e)
                    break
    except Exception as e:
        log.error(e)

def restore_meta():
    if SCENE_NAME or RELEASE_GROUP:
        params = {"apikey": API_KEY}
        req = requests.get(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/{'movie' if SERVER_TYPE == 'radarr' else 'episode'}/{MOVIE_ID if SERVER_TYPE == 'radarr' else EPISODE_ID}", params=params)

        try:
            req.raise_for_status()
            item = req.json()

            FILE_ID = item[f"{'movieFile' if SERVER_TYPE == 'radarr' else 'episodeFile'}"]["id"]

            req = requests.get(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/{'movie' if SERVER_TYPE == 'radarr' else 'episode'}file/{FILE_ID}", params=params)
            req.raise_for_status()
            file = req.json()

            file["sceneName"] = SCENE_NAME
            file["releaseGroup"] = RELEASE_GROUP

            req = requests.put(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/{'movie' if SERVER_TYPE == 'radarr' else 'episode'}file/{FILE_ID}", params=params, json=file)
            req.raise_for_status()
        except Exception as e:
            log.error(e)

if os.environ.get("radarr_eventtype"):
    SERVER_TYPE = "radarr"
else:
    SERVER_TYPE = "sonarr"

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(f"{SERVER_TYPE}PostProcessing")

EVENT_TYPE = os.environ.get(f"{SERVER_TYPE}_eventtype")
if EVENT_TYPE != "Download":
    log.info(f"Event type is not Download, but {EVENT_TYPE}.")
    sys.exit(0)

CONFIG_DIR = os.environ.get("CONFIG_DIR")
if not CONFIG_DIR:
    CONFIG_DIR = "/config"
    os.environ["CONFIG_DIR"] = CONFIG_DIR

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    API_KEY = untangle.parse(f"{CONFIG_DIR}/config.xml").Config.ApiKey.cdata
    os.environ["API_KEY"] = API_KEY

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    log.error(f"TMDB_API_KEY environment variable must be set.")
    sys.exit(1)

try:
    SUBTITLE_LANGUAGES = list(filter(str.strip, os.environ.get("SUBTITLE_LANGUAGES").lower().split(",")))
except Exception:
    SUBTITLE_LANGUAGES = []

try:
    EXCLUDED_KEYWORDS = list(filter(str.strip, os.environ.get("EXCLUDED_KEYWORDS").lower().split(",")))
except Exception:
    EXCLUDED_KEYWORDS = []

if SERVER_TYPE == "radarr":
    MOVIE_ID = int(os.environ.get("radarr_movie_id"))
    FILE_ID = int(os.environ.get("radarr_moviefile_id"))
    FILE_PATH = os.environ.get("radarr_moviefile_path")
    TMDB_ID = os.environ.get("radarr_movie_tmdbid")
    SCENE_NAME = os.environ.get("radarr_moviefile_scenename")
    RELEASE_GROUP = os.environ.get("radarr_moviefile_releasegroup")

elif SERVER_TYPE == "sonarr":
    SERIES_ID = int(os.environ.get("sonarr_series_id"))
    EPISODE_ID = int(os.environ.get("sonarr_episodefile_episodeids").split(",")[0])
    FILE_ID = int(os.environ.get("sonarr_episodefile_id"))
    FILE_PATH = os.environ.get("sonarr_episodefile_path")
    TVDB_ID = os.environ.get("sonarr_series_tvdbid")
    SCENE_NAME = os.environ.get("sonarr_episodefile_scenename")
    RELEASE_GROUP = os.environ.get("sonarr_episodefile_releasegroup")

    params = {"api_key": TMDB_API_KEY, "external_source": "tvdb_id"}
    req = requests.get(f"https://api.themoviedb.org/3/find/{TVDB_ID}", params=params)

    try:
        req.raise_for_status()
        tmdbData = req.json()
        TMDB_ID = tmdbData["tv_results"][0]["id"]
    except HTTPError as e:
        log.error(e)

    if not TMDB_ID:
        log.error(f"Could not find TMDb ID for series with TVDB ID {TVDB_ID}.")
        sys.exit(1)

params = {"api_key": TMDB_API_KEY}
req = requests.get(f"https://api.themoviedb.org/3/{'movie' if SERVER_TYPE == 'radarr' else 'tv'}/{TMDB_ID}", params=params)

try:
    req.raise_for_status()
    tmdbData = req.json()

    if "original_language" in tmdbData:
        ORIGINAL_LANGUAGE = translate(tmdbData["original_language"])
    else:
        ORIGINAL_LANGUAGE = ""
except Exception as e:
    log.error(e)

result = subprocess.run(["mkvmerge", "-J", FILE_PATH], check=True, capture_output=True, text=True)

tracks = json.loads(result.stdout)["tracks"]
videoTrack = ""
audioTrack = ""
subtitleTracks = []
nonForcedSubtitleLanguages = []

for track in tracks:
    excludeTrack = False
    if "track_name" in track["properties"]:
        for keyword in EXCLUDED_KEYWORDS:
            if keyword in track["properties"]["track_name"].lower():
                excludeTrack = True

    if track["type"] == "video":
        # Keep only the first video track
        if not videoTrack:
            videoTrack = str(track["id"])

    elif track["type"] == "audio":
        # Keep only the first matching audio track
        if not audioTrack:
            if "language" not in track["properties"] or not ORIGINAL_LANGUAGE or track["properties"]["language"] == ORIGINAL_LANGUAGE:
                if "track_name" not in track["properties"] or not excludeTrack:
                    audioTrack = str(track["id"])

    elif track["type"] == "subtitles":
        # Subtitle track language is either undefined or in the list of desired subtitle languages
        if "language" not in track["properties"] or track["properties"]["language"] in SUBTITLE_LANGUAGES:
            # No excluded keywords in track name
            if "track_name" not in track["properties"] or not excludeTrack:
                # Forced track or non-SDH track... or, SDH track iff no non-forced tracks in that language yet
                if ("forced_track" in track["properties"] and track["properties"]["forced_track"]) or "track_name" not in track["properties"] or "sdh" not in track["properties"]["track_name"].lower() or ("language" in track["properties"] and track["properties"]["language"] not in nonForcedSubtitleLanguages):
                    subtitleTracks.append(str(track["id"]))

                    # Keep track (pun not intended) of languages for which we already have non-forced track
                    if "language" in track["properties"] and "forced_track" not in track["properties"] or ("forced_track" in track["properties"] and not track["properties"]["forced_track"]):
                        nonForcedSubtitleLanguages.append(track["properties"]["language"])

if videoTrack and audioTrack:
    log.info(f"Keeping video track {videoTrack}, audio track {audioTrack}, and subtitle track(s) {','.join(subtitleTracks)} for {FILE_PATH}")

    os.rename(FILE_PATH, f"{FILE_PATH}.old")

    # Refresh as a workaround for https://github.com/Sonarr/Sonarr/issues/3366
    refresh_arr()

    mkvmerge = [
        "mkvmerge",
        "-o", f"{FILE_PATH}.new",
        "-d", videoTrack,
        "--language", f"{videoTrack}:{ORIGINAL_LANGUAGE}",
        "--default-track", videoTrack,
        "-a", audioTrack,
        "--default-track", audioTrack,
    ]

    if len(subtitleTracks) > 0:
        mkvmerge.extend(["-s", ",".join(subtitleTracks)])
    else:
        mkvmerge.append("-S")

    mkvmerge.append(f"{FILE_PATH}.old")

    # Re-order tracks so that video track is always ID 0, and audio track is always ID 1
    orderedTracks = [videoTrack, audioTrack]
    orderedTracks.extend(subtitleTracks)
    mkvmerge.extend(["--track-order", f"0:{',0:'.join(orderedTracks)}"])

    subprocess.run(mkvmerge, check=True)
    os.rename(f"{FILE_PATH}.new", FILE_PATH)
    os.remove(f"{FILE_PATH}.old")

    refresh_arr()
    restore_meta()

if os.environ.get("DISCORD_WEBHOOK"):
    log.info("Sending Discord notification.")
    subprocess.run(["/usr/local/bin/arr-discord-notifier"], check=True)
