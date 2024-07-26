'''
Base class to represent a platform.  Class will be overriden by each supported platform type.
'''
from logging_handler import create_logger, INFO, DEBUG
import os
import re
import subprocess
from sbc_gpio import DIR, EVENT, PULL
from sbc_gpio.gpio_libs._generic_gpio import GpioIn, GpioOut

# select the gpio library for the platform
import sbc_gpio.gpio_libs.lib_gpiod as lib_gpiod

# List of dict - platforms supported by this definition
SUPPORTED_PLATFORMS = [
    {
        'model': 'abc123',
        'description': 'test abc123',
        'gpio_valid_values': [1,2,3,4,5,6,7,8,9,10],
        'gpio_lib': lib_gpiod,
        'identifiers': [
            {'type': 'file', 'contents': 'abc123'}
        ],
        '_serial_location': {'type': 'file', 'contents': '.*'}
    }
]


class Boot:
    ''' Class to represent the boot process.  Abstract for the different boot methods (uboot, extlinux)'''
    active_overlays = None
    available_fixed_overlays = None
    available_dynamic_overlays = None
    
    def __init__(self, config_file:str, logger):
        self._logger = logger
        self.config_file = config_file

    def __del__(self):
        pass

    @property
    def info_str(self):
        """ Returns the info string for the class (used in logging commands) """
        return f"{self.__class__.__name__}"


class Overlay:
    ''' Class to represent overlays for the platform.  This will include fixed files and dynamic overlays '''
    pass



class SbcPlatform_Base:
    ''' Class to represent a generic platform with supported functions '''
    _platforms = SUPPORTED_PLATFORMS
    gpio_valid_values = []
    _boot = None
    _overlay = None
    model = None
    serial = None
    description = None
    _serial_location = None
    gpio_lib = None
    gpio_format = ''
    gpio_re_format = ''
    gpio_prefix = []
    gpio_chip_offset = ()

    def __init__(self, log_level=INFO, **kwargs):
        self._logger = create_logger(console_level=log_level, name=self.info_str)
        for arg, value in kwargs.items():
            setattr(self, arg, value)
        self._identify_platform()
        self._set_serial()


    def __del__(self):
        pass

    def __str__(self) -> str:
        ''' Return the platform as a string '''
        if not self.platform_matched:
            raise ValueError(f'{self.info_str}: Platform has not been identified')
        return str(self.description if self.description is not None else self.model)

    @property
    def info_str(self):
        """ Returns the info string for the class (used in logging commands) """
        return f"{self.__class__.__name__}" + (f"({self.model})" if self.model is not None else '')

    def gpio_valid(self, gpio) -> bool:
        ''' Check if a GPIO is valid on this platfom '''
        if self.gpio_valid_values is None:
            self._logger.warning(f"{self.info_str}: No list of valid GPIO values available. Assuming '{gpio}' is valid.")
            # No list of valid gpios.  Must assume everything is ok
            return True
        if self.gpio_convert(gpio) in self.gpio_valid_values:
            # GPIO (string or int) is valid
            return True
        return False
    gpio_is_valid = gpio_valid
        
    def gpio_convert(self, gpio) -> int|None:
        ''' Return the GPIO converted to an integer '''
        # Generic function to override per device class.  Make sure it is an int
        if not isinstance(gpio, int) or (isinstance(gpio,str) and not gpio.isdigit()):
            self._logger.error(f"{self.info_str}: Unable to convert '{gpio}' to an integer.")
            raise ValueError(f"{self.info_str}: Unable to convert '{gpio}' to an integer.")
        if not self.gpio_valid(int(gpio)):
            self._logger.error(f"{self.info_str}: GPIO '{gpio}' is not in the list of valud values: {self.gpio_valid_values}")
            raise ValueError(f"{self.info_str}: Unable to convert '{gpio}' to an integer.")
        return int(gpio)

    def gpio_tuple(self, gpio) -> tuple:
        ''' Return the GPIO converted to a gpio chip and pin (in tuple format with 2 fields)'''
        # Generic function to override per device class.  Return chip 0 with the integer value
        return 0, self.gpio_convert(gpio) 

    def _identify_platform(self):
        ''' loop through the platforms supported by this definition and check for a match, return the matched platform or None '''
        for platform in self._platforms:
            self._logger.debug(f"{self.info_str}: Checking platform {platform.get('model')}")
            for identifier in platform.get('identifiers', []):
                self._logger.debug(f"{self.info_str}: {platform.get('model')}: Testing identifier: {identifier}")
                if identifier.get('type', 'file') == 'file' and identifier.get('contents', None) is not None:
                    if get_file_regex(identifier['file'], identifier['contents']):
                        # save the values for the platform
                        for item, value in platform.items():
                            setattr(self, item, value)
                        self._logger.debug(f"{self.info_str}: Identified platform as {self.model} using {identifier}")
                        return
                if identifier.get('type', 'file') == 'true':
                    # This is a force to match
                    # save the values for the platform
                    for item, value in platform.items():
                        setattr(self, item, value)
                    self._logger.debug(f"{self.info_str}: Identified platform using {identifier}")
                    return
        self._logger.debug(f"{self.info_str}: Unable to identify platform. Platform List: {[platform.get('description', platform.get('model')) for platform in self._platforms]}")
                    
    def _set_serial(self) -> None:
        ''' Try to get the serial number of the device and save it to the platform object '''
        if self._serial_location is not None and self._serial_location.get('contents', None) is not None:
            if self._serial_location.get('type', 'file') == 'file':
                self.serial = get_file_regex(self._serial_location['file'], self._serial_location['contents'])
                if self.serial is not None:
                    self.serial = self.serial.string.replace('\x00', '')
            elif self._serial_location.get('type', 'file') == 'process' and self._serial_location.get('cmd', None) is not None:
                try:
                    sn = get_cmd_regex(self._serial_location['cmd'], self._serial_location['contents'])
                    if sn is not None:
                        self.serial = sn.string
                except Exception as e:
                    self._logger.warning(f"{self.info_str}: Unable to get serial number from process: {e}, serial location: {self._serial_location}")

    @property
    def platform_matched(self) -> bool:
        ''' Return True if the platform was matched '''
        if self.model is None:
            return self.model is not None
        return True
    
    def get_gpio_out(self, gpio_id, name=None, pull=PULL.NONE, log_level=INFO, initial_state=0) -> GpioOut:
        ''' Get a gpio out pin.  Gpio_id can be a string (passed to convert), an int, or a tuple (chip, pin) '''
        if not self.platform_matched:
            raise ValueError(f'{self.info_str}: Platform has not been identified')
        if self.gpio_lib is None:
            raise ValueError(f'{self.info_str}: GPIO Library not identified.  Unable to open a GPIO')
        if isinstance(gpio_id, tuple) and len(gpio_id) == 2 and isinstance(gpio_id[0], int) and isinstance(gpio_id[1], int):
            gpio_tuple = gpio_id
        else:
            gpio_tuple = tuple(self.gpio_tuple(gpio_id))
        return self.gpio_lib.GpioOut(gpio_tuple[1], gpio_tuple[0], name=name, pull=pull, log_level=log_level, initial_state=initial_state)

    def get_gpio_in(self, gpio_id, name=None, pull=PULL.DOWN, event=EVENT.BOTH, debounce_ms=100, callback=None, log_level=INFO, start_polling=True) -> GpioIn:
        ''' Get a gpio in pin.  Gpio_id can be a string (passed to convert), an int, or a tuple (chip, pin) '''
        if not self.platform_matched:
            raise ValueError(f'{self.info_str}: Platform has not been identified')
        if self.gpio_lib is None:
            raise ValueError(f'{self.info_str}: GPIO Library not identified.  Unable to open a GPIO')
        if isinstance(gpio_id, tuple) and len(gpio_id) == 2 and isinstance(gpio_id[0], int) and isinstance(gpio_id[1], int):
            gpio_tuple = gpio_id
        else:
            gpio_tuple = tuple(self.gpio_tuple(gpio_id))
        return self.gpio_lib.GpioIn(gpio_tuple[1], gpio_tuple[0], name=name, pull=pull, event=event, debounce_ms=debounce_ms,
                                  callback=callback, log_level=log_level, start_polling=start_polling)

    def spi_buses(self) -> tuple:
        ''' Returns a tuple listing the spi bus numbers that are available (only applicable on Linux).  I.e. (0,1) or (0,) '''
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
        dev_files = os.listdir('/dev')
        i2c_buses = ()
        for dev_file in dev_files:
            if 'i2c-' in dev_file:
                match = re.search("^i2c-(?P<i2c_bus>[0-9]*)$", dev_file)
                if match:
                    i2c_buses += (int(match.group('i2c_bus')),)
        return i2c_buses


def get_file_regex(filename:str, re_string:str) -> re.Match|None:
    ''' Check if file exists, open it, and return a regex search object using the provided search string '''
    if not os.path.exists(filename):
        return None
    with open(filename, 'r', encoding='utf-8') as input_file:
        file_contents = input_file.read().replace('\x00', '')
    return re.search(re_string, file_contents)


def get_cmd_regex(cmd:str, re_string:str, timeout=3, **kwargs) -> re.Match|None:
    ''' Execute a command and run the regex against the stdout (stderr is ignored) '''
    out = subprocess.run(cmd, capture_output=True, check=True, shell=True, timeout=timeout, **kwargs)
    return re.search(re_string, out.stdout.decode('utf-8').strip())
