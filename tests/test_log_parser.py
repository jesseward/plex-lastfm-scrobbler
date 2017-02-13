import io
import logging
import unittest

from plex_scrobble.plex_monitor import parse_line

logging.disable(logging.CRITICAL)


class TestUnicodeLogParser(unittest.TestCase):

    def setUp(self):
        with io.open('data/unicode_pms.log', 'r', encoding='utf-8') as fh:
            self.found = [parse_line(line) for line in fh if parse_line(line)]

    def test_unicode_logparser_5_ids(self):

        self.assertTrue(len(self.found) == 5)


class TestUniversalLogParser(unittest.TestCase):

    def setUp(self):
        with io.open('data/universal_transcode.log', 'r') as fh:
            self.found = [parse_line(line) for line in fh if parse_line(line)]

    def test_universal_logparser_2_ids(self):

        self.assertTrue(len(self.found) == 2)


if __name__ == '__main__':
    unittest.main()
