import os.path
import unittest
from os import remove

from config import config
from plex_scrobble.scrobble_cache import ScrobbleCache

import logging
logging.disable(logging.CRITICAL)


class TestScrobbleCache(unittest.TestCase):

    def setUp(self):
        """ create an empty scrobble_cache object. """
        self.sc = ScrobbleCache(config)

    def tearDown(self):
        """ clean up/remove our temporary cache after test run completes. """

        if os.path.isfile(config['plex-scrobble']['cache_location']):
            remove(config['plex-scrobble']['cache_location'])

    def test_add_record_to_cache(self):
        self.sc.add('artist', 'title', 'album')

        self.assertTrue(self.sc.length() == 1)

    def test_delete_record_from_cache(self):
        for key in self.sc.cache:
            self.sc.remove(key)
        self.assertTrue(self.sc.length() == 0)

if __name__ == '__main__':
    unittest.main()
