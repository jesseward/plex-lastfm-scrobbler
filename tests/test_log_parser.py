import unittest

from plex_scrobble.plex_monitor import parse_line

import logging
logging.disable(logging.CRITICAL)

class TestLogParser(unittest.TestCase):

    def setUp(self):
        fh = open('data/unicode_pms.log', 'r')
        self.found = [ parse_line(line) for line in fh if parse_line(line) ]
    
    def test_logparser(self):
    
        self.assertTrue(len(self.found) == 5)

if __name__ == '__main__':
    unittest.main()
