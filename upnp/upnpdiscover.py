"""module to discover UPnP devices

references:
[Multicast in Python](https://stackoverflow.com/q/603852/5014688)
[Multicast programming](https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
"""
import socket
import struct
from time import time
import argparse

VERSION = '0.1'
SEARCH_TIMEOUT = 10   # we need this global for unit test


class SSDPdatagram:
    """This class represents a SSDP datagram received from a MSEARCH request.

    It contains the raw datagram as received so we can always extract available
    information. There are also some prepared often used parameter like a
    timestamp when the datagram was fetched, network address from the sending
    host, unique identifier of the device and some more.
    """
    timestamp = 0
    ssdp_type = ''   # M-SEARCH, NOTIFY
    addr = ''
    # this are the needed fields with the same name from the replied datagram
    usn = ''   # contains also a uuid
    location = ''

    _raw_data = None    # raw received datagram

    def __init__(self, addr, raw_data):
        """The constructor prepairs raw data representing a SSDP datagram."""
        self.timestamp = time()
        self.addr = str(addr).replace(" ", "")
        self._raw_data = raw_data
        _data = self.data
        self.usn = _data.partition("USN: ")[2].partition("\r\n")[0]
        self.location = _data.partition("LOCATION: ")[2].partition("\r\n")[0]
        self.ssdp_type = _data.partition(" * ")[0]

    def id(self):
        """This returns the unique id of the datagram.

        The id consists of two parts from the datagram:
        - the URN consisting a uuid
        - the LOCATION that points to the SCPD xml file
        """
        return(self.usn + ' ' + self.location)

    @property
    def data(self):
        """This returns the decoded raw data as string so it is printable."""
        return(self._raw_data.decode())


class Mcast:
    """Common class for search and listen multicast packages"""
    # timeout = 0   no data to get
    # timeout > 0   get data, value may be used for control
    timeout = 0
    open_timestamp = 0

    _MCAST_GRP = '239.255.255.250'
    _MCAST_PORT = 1900
    # If you increase the size of RECVBUF you have more time between
    # 'open' the connection and 'get' its data before buffer overflow
    _RECVBUF = 4096

    _sock = None


class Msearch(Mcast):
    """Class for active searching of devices"""

    _devicelist = []
    _oDatagram = None

    def open(self):
        """Initialize and open a connection and join to the multicast group

        After 'open' the connection you should 'get' the data as soon as
        possible to avoid buffer overflow
        """
        global SEARCH_TIMEOUT

        self.open_timestamp = time()
        self.timeout = SEARCH_TIMEOUT
        _msg = \
            'M-SEARCH * HTTP/1.1\r\n' \
            'HOST:239.255.255.250:1900\r\n' \
            'ST:upnp:rootdevice\r\n' \
            'MX:' + str(self.timeout) + '\r\n' \
            'MAN:"ssdp:discover"\r\n' \
            '\r\n'

        # Set up UDP socket with timeout and send a M-SEARCH structure
        # to the upnp multicast address and port.
        # IP_MULTICAST_LOOP is enabled by default.
        # IP_MULTICAST_TTL is set to 1 by default.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                   socket.IPPROTO_UDP)
        self._sock.settimeout(self.timeout)
        self._sock.sendto(_msg.encode(), (self._MCAST_GRP, self._MCAST_PORT))

    def _get_datagram(self):
        """Get next SSDP datagram from multicast net within the timeout

        This method returns a SSDPdatagram object that represents a received
        SSDP record from an upnp root device on the local netwwork.
        """
        if self.timeout != 0:
            try:
                data, addr = self._sock.recvfrom(self._RECVBUF)
                if len(data) >= self._RECVBUF:
                    raise SystemExit("ERROR: receive buffer overflow")
                self._oDatagram = SSDPdatagram(addr, data)
            except socket.timeout:
                self.timeout = 0

    def get(self):
        """Process SSDP datagram object

        If we get replies with same USN (included uuid) and LOCATION we make
        it unique.
        """
        while True:
            self._get_datagram()
            # ._get_datagram() waits until it has data received, so if we
            # return from a timeout exception we have to check timeout
            if self.timeout == 0:
                return('')
            device = self._oDatagram.id()
            if device not in self._devicelist:
                self._devicelist.append(device)
                return(device + '\r\n')


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

        self.open_timestamp = time()
        self.timeout = -1
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
        if self.timeout != 0:
            try:
                data, addr = self._sock.recvfrom(self._RECVBUF)
                if len(data) >= self._RECVBUF:
                    raise SystemExit("ERROR: receive buffer overflow")
                self._oDatagram = SSDPdatagram(addr, data)
            except KeyboardInterrupt:
                self.timeout = 0

    def get(self):
        """Listen for upnp datagrams on the local network."""
        self._get_datagram()
        if self.timeout == 0:
            return('')
        rel_time = self._oDatagram.timestamp - self.open_timestamp
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
    while oMcast.timeout != 0:
        print(oMcast.get(), end='', flush=True)


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
        print_all(Msearch())
    elif args.verbose_search:
        print_all(Msearch_verbose())
    elif args.listen:
        print_all(Listen())
    elif args.version:
        print("version 0.1")
    elif args.verbose:
        print("")
    else:
        msearch()


if __name__ == '__main__':
    main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
