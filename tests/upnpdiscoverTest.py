#!/usr/bin/env python3
"""Tests for upnpdiscover"""

from unittest import TestCase, mock
from time import time

import upnp
from upnp.upnpdiscover import SSDPdatagram, Msearch, Msearch_device

addr1 = ('192.168.10.3', 1900)
datagram1 = (
    b"HTTP/1.1 200 OK\r\n"
    b"LOCATION: http://192.168.10.3:49000/fboxdesc.xml\r\n"
    b"SERVER: fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01\r\n"
    b"CACHE-CONTROL: max-age=1800\r\n"
    b"EXT:\r\n"
    b"ST: upnp:rootdevice\r\n"
    b"USN: uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9::upnp:rootdevice\r\n"
    b"\r\n")

addr2 = ('192.168.49.1', 34731)
datagram2 = (
    b"HTTP/1.1 200 OK\r\n"
    b"USN: uuid:f48c8d92-c3c0-6f29-0000-00004e74db48::upnp:rootdevice\r\n"
    b"CACHE-CONTROL: max-age=1800\r\n"
    b"EXT:\r\n"
    b"ST: upnp:rootdevice\r\n"
    b"LOCATION: http://192.168.10.107:41947/"
    b"upnp/dev/f48c8d92-c3c0-6f29-0000-00004e74db48/desc\r\n"
    b"SERVER: Linux/3.10.54 UPnP/1.0 Cling/2.0\r\n"
    b"\r\n")

addr3 = ('192.168.10.119', 47383)
datagram3 = (
    b"HTTP/1.1 200 OK\r\n"
    b"CACHE-CONTROL: max-age=1800\r\n"
    b"DATE: Sun, 23 Sep 2018 17:08:38 GMT\r\n"
    b"EXT:\r\n"
    b"LOCATION: http://192.168.10.119:8008/ssdp/device-desc.xml\r\n"
    b'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\r\n'
    b"01-NLS: d2631d76-1dd1-11b2-9c2f-ee4373b37081\r\n"
    b"SERVER: Linux/3.10.79, UPnP/1.0, Portable SDK for UPnP devices/1.6.18"
    b"\r\n"
    b"X-User-Agent: redsonic\r\n"
    b"ST: upnp:rootdevice\r\n"
    b"USN: uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277::upnp:rootdevice\r\n"
    b"BOOTID.UPNP.ORG: 0\r\n"
    b"CONFIGID.UPNP.ORG: 1\r\n"
    b"\r\n")


class upnpdiscoverTestCase(TestCase):
    """These are tests for upnpdiscover search and listen.

    The program opens an UDP socket and gets a data stream from the local
    network. Because of its time consuming dynamic nature this cannot be
    tested. So we have to patch methods 'open' and 'get' to have a constant
    test environment.
    """
    def test_SSDPdatagram(self):
        """Test the structure of a SSDP datagram object"""
        oDatagram = SSDPdatagram(addr1, datagram1)
        self.assertAlmostEqual(oDatagram.timestamp, time(), 3)
        self.assertEqual(oDatagram.addr, "192.168.10.3:1900" )
        self.assertEqual(oDatagram.uuid, "123402409-bccb-40e7-8e6c-3481C4FC71A9" )
        self.assertEqual(oDatagram.server, "fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01" )

    @mock.patch('upnp.upnpdiscover.Msearch')
    def test_msearch(self, mock_Msearch):
        """Mock Msearch to return a datagram."""
        mock_Msearch.return_value.get.return_value = \
            upnp.upnpdiscover.SSDPdatagram(addr1, datagram1)
        oMsearch = upnp.upnpdiscover.Msearch()
        result = oMsearch.get()
        self.assertIsInstance(result, SSDPdatagram)

    @mock.patch.object(Msearch, 'get')
    def test_msearch_device(self, mock_get):
        """Test device identifier

        An active device on the network may response more than one time to
        improve reliability of stateless multicast. This test checks its
        correct identifier. It is also test if the same device is only listed
        one time.
        """
        mock_get.side_effect = [
            SSDPdatagram(addr1, datagram1),
            SSDPdatagram(addr2, datagram2),
            SSDPdatagram(addr1, datagram1),
            SSDPdatagram(addr2, datagram2),
            SSDPdatagram(addr3, datagram3),
            SSDPdatagram(addr1, datagram1),
            SSDPdatagram(addr1, datagram1),
            None
            ]
        oMsearch_device = Msearch_device()
        result = oMsearch_device.get()
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(result, (
            "192.168.10.3:1900 uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9 "
            "fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01\r\n"
            )
        )
        result = oMsearch_device.get()
        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(result, (
            "192.168.49.1:34731 uuid:f48c8d92-c3c0-6f29-0000-00004e74db48 "
            "Linux/3.10.54 UPnP/1.0 Cling/2.0\r\n"
            )
        )
        result = oMsearch_device.get()
        self.assertEqual(mock_get.call_count, 5)
        self.assertEqual(result, (
            "192.168.10.119:47383 uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            "Linux/3.10.79, UPnP/1.0, Portable SDK for UPnP devices/1.6.18\r\n"
            )
        )
        result = oMsearch_device.get()
        self.assertEqual(mock_get.call_count, 8)
        self.assertIsNone(result)
