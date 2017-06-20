import errno
import logging
import os
import re
import time

# import config
import rpc
from node import Node

import logging
import os
import platform
import subprocess
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

import rpc
from lan_sync_controller.pysyncit.node import Node
from lan_sync_controller.pysyncit.persistence import FilesPersistentSet
from lan_sync_controller.constants import DIR_PATH

__author__ = 'dushyant'
__updater__ = 'daidv'

logger = logging.getLogger('syncIt')
PSCP_COMMAND = {'Linux': 'pscp', 'Windows': 'C:\pscp.exe'}
ENV = platform.system()
PIPE = subprocess.PIPE


class Handler(FileSystemEventHandler):
    def __init__(self, mfiles):
        self.mfiles = mfiles

    # @staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            filename = event.src_path
            self.mfiles.add(filename, time.time(), 'created')
            logger.info("Created file: %s", filename)

        elif event.event_type == 'modified':
            filename = event.src_path
            self.mfiles.add(filename, time.time(), 'modified')
            logger.info("Modified file: %s", filename)

        elif event.event_type == 'deleted':
            filename = event.src_path
            self.mfiles.add(filename, time.time(), 'deleted')
            try:
                self.mfiles.remove(filename)
            except KeyError:
                pass
            logger.info("Removed file: %s", filename)


class Server(Node):
    """Server class"""

    def __init__(self, username, port, watch_dirs):
        super(Server, self).__init__(username, port, watch_dirs)
        self.mfiles = FilesPersistentSet(pkl_filename='{}/node.pkl' .format(DIR_PATH))  # set() #set of modified files

    def event(self, filename, timestamp, event_type, serverip):
        print("{} {} {} {}" .format(filename, timestamp, event_type, serverip))
        self.mfiles.add(filename, timestamp, event_type, serverip)

    def pull_file(self, filename, dest_file, passwd, dest_uname, dest_ip):
        """Pull file 'filename' to the destination"""
        command = "{} -q -p -l {} -pw {} {}@{}:{} {}".format(
            PSCP_COMMAND[ENV], self.username, passwd,
            dest_uname, dest_ip, dest_file, filename).split()
        print(command)
        proc = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        proc.stdin.write('y')
        pull_status = proc.wait()
        logger.debug("returned status %s", pull_status)
        return pull_status

    def req_pull_file(self, filename):
        my_file = "{}{}".format(self.watch_dirs[0], filename)
        server_filename = my_file
        logger.debug("server filename %s returned for file %s", server_filename, filename)
        return (self.username, server_filename)

    def sync_files_to_server(self):
        """Sync all the files present in the mfiles set and push this set"""
        mfiles = self.mfiles
        while True:
            try:
                time.sleep(10)
                # TODO(daidv): Do someting like summary list mfiles, compare and return list action
                for filedata in mfiles.list():
                    filename = filedata.name
                    serverip = filedata.serverip
                    if not filename:
                        continue
                    if '.swp' in filename:
                        mfiles.remove(filename)
                        continue
                    # Add by daidv, only send file name alter for full path file to server
                    filedata_name = self.format_file_name(filedata.name)
                    server_return = rpc.req_pull_file(serverip, self.port, filedata_name)
                    if server_return:
                        server_uname, dest_file = server_return
                    else:
                        continue
                    logger.info("destination file name %s", dest_file)
                    if dest_file is None:
                        continue
                    pull_status = self.pull_file(filename, dest_file, '1', server_uname, serverip)
                    if pull_status < 0:
                        continue
                    mfiles.remove(filename)
            except KeyboardInterrupt:
                break

    def find_modified(self):
        """Find all those files which have been modified when sync demon was not running"""
        for directory in self.watch_dirs:
            dirwalk = os.walk(directory)

            for tuple in dirwalk:
                dirname, dirnames, filenames = tuple
                break

            for filename in filenames:
                file_path = os.path.join(dirname, filename)
                logger.debug("checked file if modified before client was running: %s", file_path)
                mtime = os.path.getmtime(file_path)
                # TODO save and restore last_synctime
                if mtime > self.mfiles.get_modified_timestamp():
                    logger.debug("modified before client was running %s", file_path)
                    self.mfiles.add(file_path, mtime)

    def watch_files(self):
        """keep a watch on files present in sync directories"""
        ob = Observer()
        # watched events
        ob.schedule(Handler(self.mfiles), self.watch_dirs[0])
        ob.start()
        logger.debug("watched dir %s", self.watch_dirs)
        try:
            while True:
                time.sleep(5)
        except:
            self.ob.stop()
            print "Error"
        ob.join()

    def start_watch_thread(self):
        """Start threads to find modified files """
        watch_thread = threading.Thread(target=self.watch_files)
        watch_thread.setDaemon(True)
        watch_thread.start()
        logger.info("Thread 'watchfiles' started ")

    def activate(self):
        """ Activate Server Node """
        super(Server, self).activate()
        self.start_watch_thread()
        self.find_modified()
