# `dockermod-strip-tracks` &#9986;&#65039;

[![Image Size](https://img.shields.io/docker/image-size/thecatlady/dockermod-strip-tracks/latest?style=flat-square&logoColor=white&logo=docker&label=image%20size)](https://hub.docker.com/r/thecatlady/dockermod-strip-tracks)
[![Last Commit](https://img.shields.io/github/last-commit/TheCatLady/dockermod-strip-tracks?style=flat-square&logoColor=white&logo=github)](https://github.com/TheCatLady/dockermod-strip-tracks)
[![Build Status](https://img.shields.io/github/workflow/status/TheCatLady/dockermod-strip-tracks/Build%20Docker%20Images?style=flat-square&logoColor=white&logo=github%20actions)](https://github.com/TheCatLady/dockermod-strip-tracks)<br/>
[![Python](https://img.shields.io/github/languages/top/TheCatLady/dockermod-strip-tracks?style=flat-square&logoColor=white&logo=python)](https://github.com/TheCatLady/dockermod-strip-tracks)
[![Code Quality](https://img.shields.io/lgtm/grade/python/github/TheCatLady/dockermod-strip-tracks?style=flat-square&logoColor=white&logo=lgtm&label=code%20quality)](https://lgtm.com/projects/g/TheCatLady/dockermod-strip-tracks/)
[![License](https://img.shields.io/github/license/TheCatLady/dockermod-strip-tracks?style=flat-square&logoColor=white&logo=open%20source%20initiative)](https://github.com/TheCatLady/dockermod-strip-tracks/blob/main/LICENSE)<br/>
[![Become a GitHub Sponsor](https://img.shields.io/badge/github%20sponsors-become%20a%20sponsor-ff69b4?style=flat-square&logo=github%20sponsors)](https://github.com/sponsors/TheCatLady)
[![Donate via PayPal](https://img.shields.io/badge/paypal-make%20a%20donation-blue?style=flat-square&logo=paypal)](http://paypal.me/DHoung)

[Docker Mod](https://github.com/linuxserver/docker-mods) to strip unwanted tracks from media files upon import to Radarr or Sonarr (compatible with [`linuxserver/radarr`](https://github.com/linuxserver/docker-radarr) and [`linuxserver/sonarr`](https://github.com/linuxserver/docker-sonarr))

Also fetches [@hotio](https://github.com/hotio)'s _awesome_ [Arr Discord Notifier script](https://github.com/hotio/arr-discord-notifier) for beautiful Discord notifications!

## Behavior

This [Docker Mod](https://github.com/linuxserver/docker-mods) was created for my own personal use, but it is still somewhat configurable to suit your own personal preferences.

### Initialization

On each container start, the `strip-tracks-init.sh` script will:

1. Fetch, `chmod`, and `chown` [@hotio](https://github.com/hotio)'s [Arr Discord Notifier script](https://github.com/hotio/arr-discord-notifier) (have I mentioned that it is awesome?)
2. Install the latest version of [MKVToolNix](https://mkvtoolnix.download/)
3. Install required Python dependencies for, `chmod`, and `chown` the `strip-tracks.py` script

### Media Processing

When added for the **On Import** and/or **On Upgrade** triggers in Radarr and/or Sonarr, the `strip-tracks.py` script will:

1. Query [The Movie Database (TMDb)](https://www.themoviedb.org/) to determine the original language of the movie or TV show
2. Use [`mkvmerge`](https://mkvtoolnix.download/doc/mkvmerge.html) to remove unwanted tracks from the video file, keeping only:
     - the first video track
     - the first audio track matching the original language
     - subtitle tracks matching a provided ISO 639-2 language code which do not contain any excluded keywords
3. Call the Radarr/Sonarr `command` API to refresh the movie or TV show
4. Run [@hotio](https://github.com/hotio)'s super awesome [Arr Discord Notifier script](https://github.com/hotio/arr-discord-notifier)

## Usage

This [Docker Mod](https://github.com/linuxserver/docker-mods) is configured by defining the following environment variables for your [`linuxserver/radarr`](https://github.com/linuxserver/docker-radarr) and/or [`linuxserver/sonarr`](https://github.com/linuxserver/docker-sonarr) containers:

|Parameter|Function|Required?|
|---|---|---|
|`DOCKER_MODS`|`thecatlady/dockermod-strip-tracks` (or `ghcr.io/thecatlady/dockermod-strip-tracks`)|yes|
|`TMDB_API_KEY`|Your TMDb API key|yes|
|`SUBTITLE_LANGUAGES`|Comma-delimited list of [ISO 639-2 language codes](https://www.loc.gov/standards/iso639-2/php/code_list.php) for which subtitle tracks should be kept (if not specified, no subtitles will be kept)|no|
|`EXCLUDED_KEYWORDS`|Comma-delimited list of keywords for which subtitle tracks should be excluded|no|

Please refer to [@hotio](https://github.com/hotio)'s [Arr Discord Notifier documentation](https://hotio.dev/arr-discord-notifier/) for details on how to configure and customize the Discord notifications.

## Building Locally

If you would like to make modifications to the code, you can build the Docker image yourself instead of pulling the pre-built image available from [GitHub Container Registry (GHCR)](https://github.com/users/TheCatLady/packages/container/package/dockermod-strip-tracks) and [Docker Hub](https://hub.docker.com/r/thecatlady/dockermod-strip-tracks).

```bash
git clone https://github.com/TheCatLady/dockermod-strip-tracks.git
cd dockermod-strip-tracks
docker build --no-cache --pull -t thecatlady/dockermod-strip-tracks .
```

Once the image has been built, simply follow the directions in the "Usage" section above.

## How to Contribute

Show your support by starring this project! &#x1F31F; Pull requests, bug reports, and feature requests are also welcome!

You can also support me by [becoming a GitHub sponsor](https://github.com/sponsors/TheCatLady) or [making a one-time PayPal donation](http://paypal.me/DHoung) &#x1F496;

Additionally, don't forget to show your support for both [@hotio](https://github.com/hotio) and the wonderful folks over at [LinuxServer.io](https://github.com/linuxserver)!
