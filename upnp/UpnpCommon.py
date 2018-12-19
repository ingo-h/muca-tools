
"""This are common used definitions and statements for the upnp package."""

import re
from time import time


class SSDPdatagram:
    """This class represents a SSDP datagram received from a MSEARCH request.

    It contains the raw datagram as received so we can always extract available
    information. There are also some prepared often used parameter like a
    timestamp when the datagram was fetched, network address from the sending
    host, unique identifier of the device and some more.
    """
    timestamp = 0
    ipaddr = ''
    port = '0'
    method = ''
    request = 0
    # and additional dynamic created properties from header names in datagram

    _raw_data = None    # raw received datagram

    def __init__(self, addr=('', 0), raw_data=None):
        """The constructor prepairs raw data representing a SSDP datagram."""
        self.timestamp = time()
        self._raw_data = raw_data
        self.ipaddr = addr[0]
        self.port = '' if addr[1] == 0 else str(addr[1])

        # Here we split the datagram for the network into lines and tranform
        # its fields into properties, for example this line:
        # 'SERVER: Linux/3.10.54 UPnP/1.0 Cling/2.0'
        # gets property: server with value: Linux/3.10.54 UPnP/1.0 Cling/2.0
        # To conform to property names there has to be taken some replacements.
        if raw_data is None:
            return
        lines = self.data.splitlines()
        parts = lines[0].partition(' * HTTP')
        if parts[1] != '':
            self.method = parts[0]
        for line in enumerate(lines, 1):
            parts = line[1].partition(':')
            if parts[1] != '':
                propname = parts[0].lower().strip()
                propname = re.sub(r"([^a-z0-9_])", r"_", propname)
                propname = re.sub(r"(^[0-9_])", r"x\1", propname)
                setattr(self, propname, parts[2].strip())
        if hasattr(self, 'usn'):
            self.uuid = self.usn.partition('uuid:')[2].partition('::')[0]

    @property
    def data(self):
        """This returns the decoded raw data as string so it is printable."""
        if self._raw_data is None:
            return
        return self._raw_data.decode()

    def fdevice(self, base_time=0, verbose=False):
        """This returns a formated device pattern ready for printing."""
        _rel_time = self.timestamp - base_time
        if base_time == 0 or _rel_time <= 0:
            _rel_time = '0000.0000s'
        else:
            _rel_time = '{:09.4f}s'.format(_rel_time)
        _ipaddr = ' ' + self.ipaddr if self.ipaddr != '' else ''
        _port = ':' + self.port if self.port != '' else ''

        if verbose:
            if self.data is None:
                return '{} {}{}{}\r\n'.format(
                    _rel_time, self.request, _ipaddr, _port)
            else:
                return '{} {}{}{}\r\n{}'.format(
                    _rel_time, self.request, _ipaddr, _port, self.data)
        else:
            _method = ' ' + self.method if self.method != '' else ''
            if self.data is None:
                return '{} {}{}{}{}\r\n'.format(
                    _rel_time, self.request, _method, _ipaddr, _port)
            else:
                _uuid = ' uuid:' + self.uuid if hasattr(self, 'uuid') else ''
                _server = ' ' + self.server if hasattr(self, 'server') else ''
                return '{} {}{}{}{}{}{}\r\n'.format(
                    _rel_time, self.request, _method, _ipaddr, _port, _uuid,
                    _server)


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

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
