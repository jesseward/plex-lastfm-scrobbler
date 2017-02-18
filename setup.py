import os
from setuptools import setup

NAME = 'plex-lastfm-scrobbler'
VERSION = '4.0.0'

setup(
    name='plex_scrobble',
    version=VERSION,
    author='Jesse Ward',
    author_email='jesse@jesseward.com',
    description=('Scrobble audio tracks played via Plex Media Center'),
    license='MIT',
    url='https://github.com/jesseward/plex-lastfm-scrobbler',
    packages=['plex_scrobble'],
    entry_points={
        'console_scripts': [
        'plex-scrobble = plex_scrobble.__main__:main'
        ]
    },
    install_requires=[
        'click>=6.2',
        'pylast>=1.6.0',
        'toml>=0.9.1',
        'requests>=2.12.0',
    ]
)
