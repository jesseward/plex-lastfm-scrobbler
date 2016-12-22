# -*- coding: utf-8 -*-
import logging
import shelve
import time
import pylast


class ScrobbleCache(object):
    """
    provides a light wrapper around Python Shelve. Used to persist
    a Python dict to disk.
    """

    MAX_CACHE_AGE = 10

    def __init__(self, api_key, api_secret, user_name, password,
                 cache_location='/tmp/plex_scrobble.cache'):
        """

        :param api_key: LastFM api key
        :param api_secret: LastFM api secret
        :param username: LastFM username
        :param password: LasftFM password
        :param cache_location: Location of the scrobble cache file.
        """

        self.api_key = api_key
        self.api_secret = api_secret
        self.user_name = user_name
        self.password = password
        self.cache = shelve.open(cache_location, writeback=True)
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

        self.logger.info(u'adding "{key}" "{value}" ({album}) to retry cache.'.format(
            key=key, value=value, album=album))

        self.cache[str(time.time())] = [key, value, cache_hit, album]
        self.cache.sync()

    def remove(self, key):
        """
        remove an existing entry from cache file.

        :param key: a timestamp.
        """

        self.logger.info(u'removing "{key}": "{artist}" - "{title}" ({album}) from retry cache.'.format(
            key=key, artist=self.cache[key][0], title=self.cache[key][1],
            album=self.cache[key][3]))
        del self.cache[key]
        self.cache.sync()

    def close(self):
        """ cleans up cache and flushes to disk. """

        self.cache.close()

    def cache_items(self):
        """ debug method to dump cache to stdout. """

        for key in self.cache:
            print('time={key}, artist={artist}, title={title}, album={album}age={age}'.format(
                    key=key, artist=self.cache[key][0],
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2]))

    def retry_queue(self):

        self.logger.info('Retrying scrobble cache.')

        for key in self.cache:
            # do submissions retry
            try:
                self.cache[key][2] += 1
                lastfm = pylast.LastFMNetwork(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    username=self.user_name,
                    password_hash=pylast.md5(self.password))
                lastfm.scrobble(self.cache[key][0],
                                self.cache[key][1],
                                timestamp=int(time.time()),
                                album=self.cache[key][3])
            except:
                self.logger.warn('Failed to resubmit artist={artist}, title={title}, album={album}age={age}'.format(
                    artist=self.cache[key][0],
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2]))
                if self.cache[key][2] >= ScrobbleCache.MAX_CACHE_AGE:
                    self.logger.info(u'MAX_CACHE_AGE for {key} : {artist} - {title}'.format(
                        key, self.cache[key][0], self.key[1]))
                    self.remove(key)
                continue

            # successful send to last.fm, remove from cache
            self.logger.info('cache resubmit of artist={artist}, title={title}, album={album} age={age}. Removing.'.format(
                    artist=self.cache[key][0],
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2]))
            self.remove(key)
