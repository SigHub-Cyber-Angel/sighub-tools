import json
import os
import unittest

from sighub import apt

from sighub.apt import (
    install_packages,
    install_upgrade,
    reinstall,
    update
)


class AptTests(unittest.TestCase):
    def setUp(self):
        self.expected = {
            'INSTALL_PACKAGES': 'update -y\n-y install pkg1\n-y install pkg2\n',
            'INSTALL_UPGRADE': '-y install pkg1\n',
            'REINSTALL': '-y install --reinstall pkg1\n',
            'UPDATE': 'update -y\n'
        }
        self.input = {
            'INSTALL_PACKAGES': ['pkg1', 'pkg2'],
            'INSTALL_UPGRADE': 'pkg1',
            'REINSTALL': 'pkg1'
        }

        # set apt binary to echo
        apt.APT_BIN = 'echo'

    def test_install_packages(self):
        output = install_packages(self.input['INSTALL_PACKAGES'])

        self.assertEqual(self.expected['INSTALL_PACKAGES'], output, msg=f'install_packages output is not {self.expected.get("INSTALL_PACKAGES")}: {output}')

    def test_install_upgrade(self):
        output = install_upgrade(self.input['INSTALL_UPGRADE'])

        self.assertEqual(self.expected['INSTALL_UPGRADE'], output, msg=f'install_packages output is not {self.expected.get("INSTALL_UPGRADE")}: {output}')

    def test_reinstall(self):
        output = reinstall(self.input['REINSTALL'])

        self.assertEqual(self.expected['REINSTALL'], output, msg=f'install_packages output is not {self.expected.get("REINSTALL")}: {output}')

    def test_update(self):
        output = update()

        self.assertEqual(self.expected['UPDATE'], output, msg=f'install_packages output is not {self.expected.get("UPDATE")}: {output}')

    def tearDown(self):
        pass
