#!/usr/bin/env python3
"""Module to search for UPnP devices."""
import socket
from time import time
import argparse

BUILD = '1'


class SSDPdatagram:
    """This class represents a SSDP datagram received from a MSEARCH request.

    It contains the raw datagram as received so we can always extract available
    information. There are also some prepared often used parameter like a
    timestamp when the datagram was fetched, network address from the sending
    host, unique identifier of the device and some more.
    """
    timestamp = 0
    uuid = ''
    ipaddr = ''
    port = ''
    server = ''

    _raw_data = None    # raw received datagram

    def __init__(self, arg_addr, arg_raw_data):
        """The constructor prepairs raw data representing a SSDP datagram."""
        self._raw_data = arg_raw_data
        self.timestamp = time()
        _addr = str(arg_addr).partition("', ")
        self.ipaddr = _addr[0].replace("('", "")
        self.port = _addr[2].replace(")", "")
        _data = self.data
        self.uuid = _data.partition("USN: uuid:")[2].partition("::")[0]
        self.server = _data.partition("SERVER: ")[2].partition("\r\n")[0]

    @property
    def data(self):
        """This returns the decoded raw data as string so it is printable."""
        return self._raw_data.decode()


class Mcast:
    """Common class for search and listen multicast packages."""
    # If you increase the size of RECVBUF you have more time between
    # 'open' the connection and 'get' its data before buffer overflow
    RECVBUF = 4096
    # Response time, also given to the network devices within the request
    # datagram. Devices on the network must response within this time.
    # _response_time = 0   no data to get
    # _response_time != 0  get data, value may be used for control
    _response_time = 0
    _MCAST_GRP = '239.255.255.250'
    _MCAST_PORT = 1900

    _sock = None


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

    def request(self, arg_timeout=2):
        """Request for root devices on the upnp multicast channel.

        After 'request' you should 'get' the data as soon as possible to avoid
        buffer overflow.
        """
        self._timestamp_request = time()
        self._response_time = arg_timeout
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
    class Device():
        """Class to store device data and format output."""
        timestamp = 0
        request = 0
        data = None
        _timestamp_init = 0

        def __init__(self):
            self._timestamp_init = time()

        def __call__(self):
            _rel_time = self.timestamp - self._timestamp_init
            _rel_time = "{:09.4f}".format(_rel_time)
            if self.request == 0:
                return _rel_time + 's\r\n'
            if self.data is None:
                return _rel_time + 's ' + str(self.request) + '\r\n'
            return _rel_time + 's ' + str(self.request) + ' ' + self.data


    _o_device = None
    _devicelist = []
    _count = -1
    _verbose = False

    def __init__(self, verbose=False):
        """Setup verbose output if requested."""
        self._verbose = verbose
        super().__init__()

    def request(self, retries=3):
        """Send a request for upnp root devices.

        Arguments: retries = number of requests to send
        Returns: None
        """
        self._o_device = self.Device()
        self._devicelist = []
        if retries > 0:
            self._count = retries
            super().request()
            self._o_device.timestamp = time()
            self._o_device.request = 1

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
                if self._count > 0:
                    super().request()
                    self._o_device.timestamp = time()
                    self._o_device.request += 1
                    self._o_device.data = None
                    #return _rel_time + 's ' + str(self._retry) + '\r\n'
                    return self._o_device()
                else:
                    self._count = -1
                    self._o_device.timestamp = time()
                    self._o_device.request = 0
                    self._o_device.data = None
                    #return _rel_time + 's\r\n'
                    return self._o_device()
            else:
                _device = _o_datagram.ipaddr + ' uuid:' +_o_datagram.uuid
                if _device not in self._devicelist:
                    self._devicelist.append(_device)
                    self._o_device.timestamp = _o_datagram.timestamp
                    if self._verbose:
                        #return _rel_time + 's ' + str(self._retry) + ' ' \
                        #       + _o_datagram.data
                        self._o_device.data = _o_datagram.ipaddr + ' ' \
                                             + _o_datagram.data
                        return self._o_device()
                    #return _rel_time + 's ' + str(self._retry) + ' ' \
                    #       + _device + ' ' + _o_datagram.server + '\r\n'
                    self._o_device.data = _device + ' ' + _o_datagram.server \
                                         + '\r\n'
                    return self._o_device()


def print_it(o_mcast):
    """Search for upnp root devices on the local network and print them.

    This is polymorphic execution and the result depends on the object that is
    given as argument.
    Arguments: search object
    Returns: None
    Output: print datagram
    """
    o_mcast.request()
    datagram = o_mcast.get()
    while datagram is not None:
        print(datagram, end='', flush=True)
        datagram = o_mcast.get()


def main():
    """This is the entry point of the program and the command line parser"""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true",
                       help="verbose output")
    group.add_argument("-V", "--version", action="store_true",
                       help="show program version")
    args = parser.parse_args()
    if args.verbose:
        print_it(MsearchDevice(verbose=True))
    elif args.version:
        print("Build", BUILD)
    else:
        print_it(MsearchDevice())


if __name__ == '__main__':
    main()

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
