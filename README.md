plex-lastfm-scrobbler
=====================
[![Build Status](https://api.travis-ci.org/jesseward/plex-lastfm-scrobbler.svg?branch=master)](https://api.travis-ci.org/jesseward/plex-lastfm-scrobbler)

plex-lastfm-scrobbler provides a set of scripts that allow you to scrobble played audio items to Last.FM from the Plex Media Server application. plex-lastfm-scrobbler was built to run across platforms, though only tested on Linux.

A few points

  - plex-lastfm-scrobbler is an out of process tool. Meaning it is not a Plex Media Server plug-in. This tool runs separately of your Plex Media Server.
  - Must be run on the Plex Media Server
  - Parses Plex Media Server logs for the 'got played' string in the log file.
  - Does not differentiate between clients. Meaning all media played, will be scrobbled while the script is running.
  - Your plex-media-server logs must be set at DEBUG level (not VERBOSE)

Installation
----

**Linux, OSX**

It is recommended (but not required) that you install this into a virtualenvironment.

```
virtualenv ~/.virtualenvs/plex-lastfm-scrobber
source ~/.virtualenvs/plex-lastfm-scrobber/bin/activate
```

Fetch and install the source from the github repo.
```
git clone https://github.com/jesseward/plex-lastfm-scrobbler.git
cd plex-lastfm-scrobbler
python setup.py install

```

Alternatively, you can fetch the latest zip from github

```
wget https://github.com/jesseward/plex-lastfm-scrobbler/archive/master.zip
unzip master.zip
cd plex-lastfm-scrobbler-master
python setup.py install
```

You're done.

Configuration
-----------

Run the wizard to generate config file
```
plex-scrobble --wizard
```

The plex-lastfm-scrobbler configuration file (.plex-scrobble.toml) is installed to ~/ . The following configuration values are available.

If you're running Plex Media Server on a Linux based operating system, things should work out of the box.

```
[lastfm]
# REQUIRED: You'll need to create a last.fm API application first. Do so here:
# http://www.last.fm/api/account/create
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
user_name = "LAST_FM_USERNAME"
password = "LAST_FM_PASSWORD"

[plex-scrobble]
# mediaserver_log_location references the log file location of the plex media server
# the default under /var/lib/... is the default install of plex media server on
# a Linux system. You may wish to change this value to reference your OS install.
# https://support.plex.tv/hc/en-us/articles/200250417-Plex-Media-Server-Log-Files
mediaserver_log_location = "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log"

# REQUIRED: Where do you wish to write the plex-scrobble log file.
log_file = "/tmp/plex-scrobble.log"

# REQUIRED: mediaserver_url is the location of the http service exposed by Plex Media Server
# the default values should be 'ok', assuming you're running the plex scrobble
# script from the same server as your plex media server
mediaserver_url = "http://localhost:32400"

# REQUIRED: a python data struture that stores failed scrobbles. plex-scrobble
# will retry on a 60 minute interval, maximum of 10 attempts if last.fm is
# experiencing issues.
cache_location = "/tmp/plex_scrobble.cache"

# OPTIONAL: plex_token defines the plex token used to get metadata
# Note: This is required if you use localhost or 127.0.0.1 and Plex Media Server >= 1.1.0
# You will know if you see a line like this your log_file:
# [plex_scrobble.plex_monitor fetch_metadata] [ERROR] urllib2 error reading from http://localhost:32400/library/metadata/48080 'HTTP Error 401: Unauthorized'
# Here is how you can obtain your token https://support.plex.tv/hc/en-us/articles/204059436-Finding-your-account-token-X-Plex-Token
plex_token = "YOUR_PLEX_TOKEN"
```

Running
--------

If you installed plex-lastfm-scrobble to a virtual environment, enable the virtual env.

```
source ~/.virtualenvs/plex-lastfm-scrobber/bin/activate
```

run the application
```
nohup plex-scrobble &
```

Troubleshooting & Known Issues
-------------

* If your Plex client supports the universal transcoder (see "Old and Universal transcoder @ https://support.plex.tv/hc/en-us/articles/200250377-Transcoding-Media), tracks will be scrobbled at the start of play. This is due to the way that the universal transcoder writes to the Plex log file. See issue 11 (https://github.com/jesseward/plex-lastfm-scrobbler/issues/11) for background discussion.
* We've seen instances when Plex Media Server does not report the length of an audio file. This may occur before a full library analyze has completed. When the track length is not reported by the Plex Media Server, the song will not be scrobble. Try forcing the "Analyze" audio library function. Further discussion found in issue #9 https://github.com/jesseward/plex-lastfm-scrobbler/issues/9

Or browse the github issues list to review old bugs or log a new problem.  See https://github.com/jesseward/plex-lastfm-scrobbler/issues?q=
