#!/usr/bin/env python3

import unittest
from unittest.mock import patch

from socket_tout import SocketToutClass


class socket_timeoutTestCase(unittest.TestCase):

    @patch('socket_tout.socket.socket')     # Patch the class
    def test_socket_timeout(self, mock_socket):
        oMock_socket = mock_socket.return_value   # we want the instance
        # set up our service and instantiate it
        oMock_socket.sendto.return_value = 11
        oMock_socket.recv.return_value = b'data\r\n'
        oMock_socket(side_effect=Exception('timeout'))
        oTout = SocketToutClass()
        oTout.socket_timeout()
