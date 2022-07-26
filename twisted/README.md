# SigHub twisted
[![Lint](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Lint%20twisted/badge.svg)](https://github.com/SigHub-Cyber-Angel/sighub-tools/actions?query=workflow%3ALint%20twisted)
[![Test](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Test%20twisted/badge.svg)](https://github.com/SigHub-Cyber-Angel/dashboard-backend/actions?query=workflow%3ATest%20twisted)
## Introduction
A collection of wrappers to speed up use of the Twisted framework (twistedmatrix.com).
## Supported Python Versions
Unit tests are run for Python 3.7 - 3.9.
## Installation using pip
```
pip3 install git+https://github.com/SigHub-Cyber-Angel/sighub-tools.git#egg=sighub.twisted\&subdirectory=twisted
```
## Examples
```
>>> # LoopingCallStarter
>>> import logging
>>> from sighub.twisted import LoopingCallStarter
>>> 
>>> logging.basicConfig(level="INFO")
>>> 
>>> def dummy_call():
>>>     # looping call that is run
>>>     pass
>>> 
>>> def main():
>>>	# create and start a looping call with an interval of 10 with an errback logging errors
>>>     looping = LoopingCallStarter(dummy_call, 10)
>>> 		
>>>	# create and start a looping call with an interval of 10 that runs immediately
>>>     looping = LoopingCallStarter(dummy_call, now=True, 10)
>>> 		
>>>	# create and start a looping call with an interval of 10 that stops the reactor on an error
>>>     looping = LoopingCallStarter(dummy_call, exit_on_err=True, 10)
>>> 		
>>>     logging.info("finished startup")
>>>     reactor.run()
>>> 		
>>> if __name__ == '__main__':
>>>     main()

>>> # Use sighub.capture as a twisted reader:
>>> from twisted.internet import reactor
>>> import dpkt
>>> 
>>> from sighub.capture import Capture
>>> from sighub.twisted import ReaderEventLoopWrapper, stop_running
>>> 
>>> def print_packets(data):
>>>     # print the IP protocol layer
>>>     eth = dpkt.ethernet.Ethernet(data)
>>>     print(repr(eth.data))
>>> 
>>> def main():
>>>     # create a capture
>>>     cap = Capture('eth0', callback=print_packets, on_stop=stop_running)
>>>     # pass a reader instance to the capture as the event loop
>>>     cap.set_event_loop(ReaderEventLoopWrapper())
>>> 
>>>     # enable the capture which calls ReaderEventLoopWrapper.add_reader
>>>     cap.enable()
>>> 
>>>     # add the capture event loop (instance of ReaderEventLoopWrapper) as a reader
>>>     reactor.addReader(cap.event_loop)
>>> 
>>>     # start the twisted reactor
>>>     reactor.run()
>>>
>>> if __name__ == '__main__':
>>>     main()
```
