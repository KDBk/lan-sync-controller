import logging
import getpass

from lan_sync_controller.pysyncit.server import Server
from lan_sync_controller.config_loader import SETTINGS

__author__ = 'dushyant'
__updater__ = 'daidv, kiennt'


logger = logging.getLogger('syncIt')


def setup_logging(log_filename):
    handler = logging.FileHandler(log_filename)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    print 'Logging started on file %s' % log_filename


def run(servers):
    # Username and port of this node.
    username = getpass.getuser()
    port = int(SETTINGS['default-port'])
    watch_dirs = SETTINGS['default-syncdir']
    node = Server(username, port, watch_dirs, servers)
    setup_logging("/tmp/syncit.log.%s-%s" % (username, port))
    node.activate()
