import io
from setuptools import setup

NAME = 'plex-lastfm-scrobbler'
VERSION = '4.1.0'

description = 'Scrobble audio tracks played via Plex Media Center'
try:
    with io.open('README.rst', encoding="utf-8") as fh:
            long_description = fh.read()
except IOError:
    long_description = description

setup(
    name='plex-scrobble',
    version=VERSION,
    author='Jesse Ward',
    author_email='jesse@jesseward.com',
    description=description,
	long_description=long_description,
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
    ],
    classifiers=[
        'Environment :: Console',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
