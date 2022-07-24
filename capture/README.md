# SigHub capture
[![Lint](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Lint%20capture/badge.svg)](https://github.com/SigHub-Cyber-Angel/sighub-tools/actions?query=workflow%3ALint%20capture)
[![Test](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Test%20capture/badge.svg)](https://github.com/SigHub-Cyber-Angel/dashboard-backend/actions?query=workflow%3ATest%20capture)
## Introduction
A pure Python implementation of an async packet capture with an optional BPF filter.
## Supported Python Versions
Unit tests are run for Python 3.7 - 3.9.
## Installation using pip
```
pip3 install git+https://github.com/SigHub-Cyber-Angel/sighub-tools.git#egg=sighub.capture\&subdirectory=capture
```
## Examples
```
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
```
