# muca-tools
**Mullticast tools for the linux command line**

At home I'm using UPnP for playing music in several rooms with Raspberry Pis and also multicast video streams from my IPTV provider. It works, but not as expected. I also need a command line control point to modify the volume of the Raspberry Pi renderer with scripting. I've looked around but could not find what I needed. So I decided to make it myself. As multicast devices I use mostly Raspberry Pis and its default programming language ist Python. So it seems likely to use also Python for these tools.

This is the first stable release just to search and listen on the local network for UPnP devices.
```
~$ # Active search for UPnP devices by sending a request (MSEARCH).
~$ ./upnpsearch

~$ # Continuing passive listen for notifies (NOTIFY) from UPnP devices, terminating with <ctrl>C.
~$ ./upnplisten
```
## References:
[Multicast in Python](https://stackoverflow.com/q/603852/5014688)
