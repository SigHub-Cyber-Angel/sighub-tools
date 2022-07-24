import asyncio
import socket

from unittest import TestCase

from sighub.capture import Capture

class TestCapture(TestCase):
    """ Test the Capture class
    """

    def setUp(self):
        """ Set the expected results of the tests.
        """
        self.expected = {
            'INIT_COUNT': 0,
            'INIT_IFACE': 'lo',
            'LOOP': asyncio.unix_events._UnixSelectorEventLoop,
            'LISTENER': socket.socket,
            'LFAMILY': socket.AddressFamily.AF_PACKET,
            'LTYPE': socket.SocketKind.SOCK_RAW,
            'LPROTO': 768
        }

    def test_init(self):
        """ Test the initialization of Capture.
        """
        def _packet_cb(packet):
            """ Placeholder packet callback.
            """

        cap = Capture('lo', callback=_packet_cb)

        self.assertEqual(self.expected['INIT_COUNT'], cap.count,
                         msg=f'init count is not {self.expected["INIT_COUNT"]}: {cap.count}')
        self.assertEqual(self.expected['INIT_IFACE'], cap.iface,
                         msg=f'init iface is not {self.expected["INIT_IFACE"]}: {cap.iface}')
        self.assertEqual(_packet_cb, cap.callback,
                         msg=f'init callback is not {_packet_cb}: {cap.callback}')

    def test_enable(self):
        """ Test the enabling of a Capture.
        """
        def _packet_cb(packet):
            """ Placeholder packet callback.
            """

        cap = Capture('lo', callback=_packet_cb)
        cap.set_event_loop(asyncio.get_event_loop())

        self.assertEqual(self.expected['LOOP'], type(cap.event_loop),
             msg=f'enable event_loop is not {self.expected["LOOP"]}: {type(cap.event_loop)}')

        cap.enable()

        self.assertEqual(self.expected['LISTENER'], type(cap.listener),
             msg=f'enable listener is not {self.expected["LISTENER"]}: {type(cap.listener)}')
        self.assertEqual(self.expected['LFAMILY'], cap.listener.family,
             msg=f'enable listener family is not {self.expected["LFAMILY"]}: {cap.listener.family}')
        self.assertEqual(self.expected['LTYPE'], cap.listener.type,
             msg=f'enable listener type is not {self.expected["LTYPE"]}: {cap.listener.type}')
        self.assertEqual(self.expected['LPROTO'], cap.listener.proto,
             msg=f'enable listener proto is not {self.expected["LPROTO"]}: {cap.listener.proto}')
