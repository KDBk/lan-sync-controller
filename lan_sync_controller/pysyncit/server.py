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
    def __init__(self, mfiles, rfiles, pulledfiles):
        self.mfiles = mfiles
        self.rfiles = rfiles
        self.pulled_files = pulledfiles

    # @staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            filename = event.src_path
            if not self.pulled_files.__contains__(filename):
                self.mfiles.add(filename, time.time())
                logger.info("Created file: %s", filename)
            else:
                pass
                self.pulled_files.remove(filename)

        elif event.event_type == 'modified':
            filename = event.src_path
            if not self.pulled_files.__contains__(filename):
                self.mfiles.add(filename, time.time())
                logger.info("Modified file: %s", filename)
            else:
                self.pulled_files.remove(filename)

        elif event.event_type == 'deleted':
            filename = event.src_path
            self.rfiles.add(filename)
            try:
                self.mfiles.remove(filename)
            except KeyError:
                pass
            logger.info("Removed file: %s", filename)


class Server(Node):
    """Server class"""

    def __init__(self, username, port, watch_dirs, servers):
        super(Server, self).__init__(username, port, watch_dirs)
        self.servers = servers
        self.mfiles = FilesPersistentSet(pkl_filename='{}/node.pkl' .format(DIR_PATH))  # set() #set of modified files
        self.rfiles = set()  # set of removed filess
        self.pulled_files = set()
        self.server_available = True

    def push_file(self, filename, dest_file, passwd, dest_uname, dest_ip):
        """push file 'filename' to the destination"""
        command = "{} -q -p -l {} -pw {} {} {}@{}:{}".format(
            PSCP_COMMAND[ENV], self.username, passwd,
            filename, dest_uname, dest_ip, dest_file).split()
        print(command)
        proc = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        proc.stdin.write('y')
        push_status = proc.wait()
        logger.debug("returned status %s", push_status)
        return push_status

    def req_push_file(self, filename):
        """Mark this file as to be notified to clients - this file 'filename' has been modified, pull the latest copy"""
        logger.debug("server filedata %s", filename)
        my_file = "{}{}".format(self.watch_dirs[0], filename)
        server_filename = my_file

        logger.debug("server filename %s returned for file %s", server_filename, filename)
        try:
            mtime_server = os.stat(server_filename).st_mtime
        except Exception as e:
            mtime_server = 0
        return (self.username, server_filename, mtime_server)

    def sync_files_to_server(self):
        """Sync all the files present in the mfiles set and push this set"""
        mfiles = self.mfiles
        while True:
            try:
                time.sleep(10)
                for filedata in mfiles.list():
                    filename = filedata.name
                    if not filename:
                        continue
                    if '.swp' in filename:
                        mfiles.remove(filename)
                        continue
                    if len(self.servers) == 0:
                        logger.info('Dont find any servers, skip...')
                        continue
                    for server in self.servers:
                        logger.info('push filedata object {} to server {}' .
                                    format(filedata, server))
                        passwd, server_ip, server_port = server
                        # Add by daidv, only send file name alter for full path file to server
                        filedata_name = self.format_file_name(filedata.name)
                        server_uname, dest_file, mtime_server = rpc.req_push_file(server_ip, server_port, filedata_name)
                        logger.info("destination file name %s", dest_file)
                        mtime_client = os.stat(filename).st_mtime
                        print(mtime_server, mtime_client)
                        if float(mtime_server) >= float(mtime_client):
                            mfiles.remove(filename)
                            continue
                        if dest_file is None:
                            continue
                        push_status = self.push_file(filename, dest_file, passwd, server_uname, server_ip)
                        if (push_status < 0):
                            continue
                    mfiles.remove(filename)
                self.mfiles.update_modified_timestamp()
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
        ob.schedule(Handler(self.mfiles, self.rfiles, self.pulled_files), self.watch_dirs[0])
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
