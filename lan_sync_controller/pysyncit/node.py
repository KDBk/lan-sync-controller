from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import logging
import os
import re
import subprocess
import threading


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')


class Handler(SimpleXMLRPCRequestHandler):
    def _dispatch(self, method, params):
        try:
            print self.server.funcs.items()
            return self.server.funcs[method](*params)
        except:
            import traceback
            traceback.print_exc()
            raise


class Node(object):
    """Base class for client and server"""

    def __init__(self, username, port, watch_dirs):
        self.username = username
        self.port = int(port)
        self.watch_dirs = watch_dirs

    def format_file_name(self, file_name):
        """
        Remove dir in full path of file
        author: daidv
        :param file_name:
        :return:
        """
        if file_name:
            for di in self.watch_dirs:
                if di in file_name:
                    return file_name.replace(di, '')
        else:
            return None

    def get_dest_path(self, filename):
        """ Replace username in filename with 'dest_uname'"""
        return "{}{}" .format(self.watch_dirs[0], filename)

    def ensure_dir(self):
        """create directories to be synced if not exist"""
        for dir in self.watch_dirs:
            if not os.path.isdir(dir):
                os.makedirs(dir)

    def start_server(self):
        """Start RPC Server on each node """
        server = SimpleXMLRPCServer(("0.0.0.0", self.port), allow_none =True)
        server.register_instance(self)
        server.register_introspection_functions()
        rpc_thread = threading.Thread(target=server.serve_forever)
        rpc_thread.setDaemon(True)
        rpc_thread.start()
        logger.debug("server functions on rpc %s", server.funcs.items())
        logger.info("Started RPC server thread. Listening on port %s..." , self.port)

    def start_sync_thread(self):
        # Sync file to itself server
        sync_to_server_thread = threading.Thread(target=self.sync_files_to_server)
        sync_to_server_thread.setDaemon(True)
        sync_to_server_thread.start()
        logger.info("Thread 'syncfiles' started ")

    def activate(self):
        self.ensure_dir()
        self.start_sync_thread()
        self.start_server()

