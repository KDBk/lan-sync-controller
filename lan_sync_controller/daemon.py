import logging
import sys
import time

from lan_sync_controller import base
from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.discovery import NeighborsDetector
from lan_sync_controller.pysyncit import monitor as pysyncit_monitor
from lan_sync_controller.process_handler import ProcessHandler

LOG = logging.getLogger(__name__)


class LANSyncDaemon(base.BaseDaemon):

    """
    A daemon that runs the app in background
    """

    def stop(self):
        super(LANSyncDaemon, self).stop()
        base.kill_process(self.pidfile)
        # Find and kill existed pysyncit process.
        base.kill_process('/tmp/pysyncit.pid')

    def run(self):
        # Init detector and get all vaild hosts
        # in LAN. Vaild host is the host which open
        # SETTINGS['default-port'].
        _detector = NeighborsDetector()
        # Find and kill existed pysyncit process.
        base.kill_process('/tmp/pysyncit.pid')

        syncdaemon = PySyncitDaemon('/tmp/pysyncit.pid')
        _handler = ProcessHandler(SETTINGS['default-syncapp'])
        # For comprasion purpose.
        _tmp = None
        while True:
            # List valid hosts
            servers = _detector.detect_valid_hosts()
            if len(servers) != 0:
                # Not test yet
                _handler.do_method('kill')
                # Restart if detect new host
                if not _tmp:
                    syncdaemon.start(servers)
                elif len(_tmp) != len(servers):
                    syncdaemon.restart(servers)
            _tmp = servers
            time.sleep(50)


class PySyncitDaemon(base.BaseDaemon):

    """
    A daemon that runs pysyncit in background.
    """

    def start(self, servers):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def restart(self, servers):
        """
        Restart the daemon
        """
        self.stop()
        self.start(servers)

    def run(self):
        while True:
            pysyncit_monitor.run(self.servers)
