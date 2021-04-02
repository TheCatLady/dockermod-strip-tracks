#!/usr/bin/with-contenv bash

# Fetch & chown/chmod hotio's awesome "Arr Discord Notifier" script
# https://hotio.dev/arr-discord-notifier/
curl -fsSL -o /usr/local/bin/arr-discord-notifier https://raw.githubusercontent.com/hotio/arr-discord-notifier/master/arr-discord-notifier.sh
chown abc:abc /usr/local/bin/arr-discord-notifier
chmod +x /usr/local/bin/arr-discord-notifier

# Install MKVToolNix
# https://mkvtoolnix.download/
export DEBIAN_FRONTEND=noninteractive
. /etc/lsb-release
apt-key adv --fetch-keys https://mkvtoolnix.download/gpg-pub-moritzbunkus.txt
echo "deb https://mkvtoolnix.download/ubuntu/ ${DISTRIB_CODENAME} main" | tee -i "/etc/apt/sources.list.d/mkvtoolnix.download.list" > /dev/null
apt-get update -qq < /dev/null > /dev/null
apt-get install -qq --no-install-recommends mkvtoolnix python3-minimal python3-pip < /dev/null > /dev/null
apt-get autoremove -qq < /dev/null > /dev/null
apt-get clean autoclean -qq < /dev/null > /dev/null
rm -rf /var/lib/{apt,dpkg,cache,log}/

# Install Python dependencies and chown/chmod script
pip3 install iso_639_codes requests untangle
chown abc:abc /usr/local/bin/strip-tracks.py
chmod +x /usr/local/bin/strip-tracks.py