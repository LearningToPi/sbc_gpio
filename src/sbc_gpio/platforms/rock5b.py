import re
from sbc_gpio import PLATFORM_INFO
from collections import namedtuple

# select the gpio library for the platform
from sbc_gpio.gpio_libs.gpiod import GpioIn, GpioOut

MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Radxa ROCK 5B'
    }
]
SERIAL_NUMBER = '/sys/firmware/devicetree/base/serial-number'
PLATFORM_LOCAL = namedtuple('PLATFORM_LOCAL', ('gpio_re_format', 'serial_path', 'gpio_prefix'))
PLATFORM_SPECIFIC = PLATFORM_INFO(model='Rock5B',
              description='Radxa ROCK 5B',
              gpio_valid_values=(139,138,115,113,111,112,42,41,43,150,63,47,103,110,13,14,109,100,148,44,45,149,114,105,106,107),
              local=PLATFORM_LOCAL(gpio_re_format="^(?P<chip>[0-4]?)(?P<pinprefix>[ABCD])(?P<pinnum>[0-7])$",
                                   serial_path='/sys/firmware/devicetree/base/serial-number',
                                   gpio_prefix=('A', 'B', 'C', 'D')))


def convert_gpio(gpio_str:str) -> int:
    ''' convert a gpio passed as a string to an integer '''
    gpio_tuple = convert_gpio_tuple(gpio_str=gpio_str)
    gpio_int = gpio_tuple[0] * 32 + gpio_tuple[1]
    if gpio_int not in PLATFORM_SPECIFIC.gpio_valid_values:
        raise ValueError(f'Gpio {gpio_int} not in valid range {PLATFORM_SPECIFIC.gpio_valid_values} for device {PLATFORM_SPECIFIC.model}')
    return gpio_tuple[0] * 32 + gpio_tuple[1]

def convert_gpio_tuple(gpio_str:str) -> tuple:
    ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [str prefix], [int num])'''
    match = re.search(PLATFORM_SPECIFIC.local.gpio_re_format, gpio_str.upper())
    if not match:
        raise ValueError('GPIO Format for Rock 5B is 0A0-3D8.  GPIO chip (0-4) followed by A-D and 0-8 to identify the pin on the GPIO chip. See https://wiki.radxa.com/Rock5/hardware/5b/gpio')
    if '' in match.groups():
        raise ValueError('GPIO Format for Rock 5B is 0A0-3D8.  GPIO chip (0-4) followed by A-D and 0-8 to identify the pin on the GPIO chip. See https://wiki.radxa.com/Rock5/hardware/5b/gpio')
    return int(match.group('chip')), PLATFORM_SPECIFIC.local.gpio_prefix.index(match.group('pinprefix')) * 8 + int(match.group('pinnum'))