""" A simple Python apt wrapper.
"""

import subprocess

# apt needs to be in the path when the script is called
APT_BIN = 'apt'

def run(command):
    """ run subprocess.check_output in a try block

        @param command: the list representing the command to run

        @return : False if the command ran with an error otherwise the output
    """
    try:
        return subprocess.check_output(command, universal_newlines=True)
    except subprocess.CalledProcessError:
        return False

def install_upgrade(package):
    """ install or upgrade the provided package

        @param package: the package to be installed or upgraded
    """
    return run([ APT_BIN, '-y', 'install', package ])

def reinstall(package):
    """ reinstall the provided package

        @param package: the package to be reinstalled
    """
    return run([ APT_BIN, '-y', 'install', '--reinstall', package ])

def update():
    """ update the list of available apt packages
    """
    return run([ APT_BIN, 'update', '-y' ])

def install_packages(packages, only=None, exclude=None):
    """ Install or upgrade packages provided

        @param packages: packages to be processed
        @param only: list of packages that should be installed
        @param exclude: list of packages that should be excluded from the install
    """
    # update list of available packages
    output = update()

    # install or upgrade the packages found in the configuration
    for package in packages:
        if exclude is not None and package in exclude:
            continue
        elif only is not None and package not in only:
            continue

        output = f'{output}{install_upgrade(package)}'

    return output
