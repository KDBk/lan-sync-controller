from __future__ import absolute_import, division, print_function
from datetime import datetime
import errno
import logging
import math
import socket

import scapy.config
import scapy.layers.l2
import scapy.route
from scapy.all import *

from lan_sync_controller.config_loader import SETTINGS

LOG = logging.getLogger(__name__)


SYNC_SERVERS = list()


def long2net(arg):
    """Convert long to netmask"""
    if (arg <= 0 or arg >= 0xFFFFFFFF):
        raise ValueError("illegal netmask value", hex(arg))
    return 32 - int(round(math.log(0xFFFFFFFF - arg, 2)))


def to_CIDR_notation(bytes_network, bytes_netmask):
    network = scapy.utils.ltoa(bytes_network)
    netmask = long2net(bytes_netmask)
    net = "%s/%s" % (network, netmask)
    if netmask < 16:
        LOG.warning("%s is too big. skipping" % net)
        return None

    return net


def scan_and_get_neighbors(net, interface, port, timeout=1):
    """Get list interfaces, then scan in each network
    and get available neighbors. Actually, it will  ping`
    to each ip in network, then wait for reply (received packet)
    :param net: (string)
    :param interface: (string)
    :param timeout(integer)
    """
    LOG.info('arping %s on %s' % (net, interface))

    try:
        ans, unans = scapy.layers.l2.arping(net, iface=interface,
                                            timeout=timeout,
                                            verbose=False)
        for s, r in ans.res:
            _valid_ip = r.sprintf('%ARP.psrc%')
            LOG.info('Scan tcp port - ip: %s - %s' % (port, _valid_ip))
            port_rs = scan_tcp_port(_valid_ip, port)
            LOG.info('Scan tcp port result: %s' % port_rs)
            if (port_rs == 'Open') and (_valid_ip not in SYNC_SERVERS):
                # auth_info = get_user_and_pwd(_valid_ip)
                # SYNC_SERVERS.append((auth_info[1], _valid_ip, port))
                SYNC_SERVERS.append(('1', _valid_ip, port))
    except socket.error as e:
        if e.errno == errno.EPERM:
            LOG.error('%s. Did you run as root?' % (e.strerror))
        else:
            raise


def scan_tcp_port(dst_ip, dst_port, dst_timeout=1):
    """Scan TCP port with specific ip address and port
    This host run code will be source host, define destination
    host and port that you want to scan.
    :param dst_ip: (string) destination ip address
    :param dst_port: (integer) specific port
    :param dst_timeout: (integer)
    """
    LOG.info('Start scan_tcp_port at %s' % datetime.now())
    tcp_scan_resp = sr1(IP(dst=dst_ip) / TCP(dport=dst_port),
                        timeout=dst_timeout)
    if not tcp_scan_resp:
        retrans = []
        for count in range(0, 3):
            retrans.append(sr1(IP(dst=dst_ip) / TCP(dport=dst_port),
                               timeout=dst_timeout))
            for item in retrans:
                if item:
                    scan_tcp_port(dst_ip, dst_port, dst_timeout)
            LOG.info('End scan_tcp_port at %s' % datetime.now())
            return 'Open|Filtered'
    elif tcp_scan_resp.haslayer(TCP):
        LOG.info('End scan_tcp_port at %s' % datetime.now())
        return 'Open'
    elif tcp_scan_resp.haslayer(ICMP):
        if int(tcp_scan_resp.getlayer(ICMP).type) == 3 and \
                int(tcp_scan_resp.getlayer(ICMP).code) == 3:
            LOG.info('End scan_tcp_port at %s' % datetime.now())
            return 'Closed'
        elif int(tcp_scan_resp.getlayer(ICMP).type) == 3 and \
                int(tcp_scan_resp.getlayer(ICMP).code) in [1, 2, 9, 10, 13]:
            LOG.info('End scan_tcp_port at %s' % datetime.now())
            return 'Filtered'
        else:
            LOG.info('End scan_tcp_port at %s' % datetime.now())
            return 'CHECK'


class NeighborsDetector(object):

    def __init__(self):
        self.port = int(SETTINGS['default-port'])

    def get_all_neighbors(self):
        """Get All Available Neighbors in LAN"""
        LOG.info('Start get_all_neighbors at %s' % datetime.now())
        for network, netmask, _, interface, address in \
                scapy.config.conf.route.routes:
            # skip loopback network and default gw
            if network == 0 or interface == 'lo' or interface == 'enp2s0' or \
                    address == '127.0.0.1' or address == '0.0.0.0' or address == '192.168.122.1':
                continue

            if netmask <= 0 or netmask == 0xFFFFFFFF:
                continue

            net = to_CIDR_notation(network, netmask)

            if net != '172.17.0.0/16' and interface != scapy.config.conf.iface:
                msg = ('Skipping %s because scapy currently doesn\'t\
                       support arping on non-primary network \
                       interfaces' % net)
                LOG.warning(msg)
                continue

            if net:
                scan_and_get_neighbors(net, interface, self.port)
        LOG.info('End get_all_neighbors at %s' % datetime.now())
