#!/usr/bin/env python
import re
import socket
import urllib2
import time
import xml.etree.ElementTree as ET
import logging
import shelve
import time

from lastfm import LastFm


PHT_URL = 'http://localhost:32400'
LOG_FILE = '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log'
MAX_CACHE_AGE = 5

class ScrobbleCache(object):

    def __init__(self, conf='/tmp/cache'):

        self.conf = conf
        self.cache = shelve.open(self.conf, writeback=True)
        self.logger = logging.getLogger(__name__)

    def add(self, key, value, cache_hit=1):

        self.logger.info('adding \'{key}\' \'{value}\' to retry cache.'.format(
            key=key, value=value))

        self.cache[str(time.time())] = [key, value, cache_hit]
        self.cache.sync()

    def remove(self, key):

        self.logger.info('removing \'{key}\': \'{artist}\' - \'{track}\' from retry cache.'.format(
            key=key, artist=self.cache[key][0], track=self.cache[key][1]))
        del self.cache[key]
        self.cache.sync()

    def close(self):
        self.cache.close()

    def items(self):
        for key in self.cache: 
            print '{key} : {artist} - {track}'.format(key=key,
                artist=self.cache[key][0], track=self.cache[key][1])

    def retry_queue(self):

        lastfm = LastFM('TODO: cfg object')

        for key in self.cache:
            # do submissions retry
            try:
                lastfm.scrobble(self.cache[key][0], self.cache[key][1])
                self.cache[key][2] += 1  
            except:
                # remove this record from retry cache, if we're at the retry limit
                if self.cache[key][2] >= MAX_CACHE_AGE: 
                    logger.info('MAX_CACHE_AGE for {key} : {artist} - {track}'.format(
                        key, self.cache[key][0], self.key[1]))
                    self.remove(key)
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
