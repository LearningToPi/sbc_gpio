'''
Class to represent an Intel based platform.
'''

import re
from ._base import SbcPlatform_Base

# select the gpio library for the platform
import sbc_gpio.gpio_libs.gpiod as gpiod

# List of dict - platforms supported by this definition
SUPPORTED_PLATFORMS = [
    {
        'model': 'atom-z8350',
        'description': 'Intel Atom x5-Z8350',
        'gpio_valid_values': [335, 332, 338, 329, 336, 330, 348, 346],
        'gpio_lib': gpiod,
        'identifiers': [
            {'type': 'file', 'file': '/proc/cpuinfo', 'contents': 'x5-Z8350'}
        ],
        '_serial_location': None,
        'gpio_re_format': '"^(?P<chip>[0-3]?)-(?P<pinnum>[0-9]*)$',
        'gpio_chip_offset': (414, 341, 314, 228),
        'gpio_format': 'GPIO chip (0-3) followed by a "-" and then the pin number. For Atomic Pi see https://download.fosc.space/atomic_pi/guide/html/gpio.html'
    }    
]

class SbcPlatformClass(SbcPlatform_Base):
    ''' SBC Platform representing a Rockchip based SBC '''
    _platforms = SUPPORTED_PLATFORMS

    def gpio_convert(self, gpio) -> int | None:
        ''' convert a gpio passed as a string to an integer '''
        if gpio.isnumeric() and int(gpio) in self.gpio_valid_values:
            return int(gpio)
        gpio_tuple = self.gpio_tuple(gpio=gpio)
        gpio_int = self.gpio_chip_offset[gpio_tuple[0]] + gpio_tuple[1]
        if gpio_int not in self.gpio_valid_values:
            raise ValueError(f'Gpio {gpio_int} not in valid range {self.gpio_valid_values}')
        return gpio_int
    
    def gpio_tuple(self, gpio) -> tuple:
        ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
        match = re.search(self.gpio_re_format, gpio.upper())
        if not match:
            raise ValueError("Value " + gpio + " format did not match =>" + self.gpio_format)
        if '' in match.groups():
            raise ValueError("Value " + gpio + f" groups returned empty {match.groups()} =>" + self.gpio_format)
        return int(match.group('chip')), int(match.group('pinnum'))
