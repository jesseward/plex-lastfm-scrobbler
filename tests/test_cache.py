# -*- coding: utf-8 -*-
import logging
import os.path
import six
import sys
import unittest
from os import remove

from config import config
from plex_scrobble.scrobble_cache import ScrobbleCache

# forcing to ASCII in Python 2 to ensure clients running in something 
# other than a UTF8 enabled shell are working.
if sys.version[0] == '2':
    reload(sys)
    sys.setdefaultencoding("ascii")


class TestScrobbleCache(unittest.TestCase):

    def _clean_file(self):
        """ remove the cache file if already exists. """
        if os.path.isfile(config['plex-scrobble']['cache_location']):
            remove(config['plex-scrobble']['cache_location'])

    def setUp(self):
        """ create an empty scrobble_cache object. """
        user_name = password = api_key = api_secret = config['lastfm']['user_name']
        self.sc = ScrobbleCache(api_key, api_secret, user_name, password,
                                cache_location=config['plex-scrobble']['cache_location'])
        self.album = six.u('Björk').encode('utf-8')
        self.artist = six.u('CR∑∑KS').encode('utf-8')
        self.title = six.u('deep burnt').encode('utf-8')
        self._clean_file()

    def tearDown(self):
        """ clean up/remove our temporary cache after test run completes. """
        self._clean_file()

    def test_add_record_to_cache(self):
        """ tests the addition of a test item to the cache. """
        self.sc.add(self.artist, self.title, self.album)

        self.assertTrue(self.sc.length() == 1)

    def test_delete_record_from_cache(self):
        """ tests the removal of our test item. """
        for key in self.sc.cache:
            self.sc.remove(key)
        self.assertTrue(self.sc.length() == 0)


if __name__ == '__main__':
    unittest.main()
