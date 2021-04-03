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
        payload = {"name": "RefreshMovie", "movieIds": [ID]}
    elif SERVER_TYPE == "sonarr":
        payload = {"name": "RefreshSeries", "seriesId": ID}

    params = {"apikey": untangle.parse('/config/config.xml').Config.ApiKey.cdata}
    req = requests.post(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/command", params=params, json=payload)
    try:
        req.raise_for_status()
        return req.json()
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
    log.info(f"Event type is not Download, but {EVENT_TYPE}. Nothing to do here. Exiting script.")
    sys.exit(0)

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")

try:
    SUBTITLE_LANGUAGES = list(filter(str.strip, os.environ.get("SUBTITLE_LANGUAGES").lower().split(',')))
except Exception:
    SUBTITLE_LANGUAGES = []

try:
    EXCLUDED_KEYWORDS = list(filter(str.strip, os.environ.get("EXCLUDED_KEYWORDS").lower().split(',')))
except Exception:
    EXCLUDED_KEYWORDS = []

if SERVER_TYPE == "radarr":
    ID = int(os.environ.get("radarr_movie_id"))
    FILE_PATH = os.environ.get("radarr_moviefile_path")
    TMDB_ID = os.environ.get("radarr_movie_tmdbid")
elif SERVER_TYPE == "sonarr":
    ID = int(os.environ.get("sonarr_series_id"))
    FILE_PATH = os.environ.get("sonarr_episodefile_path")
    TVDB_ID = os.environ.get("sonarr_series_tvdbid")

    params = {"api_key": TMDB_API_KEY, "external_source": "tvdb_id"}
    req = requests.get(f"https://api.themoviedb.org/3/find/{TVDB_ID}", params=params)
    try:
        req.raise_for_status()
    except HTTPError as e:
        log.error(e)

    tmdbData = req.json()
    TMDB_ID = tmdbData["tv_results"][0]["id"]

params = {"api_key": TMDB_API_KEY}
req = requests.get(f"https://api.themoviedb.org/3/{'movie' if SERVER_TYPE == 'radarr' else 'tv'}/{TMDB_ID}", params=params)
try:
    req.raise_for_status()
    tmdbData = req.json()
except Exception as e:
    log.error(e)

if "original_language" in tmdbData:
    ORIGINAL_LANGUAGE = translate(tmdbData["original_language"])
else:
    ORIGINAL_LANGUAGE = ""

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
        if videoTrack == "":
            videoTrack = str(track["id"])

    elif track["type"] == "audio":
        # Keep only the first matching audio track
        if audioTrack == "":
            if "language" not in track["properties"] or ORIGINAL_LANGUAGE == "" or track["properties"]["language"] == ORIGINAL_LANGUAGE:
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

                    if "language" in track["properties"] and "forced_track" not in track["properties"] or ("forced_track" in track["properties"] and not track["properties"]["forced_track"]):
                        nonForcedSubtitleLanguages.append(track["properties"]["language"])

if videoTrack != "" and audioTrack != "":
    log.info(f"Keeping video track {videoTrack}, audio track {audioTrack}, and subtitle tracks {','.join(subtitleTracks)} for {FILE_PATH}")

    orderedTracks = [videoTrack, audioTrack]
    orderedTracks.extend(subtitleTracks)

    os.rename(FILE_PATH, f"{FILE_PATH}.old")

    # Refresh here as a workaround for https://github.com/Sonarr/Sonarr/issues/3366
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
    mkvmerge.extend(["--track-order", f"0:{',0:'.join(orderedTracks)}"])

    subprocess.run(mkvmerge, check=True)
    os.rename(f"{FILE_PATH}.new", FILE_PATH)
    os.remove(f"{FILE_PATH}.old")

refreshData = refresh_arr()

if "id" in refreshData:
    COMMAND_ID = refreshData["id"]
    refreshComplete = False

    while not refreshComplete:
        time.sleep(5)
        params = {"apikey": untangle.parse('/config/config.xml').Config.ApiKey.cdata}
        req = requests.get(f"http://localhost:{'7878' if SERVER_TYPE == 'radarr' else '8989'}/api/v3/command", params=params)

        try:
            req.raise_for_status()
            response = req.json()
        except Exception as e:
            log.error(e)
            break

        for command in response:
            if command["id"] == COMMAND_ID:
                if command["status"] == "completed":
                    refreshComplete = True
                break

if os.environ.get("DISCORD_WEBHOOK"):
    os.environ["CONFIG_DIR"] = "/config"
    subprocess.run(["/usr/local/bin/arr-discord-notifier"], check=True)
