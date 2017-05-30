import logging
import os
import sys

from lan_sync_controller.config_loader import logging_config_loader
from lan_sync_controller.daemon import LANSyncDaemon

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


LOG = logging.getLogger(__name__)


def main():
    # Init logging with logging configuration
    logging_config_loader()
    # Init LanSyncDaemon
    LOG.info('Initiliaze LanSyncDaemon!')
    daemon = LANSyncDaemon('/tmp/lansync-daemon.pid')

    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            daemon.start()
        elif sys.argv[1] == 'stop':
            daemon.stop()
        elif sys.argv[1] == 'restart':
            daemon.restart()
        elif sys.argv[1] == 'status':
            daemon.status()
        else:
            print('Unknow argv')
            sys.exit(2)
    else:
        print('Usage: %s start|stop|restart|status' % sys.argv[0])
        sys.exit(2)


if __name__ == '__main__':
    main()
