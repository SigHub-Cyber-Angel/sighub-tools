# SigHub apt
[![Lint](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Lint%20apt/badge.svg)](https://github.com/SigHub-Cyber-Angel/sighub-tools/actions?query=workflow%3ALint%20apt)
[![Test](https://github.com/SigHub-Cyber-Angel/sighub-tools/workflows/Test%20apt/badge.svg)](https://github.com/SigHub-Cyber-Angel/dashboard-backend/actions?query=workflow%3ATest%20apt)
## Introduction
A simple Python apt wrapper.
## Supported Python Versions
Unit tests are run for Python 3.7 - 3.9.
## Installation using pip
```
pip3 install git+https://github.com/SigHub-Cyber-Angel/sighub-tools.git#egg=sighub.apt\&subdirectory=apt
```
## Examples
```
>>> from sighub import apt
>>>
>>> # install or upgrade the given package
>>> PKG_NAME = 'bison'
>>> apt.install_upgrade(PKG_NAME)
>>>
>>> # install or upgrade multiple packages but exclude 'make' from being processed
>>> PACKAGES = ('make', 'python3', 'vim')
>>> apt.install_upgrade(PACKAGES, exclude=('make'))

>>> # install or upgrade multiple packages but only 'make' and 'vim'
>>> apt.install_upgrade(PACKAGES, only=('make', 'vim'))
```
