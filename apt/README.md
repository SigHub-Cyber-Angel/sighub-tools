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
>>> from sighub.apt import LogDB
>>>
>>> # create a log database in the file "logs.json" with a table named "Logs" that is not read-only
>>> logs = LogDB('logs.json', 'Logs', False)
>>>
>>> logs.append({ "level": "INFO", "logger": "Example", "msg": "first log line." })
>>> logs.append_multiple([{ "level": "INFO", "logger": "Example", "msg": "The field names are arbitrary." }, { "level": "ERROR", "logger": "Example", "msg": "third log line." }])
>>>
>>> # get all of the logs in the database, notice a timestamp was added to the entries
>>> logs.get_all()
[{'level': 'INFO', 'logger': 'Example', 'msg': 'first log line.', 'ts': 1633877439.718299}, {'level': 'INFO', 'logger': 'Example', 'msg': 'The field names are arbitrary.', 'ts': 1633877514.193349}, {'level': 'ERROR', 'logger': 'Example', 'msg': 'third log line.', 'ts': 1633877514.193434}]
>>>
>>> # get logs after a specific timestamp
>>> logs.get_after(1633877500)
[{'level': 'INFO', 'logger': 'Example', 'msg': 'The field names are arbitrary.', 'ts': 1633877514.193349}, {'level': 'ERROR', 'logger': 'Example', 'msg': 'third log line.', 'ts': 1633877514.193434}]
>>>
>>>
>>> # get logs with a specific field value
>>> logs.get_matches({ 'level': 'INFO' })
[{'level': 'INFO', 'logger': 'Example', 'msg': 'first log line.', 'ts': 1633877439.718299}, {'level': 'INFO', 'logger': 'Example', 'msg': 'The field names are arbitrary.', 'ts': 1633877514.193349}]
```
