'''
Platform specific file for Allwinner based SOC's.  This system uses extlinux for boot and supports
dynamic overlays.  GPIO's are provided in the format P<group><number> (i.e. "PC0", "PG6").

Allwinner GPIO's are calculated using the group letter's position in alphabet - 1 (i.e. A=0, B=1, C=2, etc) * 32 + pin number
i.e.:
  PC7 = 2*32 + 7 = 71
  PH7 = 7*32 + 7 = 231
'''

import re
import string
from ._base import SbcPlatform_Base

# select the gpio library for the platform
import sbc_gpio.gpio_libs.gpiod as gpiod

# List of dict - platforms supported by this definition
SUPPORTED_PLATFORMS = [
    {
        'model': 'CB1',
        'description': 'Bigtree CB1',
        'gpio_valid_values': [71,78,76,74,231,232,230,198,70,79,224,225,77,75,73,200,199,201,234,72],
        'gpio_lib': gpiod,
        'identifiers': [
            {'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': '^BQ-H616$'}
        ],
        '_serial_location': {'type': 'file', 'file': '/sys/firmware/devicetree/base/serial-number', 'contents': '.*'},
        'gpio_re_format': "^P(?P<group>[CFGHILcfghil])(?P<pinnum>[0-9]*)$",
        'gpio_format': 'GPIO Format for Allwinner is P<group><num>. i.e. PC7, PG7'
    }
]
class SbcPlatformClass(SbcPlatform_Base):
    ''' SBC Platform representing an Allwinner based SBC '''
    _platforms = SUPPORTED_PLATFORMS

    def gpio_convert(self, gpio) -> int | None:
        ''' convert a gpio passed as a string to an integer '''
        gpio_tuple = self.gpio_tuple(gpio=gpio)
        gpio_int = gpio_tuple[1]
        if gpio_int not in self.gpio_valid_values:
            raise ValueError(f'Gpio {gpio_int} not in valid range {self.gpio_valid_values}')
        return gpio_int
    
    def gpio_tuple(self, gpio) -> tuple:
        ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
        match = re.search(self.gpio_re_format, gpio.upper())
        if not match:
            raise ValueError(self.gpio_format)
        if '' in match.groups():
            raise ValueError(self.gpio_format)
        return 0, string.ascii_lowercase.find(match.group('group').lower()) * 32 + int(match.group('pinnum'))
