import threading
import logging

from plex_monitor import monitor_log, ScrobbleCache

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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
    m = main()
