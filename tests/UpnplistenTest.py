"""Tests for the upnplisten program.

This are in general tests for the program but mainly for testing the network
socket connection to receive upnp datagram. Because these tests are time
consuming we mock the builtin network socket object for all tests in the test
case within self.setUp().
"""
from unittest import TestCase, mock
from io import StringIO
import socket

from upnp.upnplisten import Listen, print_it, socket as upnplisten_socket
from tests.CommonTest import LDATAGRAM1, LDATAGRAM2, LDATAGRAM3, \
                             LADDR1, LADDR2, LADDR3


# from upnp.upnplisten import argparse as upnplisten_argparse
#
# class UpnplistenTestCase(TestCase):
#    """Here we test units that do not need to mock network socket."""
#
#    @mock.patch('upnp.upnplisten.argparse.ArgumentParser', spec_set=True)
#    def test_argpare(self, mock_argparse):
#        """This tests the command line interpreter."""
#        Argparse = upnplisten_argparse.ArgumentParser
#        self.assertIs(Argparse, mock_argparse)
#        o_argparse = Argparse.return_value
#        self.assertIs(o_argparse, mock_argparse())
#        main()


class NetSocketTestCase(TestCase):
    """These are tests using the network socket.

    The program opens an UDP socket and gets a data stream from the local
    network. Because of its time consuming dynamic nature this cannot be
    tested. So we mock the whole builtin socket class and set the test
    conditions.
    """
    def setUp(self):
        """This patches the network socket from upnplisten for all tests."""
        patcher = mock.patch('upnp.upnplisten.socket.socket')
        self.addCleanup(patcher.stop)
        self.mock_socket = patcher.start()
        self.o_mock_socket = self.mock_socket.return_value
        self.o_mock_socket.mock_add_spec(
            ['setsockopt', 'bind', 'recvfrom'], spec_set=True)

    def test_mock_socket(self):
        """Test if general patch from self.setUp() for all tests is working."""
        self.assertIs(upnplisten_socket.socket, self.mock_socket)
        o_socket = upnplisten_socket.socket()
        self.assertIs(self.o_mock_socket, o_socket)

    def test_listen_open(self):
        """Test open() and get() from Listen class with side effects."""
        o_listen = Listen()
        o_listen.open()
        self.mock_socket.assert_called_with(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.o_mock_socket.bind.assert_called_with(('239.255.255.250', 1900))
        self.assertEqual(self.o_mock_socket.setsockopt.call_count, 2)
        self.o_mock_socket.setsockopt.assert_called_with(0, 35, (
            b'\xef\xff\xff\xfa\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x00'))

    def test1_listen_get(self):
        """Test to listen for upnp datagrams on the local network."""
        self.o_mock_socket.recvfrom.side_effect = [
            (LDATAGRAM1, LADDR1),
            (LDATAGRAM2, LADDR2),
            (LDATAGRAM3, LADDR3),
            KeyboardInterrupt()
        ]
        o_listen = Listen()
        o_listen.open()
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, (
            r'^0000\.0\d\d\ds 0 NOTIFY 192\.168\.10\.86:57535 '
            r'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d Linux/4\.14\.71-v7\+, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.19\+git20160116'
            r'\r\n$'))
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, (r'^0000.0\d\d\ds 0 M-SEARCH '
                                  r'192\.168\.10\.3:57509\r\n$'))
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result, (
            r'^0000\.0\d\d\ds 0 NOTIFY 192\.168\.10\.75:42047 '
            r'uuid:231179de-90e9-11e8-b505-4355ee6fa7cf Linux/4\.14\.70-v7\+, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.19\+git20160116'
            r'\r\n$'))
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertIsNone(result)
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertIsNone(result)

    def test2_listen_get(self):
        """Test to verbose listen for upnp datagrams on the local network."""
        self.o_mock_socket.recvfrom.side_effect = [
            (LDATAGRAM1, LADDR1),
            (LDATAGRAM2, LADDR2),
            (LDATAGRAM3, LADDR3),
            KeyboardInterrupt()
        ]
        o_listen = Listen(verbose=True)
        o_listen.open()
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result[:9], r'^0000\.0\d\d\d$')
        self.assertEqual(result[9:], 's 0 192.168.10.86:57535\r\n'
                         + LDATAGRAM1.decode())
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result[:9], r'^0000\.0\d\d\d$')
        self.assertEqual(result[9:], 's 0 192.168.10.3:57509\r\n'
                         + LDATAGRAM2.decode())
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertRegex(result[:9], r'^0000\.0\d\d\d$')
        self.assertEqual(result[9:], 's 0 192.168.10.75:42047\r\n'
                         + LDATAGRAM3.decode())
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertIsNone(result)
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 4)
        self.assertIsNone(result)

    def test3_listen_get(self):
        """Test to open the same instance two times."""
        self.o_mock_socket.recvfrom.side_effect = [
            (LDATAGRAM1, LADDR1),
            (LDATAGRAM1, LADDR1),
            KeyboardInterrupt()
        ]
        o_listen = Listen()
        o_listen.open()
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 1)
        self.assertRegex(result, (
            r'^0000\.0\d\d\ds 0 NOTIFY 192\.168\.10\.86:57535 '
            r'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d Linux/4\.14\.71-v7\+, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.19\+git20160116'
            r'\r\n$'))
        o_listen.open()
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 2)
        self.assertRegex(result, (
            r'^0000\.0\d\d\ds 0 NOTIFY 192\.168\.10\.86:57535 '
            r'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d Linux/4\.14\.71-v7\+, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.19\+git20160116'
            r'\r\n$'))
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertIsNone(result)
        result = o_listen.get()
        self.assertEqual(self.o_mock_socket.recvfrom.call_count, 3)
        self.assertIsNone(result)

    def test_print_it(self):
        """Test if the output works."""
        self.o_mock_socket.recvfrom.side_effect = [
            (LDATAGRAM1, LADDR1),
            (LDATAGRAM2, LADDR2),
            KeyboardInterrupt()
        ]
        with mock.patch('sys.stdout', new=StringIO()) as fake_output:
            print_it(Listen())
            self.assertRegex(fake_output.getvalue(), (
                r'^0000.0\d\d\ds 0 NOTIFY 192\.168\.10\.86:57535 '
                r'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d '
                r'Linux/4\.14\.71-v7\+, UPnP/1\.0, Portable SDK for UPnP '
                r'devices/1\.6\.19\+git20160116\r\n0000\.0\d\d\ds 0 M-SEARCH '
                r'192\.168\.10\.3:57509\r\n$'))

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
