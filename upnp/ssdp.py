"""Module that implements SSDP protocol.

Parts taken from netdisco version='1.4.1' and modified
https://github.com/home-assistant/netdisco/blob/master/netdisco/ssdp.py
"""
import sys
import re
import select
import socket
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import xml.etree.ElementTree as ElementTree

import requests
import netifaces


DISCOVER_TIMEOUT = 2
# MX is a suggested random wait time for a device to reply, so should be
# bound by our discovery timeout.
SSDP_MX = DISCOVER_TIMEOUT
SSDP_TARGET = ("239.255.255.250", 1900)

RESPONSE_REGEX = re.compile(r'\n(.*?)\: *(.*)\r')

MIN_TIME_BETWEEN_SCANS = timedelta(seconds=59)

# Devices and services
ST_ALL = "ssdp:all"

# Devices only, some devices will only respond to this query
ST_ROOTDEVICE = "upnp:rootdevice"


# Taken from https://stackoverflow.com/a/10077069/5014688
def etree_to_dict(tree):
    """Convert an ETree object to a dict.

    Taken from netdisco version='1.4.1'
    https://github.com/home-assistant/netdisco/blob/master/netdisco/util.py
    """
    # strip namespace
    tag_name = tree.tag[tree.tag.find("}")+1:]

    dic = {tag_name: {} if tree.attrib else None}
    children = list(tree)
    if children:
        ddict = defaultdict(list)
        for dcn in map(etree_to_dict, children):
            for k, i in dcn.items():
                ddict[k].append(i)
        dic = {tag_name:
               {k: i[0] if len(i) == 1 else i for k, i in ddict.items()}}
    if tree.attrib:
        dic[tag_name].update(('@' + k, i) for k, i in tree.attrib.items())
    if tree.text:
        text = tree.text.strip()
        if children or tree.attrib:
            if text:
                dic[tag_name]['#text'] = text
        else:
            dic[tag_name] = text
    return dic


def interface_addresses(family=netifaces.AF_INET):
    """Return local addresses of any associated network.

    Gathering of addresses which are bound to a local interface that has
    broadcast (and probably multicast) capability.

    Taken from netdisco version='1.4.1'
    https://github.com/home-assistant/netdisco/blob/master/netdisco/util.py
    """
    # pylint: disable=no-member
    return [addr['addr']
            for i in netifaces.interfaces()
            for addr in netifaces.ifaddresses(i).get(family) or []
            if 'broadcast' in addr]


class SSDP(object):
    """Control the scanning of uPnP devices and services and caches output."""

    def __init__(self):
        """Initialize the discovery."""
        self.entries = []
        self.last_scan = None

    def scan(self):
        """Scan the network."""
        self.update()

    def all(self):
        """Return all found entries.

        Will scan for entries if not scanned recently.
        """
        self.update()

        return list(self.entries)

    # pylint: disable=invalid-name
    def find_by_st(self, st):
        """Return a list of entries that match the ST."""
        self.update()

        return [entry for entry in self.entries
                if entry.st == st]

    def find_by_device_description(self, values):
        """Return a list of entries that match the description.

        Pass in a dict with values to match against the device tag in the
        description.
        """
        self.update()

        seen = set()
        results = []

        # Make unique based on the location since we don't care about ST here
        for entry in self.entries:
            location = entry.location

            if location not in seen and entry.match_device_description(values):
                results.append(entry)
                seen.add(location)

        return results

    def update(self, force_update=False):
        """Scan for new uPnP devices and services."""
        if self.last_scan is None or force_update or \
           datetime.now()-self.last_scan > MIN_TIME_BETWEEN_SCANS:

            self.remove_expired()

            self.entries.extend(
                entry for entry in scan()
                if entry not in self.entries)

            self.last_scan = datetime.now()

    def remove_expired(self):
        """Filter out expired entries."""
        self.entries = [entry for entry in self.entries
                        if not entry.is_expired]


class UPNPEntry(object):
    """Found uPnP entry."""

    DESCRIPTION_CACHE = {'_NO_LOCATION': {}}

    def __init__(self, values):
        """Initialize the discovery."""
        self.values = values
        self.created = datetime.now()

        if 'cache-control' in self.values:
            cache_directive = self.values['cache-control']
            max_age = re.findall(r'max-age *= *\d+', cache_directive)
            if max_age:
                cache_seconds = int(max_age[0].split('=')[1])
                self.expires = self.created + timedelta(seconds=cache_seconds)
            else:
                self.expires = None
        else:
            self.expires = None

    @property
    def is_expired(self):
        """Return if the entry is expired or not."""
        return self.expires is not None and datetime.now() > self.expires

    # pylint: disable=invalid-name
    @property
    def st(self):
        """Return ST value."""
        return self.values.get('st')

    @property
    def location(self):
        """Return Location value."""
        return self.values.get('location')

    @property
    def description(self):
        """Return the description from the uPnP entry."""
        url = self.values.get('location', '_NO_LOCATION')

        if url not in UPNPEntry.DESCRIPTION_CACHE:
            try:
                xml = requests.get(url, timeout=5).text
                if not xml:
                    # Samsung Smart TV sometimes returns an empty document the
                    # first time. Retry once.
                    xml = requests.get(url, timeout=5).text

                tree = ElementTree.fromstring(xml)

                UPNPEntry.DESCRIPTION_CACHE[url] = \
                    etree_to_dict(tree).get('root', {})
            except requests.RequestException:
                logging.getLogger(__name__).warning(
                    "Error fetching description at %s", url)

                UPNPEntry.DESCRIPTION_CACHE[url] = {}

            except ElementTree.ParseError:
                logging.getLogger(__name__).warning(
                    "Found malformed XML at %s: %s", url, xml)

                UPNPEntry.DESCRIPTION_CACHE[url] = {}

        return UPNPEntry.DESCRIPTION_CACHE[url]

    def match_device_description(self, values):
        """Fetch description and matches against it.

        Values should only contain lowercase keys.
        """
        device = self.description.get('device')

        if device is None:
            return False

        return all(device.get(key) in val
                   if isinstance(val, list)
                   else val == device.get(key)
                   for key, val in values.items())

    @classmethod
    def from_response(cls, response):
        """Create a uPnP entry from a response."""
        return UPNPEntry({key.lower(): item for key, item
                          in RESPONSE_REGEX.findall(response)})

    def __eq__(self, other):
        """Return the comparison."""
        return (self.__class__ == other.__class__ and
                self.values == other.values)

    def __repr__(self):
        """Return the entry."""
        return "<UPNPEntry {} - {}>".format(self.location or '', self.st or '')


def ssdp_request(ssdp_st, ssdp_mx=SSDP_MX):
    """Return request bytes for given st and mx."""
    return "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'ST: {}'.format(ssdp_st),
        'MX: {:d}'.format(ssdp_mx),
        'MAN: "ssdp:discover"',
        'HOST: {}:{}'.format(*SSDP_TARGET),
        '', '']).encode('utf-8')


# pylint: disable=invalid-name,too-many-locals,too-many-branches
def scan(timeout=DISCOVER_TIMEOUT):
    """Send a message over the network to discover uPnP devices.

    Inspired by Crimsdings
    https://github.com/crimsdings/ChromeCast/blob/master/cc_discovery.py

    Protocol explanation:
    https://embeddedinn.wordpress.com/tutorials/upnp-device-architecture/
    """
    ssdp_requests = ssdp_request(ST_ALL), ssdp_request(ST_ROOTDEVICE)

    stop_wait = datetime.now() + timedelta(seconds=timeout)

    sockets = []
    for addr in interface_addresses():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Set the time-to-live for messages for local network
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL,
                            SSDP_MX)
            sock.bind((addr, 0))
            sockets.append(sock)
        except socket.error:
            pass

    entries = {}
    for sock in [s for s in sockets]:
        try:
            for req in ssdp_requests:
                sock.sendto(req, SSDP_TARGET)
            sock.setblocking(False)
        except socket.error:
            sockets.remove(sock)
            sock.close()

    try:
        while sockets:
            time_diff = stop_wait - datetime.now()
            seconds_left = time_diff.total_seconds()
            if seconds_left <= 0:
                break

            ready = select.select(sockets, [], [], seconds_left)[0]

            for sock in ready:
                try:
                    data, address = sock.recvfrom(1024)
                    response = data.decode("utf-8")
                except UnicodeDecodeError:
                    logging.getLogger(__name__).debug(
                        'Ignoring invalid unicode response from %s', address)
                    continue
                except socket.error:
                    logging.getLogger(__name__).exception(
                        "Socket error while discovering SSDP devices")
                    sockets.remove(sock)
                    sock.close()
                    continue

                entry = UPNPEntry.from_response(response)
                entries[(entry.st, entry.location)] = entry

    finally:
        for s in sockets:
            s.close()

    return sorted(entries.values(), key=lambda entry: entry.location or '')


def main():
    """Test SSDP discovery."""
    from pprint import pprint

    print("Scanning SSDP..")
    pprint(scan())


if __name__ == "__main__":
    main()