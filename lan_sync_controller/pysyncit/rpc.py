import logging
import socket
import errno
import xmlrpclib
import logging


__author__ = 'dushyant'
__updater__ = 'daidv'


logger = logging.getLogger('syncIt')


def safe_rpc(fn):
    """decorator to add try/catch to rpc function calls"""
    def safe_fn(*args):
        try:
            result = fn(*args)
            if result is None:
                result = "success"

            return result
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED or e.errno == errno.EHOSTUNREACH:
                logger.critical("Problem connecting to rpc - no rpc server running. function: %s", fn.func_name)
                return None #rpc request failed
            else:
                raise
    return safe_fn

@safe_rpc
def req_push_file(dest_ip, dest_port, filename):
    rpc_connect = xmlrpclib.ServerProxy("http://%s:%s/"% (dest_ip, dest_port), allow_none = True)
    return rpc_connect.req_push_file(filename)

def find_available(dest_ip, dest_port):
    """rpc call to find client's rpc availability"""
    rpc_connect = xmlrpclib.ServerProxy("http://%s:%s/"% (dest_ip, dest_port), allow_none = True)
    try:
        rpc_connect.system.listMethods()
        return True
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED or e.errno == errno.EHOSTUNREACH:
            return False
        else:
            raise

