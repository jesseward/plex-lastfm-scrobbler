import unittest

from plex_scrobble.plex_monitor import parse_line

import logging
logging.disable(logging.CRITICAL)

class TestUnicodeLogParser(unittest.TestCase):

    def setUp(self):
        with  open('data/unicode_pms.log', 'r') as fh:
            self.found = [ parse_line(line) for line in fh if parse_line(line) ]
    
    def test_unicode_logparser_5_ids(self):
    
        self.assertTrue(len(self.found) == 5)

class TestUniversalLogParser(unittest.TestCase):

    def setUp(self):
        with open('data/universal_transcode.log', 'r') as fh:
            self.found = [ parse_line(line) for line in fh if parse_line(line) ]

    def test_universal_logparser_2_ids(self):

        self.assertTrue(len(self.found) == 2)

if __name__ == '__main__':
    unittest.main()
