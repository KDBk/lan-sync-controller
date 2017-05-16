import logging
import time

from lan_sync_controller.base import BaseDaemon
from lan_sync_controller.discovery import NeighborsDetector

LOG = logging.getLogger(__name__)


class LANSyncDaemon(BaseDaemon):

    """
    A daemon that runs the app in background
    """

    def run(self):
        while True:
            # Init detector and get all vaild hosts
            # in LAN. Vaild host is the host which open
            # SETTINGS['default-port'].
            _detector = NeighborsDetector()
            # List valid hosts
            _valid_host = _detector.detect_valid_hosts()
            # Do something with each host in list.
            # Check authenticate info or something.
            print(_valid_host)
            time.sleep(500)
