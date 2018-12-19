"""This are common used fixtures and tests for common used modules."""

from unittest import TestCase
from time import time
# from pprint import pprint
# pprint(vars(instance))

from upnp.UpnpCommon import SSDPdatagram


# three ssdp datagram from search response as test pattern
SADDR1 = ('192.168.10.119', 47383)
SDATAGRAM1 = (
    b'HTTP/1.1 200 OK\r\n'
    b'CACHE-CONTROL: max-age=1800\r\n'
    b'DATE: Sun, 23 Sep 2018 17:08:38 GMT\r\n'
    b'EXT:\r\n'
    b'LOCATION: http://192.168.10.119:8008/ssdp/device-desc.xml\r\n'
    b'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\r\n'
    b'01-NLS: d2631d76-1dd1-11b2-9c2f-ee4373b37081\r\n'
    b'SERVER: Linux/3.10.79, UPnP/1.0, Portable SDK for UPnP '
    b'devices/1.6.18\r\n'
    b'X-User-Agent: redsonic\r\n'
    b'ST: upnp:rootdevice\r\n'
    b'USN: uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277::upnp:rootdevice\r\n'
    b'BOOTID.UPNP.ORG: 0\r\n'
    b'CONFIGID.UPNP.ORG: 1\r\n'
    b'\r\n')

SADDR2 = ('192.168.49.1', 34731)
SDATAGRAM2 = (
    b'HTTP/1.1 200 OK\r\n'
    b'USN: uuid:f48c8d92-c3c0-6f29-0000-00004e74db48::upnp:rootdevice\r\n'
    b'CACHE-CONTROL: max-age=1800\r\n'
    b'EXT:\r\n'
    b'ST: upnp:rootdevice\r\n'
    b'LOCATION: http://192.168.10.107:41947/'
    b'upnp/dev/f48c8d92-c3c0-6f29-0000-00004e74db48/desc\r\n'
    b'SERVER: Linux/3.10.54 UPnP/1.0 Cling/2.0\r\n'
    b'\r\n')

SADDR3 = ('192.168.10.3', 1900)
SDATAGRAM3 = (
    b'HTTP/1.1 200 OK\r\n'
    b'LOCATION: http://192.168.10.3:49000/fboxdesc.xml\r\n'
    b'SERVER: fritz-box UPnP/1.0 AVM FRITZ!Box 7490 113.07.01\r\n'
    b'CACHE-CONTROL: max-age=1800\r\n'
    b'EXT:\r\n'
    b'ST: upnp:rootdevice\r\n'
    b'USN: uuid:123402409-bccb-40e7-8e6c-3481C4FC71A9::upnp:rootdevice\r\n'
    b'\r\n')


# three ssdp datagram from listen as test pattern
LADDR1 = ('192.168.10.86', 57535)
LDATAGRAM1 = (
    b'NOTIFY * HTTP/1.1\r\n'
    b'HOST: 239.255.255.250:1900\r\n'
    b'CACHE-CONTROL: max-age=100\r\n'
    b'LOCATION: http://192.168.10.86:49494/description.xml\r\n'
    b'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\r\n'
    b'01-NLS: 293e3a3c-760d-11e8-8719-a7d281e29bfc\r\n'
    b'NT: urn:schemas-upnp-org:device:MediaRenderer:1\r\n'
    b'NTS: ssdp:alive\r\n'
    b'SERVER: Linux/4.14.71-v7+, UPnP/1.0, Portable SDK for UPnP '
    b'devices/1.6.19+git20160116\r\n'
    b'X-User-Agent: redsonic\r\n'
    b'USN: uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d'
    b'::urn:schemas-upnp-org:device:MediaRenderer:1\r\n'
    b'\r\n')

LADDR2 = ('192.168.10.3', 57509)
LDATAGRAM2 = (
    b'M-SEARCH * HTTP/1.1\r\n'
    b'HOST: 239.255.255.250:1900\r\n'
    b'MAN: "ssdp:discover"\r\n'
    b'MX: 5\r\n'
    b'ST: urn:schemas-upnp-org:device:avm-aha:1\r\n'
    b'\r\n')

LADDR3 = ('192.168.10.75', 42047)
LDATAGRAM3 = (
    b'NOTIFY * HTTP/1.1\r\n'
    b'HOST: 239.255.255.250:1900\r\n'
    b'CACHE-CONTROL: max-age=100\r\n'
    b'LOCATION: http://192.168.10.75:49494/description.xml\r\n'
    b'OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01\r\n'
    b'01-NLS: 623e78c0-bc6b-11e8-93a8-dd96af54c61d\r\n'
    b'NT: urn:schemas-upnp-org:service:ConnectionManager:1\r\n'
    b'NTS: ssdp:alive\r\n'
    b'SERVER: Linux/4.14.70-v7+, UPnP/1.0, Portable SDK for UPnP '
    b'devices/1.6.19+git20160116\r\n'
    b'X-User-Agent: redsonic\r\n'
    b'USN: uuid:231179de-90e9-11e8-b505-4355ee6fa7cf'
    b'::urn:schemas-upnp-org:service:ConnectionManager:1\r\n'
    b'\r\n')


class CommonTestCase(TestCase):
    """Tests for common used modules."""

    def test1_ssdp_datagram(self):
        """Test structure of a SSDP datagram object from search response."""
        o_datagram = SSDPdatagram(addr=SADDR1, raw_data=SDATAGRAM1)
        self.assertAlmostEqual(o_datagram.timestamp, time(), 2)
        self.assertEqual(len(o_datagram.__dict__), 17)

        self.assertEqual(o_datagram.method, '')
        self.assertEqual(o_datagram.bootid_upnp_org, '0')
        self.assertEqual(o_datagram.cache_control, 'max-age=1800')
        self.assertEqual(o_datagram.configid_upnp_org, '1')
        self.assertEqual(o_datagram.date, 'Sun, 23 Sep 2018 17:08:38 GMT')
        self.assertEqual(o_datagram.ext, '')
        self.assertEqual(o_datagram.ipaddr, '192.168.10.119')
        self.assertEqual(o_datagram.location, (
            'http://192.168.10.119:8008/ssdp/device-desc.xml'))
        self.assertEqual(o_datagram.opt, '"http://schemas.upnp.org/upnp/1/0/";'
                         ' ns=01')
        self.assertEqual(o_datagram.port, '47383')
        self.assertEqual(o_datagram.request, 0)
        self.assertEqual(o_datagram.server, 'Linux/3.10.79, UPnP/1.0, '
                         'Portable SDK for UPnP devices/1.6.18')
        self.assertEqual(o_datagram.st, 'upnp:rootdevice')
        self.assertEqual(o_datagram.usn, (
            'uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277::upnp:rootdevice'))
        self.assertEqual(o_datagram.uuid,
                         '3b2867a3-b55f-8e77-5ad8-a6d0c6990277')
        self.assertEqual(o_datagram.x01_nls,
                         'd2631d76-1dd1-11b2-9c2f-ee4373b37081')
        self.assertEqual(o_datagram.x_user_agent, 'redsonic')
        self.assertEqual(o_datagram.data, SDATAGRAM1.decode())

    def test2_ssdp_datagram(self):
        """Test SSDP datagram from search response without addr and data."""
        o_datagram = SSDPdatagram()
        self.assertAlmostEqual(o_datagram.timestamp, time(), 2)
        self.assertEqual(len(o_datagram.__dict__), 4)

        self.assertEqual(o_datagram.ipaddr, '')
        self.assertEqual(o_datagram.port, '')
        self.assertEqual(o_datagram.method, '')
        self.assertEqual(o_datagram.request, 0)
        self.assertIsNone(o_datagram.data)

    def test3_ssdp_datagram(self):
        """Test SSDP datagram from search response without data."""
        o_datagram = SSDPdatagram(addr=SADDR1)
        self.assertAlmostEqual(o_datagram.timestamp, time(), 2)
        self.assertEqual(len(o_datagram.__dict__), 4)

        self.assertEqual(o_datagram.ipaddr, '192.168.10.119')
        self.assertEqual(o_datagram.port, '47383')
        self.assertEqual(o_datagram.method, '')
        self.assertEqual(o_datagram.request, 0)
        self.assertIsNone(o_datagram.data)

    def test4_ssdp_datagram(self):
        """Test SSDP datagram from search response without addr."""
        o_datagram = SSDPdatagram(raw_data=SDATAGRAM1)
        self.assertAlmostEqual(o_datagram.timestamp, time(), 2)
        self.assertEqual(len(o_datagram.__dict__), 17)

        self.assertEqual(o_datagram.ipaddr, '')
        self.assertEqual(o_datagram.port, '')
        self.assertEqual(o_datagram.method, '')
        self.assertEqual(o_datagram.request, 0)
        self.assertEqual(o_datagram.data, SDATAGRAM1.decode())

    def test5_ssdp_datagram(self):
        """Test structure of a SSDP datagram object from listen."""
        o_datagram = SSDPdatagram(addr=LADDR1, raw_data=LDATAGRAM1)
        self.assertAlmostEqual(o_datagram.timestamp, time(), 2)
        self.assertEqual(o_datagram.ipaddr, '192.168.10.86')
        self.assertEqual(o_datagram.port, '57535')
        self.assertEqual(o_datagram.request, 0)

        self.assertEqual(o_datagram.method, 'NOTIFY')
        self.assertEqual(o_datagram.host, '239.255.255.250:1900')
        self.assertEqual(o_datagram.cache_control, 'max-age=100')
        self.assertEqual(o_datagram.location,
                         'http://192.168.10.86:49494/description.xml')
        self.assertEqual(o_datagram.opt,
                         '"http://schemas.upnp.org/upnp/1/0/"; ns=01')
        self.assertEqual(o_datagram.x01_nls,
                         '293e3a3c-760d-11e8-8719-a7d281e29bfc')
        self.assertEqual(o_datagram.nt,
                         'urn:schemas-upnp-org:device:MediaRenderer:1')
        self.assertEqual(o_datagram.nts, 'ssdp:alive')
        self.assertEqual(o_datagram.server, (
            'Linux/4.14.71-v7+, UPnP/1.0, Portable SDK for UPnP '
            'devices/1.6.19+git20160116'))
        self.assertEqual(o_datagram.x_user_agent, 'redsonic')
        self.assertEqual(o_datagram.usn, (
            'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d'
            '::urn:schemas-upnp-org:device:MediaRenderer:1'))
        self.assertEqual(o_datagram.uuid,
                         'f4f7681c-3056-11e8-86bd-87a6e4e2c42d')
        self.assertEqual(o_datagram.data, LDATAGRAM1.decode())

    def test1_fdevice(self):
        """Test formating a device output from a search datagram."""
        o_datagram = SSDPdatagram(addr=SADDR1, raw_data=SDATAGRAM1)
        result = o_datagram.fdevice()
        self.assertEqual(result, (
            '0000.0000s 0 192.168.10.119:47383 '
            'uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 Linux/3.10.79, '
            'UPnP/1.0, Portable SDK for UPnP devices/1.6.18\r\n'))
        result = o_datagram.fdevice(time()+2)
        self.assertEqual(result, (
            '0000.0000s 0 192.168.10.119:47383 '
            'uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 Linux/3.10.79, '
            'UPnP/1.0, Portable SDK for UPnP devices/1.6.18\r\n'))
        result = o_datagram.fdevice(base_time=time()-1.5)
        self.assertRegex(result, (
            r'^0001\.\d\d\d\ds 0 192\.168\.10\.119:47383 '
            r'uuid:3b2867a3-b55f-8e77-5ad8-a6d0c6990277 Linux/3\.10\.79, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.18\r\n$'))

    def test2_fdevice(self):
        """Test formating a device output from a listen datagram."""
        o_datagram = SSDPdatagram(addr=LADDR1, raw_data=LDATAGRAM1)
        o_datagram.request = 3
        result = o_datagram.fdevice()
        self.assertEqual(result, (
            '0000.0000s 3 NOTIFY 192.168.10.86:57535 '
            'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d Linux/4.14.71-v7+, '
            'UPnP/1.0, Portable SDK for UPnP devices/1.6.19+git20160116\r\n'))
        result = o_datagram.fdevice(base_time=time()-1.5)
        self.assertRegex(result, (
            r'^0001\.\d\d\d\ds 3 NOTIFY 192\.168\.10\.86:57535 '
            r'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d Linux/4\.14\.71-v7\+, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.19\+git20160116'
            r'\r\n$'))

    def test3_fdevice(self):
        """Test formating device from listen datagram without addr and data."""
        o_datagram = SSDPdatagram()
        result = o_datagram.fdevice()
        self.assertEqual(result, '0000.0000s 0\r\n')
        result = o_datagram.fdevice(base_time=time()-1.5)
        self.assertRegex(result, r'^0001\.\d\d\d\ds 0\r\n$')

    def test4_fdevice(self):
        """Test formating device output from a listen datagram without data."""
        o_datagram = SSDPdatagram(addr=LADDR1)
        o_datagram.request = 2
        result = o_datagram.fdevice()
        self.assertEqual(result, '0000.0000s 2 192.168.10.86:57535\r\n')
        result = o_datagram.fdevice(base_time=time()-1.5)
        self.assertRegex(result, (r'^0001\.\d\d\d\ds 2 192\.168\.10\.86:57535'
                                  r'\r\n$'))

    def test5_fdevice(self):
        """Test formating device output from a listen datagram without addr."""
        o_datagram = SSDPdatagram(raw_data=LDATAGRAM1)
        o_datagram.request = 4
        result = o_datagram.fdevice()
        self.assertEqual(result, (
            '0000.0000s 4 NOTIFY uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d '
            'Linux/4.14.71-v7+, UPnP/1.0, Portable SDK for UPnP '
            'devices/1.6.19+git20160116\r\n'))
        result = o_datagram.fdevice(base_time=time()-1.5)
        self.assertRegex(result, (
            r'^0001\.\d\d\d\ds 4 NOTIFY '
            r'uuid:f4f7681c-3056-11e8-86bd-87a6e4e2c42d Linux/4\.14\.71-v7\+, '
            r'UPnP/1\.0, Portable SDK for UPnP devices/1\.6\.19\+git20160116'
            r'\r\n$'))

    def test6_fdevice(self):
        """Test formating a device verbose output from a search datagram."""
        o_datagram = SSDPdatagram(addr=SADDR1, raw_data=SDATAGRAM1)
        result = o_datagram.fdevice(verbose=True)
        self.assertEqual(result, '0000.0000s 0 192.168.10.119:47383\r\n'
                         + SDATAGRAM1.decode())
        result = o_datagram.fdevice(time()+2, verbose=True)
        self.assertEqual(result, '0000.0000s 0 192.168.10.119:47383\r\n'
                         + SDATAGRAM1.decode())
        result = o_datagram.fdevice(base_time=time()-1.5, verbose=True)
        self.assertRegex(result[:9], r'^0001\.\d\d\d\d$')
        self.assertEqual(result[9:], 's 0 192.168.10.119:47383\r\n'
                         + SDATAGRAM1.decode())

    def test7_fdevice(self):
        """Test formating a device verbose output from a listen datagram."""
        o_datagram = SSDPdatagram(addr=LADDR1, raw_data=LDATAGRAM1)
        o_datagram.request = 3
        result = o_datagram.fdevice(verbose=True)
        self.assertEqual(result, '0000.0000s 3 192.168.10.86:57535\r\n'
                         + LDATAGRAM1.decode())
        result = o_datagram.fdevice(base_time=time()-1.5, verbose=True)
        self.assertRegex(result[:9], r'^0001\.\d\d\d\d$')
        self.assertEqual(result[9:], 's 3 192.168.10.86:57535\r\n'
                         + LDATAGRAM1.decode())

    def test8_fdevice(self):
        """Test format device verbose listen datagram without addr and data."""
        o_datagram = SSDPdatagram()
        result = o_datagram.fdevice(verbose=True)
        self.assertEqual(result, '0000.0000s 0\r\n')
        result = o_datagram.fdevice(base_time=time()-1.5, verbose=True)
        self.assertRegex(result, r'^0001\.\d\d\d\ds 0\r\n$')

    def test9_fdevice(self):
        """Test formating device verbose from listen datagram without data."""
        o_datagram = SSDPdatagram(addr=LADDR1)
        o_datagram.request = 2
        result = o_datagram.fdevice(verbose=True)
        self.assertEqual(result, '0000.0000s 2 192.168.10.86:57535\r\n')
        result = o_datagram.fdevice(base_time=time()-1.5, verbose=True)
        self.assertRegex(result, (r'^0001\.\d\d\d\ds 2 '
                                  r'192\.168\.10\.86:57535\r\n$'))

    def test10_fdevice(self):
        """Test formating device verbose from listen datagram without addr."""
        o_datagram = SSDPdatagram(raw_data=LDATAGRAM1)
        o_datagram.request = 4
        result = o_datagram.fdevice(verbose=True)
        self.assertEqual(result, '0000.0000s 4\r\n' + LDATAGRAM1.decode())
        result = o_datagram.fdevice(base_time=time()-1.5, verbose=True)
        self.assertRegex(result[:9], r'^0001\.\d\d\d\d$')
        self.assertEqual(result[9:], 's 4\r\n' + LDATAGRAM1.decode())

# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab autoindent nowrap
