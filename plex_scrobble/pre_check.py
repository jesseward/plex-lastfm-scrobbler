import inspect
import os
import textwrap

from plex_scrobble.plex_monitor import parse_line

class PLSSanity(object):

    WIDTH = 70
    BAR = '-' * WIDTH

    def __init__(self, config):
        self.config = config

    def run(self):
        ''' executes all tests and renders output. '''

        print self.BAR
        print '\n'.join(textwrap.wrap(
            '| Running a few tests against your installation to ensure that '
            'required Plex Media Server files are in place.', self.WIDTH,
            subsequent_indent='| '))
        print self.BAR
        self.verify_plex_log_file_exists()
        self.detect_played_audio_in_PMS_log()
        self.was_lastfm_authorization_granted()
        print self.BAR

    def _output(self, hints=None):

        print '| * {caller:50}\t => {result}'.format(caller=inspect.stack()[1][3],
                result='[FAIL]' if hints else '[PASS]')
        if hints:
            print '\n'.join(textwrap.wrap('|\tCheck: {hint}'.format(hint=hints),
                self.WIDTH, subsequent_indent='|\t'))

    def verify_plex_log_file_exists(self):
        ''' confirm Plex Media Server log file exists on the file system.'''

        if os.path.isfile(self.config.get('plex-scrobble',
            'mediaserver_log_location')):
            self._output()
        else:
            self._output(hints='Log file does not exist, please ensure you have'
            ' correctly set mediaserver_log location in your Plex Scrobbler'
            ' configuration.')

    def detect_played_audio_in_PMS_log(self):

        if not os.path.isfile(self.config.get('plex-scrobble', 'mediaserver_log_location')):
            
            self._output(hints='Log file does not exist, please ensure you have'
            'correctly set mediaserver_log location in your Plex Scrobbler'
            'configuration.')
            return

        with open(self.config.get('plex-scrobble', 'mediaserver_log_location')) as fh:

            for line in fh:

                played = parse_line(line)

                if played:
                    self._output()
                    return

        self._output(hints='Unable to detect any instances of audio files played'
        ' in your plex media server log file. Please ensure you have listened to'
        ' a song in full and you have enabled Plex to log in DEBUG mode.')

    def was_lastfm_authorization_granted(self):
        if os.path.isfile(self.config.get('plex-scrobble', 'session')):
                self._output()
        else:
            self._output(hints='Your last.fm authtoken does not exist. Please run'
            '"python plex-scrobbler.py -a" and follow instructions to grant'
            'authorization to your last.fm account.')
