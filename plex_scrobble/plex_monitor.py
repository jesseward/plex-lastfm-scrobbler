#!/usr/bin/env python
import re
import socket
import urllib2
import time
import xml.etree.ElementTree as ET
import logging
import shelve

from lastfm import LastFm


PHT_URL = 'http://localhost:32400'
LOG_FILE = '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log'


class ScrobbleCache(object):

    def __init__(self, conf='/tmp/cache'):

        self.conf = conf
        self.cache = shelve.open(self.conf, writeback=True)
        self.logger = logging.getLogger(__name__)

    def add(self, key, value):

        self.logger.info('adding \'{key}\' \'{value}\' to retry cache.'.format(
            key=key, value=value))

        self.cache[key] = value

    def remove(self, key):

        self.logger.info('removing \'{key}\' \'{value}\' to retry cache.'.format(
            key=key, value=value))
        del self.cache[key]

    def close(self):
        self.cache.close()

    def items(self):
        for key in self.cache: print self.cache[key]

    def retry_queue(self):

        lastfm = LastFM('blah')
        for key in self.cache:
            # do submissions retry
            try:
                lastfm.scrobble(artist, album)
            except:
                continue


def parse_line(l):
    ''' Matches based on a "got played" PHT audio media object.  '''

    logger = logging.getLogger(__name__)
    logger.debug('Parsing log line : {log}'.format(log=l))

    played = re.compile(r".*\sDEBUG\s-\sLibrary\sitem\s(\d+)\s'.*'\sgot\splayed\sby\saccount.*")
    m = played.match(l)

    if m:
        logger.info('extracted media id \'{id}\''.format(id=m.group(1)))
        return m.group(1)


def fetch_metadata(id):
    ''' retrieves the metadata information from the PHT api. '''

    logger = logging.getLogger(__name__)
    url = '{url}/library/metadata/{id}'.format(url=PHT_URL, id=id)
    logger.info('fetching metadata from {url}'.format(url=url))

    # fail if request is greater than 2 seconds.
    try:
        metadata = urllib2.urlopen(url, timeout=2)
    except urllib2.URLError, e:
        logger.error('urllib2 error reading from {url} \'{error}\''.format(url=url,
                      error=e))
        return False
    except socket.timeout, e:
        logger.error('Timeout reading from {url} \'{error}\''.format(url, error=e))
        return False

    tree = ET.fromstring(metadata.read())
    track = tree.find('Track')
    artist = track.get('grandparentTitle')
    song = track.get('title')

    if not all((artist, song)):
        logger.warn('unable to retrieve meatadata keys track={track}, artist={artist}'.
                format(track=track, artist=artist))
        return False

    return {'track': song, 'artist': artist}


def monitor_log():

    logger = logging.getLogger(__name__)

    f = open(LOG_FILE)
    f.seek(0, 2)
    while True:
        time.sleep(.05)
        line = f.readline()

        # read all new lines starting at the end. We attempt to match
        # based on a regex value. If we have a match, extract the media file
        # id and send it off to last.fm for scrobble.
        if line:
            played = parse_line(line)
            print line

            if not played: continue

            metadata = fetch_metadata(played)

            if not metadata: continue

            # submit to last.fm
            lastfm = LastFm('test')
            a = lastfm.scrobble(metadata['artist'], metadata['track'])

            if not a:
                cache = ScrobbleCache()
                cache.add({time: [metadata['artist'], metadata['track']]})
                cache.close

if __name__ == '__main__': 
    logger = logging.getLogger(__name__)
    m = monitor_log()
