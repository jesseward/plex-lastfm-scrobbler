# -*- coding: utf-8 -*-
import logging
import os
import pickle
import time
import threading

from uuid import uuid1

import pylast

lock = threading.Lock()


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
        self.logger = logging.getLogger(__name__)
        self.cache_location = cache_location
        self.cache = {}

        try:
            self._load()
        except IOError as e:
            self.logger.warning('Unable to open cache file. resetting cache. error={0}'.format(e))
            self.sync()
        except (EOFError, KeyError) as e:
            self.logger.error('Unable to read cache file type. possibly corrupted or not of Python Pickle type, renaming to .old. error={0}'.format(e))
            os.rename(self.cache_location, self.cache_location + '.old')
            self.sync()


    def length(self):
        return len(self.cache)

    def _load(self):
        lock.acquire()
        try:
            with open(self.cache_location, 'rb') as fh:
                self.cache = pickle.load(fh)
        except Exception as e:
            lock.release()
            raise e
        lock.release()

    def sync(self):
        lock.acquire()
        with open(self.cache_location, 'wb') as fh:
            pickle.dump(self.cache, fh)
        lock.release()
        self._load()
        return True

    def add(self, artist, title, album, cache_hit=1):
        """
        Add missed scrobble to the retry cache.

        :param artist: a str representing the artist name
        :param title: a str representing the song title
        :param album: a str representing an album name
        :param cache_hit: number of times the item has been retried.
        """

        self.logger.info('adding "{artist}" "{title}" ({album}) to retry cache.'.format(
            artist=artist, title=title, album=album))

        self.cache[str(uuid1())] = [artist, title, cache_hit, album]
        return self.sync()

    def remove(self, key):
        """
        remove an existing entry from cache file.

        :param key: a string representing a uuid1 value.
        """

        self.logger.info('removing "{key}" from retry cache.'.format(key=key))

        try:
            del self.cache[key]
        except KeyError:
            self.logger.warning('Unable to remove, {0} not found in cache.'.format(key))
            return

        return self.sync()

    def cache_items(self):
        """ debug method to dump cache to stdout. """

        for key in self.cache:
            print('time={key}, artist={artist}, title={title}, album={album}, age={age}'.format(
                    key=key, artist=self.cache[key][0],
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2]))

    def retry_queue(self):

        self.logger.info('Retrying scrobble cache.')

        for key in self.cache.keys():
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
                self.logger.warning('Failed to resubmit artist={artist}, title={title}, album={album}, age={age}'.format(
                    artist=self.cache[key][0],
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2]))
                if self.cache[key][2] >= ScrobbleCache.MAX_CACHE_AGE:
                    self.logger.info('MAX_CACHE_AGE for {key} : {artist} - {title}'.format(key=key, artist=self.cache[key][0], title=self.cache[key][1]))
                    self.remove(key)
                continue

            # successful send to last.fm, remove from cache
            self.logger.info('cache resubmit of artist={artist}, title={title}, album={album} age={age}. Removing.'.format(
                    artist=self.cache[key][0],
                    title=self.cache[key][1],
                    album=self.cache[key][3],
                    age=self.cache[key][2]))
            self.remove(key)
        self.sync()
