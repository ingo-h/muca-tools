#!/usr/bin/env python3
"""Tests for upnpsearch"""

from unittest import TestCase, mock
import socket
from time import time

from upnp.upnpsearch import SSDPdatagram, Msearch, MsearchDevice


class UpnpsearchTestCase(TestCase):
    """These are tests for upnpsearch.

    The program opens an UDP socket and gets a data stream from the local
    network. Because of its time consuming dynamic nature this cannot be
    tested. So we mock the whole builtin socket class and set the test
    conditions.
    """
    # three ssdp datagram as test pattern
    addr1 = ('192.168.10.119', 47383)
    datagram1 = (
        b"HTTP/1.1 200 OK\r\n"
        b"CACHE-CONTROL: max-age=1800\r\n"
        b"DATE: Sun, 23 Sep 2018 17:08:38 GMT\r\n"
        b"EXT:\r\n"
        b"LOCATION: http://192.168.10.119:8008/ssdp/device-desc.xml\r\n"
        b'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\r\n'
        b"01-NLS: d2631d76-1dd1-11b2-9c2f-ee4373b37081\r\n"
        b"SERVER: Linux/3.10.79, UPnP/1.0, Portable SDK for UPnP "
        b"devices/1.6.18\r\n"
        b"X-User-Agent: redsonic\r\n"
        b"ST: upnp:rootdevice\r\n"
        b"USN: uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277::upnp:rootdevice\r\n"
        b"BOOTID.UPNP.ORG: 0\r\n"
        b"CONFIGID.UPNP.ORG: 1\r\n"
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

    addr3 = ('192.168.10.3', 1900)
    datagram3 = (
        b"HTTP/1.1 200 OK\r\n"
        b"LOCATION: http://192.168.10.3:49000/fboxdesc.xml\r\n"
        b"SERVER: fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01\r\n"
        b"CACHE-CONTROL: max-age=1800\r\n"
        b"EXT:\r\n"
        b"ST: upnp:rootdevice\r\n"
        b"USN: uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9::upnp:rootdevice\r\n"
        b"\r\n")

    def test_ssdp_datagram(self):
        """Test the structure of a SSDP datagram object."""
        o_datagram = SSDPdatagram(self.addr1, self.datagram1)
        self.assertAlmostEqual(o_datagram.timestamp, time(), 3)
        self.assertEqual(o_datagram.ipaddr, "192.168.10.119")
        self.assertEqual(o_datagram.port, "47383")
        self.assertEqual(o_datagram.uuid,
                         "3b2867a3-b55f-8e77-5ad8-a6d0c6990277")
        self.assertEqual(
            o_datagram.server,
            "Linux/3.10.79, UPnP/1.0, Portable SDK for UPnP devices/1.6.18")
        self.assertEqual(o_datagram.data, self.datagram1.decode())

    @mock.patch('upnp.upnpsearch.socket.socket')
    def test_msearch(self, mock_socket):
        """Test request() and get() from Msearch class with side effects."""
        inst_mock_socket = mock_socket.return_value
        inst_mock_socket.mock_add_spec(
            ['settimeout', 'sendto', 'recvfrom'], spec_set=True
        )
        o_msearch = Msearch()
        o_msearch.request()
        mock_socket.assert_called_with(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        inst_mock_socket.recvfrom.return_value = self.datagram1, self.addr1
        o_datagram = o_msearch.get()
        inst_mock_socket.settimeout.assert_called_with(3)
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 1)
        self.assertIsInstance(o_datagram, SSDPdatagram)
        self.assertEqual(o_datagram.uuid,
                         "3b2867a3-b55f-8e77-5ad8-a6d0c6990277")

        o_msearch.RECVBUF = 128
        with self.assertRaises(SystemExit) as sysex:
            o_datagram = o_msearch.get()
            self.assertEqual(sysex.exception, "ERROR: receive buffer overflow")

        inst_mock_socket.recvfrom.side_effect = socket.timeout()
        o_datagram = o_msearch.get()
        self.assertIsNone(o_datagram)
        o_datagram = o_msearch.get()
        self.assertIsNone(o_datagram)
        inst_mock_socket.reset_mock()

    @mock.patch('upnp.upnpsearch.socket.socket')
    def test_msearch_device(self, mock_socket):
        """Test Msearch devices."""
        inst_mock_socket = mock_socket.return_value
        inst_mock_socket.mock_add_spec(
            ['settimeout', 'sendto', 'recvfrom'], spec_set=True
        )
        o_msearch_device = MsearchDevice()
        result = o_msearch_device.get()
        self.assertIsNone(result)
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 0)
        o_msearch_device.request(retries=-1)
        result = o_msearch_device.get()
        self.assertIsNone(result)
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 0)
        o_msearch_device.request(retries=0)
        result = o_msearch_device.get()
        self.assertIsNone(result)
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 0)

        inst_mock_socket.recvfrom.side_effect = [
            (self.datagram1, self.addr1),
            socket.timeout(),
            (self.datagram2, self.addr2)
        ]
        o_msearch_device.request(retries=1)
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, (
            r"0000\.00\d\ds 1 192\.168\.10\.119 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n"))
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, r'0000\.00..s\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 2)
        self.assertIsNone(result)

        inst_mock_socket.recvfrom.side_effect = [
            (self.datagram1, self.addr1),
            socket.timeout(),
            (self.datagram2, self.addr2),
            (self.datagram1, self.addr1),
            socket.timeout()
        ]
        o_msearch_device.request(retries=2)
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result, (
            r"0000\.00\d\ds 1 192\.168\.10\.119 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n"))
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 4)
        self.assertRegex(result, r'0000\.00..s 2\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 5)
        self.assertRegex(result, (
            r"0000\.00\d\ds 2 192\.168\.49\.1 "
            r"uuid:f48c8d92-c3c0-6f29-0000-00004e74db48 "
            r"Linux/3\.10\.54 UPnP/1\.0 Cling/2\.0\r\n"))
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 7)
        self.assertRegex(result, r'0000\.00..s\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 7)
        self.assertIsNone(result)

        inst_mock_socket.recvfrom.side_effect = [
            socket.timeout(),
            (self.datagram1, self.addr1),
            (self.datagram2, self.addr2),
            (self.datagram1, self.addr1),
            (self.datagram1, self.addr1),
            (self.datagram2, self.addr2),
            (self.datagram3, self.addr3),
            socket.timeout(),
            socket.timeout()
        ]
        o_msearch_device.request(retries=3)
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 8)
        self.assertRegex(result, r'0000\.00\d\ds 2\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 9)
        self.assertRegex(result, (
            r"0000\.00\d\ds 2 192\.168\.10\.119 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n"))
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 10)
        self.assertRegex(result, (
            r"0000\.00\d\ds 2 192\.168\.49\.1 "
            r"uuid:f48c8d92-c3c0-6f29-0000-00004e74db48 "
            r"Linux/3\.10\.54 UPnP/1\.0 Cling/2\.0\r\n"))
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 14)
        self.assertRegex(result, (
            r"0000\.00\d\ds 2 192\.168\.10\.3 "
            r"uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9 "
            r"fritz-box UPnP/1\.0 AVM FRITZ!Box 7490 113\.07\.01\r\n"))
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 15)
        self.assertRegex(result, r'0000\.00\d\ds 3\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 16)
        self.assertRegex(result, r'0000\.00\d\ds\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 16)
        self.assertIsNone(result)

        inst_mock_socket.recvfrom.side_effect = [
            socket.timeout(),
            socket.timeout(),
            (self.datagram1, self.addr1),
            socket.timeout(),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice(verbose=True)
        o_msearch_device.request(retries=4)
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 17)
        self.assertRegex(result, r'0000\.00\d\ds 2\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 18)
        self.assertRegex(result, r'0000\.00\d\ds 3\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 19)
        result = result.partition(r's 3 192.168.10.119 ')
        self.assertRegex(result[0], r'0000\.00\d\d')
        self.assertEqual(result[2], self.datagram1.decode())
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 20)
        self.assertRegex(result, r'0000\.00\d\ds 4\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 21)
        self.assertRegex(result, r'0000\.00\d\ds\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 21)
        self.assertIsNone(result)

        inst_mock_socket.recvfrom.side_effect = [
            socket.timeout(),
            socket.timeout(),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice()
        o_msearch_device.request(retries=3)
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 22)
        self.assertRegex(result, r'0000\.00\d\ds 2\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 23)
        self.assertRegex(result, r'0000\.00\d\ds 3\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 24)
        self.assertRegex(result, r'0000\.00\d\ds\r\n')
        result = o_msearch_device.get()
        self.assertEqual(inst_mock_socket.recvfrom.call_count, 24)
        self.assertIsNone(result)
