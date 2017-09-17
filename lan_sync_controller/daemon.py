import getpass
import logging
import time
from threading import Thread

from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.discovery import NeighborsDetector, SYNC_SERVERS
from lan_sync_controller.pysyncit.server import Server
# from lan_sync_controller.process_handler import ProcessHandler

LOG = logging.getLogger(__name__)


class LANSyncDaemon(object):

    """
    A daemon that runs the app in background
    """

    def run(self):
        # Init detector and get all vaild hosts
        # in LAN. Vaild host is the host which open
        # SETTINGS['default-port'].
        detector = NeighborsDetector()
        # username = getpass.getuser()
        ip = SETTINGS['default-ip']
        port = int(SETTINGS['default-port'])
        watch_dirs = [SETTINGS['default-syncdir']]
        node = Server('nqa', ip, port, watch_dirs)
        # Have to active before start detect valid host
        # to open port.
        node.activate()
        # node.username = 'kiennt'
        # _handler = ProcessHandler(SETTINGS['default-syncapp'])
        while True:
            # List valid hosts
            detector.get_all_neighbors()
            # node.servers = detector.valid_hosts.values()
            # Long sleep. If this is low, loop will go too fast.
            # PySyncit can't push modified file, new loop cycle - refresh?
            # So, i think (just think, plz re-test) we should open 2 port.
            # 1 for detect job, 1 for sync job.
            time.sleep(5)
