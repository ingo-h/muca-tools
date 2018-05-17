#!/usr/bin/env python3

import socket


class SocketToutClass():

    def socket_timeout(self):
        """Set up UDP socket with timeout"""

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #sock.bind((_MCAST_GRP, _MCAST_PORT))
        #mreq = struct.pack("4sl", socket.inet_aton(_MCAST_GRP), socket.INADDR_ANY)
        #sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(2)
        cnt = sock.sendto(b'hello world', ('239.255.255.250', 1900))
        print('sent', cnt, 'bytes')
        try:
            while True:
                data = sock.recv(4096)
                print(data.decode(), end='')
        except socket.timeout:
            print('timed out')
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    oTout = SocketToutClass()
    oTout.socket_timeout()
