#!/usr/bin/python3
""" Print 20 packets captured on flows to or from port 443.
"""

import asyncio
# allow this example to be run from the examples directory
import context
from sighub.capture import Capture, Filter

# produced using `tcpdump -dd port 443`
TEST_FILTER = """{ 0x28, 0, 0, 0x0000000c },
{ 0x15, 0, 8, 0x000086dd },
{ 0x30, 0, 0, 0x00000014 },
{ 0x15, 2, 0, 0x00000084 },
{ 0x15, 1, 0, 0x00000006 },
{ 0x15, 0, 17, 0x00000011 },
{ 0x28, 0, 0, 0x00000036 },
{ 0x15, 14, 0, 0x000001bb },
{ 0x28, 0, 0, 0x00000038 },
{ 0x15, 12, 13, 0x000001bb },
{ 0x15, 0, 12, 0x00000800 },
{ 0x30, 0, 0, 0x00000017 },
{ 0x15, 2, 0, 0x00000084 },
{ 0x15, 1, 0, 0x00000006 },
{ 0x15, 0, 8, 0x00000011 },
{ 0x28, 0, 0, 0x00000014 },
{ 0x45, 6, 0, 0x00001fff },
{ 0xb1, 0, 0, 0x0000000e },
{ 0x48, 0, 0, 0x0000000e },
{ 0x15, 2, 0, 0x000001bb },
{ 0x48, 0, 0, 0x00000010 },
{ 0x15, 0, 1, 0x000001bb },
{ 0x6, 0, 0, 0x00040000 },
{ 0x6, 0, 0, 0x00000000 },"""

def stop_everything() -> None:
    """ Stop the event loop.
    """
    asyncio.get_event_loop().stop()

def print_packets(packet: bytes) -> None:
    """ Print a raw packet.

    Args:
        packet (bytes): a packet represented as bytes
    """

    print(packet)

def main() -> None:
    """ Executed when this library is called as a program.
    """

    # the interface to capture on
    interface: str= "eth0"
    # create the capture object
    https_capture: Capture = Capture(interface, callback=print_packets, on_stop=stop_everything)

    # set the BPF filter for the capture
    https_capture.set_filter(Filter(TEST_FILTER, num=20))

    # set the asyncio event loop for the capture
    https_capture.set_event_loop(asyncio.get_event_loop())
    # open the capture socket
    https_capture.enable()

    # start capturing
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    main()
