from collections import namedtuple
from sbc_gpio import PLATFORM_INFO

# select the gpio library for the platform
from sbc_gpio.gpio_libs.gpiod import GpioIn, GpioOut

MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Raspberry Pi 4 Model B'
    }
]

SERIAL_NUMBER = '/sys/firmware/devicetree/base/serial-number'

PLATFORM_LOCAL = namedtuple('PLATFORM_LOCAL', ('serial_path'))
PLATFORM_SPECIFIC = PLATFORM_INFO(model='Pi4B',
              description='Raspberry Pi 4 Model B',
              gpio_valid_values=[0, 1, 2, 3, 4, 5, 6, 7 , 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
              local=PLATFORM_LOCAL(serial_path='/sys/firmware/devicetree/base/serial-number'))
