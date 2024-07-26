'''
Class to represent a Rockchip based platform.
'''

import re
from ._base import SbcPlatform_Base

# select the gpio library for the platform
import sbc_gpio.gpio_libs.lib_gpiod as lib_gpiod

# List of dict - platforms supported by this definition
SUPPORTED_PLATFORMS = [
    {
        'model': 'OrangePi5',
        'description': 'Orange Pi 5',
        'gpio_valid_values': [47,46,54,138,139,28,49,48,50,131,132,29,59,58,92,52,35],
        'gpio_lib': lib_gpiod,
        'identifiers': [
            {'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': '^Orange Pi 5$'}
        ],
        '_serial_location': {'type': 'process', 'cmd': "/usr/bin/cat /proc/cpuinfo  | grep -i Serial | awk -F ': ' '{print $2}'", 'contents': '.*'},
        'gpio_re_format': '^(?P<chip>[0-4]?)(?P<pinprefix>[ABCD])(?P<pinnum>[0-7])$',
        'gpio_prefix': ['A', 'B', 'C', 'D']
    },
    {
        'model': 'Rock5B',
        'description': 'Radxa Rock 5B',
        'gpio_valid_values': [139,138,115,113,111,112,42,41,43,150,63,47,103,110,13,14,109,100,148,44,45,149,114,105,106,107],
        'gpio_lib': lib_gpiod,
        'identifiers': [
            {'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': '^Radxa ROCK 5B'}
        ],
        '_serial_location': {'type': 'process', 'cmd': "/usr/bin/cat /proc/cpuinfo  | grep -i Serial | awk -F ': ' '{print $2}'", 'contents': '.*'},
        'gpio_re_format': '^(?P<chip>[0-4]?)(?P<pinprefix>[ABCD])(?P<pinnum>[0-7])$',
        'gpio_prefix': ['A', 'B', 'C', 'D'],
        'gpio_format': 'GPIO Format for Rock 5B is 0A0-3D8.  GPIO chip (0-4) followed by A-D and 0-8 to identify the pin on the GPIO chip. See https://wiki.radxa.com/Rock5/hardware/5b/gpio'
    },
    
]

class SbcPlatformClass(SbcPlatform_Base):
    ''' SBC Platform representing a Rockchip based SBC '''
    _platforms = SUPPORTED_PLATFORMS

    def gpio_convert(self, gpio) -> int | None:
        ''' convert a gpio passed as a string to an integer '''
        gpio_tuple = self.gpio_tuple(gpio=gpio)
        gpio_int = gpio_tuple[0] * 32 + gpio_tuple[1]
        if gpio_int not in self.gpio_valid_values:
            raise ValueError(f'Gpio {gpio_int} not in valid range {self.gpio_valid_values}')
        return gpio_tuple[0] * 32 + gpio_tuple[1]
    
    def gpio_tuple(self, gpio) -> tuple:
        ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
        if str(gpio).isnumeric():
            return 0, int(gpio)
        match = re.search(self.gpio_re_format, gpio.upper())
        if not match:
            raise ValueError("Value " + gpio + " format did not match =>" + self.gpio_format)
        if '' in match.groups():
            raise ValueError("Value " + gpio + f" groups returned empty {match.groups()} =>" + self.gpio_format)
        return int(match.group('chip')), self.gpio_prefix.index(match.group('pinprefix')) * 8 + int(match.group('pinnum'))
