import threading
import logging

from plex_scrobble.plex_monitor import monitor_log, ScrobbleCache


def cache_retry():

    threading.Timer(7200, cache_retry).start()
    cache = ScrobbleCache()
    cache.retry_queue()
    cache.close

def main():

    logger.info('starting log monitor thread.')
    log_watch = threading.Thread(target=monitor_log)
    log_watch.start()

if __name__ == '__main__':

    FORMAT = '%(asctime)-15s [%(process)d] [%(name)s %(funcName)s] [%(levelname)s] %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    m = main()
