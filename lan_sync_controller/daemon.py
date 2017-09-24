import logging
import time
import uuid
import subprocess
import os

import psutil

from lan_sync_controller import base
from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.connector import MySQLConnector
from lan_sync_controller.constants import DIR_PATH
from lan_sync_controller.discovery import NeighborsDetector, SCANNED_SERVERS
from lan_sync_controller.process_handler import ProcessHandler
from lan_sync_controller.process_handler import start_application
from lan_sync_controller.pysyncit.server import Server

LOG = logging.getLogger(__name__)
PIPE = subprocess.PIPE


class LANSyncDaemon(base.BaseDaemon):

    """
    A daemon that runs the app in background
    """

    def __init__(self, pidfile):
        super(LANSyncDaemon, self).__init__()
        self.mysql_connector = MySQLConnector()

    def stop(self):
        procs = [proc for proc in psutil.process_iter()
                 if 'serf' in proc.name()]
        for proc in procs:
            proc.kill()
        self.mysql_connector.close()
        super(LANSyncDaemon, self).stop()

    def run(self):
        # Init detector and get all vaild hosts
        # in LAN. Vaild host is the host which open
        # SETTINGS['default-port'].
        detector = NeighborsDetector()
        username = SETTINGS['default-user']
        port = int(SETTINGS['default-port'])
        watch_dirs = [SETTINGS['default-syncdir']]
        ip = SETTINGS['default-ip']

        # Run Serf init
        serf_path = DIR_PATH + '/serf_init.sh'
        serf_main_path = DIR_PATH + '/serf/main.py'
        serf_command = 'bash {} {} {} {}' . format(
            serf_path, str(uuid.uuid4()), ip, serf_main_path).split()
        LOG.info(serf_command)
        subprocess.call(serf_command)

        node = Server(username, ip, port, watch_dirs)
        # Have to active before start detect valid host
        # to open port.
        node.activate()
        prhandler = ProcessHandler(SETTINGS['default-syncapp'])
        exe = prhandler.get_executable_file()

        while True:
            # List valid hosts
            detector.get_all_neighbors()

            if SCANNED_SERVERS.keys():
                random_server = SCANNED_SERVERS.keys()[0]
                proc = subprocess.Popen(
                    ['serf', 'join', random_server],
                    stdout=PIPE, stderr=PIPE, stdin=PIPE)
                output, error = proc.communicate()
                LOG.info("Serf join: {} {}".format(output, error))
            
            # Get list file and timestamp from master: [name, last_modified]
            files = self.mysql_connector.get_files()
            # Check local change vs master change and decide to download it into local
            for _file in files:
                filepath = "/".join(watch_dirs[0], _file[0])
                local_modified_time = os.path.getmtime(filepath)
                if local_modified_time < _file[1]:
                    # File is out of dated, download it by SwiftConnector
            time.sleep(10)
