#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import platform
import logging
import time
import threading

import click
import toml

from plex_scrobble.plex_monitor import monitor_log
from plex_scrobble.scrobble_cache import ScrobbleCache


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
        'FreeBSD': '/usr/local/plexdata/Plex Media Server/Logs/Plex Media Server.log',
        }

    return LOG_DEFAULTS[platform.system()]


def cache_retry(config, logger):
    """
    Thread timer for the cache retry logic.

    :param config: config (ConfigParser obj)
    """

    retry = 3600
    logger.info('starting cache_retry thread.')
    user_name = config['lastfm']['user_name']
    password = config['lastfm']['password']
    api_key = config['lastfm']['api_key']
    api_secret = config['lastfm']['api_secret']
    cache_location = config['plex-scrobble']['cache_location']

    while True:
        try:
            cache = ScrobbleCache(api_key, api_secret, user_name, password,
                                  cache_location=cache_location)
        except Exception as e:
            logger.warn('ERROR: {0}, retrying in {1} seconds'.format(e, retry))
            time.sleep(retry)
            continue
        # do not retry if cache is empty.
        if cache.length() > 0:
            cache.retry_queue()

        cache.close()
        time.sleep(retry)


def loop(config, logger):
    """
    The main thread loop

    :param config: config (ConfigParser obj)
    """

    logger.info('starting log monitor thread.')
    log_watch = threading.Thread(target=monitor_log, name='monitor_log',
                                 args=(config,))
    log_watch.daemon = True
    log_watch.start()

    # retry cache every hour.
    cache_thread = threading.Thread(target=cache_retry, name='cache_retry',
                                    args=(config, logger))
    cache_thread.daemon = True
    cache_thread.start()

    # main thread ended/crashed. exit.
    log_watch.join()
    cache_thread.join()
    sys.exit(1)


def load_config(path):
    config = toml.load(path)

    assert 'lastfm' in config, 'Missing lastfm config block'

    for k in ['api_key', 'api_secret', 'user_name', 'password']:
        assert k in config['lastfm'], 'Missing required lastfm option: {0}'.format(k)

    for k in ['mediaserver_url', 'cache_location', 'log_file']:
        assert k in config['plex-scrobble'], 'Missing required plex-scrobble option: {0}'.format(k)

    return config


def config_wizard():
    click.echo('''
You'll need to create a last.fm API application first. Do so here:

    http://www.last.fm/api/account/create

What you fill in doesn't matter at all, just make sure to save the API
Key and Shared Secret.
''')

    plex_scrobble = {
        'mediaserver_url': 'http://localhost:32400',
        'log_file': '/tmp/plex-scrobble.log',
        'cache_location': '/tmp/plex_scrobble.cache',
        'mediaserver_log_location': platform_log_directory()
    }

    config = {
        'lastfm': {
            key: click.prompt(key, type=str)
            for key in ['user_name', 'password', 'api_key', 'api_secret']
        }
    }

    config['plex-scrobble'] = {
        key: click.prompt(key, default=plex_scrobble[key])
        for key in list(plex_scrobble.keys())
    }

    generated = toml.dumps(config)
    click.echo('Generated config:\n\n%s' % generated)

    if click.confirm('Write to ~/.plex-scrobble.toml?'):
        with open(os.path.expanduser('~/.plex-scrobble.toml'), 'w') as fp:
            fp.write(generated)


@click.command()
@click.option('--config-file', required=False,
              help='The location to the configuration file.')
@click.option('--wizard', is_flag=True, help='Generate a config file.')
def main(config_file, wizard):

    if wizard:
        return config_wizard()

    path = config_file if config_file else '~/.plex-scrobble.toml'
    path = os.path.expanduser(path)
    if os.path.exists(path):
        config = load_config(path)
    else:
        click.secho('Config file not found!\n\nUse --wizard to create a config', fg='red')
        sys.exit(1)

    FORMAT = '%(asctime)-15s [%(process)d] [%(name)s %(funcName)s] [%(levelname)s] %(message)s'
    logging.basicConfig(filename=config['plex-scrobble']['log_file'],
                        format=FORMAT, level=logging.DEBUG)
    logger = logging.getLogger('main')

    loop(config, logger)


if __name__ == '__main__':
    sys.exit(main())
