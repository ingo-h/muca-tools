#!/usr/bin/env python3
"""Tests for upnpdiscover"""

import unittest
from unittest.mock import patch

from upnp.upnpdiscover import SsdpClass


class upnpdiscoverTestCase(unittest.TestCase):
    """Tests for upnpdiscover search and listen"""

    @patch('upnp.upnpdiscover.socket.socket')     # Patch the class
    def test_msearch(self, mock_socket):
        """Test upnpdiscover but without online network socket (mocking)"""
        oMock_socket = mock_socket.return_value   # we want the instance

        # instantiate our service and set it up
        oMock_socket.recvfrom.return_value = [b'method msearch\r\n',
                                              '192.168.169.170']
        oSsdp = SsdpClass()
        oSsdp._unittest = True
        oSsdp.msearch()
        oMock_socket.settimeout.assert_called_with(2)

        oMock_socket.recvfrom.return_value = [b'method listen\r\n',
                                              '192.168.169.170']
        oSsdp.listen()
