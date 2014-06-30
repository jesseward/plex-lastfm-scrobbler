import urllib2
import urllib
import urlparse
import xml.etree.ElementTree
import re
from htmlentitydefs import name2codepoint
import hashlib
import sys
import logging
import time
import os


class LastFm(object):

    key = 'e692f685cdb9434ade9e72307fe53b05'
    secret = '7b42044139a817d6801e2da35943a0da'
    USER_AGENT = 'plex-lastfm-scrobbler'

    def __init__(self, cfg):

        self.logger = logging.getLogger(__name__)
        self.cfg = cfg

    def get_session(self):

        if os.path.exists(os.path.expanduser('~/.lastfmsess')):
            sessfp = open(os.path.expanduser('~/.lastfmsess'), 'r')
            session = sessfp.read().strip()
            sessfp.close()
        return session


    def _htmlentitydecode(s):
        os = re.sub('&(%s);' % '|'.join(name2codepoint),
            lambda m: unichr(name2codepoint[m.group(1)]), s)
        return os


    def _cleanname(self, x):
        if x is None:
            return ''
        return self._htmlentitydecode(x)


    def _etree_to_dict(self, etree):
        result = {}
        for i in etree:
            if i.tag not in result:
                result[i.tag] = []
            if len(i):
                result[i.tag].append(self._etree_to_dict(i))
            else:
                result[i.tag].append(self._cleanname(i.text))
        return result


    def _do_raw_lastfm_query(self, url):

        f = urllib2.Request(url)
        f.add_header('User-Agent', self.USER_AGENT)
        try:
            f = urllib2.urlopen(f)
        except urllib2.URLError, e:
            self.logger.error('Unable to submit query {url} - {error}'.format(
                url=url, error=e))
            raise

        tree = xml.etree.ElementTree.ElementTree(file=f)
        result = self._etree_to_dict(tree.getroot())
        return result


    def _do_lastfm_post(self, url, data):
        
        f = urllib2.Request(url)
        f.add_header('User-Agent', self.USER_AGENT)
        try:
            f = urllib2.urlopen(f, data)
        except urllib2.URLError, e:
            self.logger.error('Unable to submit post data {url} - {error}'.format(
                url=url, error=e))
            raise


    def _do_lastfm_query(self, type, method, **kwargs):

        args = {
            'method': method,
            'api_key': self.key,
            }
        for k, v in kwargs.items():
            args[k] = v.encode('utf8')

        s = ''
        for k in sorted(args.keys()):
            s+=k+args[k]
        s+=self.secret

        if 'sk' in args.keys() or 'token' in args.keys():
            args['api_sig'] = hashlib.md5(s).hexdigest()

        if type == 'GET':
            url = urlparse.urlunparse(('http',
                'ws.audioscrobbler.com',
                '/2.0/',
                '',
                urllib.urlencode(args),
                ''))
            return self._do_raw_lastfm_query(url)
        elif type == 'POST':
            url = urlparse.urlunparse(('http',
                'ws.audioscrobbler.com',
                '/2.0/', '', '', ''))
            self._do_lastfm_post(url, urllib.urlencode(args))


    def _get_auth_token(self):
        token = self._do_lastfm_query('GET', 'auth.getToken')
        return token['token'][0]


    def scrobble(self, artist, track):
    
        session = self.get_session()
        ts = '%d' % (time.time() - 100)

        self.logger.info('submitting {artist} - {track} to last.fm.'.format(
                artist=artist, track=track))

        try:
            self._do_lastfm_query('POST', 'track.scrobble', timestamp=ts,
                artist=artist, track=track, sk=session)
        except:
            return False

        return True

    def last_fm_auth(self):
        
        print '== Requesting last.fm auth =='

        token = self._get_auth_token()
        accepted = 'n'

        print 'Please accept authorizated at http://www.last.fm/api/auth/?api_key={key}&token={token}'.format(
                key=key, token=token)
        while accepted.lower() == 'n':
            print
            accepted = raw_input('Have you authorized me [y/N] :')

        try:
            sess = self._do_lastfm_query('GET', 'auth.getSession', token=token)
            key = sess['session'][0]['key'][0]
        except urllib2.HTTPError, e:
            self.logger.error('Unable to send authorization request {error}'.format(error=e))
            return False

        fp = open(os.path.expanduser('~/.lastfmsess'), 'w')
        fp.write(key)
        fp.close()
        self.logger.info('Last.FM authorization successful.')
