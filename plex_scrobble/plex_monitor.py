import re
import os
import socket
import urllib2
import xml.etree.ElementTree as ET
import logging
import time

from lastfm import LastFm
from scrobble_cache import ScrobbleCache


def parse_line(log_line):
    """
    Matches known audio metadata log entries entries against input (log_line)

    :param log_line: a str containing a plex media server log line
    :return: plex media server  metadata id
    :rtype: integer (or None)
    """

    logger = logging.getLogger(__name__)

    REGEX = [
        # universal-transcoder
        re.compile('.*GET\s\/music\/:\/transcode\/universal\/start\.mp3.*metadata%2F(\d+)\&.*'),
        # stream based transcoder
        re.compile('.*\sDEBUG\s-\sLibrary\sitem\s(\d+)\s\'.*\'\sgot\splayed\sby\saccount.*')
    ]

    for regex in REGEX:
        m = regex.match(log_line)

        if m:
            logger.info('Found played song and extracted library id \'{l_id}\' from plex log '.format(l_id=m.group(1)))
            return m.group(1)


def fetch_metadata(l_id, config):
    """ retrieves the metadata information from the Plex media Server api. """

    logger = logging.getLogger(__name__)
    url = '{url}/library/metadata/{l_id}'.format(url=config.get('plex-scrobble',
      'mediaserver_url'), l_id=l_id)
    logger.info('Fetching library metadata from {url}'.format(url=url))

    req = urllib2.Request(url)

    if config.get('plex-scrobble', 'plex_token'):
        req.add_header('X-Plex-Token', config.get('plex-scrobble', 'plex_token'))

    # fail if request is greater than 2 seconds.
    try:
        metadata = urllib2.urlopen(req, timeout=2)
    except urllib2.URLError, e:
        logger.error('urllib2 error reading from {url} \'{error}\''.format(url=url,
                      error=e))
        return False
    except socket.timeout, e:
        logger.error('Timeout reading from {url} \'{error}\''.format(url=url, error=e))
        return False

    tree = ET.fromstring(metadata.read())
    track = tree.find('Track')

    # BUGFIX: https://github.com/jesseward/plex-lastfm-scrobbler/issues/7
    if track is None:
        logger.info('Ignoring played item library-id={l_id}, could not determine audio library information.'.
                format(l_id=l_id))
        return False

    # if present use originalTitle. This appears to be set if
    # the album is various artist
    artist = track.get('originalTitle')
    if not artist:
        artist = track.get('grandparentTitle')

    song = track.get('title')

    # BUGFIX : https://github.com/jesseward/plex-lastfm-scrobbler/issues/19
    # add support for fetching album metadata from the track object.
    album = track.get('parentTitle')
    if not album:
        logger.warn('unable to locate album name for ibary-id={l_id}'.format(
            l_id=l_id))
        album = None

    if not all((artist, song)):
        logger.warn('unable to retrieve meatadata keys for libary-id={l_id}'.
                format(l_id=l_id))
        return False

    return {'track': song, 'artist': artist, 'album': album}


def monitor_log(config):

    logger = logging.getLogger(__name__)
    st_mtime = False
    last_played = None

    try:
        f = open(config.get('plex-scrobble', 'mediaserver_log_location'))
    except IOError:
        logger.error('Unable to read log-file {0}. Shutting down.'.format(config.get(
          'plex-scrobble', 'mediaserver_log_location')))
        return
    f.seek(0, 2)

    while True:

        time.sleep(.03)

        # reset our file handle in the event the log file was not written to
        # within the last 60 seconds. This is a very crude attempt to support
        # the log file i/o rotation detection cross-platform.
        if int(time.time()) - int(os.fstat(f.fileno()).st_mtime) >= 60:

            if int(os.fstat(f.fileno()).st_mtime) == st_mtime: continue

            logger.debug('Possible log file rotation, resetting file handle (st_mtime={mtime})'.format(
                mtime=time.ctime(os.fstat(f.fileno()).st_mtime) ))
            f.close()

            try:
                f = open(config.get('plex-scrobble', 'mediaserver_log_location'))
            except IOError:
                logger.error('Unable to read log-file {0}. Shutting down.'.format(config.get(
                  'plex-scrobble', 'mediaserver_log_location')))
                return

            f.seek(0, 2)
            st_mtime = int(os.fstat(f.fileno()).st_mtime)

        line = f.readline()

        # read all new lines starting at the end. We attempt to match
        # based on a regex value. If we have a match, extract the media file
        # id and send it off to last.fm for scrobble.
        if line:
            played = parse_line(line)

            if not played: continue

            # when playing via a client, log lines are duplicated (seen via iOS)
            # this skips dupes. Note: will also miss songs that have been repeated
            if played == last_played:
                logger.warn('Dupe detection : {0}, not submitting'.format(last_played))
                continue

            metadata = fetch_metadata(played, config)

            if not metadata: continue

            # submit to last.fm
            lastfm = LastFm(config)
            a = lastfm.scrobble(metadata['artist'], metadata['track'],
                    metadata['album'])

            # scrobble was not successful , add to our retry queue
            if not a:
                cache = ScrobbleCache(config)
                cache.add(metadata['artist'], metadata['track'], metadata['album'])
                cache.close

            last_played = played
