#!/usr/bin/env python3
"""module to discover UPnP devices

references:
[Multicast in Python](https://stackoverflow.com/q/603852/5014688)
[Multicast programming](https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
"""
import socket
import struct
from time import time
import argparse

BUILD = '1'
SEARCH_TIMEOUT = 2   # we need this global for unit test


class SSDPdatagram:
    """This class represents a SSDP datagram received from a MSEARCH request.

    It contains the raw datagram as received so we can always extract available
    information. There are also some prepared often used parameter like a
    timestamp when the datagram was fetched, network address from the sending
    host, unique identifier of the device and some more.
    """
    timestamp = 0
    addr = ''
    uuid = ''
    #ssdp_type = ''   # M-SEARCH, NOTIFY
    server = ''
    #location = ''

    _raw_data = None    # raw received datagram

    def __init__(self, addr, raw_data):
        """The constructor prepairs raw data representing a SSDP datagram."""
        self._raw_data = raw_data
        self.timestamp = time()
        _addr = str(addr).replace("('", "")
        _addr = _addr.replace("', ", ":")
        self.addr = _addr.replace(")", "")
        _data = self.data
        #self.usn = _data.partition("USN: ")[2].partition("\r\n")[0]
        self.uuid = _data.partition("USN: uuid:")[2].partition("::")[0]
        #self.ssdp_type = _data.partition(" * ")[0]
        self.server = _data.partition("SERVER: ")[2].partition("\r\n")[0]
        #self.location = _data.partition("LOCATION: ")[2].partition("\r\n")[0]

    @property
    def data(self):
        """This returns the decoded raw data as string so it is printable."""
        return(self._raw_data.decode())


class Mcast:
    """Common class for search and listen multicast packages"""
    _open_timestamp = 0

    _MCAST_GRP = '239.255.255.250'
    _MCAST_PORT = 1900
    # If you increase the size of RECVBUF you have more time between
    # 'open' the connection and 'get' its data before buffer overflow
    _RECVBUF = 4096
    # _timeout = 0   no data to get
    # _timeout != 0  get data, value may be used for control
    _timeout = 0

    _sock = None


class Msearch(Mcast):
    """Class for active searching of devices"""

    def open(self):
        """Initialize and open a connection and join to the multicast group

        After 'open' the connection you should 'get' the data as soon as
        possible to avoid buffer overflow
        """
        global SEARCH_TIMEOUT

        self._open_timestamp = time()
        self._timeout = 1   # SEARCH_TIMEOUT
        _msg = \
            'M-SEARCH * HTTP/1.1\r\n' \
            'HOST: 239.255.255.250:1900\r\n' \
            'MAN: "ssdp:discover"\r\n' \
            'MX: ' + str(SEARCH_TIMEOUT) + '\r\n' \
            'ST: upnp:rootdevice\r\n' \
            '\r\n'

        # Set up UDP socket with timeout and send a M-SEARCH structure
        # to the upnp multicast address and port.
        # IP_MULTICAST_LOOP is enabled by default.
        # IP_MULTICAST_TTL is set to 1 by default.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                   socket.IPPROTO_UDP)
        self._sock.settimeout(self._timeout)
        self._sock.sendto(_msg.encode(), (self._MCAST_GRP, self._MCAST_PORT))

    def get(self):
        """Get next SSDP datagram from multicast net within the timeout

        This method returns a SSDPdatagram object that represents a received
        SSDP record from an upnp root device on the local netwwork.
        """
        if self._timeout == 0:
            return
        else:
            try:
                data, addr = self._sock.recvfrom(self._RECVBUF)
                if len(data) >= self._RECVBUF:
                    raise SystemExit("ERROR: receive buffer overflow")
                return(SSDPdatagram(addr, data))
            except socket.timeout:
                self._timeout = 0
                return


class Msearch_device(Msearch):
    """Search for the next device on the network.

    An active device on the network may response more than one time to improve
    reliability of stateless multicast. Here we are only intersted in devices,
    so we make them unique.
    """
    _oDatagram = None
    _device = None
    _devicelist = []

    def get(self):   # overload get() from parent
        while True:
            _oDatagram = Msearch.get(self)
            if _oDatagram is None:
                return
            _device = _oDatagram.addr + ' uuid:' +_oDatagram.uuid
            if _device not in self._devicelist:
                self._devicelist.append(_device)
                return(_device + ' ' + _oDatagram.server + '\r\n')


class Msearch_verbose(Msearch):
    def get(self):   # overload get() from parent
        Msearch.get(self)
        #return(str(self._oDatagram.addr) + ' ' + self._oDatagram.data)


class Listen(Mcast):
    """Passive listen for notifies from devices on the local network

    We are only listen to the upnp multicast group.
    """
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
                data, addr = self._sock.recvfrom(self._RECVBUF)
                if len(data) >= self._RECVBUF:
                    raise SystemExit("ERROR: receive buffer overflow")
                self._oDatagram = SSDPdatagram(addr, data)
            except KeyboardInterrupt:
                self._timeout = 0

    def get(self):
        """Listen for upnp datagrams on the local network."""
        self._get_datagram()
        if self._timeout == 0:
            return('')
        rel_time = self._oDatagram.timestamp - self._open_timestamp
        rel_time = "{:09.4f}".format(rel_time)
        device = self._oDatagram.id()
        return(rel_time + ' ' + self._oDatagram.ssdp_type + ' ' +
               self._oDatagram.addr + ' ' + device + '\r\n')


class Listen_default(Msearch):
    def get(self):   # overload get() from parent
        Msearch.get(self)
        return(str(self._oDatagram.addr) + ' ' + self._oDatagram.data)


def print_all(oMcast):
    """Search for upnp root devices on the local network.

    This is polymorphic execution and the result depends on the object that is
    given as parameter.
    """
    oMcast.open()
    datagram = oMcast.get()
    while datagram is not None:
        print(datagram, end='', flush=True)
        datagram = oMcast.get()


def main():
    """Discover UPnP devices on the local network"""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--listen", action="store_true",
                       help="passive listen for notifies from devices")
    group.add_argument("-s", "--search", action="store_true",
                       help="active search for UPnP devices")
    group.add_argument("-S", "--verbose_search", action="store_true",
                       help="active search for UPnP devices")
    group.add_argument("-v", "--version", action="store_true",
                       help="show program version")
    args = parser.parse_args()
    if args.search:
        print_all(Msearch_device())
    elif args.verbose_search:
        print_all(Msearch_verbose())
    elif args.listen:
        print_all(Listen())
    elif args.version:
        print("version 0.1")
    elif args.verbose_search:
        print("")
    else:
        print_all(Msearch_device())


if __name__ == '__main__':
    main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
