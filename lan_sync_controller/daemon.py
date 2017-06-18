import logging
import time

from lan_sync_controller import base
from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.discovery import NeighborsDetector, SYNC_SERVERS
from lan_sync_controller.process_handler import ProcessHandler
from lan_sync_controller.process_handler import start_application
from lan_sync_controller.pysyncit.server import Server

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
        username = SETTINGS['default-user']
        port = int(SETTINGS['default-port'])
        watch_dirs = [SETTINGS['default-syncdir']]
        node = Server(username, port, watch_dirs, SYNC_SERVERS)
        # Have to active before start detect valid host
        # to open port.
        node.activate()
        prhandler = ProcessHandler(SETTINGS['default-syncapp'])
        exe = prhandler.get_executable_file()
        while True:
            # List valid hosts
            detector.get_all_neighbors()
            if len(node.servers) > 0 and prhandler.is_running():
                # Turn off default sync app (GGDrive, etc)
                prhandler.terminate()
            elif len(node.servers) == 0:
                start_application(exe)
            time.sleep(10)
