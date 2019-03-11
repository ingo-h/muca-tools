"""Tests for the upnpsearch program.

This are in general tests for the program but mainly for testing the network
socket connection to send and receive upnp datagram. Because these tests are
time consuming we mock the builtin network socket object for all tests in the
test case within self.setUp().
"""
from unittest import TestCase, mock
from io import StringIO
import socket

from muca.upnp.Common import SSDPdatagram
from muca.upnp.Search import Msearch, MsearchDevice, print_it, \
                            socket as upnpsearch_sock
from tests.CommonTest import SDATAGRAM1, SDATAGRAM2, SDATAGRAM3, \
                             SADDR1, SADDR2, SADDR3


REQUEST = \
    b'M-SEARCH * HTTP/1.1\r\n' \
    b'HOST: 239.255.255.250:1900\r\n' \
    b'MAN: "ssdp:discover"\r\n' \
    b'MX: 2\r\n' \
    b'ST: upnp:rootdevice\r\n' \
    b'\r\n'


class NetSocketTestCase(TestCase):
    """These are tests using the network socket.

    The program opens an UDP socket and gets a data stream from the local
    network. Because of its time consuming dynamic nature this cannot be
    tested. So we mock the whole builtin socket class and set the test
    conditions.
    """
    def setUp(self):
        """This patches the network socket from upnpsearch for all tests."""
        patcher = mock.patch('muca.upnp.Search.socket.socket')
        self.addCleanup(patcher.stop)
        self.mock_socket = patcher.start()
        self.o_mock_socket = self.mock_socket.return_value
        self.o_mock_socket.mock_add_spec(
            ['settimeout', 'sendto', 'recvfrom'], spec_set=True)

    def test_mock_socket(self):
        """Test if general patch from self.setUp() for all tests is working."""
        self.assertIs(upnpsearch_sock.socket, self.mock_socket)
        o_socket = upnpsearch_sock.socket()
        self.assertIs(self.o_mock_socket, o_socket)

    def test1_msearch(self):
        """Test request() and get() from Msearch class with side effects."""
        o_msearch = Msearch()
        self.mock_socket.assert_called_with(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        o_msearch.request()
        self.o_mock_socket.sendto.assert_called_with(
            REQUEST, ('239.255.255.250', 1900))

        self.o_mock_socket.recvfrom.return_value = SDATAGRAM1, SADDR1
        o_datagram = o_msearch.get()
        self.o_mock_socket.settimeout.assert_called_with(3)
        self.assertEqual(self.o_mock_socket.settimeout.call_count, 1)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertIsInstance(o_datagram, SSDPdatagram)
        self.assertEqual(o_datagram.uuid,
                         "3b2867a3-b55f-8e77-5ad8-a6d0c6990277")

        o_msearch.RECVBUF = 128
        with self.assertRaises(SystemExit) as sysex:
            o_datagram = o_msearch.get()
            self.assertEqual(sysex.exception, "ERROR: receive buffer overflow")

        self.assertEqual(self.o_mock_socket.settimeout.call_count, 2)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.o_mock_socket.recvfrom.side_effect = socket.timeout()
        o_datagram = o_msearch.get()
        self.assertEqual(self.o_mock_socket.settimeout.call_count, 3)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertIsNone(o_datagram)
        o_datagram = o_msearch.get()
        self.assertEqual(self.o_mock_socket.settimeout.call_count, 3)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertIsNone(o_datagram)

    def test2_msearch(self):
        """Test calling request() two times on same instance from Msearch."""
        o_msearch = Msearch()
        o_msearch.request()
        self.o_mock_socket.sendto.assert_called_with(
            REQUEST, ('239.255.255.250', 1900))
        self.o_mock_socket.recvfrom.return_value = SDATAGRAM1, SADDR1
        o_datagram = o_msearch.get()
        self.o_mock_socket.settimeout.assert_called_with(3)
        self.assertEqual(self.o_mock_socket.settimeout.call_count, 1)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertIsInstance(o_datagram, SSDPdatagram)
        self.assertEqual(o_datagram.uuid,
                         "3b2867a3-b55f-8e77-5ad8-a6d0c6990277")
        o_msearch.request()
        self.o_mock_socket.sendto.assert_called_with(
            REQUEST, ('239.255.255.250', 1900))
        o_datagram = o_msearch.get()
        self.o_mock_socket.settimeout.assert_called_with(3)
        self.assertEqual(self.o_mock_socket.settimeout.call_count, 2)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertIsInstance(o_datagram, SSDPdatagram)
        self.assertEqual(o_datagram.uuid,
                         "3b2867a3-b55f-8e77-5ad8-a6d0c6990277")

    def test1_msearch_device(self):
        """Test with no request and requests with negative and 0 retries."""
        o_msearch_device = MsearchDevice()
        result = o_msearch_device.get()
        self.assertIsNone(result)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 0)
        o_msearch_device.request(retries=-1)
        result = o_msearch_device.get()
        self.assertIsNone(result)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 0)
        o_msearch_device.request(retries=0)
        result = o_msearch_device.get()
        self.assertIsNone(result)
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 0)

    def test2_msearch_device(self):
        """Test with one request but subsequent pending data."""
        self.o_mock_socket.recvfrom.side_effect = [
            (SDATAGRAM1, SADDR1),
            socket.timeout(),
            (SDATAGRAM2, SADDR2)
        ]
        o_msearch_device = MsearchDevice()
        o_msearch_device.request(retries=1)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 1 192\.168\.10\.119:47383 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, r'^0000\.00..s 0\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertIsNone(result)

    def test3_msearch_device(self):
        """Test with two requests and data on each request."""
        self.o_mock_socket.recvfrom.side_effect = [
            (SDATAGRAM1, SADDR1),
            socket.timeout(),
            (SDATAGRAM2, SADDR2),
            (SDATAGRAM1, SADDR1),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice()
        o_msearch_device.request(retries=2)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 1 192\.168\.10\.119:47383 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, r'^0000\.00..s 2\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 2 192\.168\.49\.1:34731 "
            r"uuid:f48c8d92-c3c0-6f29-0000-00004e74db48 "
            r"Linux/3\.10\.54 UPnP/1\.0 Cling/2\.0\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 5)
        self.assertRegex(result, r'^0000\.00..s 0\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 5)
        self.assertIsNone(result)

    def test4_msearch_device(self):
        """Test with three requests, data only on second request."""
        self.o_mock_socket.recvfrom.side_effect = [
            socket.timeout(),
            (SDATAGRAM1, SADDR1),
            (SDATAGRAM2, SADDR2),
            (SDATAGRAM1, SADDR1),
            (SDATAGRAM1, SADDR1),
            (SDATAGRAM2, SADDR2),
            (SDATAGRAM3, SADDR3),
            socket.timeout(),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice()
        o_msearch_device.request(retries=3)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, r'^0000\.00\d\ds 2\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 2 192\.168\.10\.119:47383 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 2 192\.168\.49\.1:34731 "
            r"uuid:f48c8d92-c3c0-6f29-0000-00004e74db48 "
            r"Linux/3\.10\.54 UPnP/1\.0 Cling/2\.0\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 7)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 2 192\.168\.10\.3:1900 "
            r"uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9 "
            r"fritz-box UPnP/1\.0 AVM FRITZ!Box 7490 113\.07\.01\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 8)
        self.assertRegex(result, r'^0000\.00\d\ds 3\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 9)
        self.assertRegex(result, r'^0000\.00\d\ds 0\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 9)
        self.assertIsNone(result)

    def test5_msearch_device(self):
        """Test with four verbose requests, data only on third request."""
        self.o_mock_socket.recvfrom.side_effect = [
            socket.timeout(),
            socket.timeout(),
            (SDATAGRAM1, SADDR1),
            socket.timeout(),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice(verbose=True)
        o_msearch_device.request(retries=4)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, r'^0000\.00\d\ds 2\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, r'^0000\.00\d\ds 3\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result[:9], r'^0000\.00\d\d$$')
        self.assertEqual(result[9:], 's 3 192.168.10.119:47383\r\n'
                         + SDATAGRAM1.decode())
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertRegex(result, r'^0000\.00\d\ds 4\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 5)
        self.assertRegex(result, r'^0000\.00\d\ds 0\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 5)
        self.assertIsNone(result)

    def test6_msearch_device(self):
        """Test with three requests but no data."""
        self.o_mock_socket.recvfrom.side_effect = [
            socket.timeout(),
            socket.timeout(),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice()
        o_msearch_device.request(retries=3)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, r'^0000\.00\d\ds 2\r\n$')
        self.assertNotEqual(result[:9], '0000.0000')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, r'^0000\.00\d\ds 3\r\n$')
        self.assertNotEqual(result[:9], '0000.0000')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result, r'^0000\.00\d\ds 0\r\n$')
        self.assertNotEqual(result[:9], '0000.0000')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertIsNone(result)

    def test7_msearch_device(self):
        """Test with one request and then new one request getting same data."""
        self.o_mock_socket.recvfrom.side_effect = [
            (SDATAGRAM1, SADDR1),
            socket.timeout(),
            (SDATAGRAM1, SADDR1),
            socket.timeout()
        ]
        o_msearch_device = MsearchDevice()
        o_msearch_device.request(retries=1)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 1 192\.168\.10\.119:47383 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, r'^0000\.00\d\ds 0\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertIsNone(result)

        o_msearch_device.request(retries=1)
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result, (
            r"^0000\.0\d\d\ds 1 192\.168\.10\.119:47383 "
            r"uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 "
            r"Linux/3\.10\.79, UPnP/1\.0, Portable SDK for UPnP "
            r"devices/1\.6\.18\r\n$"))
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertRegex(result, r'^0000\.00\d\ds 0\r\n$')
        result = o_msearch_device.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertIsNone(result)

    def test_print_it(self):
        """Test if the output works."""
        # set three timeouts because default retries = 3
        self.o_mock_socket.recvfrom.side_effect = [
            (SDATAGRAM2, SADDR2),
            socket.timeout(),
            socket.timeout(),
            (SDATAGRAM3, SADDR3),
            socket.timeout()
        ]
        with mock.patch('sys.stdout', new=StringIO()) as fake_output:
            print_it(MsearchDevice())
            self.assertRegex(fake_output.getvalue(), (
                r"^0000\.0\d\d\ds 1 192\.168\.49\.1:34731 "
                r"uuid:f48c8d92-c3c0-6f29-0000-00004e74db48 "
                r"Linux/3\.10\.54 UPnP/1\.0 Cling/2\.0\r\n"
                r"0000\.0\d\d\ds 2\r\n"
                r"0000\.0\d\d\ds 3\r\n"
                r"0000\.0\d\d\ds 3 192\.168\.10\.3:1900 "
                r"uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9 "
                r"fritz-box UPnP/1\.0 AVM FRITZ!Box 7490 113\.07\.01\r\n"
                r"0000\.0\d\d\ds 0\r\n$"))

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
