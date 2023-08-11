'''
Platform specific file for the Radxa Rock 5B.  This system uses extlinux for boot and supports
dynamic overlays.  GPIO's are provided in the format <chip><bank><number> (i.e. "0A3", "3B3").
'''

from sbc_gpio import PLATFORM_INFO

# select the gpio library for the platform
from sbc_gpio.gpio_libs.gpiod import GpioIn, GpioOut #pylint: disable=W0611,C0411

SERIAL_NUMBER = '/sys/firmware/devicetree/base/serial-number'

PLATFORM_SPECIFIC = PLATFORM_INFO(
              gpio_valid_values=(58, 57, 55, 42, 43, 47, 52, 53, 48, 45, 37, 39, 59, 63, 60, 5, 6, 38, 54, 51, 50, 49, 56, 40, 46, 36, 61, 44),
              dynamic_overlay_dir=None,
              dynamic_overlays=None,
              config_file=None,
              update_extlinux_script=None,
              extlinux_conf=None,
              local=None)


MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'StarFive VisionFive V2', 'model': 'VisionFive-2', 'platform': PLATFORM_SPECIFIC
    }
]

SUPPORTED_MODELS = [x.get('model', 'n/a') for x in MODEL_IDENTIFIER]

GPIO_ERROR = 'GPIO Format is a numeric number <64. For StarFive VisionFive 2 see https://doc-en.rvspace.org/VisionFive2/PDF/VisionFive2_40-Pin_GPIO_Header_UG.pdf'

def convert_gpio(gpio_str:str|int) -> int:
    ''' convert a gpio passed as a string to an integer '''
    if (isinstance(gpio_str, int) or gpio_str.isnumeric()) and int(gpio_str) in PLATFORM_SPECIFIC.gpio_valid_values:
        return int(gpio_str)
    raise ValueError(f'Gpio {gpio_str} not in valid range {PLATFORM_SPECIFIC.gpio_valid_values}')

def convert_gpio_tuple(gpio_str:str|int) -> tuple:
    ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
    return 0, convert_gpio(gpio_str)
