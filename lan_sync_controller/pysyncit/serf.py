#!/usr/bin/python

import os
import sys
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
def event(port, filename, timestamp, event_type, serverip):
    rpc_connect = xmlrpclib.ServerProxy("http://%s:%s/"% ('localhost', port), allow_none=True)
    return rpc_connect.event(filename, timestamp, event_type, serverip)


def main():
	if os.getenv('SERF_EVENT', 'default') == 'user':
		result = os.getenv('SERF_USER_EVENT', '|||')
		name, filename, timestamp, serverip = result.split('|')
		event('9696', filename, timestamp, name, serverip)


if __name__ == '__main__':
	main()
