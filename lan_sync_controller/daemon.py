import logging
import time

from lan_sync_controller import base
from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.discovery import NeighborsDetector, SCANNED_SERVERS
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
        ip = SETTINGS['default-ip']
        node = Server(username, ip, port, watch_dirs)
        # Have to active before start detect valid host
        # to open port.
        node.activate()
        prhandler = ProcessHandler(SETTINGS['default-syncapp'])
        exe = prhandler.get_executable_file()
        while True:
            # List valid hosts
            detector.get_all_neighbors()
            # LOG.info('Current nodes:')
            # LOG.info(node.servers)
            # if len(node.servers) > 0 and prhandler.is_running():
            #     # Turn off default sync app (GGDrive, etc)
            #     prhandler.suspend()
            # elif len(node.servers) == 0 and not prhandler.is_running() \
            #         and exe:
            #     start_application(exe)
            time.sleep(10)
