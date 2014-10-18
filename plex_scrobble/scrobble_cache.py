import logging
import shelve
import time

from lastfm import LastFm


class ScrobbleCache(object):
    ''' provides a light wrapper around Python Shelve. Used to persist
        a Python dict to disk. '''

    def __init__(self, config):

        self.config = config
        self.cache = shelve.open(self.config.get('plex-scrobble', 'cache_location'),
                writeback=True)
        self.logger = logging.getLogger(__name__)

    def length(self):
        return len(self.cache)

    def add(self, key, value, album, cache_hit=1):

        self.logger.info(u'adding \'{key}\' \'{value}\' ({album}) to retry cache.'.format(
            key=key, value=value, album=album))

        self.cache[str(time.time())] = [key, value, cache_hit, album]
        self.cache.sync()

    def remove(self, key):
        ''' remove an existing entry from cache file. '''

        self.logger.info(u'removing \'{key}\': \'{artist}\' - \'{track}\' ({album})from retry cache.'.format(
            key=key, artist=self.cache[key][0], track=self.cache[key][1],
            album=self.cache[key][3]))
        del self.cache[key]
        self.cache.sync()

    def close(self):
        ''' cleans up cache and flushes to disk. '''

        self.cache.close()

    def cache_items(self):
        ''' debug method to dump cache to stdout. '''

        for key in self.cache:
            print u'time={key}, artist={artist}, track={track}, album={album}age={age}'.format(
                
                    key=key, artist=self.cache[key][0], 
                    track=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2])

    def retry_queue(self):

        self.logger.info('Retrying scrobble cache.')
        a = True
        lastfm = LastFm(self.config)

        for key in self.cache:
            # do submissions retry
            try:
                a = lastfm.scrobble(self.cache[key][0], self.cache[key][1],
                        self.cache[key][3])
                self.cache[key][2] += 1
            except:
                pass

            # if it was a failed submission
            if not a:
                # remove this record from retry cache, if we're at the retry limit
                if self.cache[key][2] >= MAX_CACHE_AGE:
                    self.logger.info(u'MAX_CACHE_AGE for {key} : {artist} - {track}'.format(
                        key, self.cache[key][0], self.key[1]))
                    self.remove(key)
            else:
                # successful send to last.fm, remove from cache
                self.remove(key)
