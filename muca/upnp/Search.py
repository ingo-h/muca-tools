"""Module to search for UPnP devices."""

import socket
import argparse
from time import time

from muca.Common import build
from muca.upnp.Common import SSDPdatagram, Mcast


class Msearch(Mcast):
    """Class for active searching of devices.

    references for network socket programming:
    [Multicast in Python](https://stackoverflow.com/q/603852/5014688)
    [Multicast programming](https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
    """
    _timestamp_request = 0

    def __init__(self):
        """Open a UDP network connection. """
        # Set up UDP socket with timeout and send a M-SEARCH structure
        # to the upnp multicast address and port.
        # IP_MULTICAST_LOOP is enabled by default.
        # IP_MULTICAST_TTL is set to 1 by default.
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                   socket.IPPROTO_UDP)

    def request(self, ssdp_response_time=2):
        """Request for root devices on the upnp multicast channel.

        After 'request' you should 'get' the data as soon as possible to avoid
        buffer overflow.
        """
        self._timestamp_request = time()
        self._response_time = ssdp_response_time
        _msg = \
            'M-SEARCH * HTTP/1.1\r\n' \
            'HOST: 239.255.255.250:1900\r\n' \
            'MAN: "ssdp:discover"\r\n' \
            'MX: ' + str(self._response_time) + '\r\n' \
            'ST: upnp:rootdevice\r\n' \
            '\r\n'
        self._sock.sendto(_msg.encode(), (self._MCAST_GRP, self._MCAST_PORT))

    def get(self):
        """Get next SSDP datagram from multicast net within a timeout.

        This method returns a SSDPdatagram object that represents a received
        SSDP record from an upnp root device on the local netwwork. A call
        returns only when a datagram has received or when the timeout has
        expired. The timeout is the given response time for the devices (plus a
        small network delay).
        """
        if self._response_time == 0:
            return
        else:
            try:
                # The timeout (in sec) for the socket is reduced after every
                # received data so the over all transfer has finished after the
                # given response time (plus a small network delay added).
                _tout = int(round(
                    self._response_time \
                    - (time() - self._timestamp_request))) \
                    + 1
                self._sock.settimeout(_tout)
                data, addr = self._sock.recvfrom(self.RECVBUF)
                if len(data) >= self.RECVBUF:
                    raise SystemExit("ERROR: receive buffer overflow")
                return SSDPdatagram(addr, data)
            except socket.timeout:
                self._response_time = 0
                return


class MsearchDevice(Msearch):
    """Search for the next device on the network.

    Because of stateless communication of multicast it may be possible that
    requests are lost. To improve reliability requests are send more than one
    time. Most devices will response on every request but we make the responses
    unique. Only the first response is reported.
    """
    _timestamp_first_request = 0
    _devicelist = []
    _count = -1
    _retry = 0
    _verbose = False

    def __init__(self, verbose=False):
        """Setup verbose output if requested."""
        super().__init__()
        self._verbose = verbose

    def request(self, retries=3):
        """Send a request for upnp root devices.

        Arguments: retries = number of requests to send
        Returns: None
        """
        if retries > 0:
            self._timestamp_first_request = time()
            self._devicelist = []
            self._count = retries
            super().request()
            self._retry = 1

    def get(self):   # overload get() from parent
        """Get the next response from the network.

        Arguments: None
        Returns: a received datagram, may be empty only with time and retry
        number.
        """
        if self._count < 0:
            return

        while True:
            _o_datagram = super().get()
            if _o_datagram is None:
                self._count -= 1
                _o_dummy_datagram = SSDPdatagram()
                if self._count > 0:
                    super().request()
                    self._retry += 1
                    _o_dummy_datagram.request = self._retry
                    #return _rel_time + 's ' + str(self._retry) + '\r\n'
                else:
                    self._count = -1
                    _o_dummy_datagram.request = 0
                    #return _rel_time + 's ' + '0' + '\r\n'
                return _o_dummy_datagram.fdevice(
                    base_time=self._timestamp_first_request)
            else:
                _device = _o_datagram.ipaddr + ' ' +_o_datagram.uuid
                if _device not in self._devicelist:
                    self._devicelist.append(_device)
                    _o_datagram.request = self._retry
                    return _o_datagram.fdevice(
                        base_time=self._timestamp_first_request,
                        verbose=self._verbose)

def print_it(o_mcast):
    """Search for upnp root devices on the local network and print them.

    This is polymorphic execution and the result depends on the object that is
    given as argument.
    Arguments: search object
    Returns: None
    Output: print datagrams
    """
    o_mcast.request()
    datagram = o_mcast.get()
    while datagram is not None:
        print(datagram, end='', flush=True)
        datagram = o_mcast.get()


def main():
    """This is the entry point of the program and the command line parser"""
    parser = argparse.ArgumentParser(
        description='Active scan three times for UPnP devices')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="verbose active search for UPnP devices")
    group.add_argument("-V", "--version", action="store_true",
                       help="show program version")
    args = parser.parse_args()
    if args.verbose:
        print_it(MsearchDevice(verbose=True))
    elif args.version:
        print("Build", build())
    else:
        print_it(MsearchDevice())


if __name__ == '__main__':
    main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
