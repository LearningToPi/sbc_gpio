'''
Platform specific file for Allwinner based SOC's.  This system uses extlinux for boot and supports
dynamic overlays.  GPIO's are provided in the format P<group><number> (i.e. "PC0", "PG6").

Allwinner GPIO's are calculated using the group letter's position in alphabet - 1 (i.e. A=0, B=1, C=2, etc) * 32 + pin number
i.e.:
  PC7 = 2*32 + 7 = 71
  PH7 = 7*32 + 7 = 231
'''
import os
import re
import string
from collections import namedtuple
import jinja2
from sbc_gpio import PLATFORM_INFO
from sbc_gpio.dynamic_dts import DynamicOverlay
from ._generic import set_gpio_flags

# select the gpio library for the platform
from sbc_gpio.gpio_libs.gpiod import GpioIn, GpioOut #pylint: disable=W0611,C0411

GPIO_FORMAT = 'GPIO Format for Allwinner is P<group><num>. i.e. PC7, PG7'

SERIAL_NUMBER = '/sys/firmware/devicetree/base/serial-number'

PLATFORM_LOCAL = namedtuple('PLATFORM_LOCAL', ('gpio_re_format'))


PLATFORM_SPECIFIC = PLATFORM_INFO(
              gpio_valid_values=(71,78,76,74,231,232,230,198,70,79,224,225,77,75,73,200,199,201,234,72),
              dynamic_overlay_dir='/boot/dynamic_overlay',
              dynamic_overlays=None,
              config_file='/boot/BoardEnv.txt',
              update_extlinux_script=None,
              extlinux_conf=None,
              local=PLATFORM_LOCAL(gpio_re_format="^P(?P<group>[CFGHILcfghil])(?P<pinnum>[0-9]*)$"))


MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'BQ-H616', 'model': 'CB1', 
        'description': 'Bigtree CB1', 'platform': PLATFORM_SPECIFIC
    }
]

SUPPORTED_MODELS = [x.get('model', 'n/a') for x in MODEL_IDENTIFIER]


def convert_gpio(gpio_str:str) -> int:
    ''' convert a gpio passed as a string to an integer '''
    gpio_tuple = convert_gpio_tuple(gpio_str=gpio_str)
    gpio_int = gpio_tuple[1]
    if gpio_int not in PLATFORM_SPECIFIC.gpio_valid_values:
        raise ValueError(f'Gpio {gpio_int} not in valid range {PLATFORM_SPECIFIC.gpio_valid_values}')
    return gpio_int

def convert_gpio_tuple(gpio_str:str) -> tuple:
    ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
    match = re.search(PLATFORM_SPECIFIC.local.gpio_re_format, gpio_str.upper())
    if not match:
        raise ValueError(GPIO_FORMAT)
    if '' in match.groups():
        raise ValueError(GPIO_FORMAT)
    return 0, string.ascii_lowercase.find(match.group('group').lower()) * 32 + int(match.group('pinnum'))
