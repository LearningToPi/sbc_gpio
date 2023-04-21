'''

'''

import os
from importlib import import_module
import logging
import re
import sys
from logging_handler import create_logger, INFO
from collections import namedtuple
from . import DIR, EVENT, PULL
from sbc_gpio.gpio_libs._generic_gpio import GpioIn, GpioOut

PLATFORM_BASE_DIR = os.path.join(os.path.dirname(__file__), 'platforms')

PLATFORM_INFO = namedtuple('PLATFORM_INFO', ('model', 'description', 'gpio_valid_values', 'local'))

class SBCPlatform:
    ''' Class to handle platform specific commands on SBC '''
    def __init__(self, log_level=INFO):
        self._platform = None
        self._gpio_func = None
        self._logger = create_logger(console_level=log_level, name=self.info_str)
        self.serial = 'n/a'
        self.supported_platforms = []

        # Get a list of the platform files
        self._logger.debug(f"{self.info_str}: Listing platform files from: {PLATFORM_BASE_DIR}")
        platform_files = os.listdir(PLATFORM_BASE_DIR)
        mod = None
        for platform_file in platform_files:
            if platform_file.endswith('.py') and not platform_file.startswith('_'):
                try:
                    mod = import_module(f"sbc_gpio.platforms.{platform_file.split('.py')[0]}")
                    self.supported_platforms.append(mod.PLATFORM_SPECIFIC.model)
                    match_found = False
                    # run the platform identifier tests
                    for identifier in mod.MODEL_IDENTIFIER:
                        if identifier.get('type').lower() == 'true':
                            self._logger.debug(f"{self.info_str}: Platform matched in file {platform_file}")
                            # true identifier will always return true.  useful for testing
                            match_found = True
                            break

                        if identifier.get('type', 'file') == 'file' and os.path.exists(identifier['file']):
                            # file identifier will check the contents of the specified file for a provided regex
                            with open(identifier['file'], 'r', encoding='utf-8') as input_file:
                                file_contents = input_file.read()
                            if re.search(identifier['contents'], file_contents):
                                self._logger.debug(f"{self.info_str}: Platform matched in file {platform_file}")
                                match_found = True
                                break
                    # if we found a match, break out
                    if match_found:
                        break
                    # clear the loaded modules since we hit the end and didn't find a match
                    mod = None

                except Exception as e:
                    self._logger.error('Unable to import %s.  Error: %s', platform_file, e)

        # save the platform specific info and functions
        if mod is not None:
            self._platform = mod.PLATFORM_SPECIFIC
            if 'SERIAL_NUMBER' in dir(mod):
                with open(mod.SERIAL_NUMBER, 'r', encoding='utf-8') as input_file:
                    self.serial = input_file.read()
                    self.serial = ''.join([c for c in self.serial if str(c).isprintable()])
            if 'convert_gpio' in dir(mod):
                self.convert_gpio = mod.convert_gpio
            if 'convert_gpio_tuple' in dir(mod):
                self.convert_gpio_tuple = mod.convert_gpio_tuple
            self._GpioIn_Class = mod.GpioIn
            self._GpioOut_Class = mod.GpioOut
            self._logger.info(f"{self.info_str}: Platform identified as {self._platform.model} ({self.description})")
        else:
            raise ValueError(f"Unable to identify platform.  Supported devices are: {','.join(self.supported_platforms)}")            

    def __str__(self):
        return self.model

    def __del__(self):
        self.close()

    def close(self):
        pass

    @property
    def model(self):
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.model
        return ''
        
    @property
    def description(self):
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.description
        return ''
        
    @property
    def gpio_valid_values(self):
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.gpio_valid_values
        return []
        
    @property
    def _local(self):
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.local

    def convert_gpio(self, *args) -> int:
        ''' function placeholder - replaced with platform specific function, otherwise returns first parameter '''
        return args[0]
    
    def convert_gpio_tuple(self, *args) -> tuple:
        ''' function placeholder - replaced with platform specific function, otherwise returns chip 0 and the first parameter as a tuple '''
        return 0, args[0]

    def get_gpio_out(self, gpio_id, name=None, pull=PULL.NONE, log_level=INFO, initial_state=0) -> GpioOut:
        ''' Get a gpio out pin.  Gpio_id can be a string (passed to convert), an int, or a tuple (chip, pin) '''
        gpio_tuple = tuple()
        if isinstance(gpio_id, int):
            gpio_tuple = (0, gpio_id)
        elif isinstance(gpio_id, str):
            gpio_tuple = self.convert_gpio_tuple(gpio_id)
        elif isinstance(gpio_id, tuple) and len(gpio_id) == 2:
            gpio_tuple = gpio_id
        else:
            raise ValueError('"gpio_id" must be an integer for a pin, or a tuple containing the gpio chip and gpio pin (chip, pin)')
        return self._GpioOut_Class(gpio_tuple[1], gpio_tuple[0], name=name, pull=pull, log_level=log_level, initial_state=initial_state)
    
    def get_gpio_in(self, gpio_id, name=None, pull=PULL.DOWN, event=EVENT.BOTH, debounce_ms=100, callback=None, log_level=INFO, start_polling=True) -> GpioIn:
        ''' Get a gpio in pin.  Gpio_id can be a string (passed to convert), an int, or a tuple (chip, pin) '''
        gpio_tuple = tuple()
        if isinstance(gpio_id, int):
            gpio_tuple = (0, gpio_id)
        elif isinstance(gpio_id, str):
            gpio_tuple = self.convert_gpio_tuple(gpio_id)
        elif isinstance(gpio_id, tuple) and len(gpio_id) == 2:
            gpio_tuple = gpio_id
        else:
            raise ValueError('"gpio_id" must be an integer for a pin, or a tuple containing the gpio chip and gpio pin (chip, pin)')
        return self._GpioIn_Class(gpio_tuple[1], gpio_tuple[0], name=name, pull=pull, event=event, debounce_ms=debounce_ms,
                                  callback=callback, log_level=log_level, start_polling=start_polling)

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
            if 'spidev' in dev_file:
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
            if 'spidev' in dev_file:
                match = re.search("^spidev(?P<spi_bus>[0-9]).(?P<spi_cs>[0-9])$", dev_file)
                if match and int(match.group('spi_bus')) == spi_bus:
                    spi_cs += (int(match.group('spi_cs')),)
        return spi_cs


    def i2c_buses(self) -> tuple:
        ''' Returns a tuple listing the i2c bus numbers that are available (only applicable on Linux).  I.e (0,1,5,7) '''
        if 'linux' not in sys.platform.lower():
            raise NotImplementedError('spi_buses() only supported on Linux')
        dev_files = os.listdir('/dev')
        i2c_buses = ()
        for dev_file in dev_files:
            if 'i2c-' in dev_file:
                match = re.search("^i2c-(?P<i2c_bus>[0-9])$", dev_file)
                if match:
                    i2c_buses += (int(match.group('i2c_bus')),)
        return i2c_buses

