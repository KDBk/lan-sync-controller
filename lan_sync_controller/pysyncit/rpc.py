import logging
import socket
import errno
import xmlrpclib


LOG = logging.getLogger(__name__)


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
                LOG.critical(
                    "Problem connecting to rpc - no rpc server running. function: %s", fn.func_name)
                return None  # rpc request failed
            else:
                raise
    return safe_fn


@safe_rpc
def req_pull_file(dest_ip, dest_port, filename):
    rpc_connect = xmlrpclib.ServerProxy('http://%s:%s/' % (dest_ip, dest_port),
                                        allow_none=1)
    return rpc_connect.req_pull_file(filename)


@safe_rpc
def req_push_file(dest_ip, dest_port, filename):
    rpc_connect = xmlrpclib.ServerProxy(
        "http://%s:%s/" % (dest_ip, dest_port), allow_none=1)
    return rpc_connect.req_push_file(filename)


@safe_rpc
def event(port, filename, timestamp, event_type, serverip):
    rpc_connect = xmlrpclib.ServerProxy(
        "http://%s:%s/" % ('localhost', port), allow_none=1)
    return rpc_connect.event(filename, timestamp, event_type, serverip)


def find_available(dest_ip, dest_port):
    """rpc call to find client's rpc availability"""
    rpc_connect = xmlrpclib.ServerProxy(
        "http://%s:%s/" % (dest_ip, dest_port), allow_none=1)
    try:
        rpc_connect.system.listMethods()
        return True
    except socket.error as e:
        if e.errno == errno.ECONNREFUSED or e.errno == errno.EHOSTUNREACH:
            return False
        else:
            raise
