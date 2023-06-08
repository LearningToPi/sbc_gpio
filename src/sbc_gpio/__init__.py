'''
PyPi Package: sbc_gpio
Homepage: https://www.learningtopi.com/python-modules-applications/sbc_gpio/
Git: https://github.com/LearningToPi/sbc_gpio

Description:
===========
This library is intended to provide an abstraction layer between the SBC and GPIO.  In particular
the Raspberry Pi group of devices uses a proprietary GPIO library (RPi.GPIO) that is not accessible
on other SBC platforms (for example Rock Pi, Banana Pi, Atomic Pi, etc).  This library is intended
to provide an abstract class that can allow for portable code between platforms.

The SBCPlatform class allows for identifying the platform based on platform specific criteria.  The
abstract GpioIn and GpioOut classes are used to provide access to GPIO libraries that are assigned
based on the identified platform.

Usage Example:
=============
from sbc_gpio import SBCPlatform, EVENT, DIR, PULL

# get the platform and associated GPIO library
platform = SBCPlatform()
print(platform)
print(platform.serial)

# Get a GPIO out and in pin
def callback_func(event:str, time:float, state:str)
    print(time, event, state)
gpio_out = platform.get_gpio_out(gpio_id='3B3', name='test_out', pull=PULL.NONE, initial_state=0)
gpio_in = platform.get_gpio_in(gpio_id='3B2', name='test_in', pull=PULL.DOWN, event=EVENT.BOTH, 
                               debounce_ms=100, callback=callback_func)
gpio_out.set_high()
gpio_out.set_low()


Folder Structure:
.\\DIR.py, .\\EVENT.py, .\\PULL.py:
    These files include constants that are used for consistent usage between GPIO libraries.

.\\platforms:
    This folder includes a file for each platform that can be identified by this library.  Each
    file should contain the following:
        MODEL_IDENTIFIER = [ <list of supported mechanisms for identifying the platform> ]
        PLATFORM_LOCAL = namedtuple('PLATFORM_LOCAL', (<tuple of platform specific values>))
        PLATFORM_SPECIFIC = PLATFORM_INFO(model=<short device model>, description=<long device model>,
                                          gpio_valid_values=[<list of valid integer gpio's>],
                                          local=PLATFORM_LOCAL(<instance of PLATFORM_LOCAL>))
        <optional>
        def convert_gpio(gpio_str:str) -> int:
            # Function to convert a passed string that is platform specific to a GPIO integer

        def convert_gpio_tuple(gpio_str:str) -> tuple:
            # Function to convert a passed string that is platform specific to a tuple that 
            #  contains the gpio chip and gpio integer.

.\\gpio_libs:
    This folder includes a "_generic_gpio.py" lib that represents a generic GPIO input or output.
    All GPIO library files in this folder will inherit these base clases.  The base classes allow
    the abstraction of the underlying GPIO library to make code more portable between SBC's.

    Each GPIO library file should override the GpioIn and GpioOut classes and provide GPIO class
    specific functionality.

.\\device_tests:
    This folder contains a series of test files based on the _test_base.py file.  These tests
    can be used to validate functionality on the different SBC platforms supported using the
    GPIO libraries available.

.\\tests:
    This folder contains the unittest files for running the SBC device tests.

.\\__main__.py:
    Running the module directly can be used to output information on the current device platform
    or execute tests on the platform.  See the __main__.py file for more details.

    
MIT License

Copyright (c) 2022 LearningToPi <contact@learningtopi.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import os
from importlib import import_module
import re
import sys
import subprocess
from collections import namedtuple
from logging_handler import create_logger, INFO
from . import DIR, EVENT, PULL
from .gpio_libs._generic_gpio import GpioIn, GpioOut
from .dynamic_dts import DynamicOverlay

PLATFORM_BASE_DIR = os.path.join(os.path.dirname(__file__), 'platforms')

PLATFORM_INFO = namedtuple('PLATFORM_INFO', ('model', 'description', 'gpio_valid_values',
                                             'dynamic_overlay_dir', 'dynamic_overlays', 'config_file',
                                             'update_extlinux_script', 'extlinux_conf', 'local'))

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
            self._platform_write_dynamic_overlay = mod.write_dynamic_overlay if 'write_dynamic_overlay' in dir(mod) else None
            self._compile_dtbo = mod.compile_dtbo if 'compile_dtbo' in dir(mod) else None
            self._GpioIn_Class = mod.GpioIn
            self._GpioOut_Class = mod.GpioOut
            self._logger.info(f"{self.info_str}: Platform identified as {self._platform.model} ({self.description})")
        else:
            raise ValueError(f"Unable to identify platform.  Supported devices are: {','.join(self.supported_platforms)}")

    def __str__(self):
        return self.model

    @property
    def model(self):
        ''' Return the model of the device as a string '''
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.model
        return ''

    @property
    def description(self):
        ''' Return a description of the platform as a string '''
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.description
        return ''

    @property
    def gpio_valid_values(self):
        ''' Return a list of valid GPIO values as a list '''
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.gpio_valid_values
        return []

    @property
    def _local(self):
        ''' Return the platform local settings '''
        if isinstance(self._platform, PLATFORM_INFO):
            return self._platform.local
        return None

    def convert_gpio(self, *args) -> int: # pylint: disable=E0202
        ''' function placeholder - replaced with platform specific function, otherwise returns first parameter '''
        return args[0]

    def convert_gpio_tuple(self, *args) -> tuple: # pylint: disable=E0202
        ''' function placeholder - replaced with platform specific function, otherwise returns chip 0 and the first parameter as a tuple '''
        return 0, args[0]

    def gpio_is_valid(self, gpio_id) -> bool:
        ''' Checks if a passed value is a valid GPIO for the platform '''
        if isinstance(gpio_id, int) and gpio_id in self.gpio_valid_values:
            return True
        if self.convert_gpio(gpio_id) in self.gpio_valid_values:
            return True
        return False

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
        return f"{self.__class__.__name__}" + (f"({self._platform.model})" if self._platform is not None else '')

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

    def write_dynamic_overlays(self):
        ''' Read any dynamic overlays from the config file and write dts and dtbo files'''
        # check that dynamic DTS is supported
        if self._platform is None or not isinstance(self._platform.dynamic_overlay_dir, str) or not isinstance(self._platform.dynamic_overlays, dict) or len(self._platform.dynamic_overlays) == 0:
            self._logger.warning(f"{self.info_str}: Platform does not support dynamic overlay configuration.")
            self._logger.info(f"{self.info_str}: Dynamic overlay configuration aborted.")
            return

        # create dynamic_overlay folder
        try:
            os.makedirs(self._platform.dynamic_overlay_dir, mode=0o755, exist_ok=True)

            # Delete any existing dynamic overlay files (will recreate ones that still exist in the config)
            dynamic_overlay_files = os.listdir(self._platform.dynamic_overlay_dir)
            dynamic_overlay_files = [f for f in dynamic_overlay_files if os.path.isfile(self._platform.dynamic_overlay_dir+'/'+f)]
            self._logger.debug(f"{self.info_str}: Files currently in {self._platform.dynamic_overlay_dir}: {dynamic_overlay_files}")
            for file in dynamic_overlay_files:
                self._logger.debug(f"{self.info_str}: Deleting file {file}")
                os.remove(os.path.join(self._platform.dynamic_overlay_dir, file))
        except PermissionError:
            self._logger.error(f"{self.info_str}: Insufficient permisions to write to {self._platform.dynamic_overlay_dir}. Check permissions or run with sudo!")
            self._logger.info(f"{self.info_str}: Dynamic overlay configuration aborted.")
            return

        # Read all dynamic overlays from the config file
        dynamic_overlays = {}
        try:
            with open(self._platform.config_file, 'r', encoding='utf-8') as input_file:
                config_lines = input_file.readlines()
            for config_line in config_lines:
                dynamic_dts_re = re.search(r'^dynamic_overlay=(?P<driver>[^\s,]*),*(?P<options>[^\s]*)', config_line)
                if dynamic_dts_re:
                    overlay_name = dynamic_dts_re.group('driver')
                    overlay_params = dynamic_dts_re.group('options')
                    self._logger.debug(f"{self.info_str}: {self._platform.config_file}: Found dynamic overlay {overlay_name}, passed params: {overlay_params}")

                    # parse the overlay parameters, comma after overlay name and between options.  = between option name and value.  If no value, assume TRUE if present
                    _tmp_params = overlay_params.split(',')
                    overlay_params = {}
                    for _param in _tmp_params:
                        if _param != '':
                            _param_split = _param.split('=')
                            overlay_params[_param_split[0]] = _param_split[1] if len(_param_split) > 1 else True

                    # update overlay with config
                    if overlay_name not in self._platform.dynamic_overlays:
                        self._logger.warning(f"{self.info_str}: Overlay {overlay_name} not in list of supported dynamic overlays: {self._platform.dynamic_overlays.keys()}")
                        continue
                    if overlay_name not in dynamic_overlays:
                        # we haven't configured the overlay yet, so pull it in and update the parameters
                        dynamic_overlays[overlay_name] = DynamicOverlay(name=overlay_name, params=self._platform.dynamic_overlays[overlay_name]['params'])
                    try:
                        dynamic_overlays[overlay_name].set_params(overlay_params)
                    except ValueError as e:
                        self._logger.error(f"{self.info_str}: Error configuring overlay {overlay_name}: {e}")
                        continue

            # verify that all configured dynamic overlays have all required configurations
            for key, item in dynamic_overlays.items():
                if not item.ok:
                    self._logger.error(f"{self.info_str}: Overlay {key} is missing required parameters: {item.missing_params}")
                    for missing_param in item.missing_params:
                        self._logger.info(f"    Param {missing_param} help: {item.get_param(missing_param).param_help}")
                    continue

                # write the DTS file
                if self._platform_write_dynamic_overlay is not None:
                    self._logger.info(f"{self.info_str}: Writing dynamic overlay " + os.path.join(self._platform.dynamic_overlay_dir, f"{item.name}-{item.get_param('gpio').set_value}.dts"))
                    self._platform_write_dynamic_overlay(item)
                else:
                    self._logger.error(f"{self.info_str}: Unable to write overlay {key}.  Missing required platform function.")

                # compile DTBO
                if self._platform_write_dynamic_overlay is not None:
                    self._logger.info(f"{self.info_str}: Compiling dynamic overlay " + os.path.join(self._platform.dynamic_overlay_dir, f"{item.name}-{item.get_param('gpio').set_value}.dtbo"))
                    dts_file = os.path.join(self._platform.dynamic_overlay_dir, f"{item.name}-{item.get_param('gpio').set_value}.dts")
                    dtbo_file = os.path.join(self._platform.dynamic_overlay_dir, f"{item.name}-{item.get_param('gpio').set_value}.dtbo")
                    subprocess.run(f"dtc -O dtb -o {dtbo_file} {dts_file}", check=True, shell=True)
                    # verify file exists
                    if not os.path.exists(dtbo_file):
                        raise TimeoutError(f'Error creating DTBO {dtbo_file}')
                else:
                    self._logger.error(f"{self.info_str}: Unable to write overlay {key}.  Missing required platform function.")

            # Run update extlinux script if required
            if self._platform.update_extlinux_script is not None:
                self._logger.info(f"{self.info_str}: Running extlinux update script {self._platform.update_extlinux_script}")
                subprocess.run(self._platform.update_extlinux_script, check=True)

            if self._platform.extlinux_conf is not None:
                for key, item in dynamic_overlays.items():
                    # add dynamic overlay to extlinux config
                    self._logger.info(f"{self.info_str}: Updating extlinux config file {self._platform.extlinux_conf}")
                    dtbo_file = os.path.join(self._platform.dynamic_overlay_dir, f"{item.name}-{item.get_param('gpio').set_value}.dtbo").replace('/boot', '')
                    with open(self._platform.extlinux_conf, 'r', encoding='utf-8') as input_file:
                        extlinux_conf = input_file.readlines()
                    # loop through and find each label point
                    label_lines = [line for line in extlinux_conf if line.startswith('label')]
                    fdtoverlays_lines = [line for line in extlinux_conf if re.search(r'\s*fdtoverlays\s*.*', line)]
                    if len(fdtoverlays_lines) == 0:
                        # there are no fdtoverlay settings, so we need to add it in after the label line
                        for label_line in label_lines:
                            self._logger.debug(f"{self.info_str}: Adding new fdtoverlays line after label in extlinux.conf")
                            extlinux_conf.insert(extlinux_conf.index(label_line) + 1, f"    fdtoverlays {dtbo_file}\n")
                    else:
                        for fdtoverlays_line in fdtoverlays_lines:
                            self._logger.debug(f"{self.info_str}: adding dynamic overlay to existng fdtoverlays in extlinux.conf")
                            extlinux_conf[extlinux_conf.index(fdtoverlays_line)] = extlinux_conf[extlinux_conf.index(fdtoverlays_line)].rstrip() + f" {dtbo_file}\n"

                    self._logger.info(f"{self.info_str}: Writing updated extlinux configuration file {self._platform.extlinux_conf}")
                    with open(self._platform.extlinux_conf, 'w', encoding='utf-8') as output_file:
                        output_file.writelines(extlinux_conf)

        except Exception as e:
            self._logger.error(f"{self.info_str}: Error creating dynamic overlays: {e}")
