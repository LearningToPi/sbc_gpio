'''
Class to represent a RISC-V based platform using a StarFive SoC.
'''

import re
from ._base import SbcPlatform_Base

# select the gpio library for the platform
import sbc_gpio.gpio_libs.lib_gpiod as lib_gpiod

# List of dict - platforms supported by this definition
SUPPORTED_PLATFORMS = [
    {
        'model': 'VisionFive-2',
        'description': 'StarFive VisionFive V2',
        'gpio_valid_values': [58, 57, 55, 42, 43, 47, 52, 53, 48, 45, 37, 39, 59, 63, 60, 5, 6, 38, 54, 51, 50, 49, 56, 40, 46, 36, 61, 44],
        'gpio_lib': lib_gpiod,
        'identifiers': [
            {'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'StarFive VisionFive V2'}
        ],
        '_serial_location': {'type': 'file', 'file': '/sys/firmware/devicetree/base/serial-number', 'contents': '.*'},
        'gpio_format': 'GPIO Format is a numeric number <64. For StarFive VisionFive 2 see https://doc-en.rvspace.org/VisionFive2/PDF/VisionFive2_40-Pin_GPIO_Header_UG.pdf'
    }    
]

class SbcPlatformClass(SbcPlatform_Base):
    ''' SBC Platform representing a Rockchip based SBC '''
    _platforms = SUPPORTED_PLATFORMS

    def gpio_convert(self, gpio) -> int | None:
        ''' convert a gpio passed as a string to an integer '''
        if (isinstance(gpio, int) or gpio.isnumeric()) and int(gpio) in self.gpio_valid_values:
            return int(gpio)
        raise ValueError(f'Gpio {gpio} not in valid range {self.gpio_valid_values}')
    
    def gpio_tuple(self, gpio) -> tuple:
        ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
        return 0, self.gpio_convert(gpio)
