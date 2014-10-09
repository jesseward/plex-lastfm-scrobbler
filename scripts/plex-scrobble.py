#!/usr/bin/env python
import os
import sys
import platform
import logging
import threading
import ConfigParser
from optparse import OptionParser

from plex_scrobble.lastfm import LastFm
from plex_scrobble.plex_monitor import monitor_log
from plex_scrobble.scrobble_cache import ScrobbleCache

def platform_log_directory():
    ''' Retrieves the default platform specific default log location.
        This is called if the user does not specify a log location in
        the configuration file.
        github issue https://github.com/jesseward/plex-lastfm-scrobbler/issues/5
    '''

    LOG_DEFAULTS = {
        'Darwin': os.path.expanduser('~/Library/Logs/Plex Media Server.log'),
        'Linux': '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log',
        'Windows': os.path.join(os.environ.get('LOCALAPPDATA', 'c:'), 'Plex Media Server/Logs/Plex Media Server.log'),
        }

    return LOG_DEFAULTS[platform.system()]


def cache_retry(config):
    '''Thread timer for the cache retry logic.

    Args:
        config (ConfigParser obj) : user specific configuration params
    '''

    logger.info('starting cache_retry thread.')
    cache = ScrobbleCache(config)
    # do not retry if cache is empty.
    if cache.length() > 0:
        cache.retry_queue()

    cache.close()
    # retry cache every hour.
    threading.Timer(3600, cache_retry, args=(config,)).start()

def main(config):
    ''' The main thread loop

    Args:
        config (ConfigParser obj) : user specific configuration params
    '''

    logger.info('starting log monitor thread.')
    log_watch = threading.Thread(target=monitor_log, args=(config,))
    log_watch.start()

    # main thread ended/crashed. exit.
    log_watch.join()
    sys.exit(1)

if __name__ == '__main__':

    p = OptionParser()
    p.add_option('-c', '--config', action='store', dest='config_file',
        help='The location to the configuration file.')
    p.add_option('-a', '--authenticate', action='store_true', dest='authenticate',
        default=False, help='Generate a new last.fm session key.')

    p.set_defaults(config_file=os.path.expanduser(
      '~/.config/plex-lastfm-scrobbler/plex_scrobble.conf'))

    (options, args) = p.parse_args()

    if not os.path.exists(options.config_file):
        print 'Exiting, unable to locate config file {0}. use -c to specify config target'.format(
            options.config_file)
        sys.exit(1)

    # apply defaults to *required* configuration values.
    config = ConfigParser.ConfigParser(defaults = {
        'config file location': options.config_file,
        'session': os.path.expanduser('~/.config/plex-lastfm-scrobbler/session_key'),
        'mediaserver_url': 'http://localhost:32400',
        'mediaserver_log_location': platform_log_directory(),
        'log_file': '/tmp/plex_scrobble.log'
      })
    config.read(options.config_file)

    FORMAT = '%(asctime)-15s [%(process)d] [%(name)s %(funcName)s] [%(levelname)s] %(message)s'
    logging.basicConfig(filename=config.get('plex-scrobble',
      'log_file'), format=FORMAT, level=logging.DEBUG)
    logger = logging.getLogger('main')

    # dump our configuration values to the logfile
    for key in config.items('plex-scrobble'):
        logger.debug('config : {0} -> {1}'.format(key[0], key[1]))

    # if a valid session object does not exist, prompt user
    # to authenticate.
    if (not os.path.exists(config.get('plex-scrobble','session')) or
      options.authenticate):
        logger.info('Prompting to authenticate to Last.fm.')
        last_fm = LastFm(config)
        last_fm.last_fm_auth()
        print 'Please relaunch plex-scrobble service.'
        logger.warn('Exiting application.')
        sys.exit(0)

    m = main(config)
    c = cache_retry(config)
