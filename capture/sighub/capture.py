""" A pure Python implementation of an async packet capture with an optional BPF filter.

Examples

Printing 20 packets captured on eth0 without any filter:
>>> import asyncio
>>> from sighub.capture import Capture

>>> def stop_everything() -> None:
...     asyncio.get_event_loop().stop()

>>> def print_packets(packet: bytes) -> None:
...     print(packet)

>>> def main():
...     cap = Capture('eth0', callback=print_packets, on_stop=stop_everything)
...     cap.set_event_loop(asyncio.get_event_loop())
...     cap.enable()
...     asyncio.get_event_loop().run_forever()

>>> if __name__ == '__main__':
...     main()
"""

import ctypes
import asyncio
import re
import socket
import struct
from typing import Callable, Optional

# Callable type aliases
CallbackFunction = Callable[[bytes], None]
OnStopFunction = Callable[[], None]

# From linux/if_ether.h
ETH_P_ALL = socket.ntohs(0x0003)

# From asm-generic/socket.h
SO_ATTACH_FILTER = 26

# RE for the following format
# { 0x15, 0, 4, 0x00000800 },
JIT_RE = re.compile(r'{\s+([^,]+),\s+([^,]+),\s+([^,]+),\s+(\S+)')

class Filter:
    """ A BPF filter compiled from the C filter output of `tcpdump -dd`.
        Adapted from:
            https://github.com/omaidf/KRACK-toolkit
            http://allanrbo.blogspot.com/2011/12/raw-sockets-with-bpf-in-python.html
    """

    def __init__(self, c_filter: str, num: int=100):
        """ Create a BPF filter to be used with capture.Capture.

        Args:
            c_filter (str): the output of `tcpdump -dd` in a single string with line returns
            num (int): the number of packets to capture (default 100, -1 == inifite)

        Returns:
            Filter: a Filter object
        """

        self.c_filter = c_filter
        self.num = num
        self.bpf: Optional[ctypes.Array[ctypes.c_char]] = None
        self.prog: Optional[bytes] = None

    def load(self) -> bytes:
        """ Load the filter in memory and return the length and pointer
            to be used with SO_ATTACH_FILTER.

        Returns:
            bytes: the length and pointer (HL) to be used with SO_ATTACH_FILTER
        """

        _filter = []
        for line in self.c_filter.split("\n"):
            # ensure any extra line returns do not break the filter
            if not line:
                continue

            # extract the instruction, jump if true, jump if false and value from the line
            match = re.match(JIT_RE, line)

            # skip an lines that do not match the expected C array format
            if match is None:
                continue

            s_instruct, s_jtrue, s_jfalse, s_value = match.groups()
            instruct = int(s_instruct, 16)
            jtrue, jfalse = ( int(s_jtrue), int(s_jfalse) )
            value = int(s_value, 16)

            # convert the full instruction to binary form and add it to the filter
            _filter.append(struct.pack('HBBI', instruct, jtrue, jfalse, value))

        # create a mutable memory block containing the filter
        # we need to keep a reference to this,
        # otherwise the filter is not in memory when we try to attach it to the socket
        self.bpf = ctypes.create_string_buffer(b''.join(_filter))

        # pack the length of the filter and a pointer to the filter as required by SO_ATTACH_FILTER
        prog = struct.pack('HL', len(_filter), ctypes.addressof(self.bpf))

        return prog

    def get_prog(self) -> Optional[bytes]:
        """ Get the length of the filter and pointer to the filter
            to be used with SO_ATTACH_FILTER

        Returns:
            Optional[bytes]: the length and pointer (HL) to be used with SO_ATTACH_FILTER
                             if already loaded
        """

        return self.prog

# pylint: disable=R0902
class Capture:
    """ An async network capture that runs once the asyncio event_loop is started.
    """
    def __init__(self, iface: str, callback: CallbackFunction, on_stop: OnStopFunction=None):
        """ Create a packet capture which will return the packets to the given callback.

        Args:
            iface (str): the interface to capture on
            callback (CallbackFunction): function to be called with the packets
            on_stop (Optional[OnStopFunction]): function to call when the capture is stopped

        Returns:
            Capture: a Capture object
        """
        self.count: int = 0
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.iface: str = iface
        self.callback: CallbackFunction = callback
        self.on_stop: Optional[OnStopFunction] = on_stop
        self.bpf: Optional[Filter] = None
        self.next = None
        self.listener = None

    def set_event_loop(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """ Set the event loop that will handle events from this capture.
        """
        self.event_loop = event_loop

    def set_filter(self, bpf: Filter):
        """ Set a BPF filter for this capture.
            The filter can produced using `tcpdump -dd port 443`.
        """
        self.bpf: Filter = bpf

    def status(self) -> str:
        """ Get the current status when counting packets.

        Returns:
            str: a text describing the current status of the ongoing capture
        """

        if self.bpf is not None and self.bpf.num != -1:
            return f"captured {self.count}/{self.bpf.num} packets"

        return "capturing infinite packets!"

    def stop(self) -> None:
        """ Stop the capture.
        """

        self.listener.close()

        if self.on_stop is not None:
            self.on_stop()

    def _callback(self) -> None:
        """ Receive and pass packets to the callback.
        """

        self.callback(self.listener.recv(9000))

    def _counter(self) -> None:
        """ Packet counter when count != -1.
        """

        self.count += 1
        self.next()

        if self.bpf is not None and self.count >= self.bpf.num:
            self.stop()

    def enable(self) -> None:
        """ Open the capture socket and setup the callback.
            The asyncio event_loop must be set by calling set_event_loop first.
            In order to start capturing packets, start the event_loop afte calling enable.

        Raises:
            NoEventLoopError: If enable is called before set_event_loop.
        """

        if self.event_loop is None:
            raise NoEventLoopError("event_loop not set before calling enable")

        # create a socket to capture ethernet frames
        self.listener = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, ETH_P_ALL)

        # attach the BPF filter to the socket if provided
        if self.bpf is not None:
            self.listener.setsockopt(socket.SOL_SOCKET, SO_ATTACH_FILTER, self.bpf.load())

        # bind the socket to the provided interface
        self.listener.bind((self.iface, 0))

        # add the counter if provided
        first = self._callback
        if self.bpf is not None and self.bpf.num != -1:
            self.next = first
            first = self._counter

        # create the asyncio callback
        self.event_loop.add_reader(self.listener.fileno(), first)

class NoEventLoopError(Exception):
    """ Capture exception when the event loop has not yet been set.
    """
