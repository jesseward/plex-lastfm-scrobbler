import logging
import shelve
import time

import pylast

MAX_CACHE_AGE = 10


class ScrobbleCache(object):
    """
    provides a light wrapper around Python Shelve. Used to persist
    a Python dict to disk.
    """

    def __init__(self, config):
        """

        :param config: Configuration object
        """

        self.config = config
        self.cache = shelve.open(self.config['plex-scrobble']['cache_location'],
                writeback=True)
        self.logger = logging.getLogger(__name__)

    def length(self):
        return len(self.cache)

    def add(self, key, value, album, cache_hit=1):
        """
        Add missed scrobble to the retry cache.

        :param key: a time - timestamp
        :param value: a str representing an artist name
        :param album: a str representing an album name
        :param cache_hit: number of times the item has been retried.
        """

        self.logger.info(u'adding \'{key}\' \'{value}\' ({album}) to retry cache.'.format(
            key=key, value=value, album=album))

        self.cache[str(time.time())] = [key, value, cache_hit, album]
        self.cache.sync()

    def remove(self, key):
        """
        remove an existing entry from cache file.

        :param key: a timestamp.
        """

        self.logger.info(u'removing \'{key}\': \'{artist}\' - \'{title}\' ({album})from retry cache.'.format(
            key=key, artist=self.cache[key][0], title=self.cache[key][1],
            album=self.cache[key][3]))
        del self.cache[key]
        self.cache.sync()

    def close(self):
        ''' cleans up cache and flushes to disk. '''

        self.cache.close()

    def cache_items(self):
        """ debug method to dump cache to stdout. """

        for key in self.cache:
            print u'time={key}, artist={artist}, title={title}, album={album}age={age}'.format(
                
                    key=key, artist=self.cache[key][0], 
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2])

    def retry_queue(self):

        self.logger.info('Retrying scrobble cache.')
        a = True

        for key in self.cache:
            # do submissions retry
            try:
                self.cache[key][2] += 1
                lastfm = pylast.LastFMNetwork(
                    api_key=config['lastfm']['api_key'],
                    api_secret=config['lastfm']['api_secret'],
                    username=config['lastfm']['user_name'],
                    password_hash=pylast.md5(config['lastfm']['password']))
                a = lastfm.scrobble(self.cache[key][0],
                                    self.cache[key][1],
                                    timestamp=int(time.time()),
                                    album=self.cache[key][3])
            except:
                pass

            # if it was a failed submission
            if not a:
                # remove this record from retry cache, if we're at the retry limit
                if self.cache[key][2] >= MAX_CACHE_AGE:
                    self.logger.info(u'MAX_CACHE_AGE for {key} : {artist} - {title}'.format(
                        key, self.cache[key][0], self.key[1]))
                    self.remove(key)
            else:
                # successful send to last.fm, remove from cache
                self.remove(key)
