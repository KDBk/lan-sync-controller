import getpass
import logging
import time

from lan_sync_controller import base
from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.discovery import NeighborsDetector
from lan_sync_controller.pysyncit.server import Server
# from lan_sync_controller.process_handler import ProcessHandler

LOG = logging.getLogger(__name__)


class LANSyncDaemon(base.BaseDaemon):

    """
    A daemon that runs the app in background
    """

    def run(self):
        # Init detector and get all vaild hosts
        # in LAN. Vaild host is the host which open
        # SETTINGS['default-port'].
        detector = NeighborsDetector()
        username = getpass.getuser()
        port = int(SETTINGS['default-port'])
        watch_dirs = SETTINGS['default-syncdir']
        servers = list()
        node = Server(username, port, watch_dirs, servers)
        # Have to active before start detect valid host
        # to open port.
        node.activate()
        # _handler = ProcessHandler(SETTINGS['default-syncapp'])
        while True:
            # List valid hosts
            detector.detect_valid_hosts()
            node.servers = detector.valid_host
            time.sleep(10)
