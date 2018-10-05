#!/usr/bin/env python3
"""Tests for upnpdiscover"""

from unittest import TestCase, mock
import time

import upnp
#from upnp import upnpdiscover
#from upnp.upnpdiscover import SSDPdatagram, Msearch, Msearch_verbose

addr1 = ('192.168.49.1', 34731)
datagram1 = (
    "HTTP/1.1 200 OK\r\n"
    "USN: uuid:f48c8d92-c3c0-6f29-0000-00004e74db48::upnp:rootdevice\r\n"
    "CACHE-CONTROL: max-age=1800\r\n"
    "EXT:\r\n"
    "ST: upnp:rootdevice\r\n"
    "LOCATION: http://192.168.10.107:41947/"
    "upnp/dev/f48c8d92-c3c0-6f29-0000-00004e74db48/desc\r\n"
    "SERVER: Linux/3.10.54 UPnP/1.0 Cling/2.0\r\n"
    "\r\n")

addr2 = ('192.168.10.3', 1900)
datagram2 = (
    "HTTP/1.1 200 OK\r\n"
    "LOCATION: http://192.168.10.3:49000/fboxdesc.xml\r\n"
    "SERVER: fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01\r\n"
    "CACHE-CONTROL: max-age=1800\r\n"
    "EXT:\r\n"
    "ST: upnp:rootdevice\r\n"
    "USN: uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9::upnp:rootdevice\r\n"
    "\r\n")

addr3 = ('192.168.10.3', 1900)
datagram3 = (
    "HTTP/1.1 200 OK\r\n"
    "LOCATION: http://192.168.10.3:49000/fboxdesc.xml\r\n"
    "SERVER: fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01\r\n"
    "CACHE-CONTROL: max-age=1800\r\n"
    "EXT:\r\n"
    "ST: upnp:rootdevice\r\n"
    "USN: uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9::upnp:rootdevice\r\n"
    "\r\n")


class upnpdiscoverTestCase(TestCase):
    """This are tests for upnpdiscover search and listen.

    The program opens an UDP socket and gets a data stream from the local
    network. Because of its time consuming dynamic nature this cannot be
    tested. So we have to patch methods 'open' and 'get' to have a constant
    test environment.
    """
    @mock.patch('upnp.upnpdiscover.Msearch')
    def test_msearch(self, mock_Msearch):
        mock_Msearch.return_value.get.return_value = \
            upnp.upnpdiscover.SSDPdatagram(addr1, datagram1.encode())
        oMsearch = upnp.upnpdiscover.Msearch()
        result = oMsearch.get()
        self.assertIsInstance(result, upnp.upnpdiscover.SSDPdatagram)

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
