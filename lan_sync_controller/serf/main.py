#!/usr/bin/python

import errno
import logging
import os
import socket
import sys
import xmlrpclib

import scapy.all

sys.path.insert(0, os.getcwd())
from lan_sync_controller.config_loader import SETTINGS

LOG = logging.getLogger(__name__)


def get_local_addresses():
    """Get local addresses"""
    return [x[4] for x in scapy.all.conf.route.routes if x[2] != '0.0.0.0']


def safe_rpc(fn):
    """Decorator to add try/catch to rpc function calls"""
    def safe_fn(*args):
        try:
            result = fn(*args)
            if result is None:
                result = 1

            return result
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED or e.errno == errno.EHOSTUNREACH:
                msg = ('Problem when connect to RPC - No RPC server is '
                       'running now, function: %s', fn.func_name)
                LOG.error(msg)
                return None
            else:
                raise e
    return safe_fn


@safe_rpc
def event(port, filename, timestamp, event_type, serverip):
    if serverip not in get_local_addresses():
        url = 'http://%s:%s/' % ('localhost', port)
        rpc_connect = xmlrpclib.ServerProxy(url, allow_none=True)
        return rpc_connect.event(filename, timestamp, event_type, serverip)
    else:
        return None


def main():
    if os.getenv('SERF_EVENT', 'default') == 'user':
        result = os.getenv('SERF_USER_EVENT', '|||')
        event_type, filename, timestamp, serverip = result.split('|')
        LOG.info('Result: %s', result)
        event(SETTINGS['default-port'], filename, timestamp,
              event_type, serverip)


if __name__ == '__main__':
    main()
