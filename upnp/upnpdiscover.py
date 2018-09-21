"""module to discover UPnP devices

references:
[Multicast in Python](https://stackoverflow.com/q/603852/5014688)
[Multicast programming](https://www.tldp.org/HOWTO/Multicast-HOWTO-6.html)
"""

import socket
import struct
import argparse


class SsdpClass():
    """Handle Simple Service Discovery Protocol"""

    _MCAST_GRP = '239.255.255.250'
    _MCAST_PORT = 1900

    _unittest = False

    def msearch(self):
        """Active search for UPnP devices on the local network"""

        timeout = 2
        msg = \
            'M-SEARCH * HTTP/1.1\r\n' \
            'HOST:239.255.255.250:1900\r\n' \
            'ST:upnp:rootdevice\r\n' \
            'MX:' + str(timeout) + '\r\n' \
            'MAN:"ssdp:discover"\r\n' \
            '\r\n'

        # Set up UDP socket with timeout and send a M-SEARCH structure
        # to the upnp multicast address and port.
        # IP_MULTICAST_LOOP is enabled by default.
        # IP_MULTICAST_TTL is set to 1 by default.
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.settimeout(timeout)
        sock.sendto(msg.encode(), (self._MCAST_GRP, self._MCAST_PORT))

        # print received data within the timeout
        if self._unittest:
            data, addr = sock.recvfrom(4096)
            print(addr, data.decode(), end='')
        else:
            try:
                while True:
                    data, addr = sock.recvfrom(4096)
                    print(addr, data.decode(), end='')
            except socket.timeout:
                pass

    def listen(self):
        """Passive listen for notifies from devices on the local network"""

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                             socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # use MCAST_GRP instead of '' to listen only to MCAST_GRP,
        # not all groups on MCAST_PORT
        sock.bind(('', self._MCAST_PORT))
        mreq = struct.pack("4sl", socket.inet_aton(self._MCAST_GRP),
                           socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        if self._unittest:
            data, addr = sock.recvfrom(4096)
            print(addr, data.decode(), end='')
        else:
            try:
                while True:
                    data, addr = sock.recvfrom(4096)
                    print(addr, '\n' + data.decode(), end='')
            except KeyboardInterrupt:
                pass


def main():
    """Discover UPnP devices on the local network"""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--listen", action="store_true",
                       help="passive listen for notifies from devices")
    group.add_argument("-s", "--search", action="store_true",
                       help="active search for UPnP devices")
    group.add_argument("-v", "--version", action="store_true",
                       help="show program version")
    args = parser.parse_args()
    o_ssdp = SsdpClass()
    if args.search:
        o_ssdp.msearch()
    elif args.listen:
        o_ssdp.listen()
    elif args.version:
        print("version 0.0")
    else:
        o_ssdp.msearch()


if __name__ == '__main__':
    main()
