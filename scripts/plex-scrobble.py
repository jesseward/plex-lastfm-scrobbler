#!/usr/bin/env python
import os
import sys
import platform
import logging
import time
import threading
import ConfigParser
from optparse import OptionParser

from plex_scrobble.lastfm import LastFm
from plex_scrobble.plex_monitor import monitor_log
from plex_scrobble.scrobble_cache import ScrobbleCache
from plex_scrobble.pre_check import PLSSanity

def platform_log_directory():
    """
    Retrieves the default platform specific default log location.
    This is called if the user does not specify a log location in
    the configuration file.
    github issue https://github.com/jesseward/plex-lastfm-scrobbler/issues/5
    """

    LOG_DEFAULTS = {
        'Darwin': os.path.expanduser('~/Library/Logs/Plex Media Server.log'),
        'Linux': '/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log',
        'Windows': os.path.join(os.environ.get('LOCALAPPDATA', 'c:'), 'Plex Media Server/Logs/Plex Media Server.log'),
        'FreeBSD': '/usr/local/plexdata/Plex Media Server/Logs/Plex Media Server.log',
        }

    return LOG_DEFAULTS[platform.system()]


def cache_retry(config):
    """
    Thread timer for the cache retry logic.

    :param config: config (ConfigParser obj)
    """

    while True:
        logger.info('starting cache_retry thread.')
        cache = ScrobbleCache(config)
        # do not retry if cache is empty.
        if cache.length() > 0:
            cache.retry_queue()

        cache.close()
        time.sleep(3600)

def main(config):
    """
    The main thread loop

    :param config: config (ConfigParser obj)
    """

    logger.info('starting log monitor thread.')
    log_watch = threading.Thread(target=monitor_log, args=(config,))
    log_watch.daemon = True
    log_watch.start()

    # retry cache every hour.
    cache_thread = threading.Thread(target=cache_retry, args=(config,))
    cache_thread.daemon = True
    cache_thread.start()

    # main thread ended/crashed. exit.
    log_watch.join()
    cache_thread.join()
    sys.exit(1)

if __name__ == '__main__':

    p = OptionParser()
    p.add_option('-c', '--config', action='store', dest='config_file',
        help='The location to the configuration file.')
    p.add_option('-p', '--precheck', action='store_true', dest='precheck',
        default=False, help='Run a pre-check to ensure a correctly configured system.')
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

    # ISSUE https://github.com/jesseward/plex-lastfm-scrobbler/issues/34
    try:
        config.read(options.config_file)
    except ConfigParser.Error:
        print 'ERROR: unable to parse config file "{file}". Syntax error?'.format(
            file=options.config_file)
        sys.exit(1)
    
    FORMAT = '%(asctime)-15s [%(process)d] [%(name)s %(funcName)s] [%(levelname)s] %(message)s'
    logging.basicConfig(filename=config.get('plex-scrobble',
      'log_file'), format=FORMAT, level=logging.DEBUG)
    logger = logging.getLogger('main')

    # dump our configuration values to the logfile
    for key in config.items('plex-scrobble'):
        logger.debug('config : {0} -> {1}'.format(key[0], key[1]))

    if options.precheck:
        pc = PLSSanity(config)
        pc.run()
        logger.warn('Precheck completed. Exiting.')
        sys.exit(0)

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

    logger.debug('using last.fm session key={key} , st_mtime={mtime}'.format(
        key=config.get('plex-scrobble','session'),
        mtime=time.ctime(os.path.getmtime(config.get('plex-scrobble','session'))) ))

    m = main(config)
