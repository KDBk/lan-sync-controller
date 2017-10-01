import errno
import logging
import os
import re
import rpc
import platform
import subprocess
import threading
import time
import hashlib
import shutil

from serfclient.client import SerfClient
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from lan_sync_controller.config_loader import SETTINGS
from lan_sync_controller.connector import MySQLConnector
from lan_sync_controller.connector import SwiftConnector
from lan_sync_controller.pysyncit.node import Node
from lan_sync_controller.pysyncit.persistence import FilesPersistentSet
from lan_sync_controller.constants import DIR_PATH
from lan_sync_controller.constants import PSCP_COMMAND

__author__ = 'dushyant'
__updater__ = 'daidv'

LOG = logging.getLogger(__name__)
ENV = platform.system()
PIPE = subprocess.PIPE


class Handler(FileSystemEventHandler):
    def __init__(self, mfiles, ip, mysql_connector, serf_client):
        self.mfiles = mfiles
        self.ip = ip
        self.serf_client = serf_client or SerfClient()
        self.swift_connector = SwiftConnector()
        self.mysql_connector = mysql_connector

    def on_any_event(self, event):
        if event.is_directory:
            return None
        elif event.src_path.split('/').pop().startswith('.'):
            pass
        elif event.event_type == 'created':
            filename = event.src_path
            timestamp = time.time()
            self.serf_client.event('created|{}|{}|{}'.format(
                filename, timestamp, self.ip))
            LOG.info("Created file: %s", filename)
            self.upload_file(filename)
            LOG.info("Uploaded file to Cloud: %s", filename)

        elif event.event_type == 'modified':
            filename = event.src_path
            timestamp = time.time()
            self.serf_client.event('modified|{}|{}|{}'.format(
                filename, timestamp, self.ip))
            LOG.info("Modified file: %s", filename)
            self.upload_file(filename)
            LOG.info("Uploaded file to Cloud: %s", filename)

        elif event.event_type == 'deleted':
            filename = event.src_path
            timestamp = time.time()
            self.serf_client.event('deleted|{}|{}|{}'.format(
                filename, timestamp, self.ip))
            try:
                self.mfiles.remove(filename)
            except KeyError:
                pass
            LOG.info("Removed file: %s", filename)

    def upload_file(self, filepath):
        """ This function will be called in create and modified event."""
        # In case, we are uploading file to server, then pass this
        # In other case, we should update metadate to server and upload it to Swift
        # encode_name = ".{}".format(hashlib.md5(filepath).hexdigest())
        # NOTE(kiennt): Temporary comment out, wrong logic
        # if not os.path.isfile(encode_name):
        #     last_modified = os.path.getmtime(filepath)
        #     shutil.copy2(filepath, encode_name)
        #     file_name = filepath.split("/").pop()
        #     self.mysql_connector.insert_or_update(filepath, last_modified)
        #     self.swift_connector.upload(encode_name, file_name)

        # rstrip to make sure filepath doesn't end with '/'
        file_name = filepath.rstrip('/').split('/').pop()
        sync_dir = SETTINGS['default-syncdir'].rstrip('/')
        while True:
            encode_name = ".{}".format(hashlib.md5(file_name).hexdigest())
            encode_path = sync_dir + '/' + encode_name
            if not os.path.isfile(encode_path):
                last_modified = os.path.getmtime(filepath)
                shutil.copy2(filepath, encode_path)
                self.mysql_connector.insert_or_update(filepath, last_modified)
                self.swift_connector.upload(encode_path, file_name)
                os.remove(encode_path)
                break


class Server(Node):
    """Server class"""

    def __init__(self, username, ip, port, watch_dirs, mysql_connector):
        super(Server, self).__init__(username, ip, port, watch_dirs)
        # set() #set of modified files
        self.mfiles = FilesPersistentSet(
            pkl_filename='{}/node.pkl' .format(DIR_PATH))
        self.serf_client = SerfClient()
        self.swift_connector = SwiftConnector()
        self.mysql_connector = mysql_connector

    def event(self, filename, timestamp, event_type, serverip):
        if serverip != self.ip:
            self.mfiles.add(filename, timestamp, event_type, serverip)

    def pull_file(self, filename, dest_file, passwd, dest_uname, dest_ip):
        """Pull file 'filename' to the destination"""
        # MUST COPY SSH ID_RSA PUB TO ANOTHER HOST (FUCK)
        ssh_private_key = '/home/%s/.ssh/id_rsa' % self.username
        rsync_path = DIR_PATH + '/run_rsync.sh'
        rsync_command = 'bash {} {} {} {} {} {}' . format(
            rsync_path, ssh_private_key, dest_uname,
            dest_ip, dest_file, filename).split()
        LOG.info(rsync_command)
        proc = subprocess.Popen(
            rsync_command, stdout=PIPE, stderr=PIPE, stdin=PIPE)
        output, error = proc.communicate()
        LOG.info("Communicate log: {} {}".format(output, error))

    def req_pull_file(self, filename):
        # NOTE(kiennt): Always remove the last '/' character. Can do a check
        #               but it doesn't worth.
        my_file = "{}/{}".format(self.watch_dirs[0].rstrip('/'), filename)
        server_filename = my_file
        LOG.debug("server filename %s returned for file %s",
                  server_filename, filename)
        return (self.username, server_filename)

    def sync_files_to_server(self):
        """Sync all the files present in the mfiles set and push this set"""
        mfiles = self.mfiles
        passwd = SETTINGS['default-password']
        while True:
            try:
                time.sleep(10)
                # TODO(daidv): Do someting like summary list mfiles, compare and return list action
                for filedata in mfiles.list():
                    filename = filedata.name
                    mfiles.remove(filename)
                    serverip = filedata.serverip
                    if not filename:
                        continue
                    if '.swp' in filename:
                        continue
                    # Add by daidv, only send file name alter for full path file to server
                    filedata_name = self.format_file_name(filedata.name)
                    if filedata_name.startswith('.'):
                        continue
                    server_return = rpc.req_pull_file(
                        serverip, self.port, filedata_name)
                    if server_return:
                        server_uname, dest_file = server_return
                    else:
                        continue
                    LOG.info("destination file name {} {} {}".format(
                        dest_file, filedata_name, filedata.name))
                    if dest_file is None:
                        continue
                    pull_status = self.pull_file("{}{}".format(
                        self.watch_dirs[0], filedata_name), dest_file, passwd,
                        server_uname, serverip)
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
                LOG.debug(
                    "checked file if modified before client was running: %s", file_path)
                mtime = os.path.getmtime(file_path)
                # TODO save and restore last_synctime
                if mtime > self.mfiles.get_modified_timestamp():
                    LOG.debug(
                        "modified before client was running %s", file_path)
                    self.serf_client.event('modified|{}|{}|{}'.format(
                        filename, mtime, self.ip))

    def watch_files(self):
        """keep a watch on files present in sync directories"""
        ob = Observer()
        # watched events
        ob.schedule(Handler(self.mfiles, self.ip, self.mysql_connector,
                            self.serf_client), self.watch_dirs[0])
        ob.start()
        LOG.debug("watched dir %s", self.watch_dirs)
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
        LOG.info("Thread 'watchfiles' started ")

    def activate(self):
        """ Activate Server Node """
        super(Server, self).activate()
        self.start_watch_thread()
        self.find_modified()
