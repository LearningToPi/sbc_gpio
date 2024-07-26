'''
Platform specific file for the Radxa Rock 5B.  This system uses extlinux for boot and supports
dynamic overlays.  GPIO's are provided in the format <chip><bank><number> (i.e. "0A3", "3B3").
'''
import re
from collections import namedtuple
from sbc_gpio import PLATFORM_INFO

# select the gpio library for the platform
from sbc_gpio.gpio_libs.lib_gpiod import GpioIn, GpioOut #pylint: disable=W0611,C0411

SERIAL_NUMBER = None

PLATFORM_LOCAL = namedtuple('PLATFORM_LOCAL', ('gpio_re_format', 'gpio_chip_offset'))

PLATFORM_SPECIFIC = PLATFORM_INFO(
              gpio_valid_values=(335, 332, 338, 329, 336, 330, 348, 346),
              dynamic_overlay_dir=None,
              dynamic_overlays=None,
              config_file=None,
              update_extlinux_script=None,
              extlinux_conf=None,
              local=PLATFORM_LOCAL(gpio_re_format="^(?P<chip>[0-3]?)-(?P<pinnum>[0-9]*)$",
                                   gpio_chip_offset=(414, 341, 314, 228)))


MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/proc/cpuinfo', 'contents': 'x5-Z8350', 'description': 'Intel Atom x5-Z8350', 'model': 'atom-z8350', 'platform': PLATFORM_SPECIFIC
    }
]

SUPPORTED_MODELS = [x.get('model', 'n/a') for x in MODEL_IDENTIFIER]

GPIO_ERROR = 'GPIO Format is:  GPIO chip (0-3) followed by a "-" and then the pin number. For Atomic Pi see https://download.fosc.space/atomic_pi/guide/html/gpio.html'

def convert_gpio(gpio_str:str) -> int:
    ''' convert a gpio passed as a string to an integer '''
    if gpio_str.isnumeric() and int(gpio_str) in PLATFORM_SPECIFIC.gpio_valid_values:
        return int(gpio_str)
    gpio_tuple = convert_gpio_tuple(gpio_str=gpio_str)
    gpio_int = PLATFORM_SPECIFIC.local.gpio_chip_offset[gpio_tuple[0]] + gpio_tuple[1]
    if gpio_int not in PLATFORM_SPECIFIC.gpio_valid_values:
        raise ValueError(f'Gpio {gpio_int} not in valid range {PLATFORM_SPECIFIC.gpio_valid_values}')
    return gpio_int

def convert_gpio_tuple(gpio_str:str) -> tuple:
    ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
    match = re.search(PLATFORM_SPECIFIC.local.gpio_re_format, gpio_str.upper())
    if not match:
        raise ValueError("Value " + gpio_str + " format did not match =>" + GPIO_ERROR)
    if '' in match.groups():
        raise ValueError("Value " + gpio_str + f" groups returned empty {match.groups()} =>" + GPIO_ERROR)
    return int(match.group('chip')), int(match.group('pinnum'))

