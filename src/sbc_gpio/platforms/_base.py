import sys
import os
import signal
import re
import gpiod
import asyncio
from threading import Thread, Lock
from datetime import timedelta
import logging
from time import time, sleep
import subprocess

DEFAULT_IDENTIFIER = 'file'


class SBCPlatformBase:
    ''' Base class to represent a platform '''
    def __init__(self, logger=logging):
        self._lirc_status = {}
        self._stop_tests = False
        self._logger = logger
        pass

    def __del__(self):
        self.close()

    def close(self):
        pass

    @property
    def info_str(self):
        """ Returns the info string for the class (used in logging commands) """
        return f"{self.__class__.__name__}"

    def spi_buses(self) -> tuple:
        ''' Returns a tuple listing the spi bus numbers that are available (only applicable on Linux).  I.e. (0,1) or (0,) '''
        if 'linux' not in sys.platform.lower():
            raise NotImplementedError('spi_buses() only supported on Linux')
        dev_files = os.listdir('/dev')
        spi_buses = ()
        for dev_file in dev_files:
            if "spidev" in dev_file:
                match = re.search("^spidev(?P<spi_bus>[0-9]).(?P<spi_cs>[0-9])$", dev_file)
                if match:
                    spi_buses += (int(match.group('spi_bus')),)
        return spi_buses

    def spi_bus_cs(self, spi_bus:int) -> tuple:
        ''' Returns a tuple listing the spi cs numbers that are available for the passed bus (only applicable on Linux).  I.e. (0,1) or (0,) '''
        if 'linux' not in sys.platform.lower():
            raise NotImplementedError('spi_buses() only supported on Linux')
        dev_files = os.listdir('/dev')
        spi_cs = ()
        for dev_file in dev_files:
            if "spidev" in dev_file:
                match = re.search("^spidev(?P<spi_bus>[0-9]).(?P<spi_cs>[0-9])$", dev_file)
                if match and int(match.group('spi_bus')) == spi_bus:
                    spi_cs += (int(match.group('spi_cs')),)
        return spi_cs

