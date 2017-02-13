# -*- coding: utf-8 -*-
import io
import unittest

from mock import patch

from config import config
from plex_scrobble.plex_monitor import fetch_metadata


class TestFetchMetaData(unittest.TestCase):

    def test_fetch_metadata_unicode(self):
        """ Validates parsing of response data from the PMS metadata API. """

        with patch('plex_scrobble.plex_monitor.requests.get') as mock_get:
            with io.open('data/unicode_audio_payload_fetch_metadata.xml', 'r', encoding='utf-8') as fh:
                mock_get.return_value.text = fh.read()
            metadata = fetch_metadata(64738, config)

        self.assertEqual(metadata['artist'], b'\xe3\x81\x98\xe3\x82\x93 Feat. \xe3\x83\xa1\xe3\x82\xa4\xe3\x83\xaa\xe3\x82\xa2')
        self.assertEqual(metadata['album'], b'daze / days')
        self.assertEqual(metadata['title'], b'daze')


if __name__ == '__main__':
        unittest.main()
