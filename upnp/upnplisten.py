#!/usr/bin/env python3
"""module to discover UPnP devices"""

import socket
import argparse
import struct
from time import time

from Common import build
from upnp.UpnpCommon import SSDPdatagram, Mcast


class Listen(Mcast):
    """Passive listen for notifies from devices on the local network

    We are only listen to the upnp multicast group.
    """
    _verbose = False
    _open_timestamp = 0
    _timeout = 0
    _sock = None
    _o_datagram = None

    def __init__(self, verbose=False):
        """Setup verbose output if requested."""
        self._verbose = verbose

    def open(self):
        """Initialize and open a connection and join to the multicast group"""

        self._open_timestamp = time()
        self._timeout = -1
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                   socket.IPPROTO_UDP)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # use MCAST_GRP instead of '' to listen only to MCAST_GRP,
        # not all groups on MCAST_PORT
        # self._sock.bind(('', self._MCAST_PORT))
        self._sock.bind((self._MCAST_GRP, self._MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self._MCAST_GRP),
                           socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                              mreq)

    def _get_datagram(self):
        """Listen to the next SSDP datagram on the local network"""
        if self._timeout != 0:
            try:
                data, addr = self._sock.recvfrom(self.RECVBUF)
                if len(data) >= self.RECVBUF:
                    raise SystemExit("ERROR: receive buffer overflow")
                self._o_datagram = SSDPdatagram(addr, data)
            except KeyboardInterrupt:
                self._timeout = 0

    def get(self):
        """Listen for upnp datagrams on the local network."""
        self._get_datagram()
        if self._timeout == 0:
            return
        return self._o_datagram.fdevice(base_time=self._open_timestamp,
                                        verbose=self._verbose)


def print_it(o_mcast):
    """Listen to upnp root devices on the local network and print them.

    This is polymorphic execution and the result depends on the object that is
    given as argument.
    Arguments: search object
    Returns: None
    Output: print datagrams
    """
    o_mcast.open()
    datagram = o_mcast.get()
    while datagram is not None:
        print(datagram, end='', flush=True)
        datagram = o_mcast.get()


def main():
    """This is the entry point of the program and the command line parser"""
    parser = argparse.ArgumentParser(
        description='Passive listen to UPnP datagrams, stop with <ctrl>+C')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="verbose output")
    group.add_argument("-V", "--version", action="store_true",
                       help="show program version")
    args = parser.parse_args()
    if args.verbose:
        print_it(Listen(verbose=True))
    elif args.version:
        print("Build", build())
    else:
        print_it(Listen())


if __name__ == '__main__':
    main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
