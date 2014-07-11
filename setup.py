import os
from setuptools import setup

NAME = 'plex-lastfm-scrobbler'
VERSION = '0.0.1'

setup(
    name = 'plex_scrobble',
    version = '0.0.1',
    author = 'Jesse Ward',
    author_email = 'jesse@jesseward.com',
    description = ('Scrobble audio tracks played via Plex Media Center'),
    license = 'MIT',
    url = 'https://github.com/jesseward/plex-lastfm-scrobbler',
    scripts = ['scripts/plex-scrobble.py'],
    packages=['plex_scrobble'],
    data_files = [(
      os.path.expanduser('~/.config/{0}/'.format(NAME)),
      ['conf/plex_scrobble.conf'],
      )]
)
