import logging
import os.path
import unittest
from os import remove

from config import config
from plex_scrobble.scrobble_cache import ScrobbleCache

logging.disable(logging.CRITICAL)


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
        self._clean_file()

    def tearDown(self):
        """ clean up/remove our temporary cache after test run completes. """
        self._clean_file()

    def test_add_record_to_cache(self):
        """ tests the addition of a test item to the cache. """
        self.sc.add('artist', 'title', 'album')

        self.assertTrue(self.sc.length() == 1)

    def test_delete_record_from_cache(self):
        """ tests the removal of our test item. """
        for key in self.sc.cache:
            self.sc.remove(key)
        self.assertTrue(self.sc.length() == 0)


if __name__ == '__main__':
    unittest.main()
