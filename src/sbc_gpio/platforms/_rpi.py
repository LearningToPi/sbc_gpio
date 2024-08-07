'''
Platform specific file for the Raspberry Pi 4B.  This system does NOT use extlinux for boot so
dynamic overlays are not needed or supported.  GPIO's are provided as a simple GPIO # (i.e. 14, 21).
This configuration should also apply to other Raspberry Pi family devices and may be updated in
the future to include other platforms.
'''

from sbc_gpio import PLATFORM_INFO

# select the gpio library for the platform
try:
    # try using The RPi.GPIO library
    from sbc_gpio.gpio_libs.rpi_gpio import GpioIn, GpioOut #pylint: disable=W0611
except ImportError:
    # fallback to gpiod
    from sbc_gpio.gpio_libs.lib_gpiod import GpioIn, GpioOut #pylint: disable=W0611,C0411

PLATFORM_SPECIFIC = PLATFORM_INFO(
              gpio_valid_values=[0, 1, 2, 3, 4, 5, 6, 7 , 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27],
              dynamic_overlay_dir='/boot/dynamic_overlay',
              dynamic_overlays=None,
              config_file='/boot/config.txt',
              update_extlinux_script=None,
              extlinux_conf=None,
              local=None)

MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Raspberry Pi 4 Model B', 'model': 'Pi4B', 'platform': PLATFORM_SPECIFIC
    },
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Raspberry Pi 3 Model B', 'model': 'Pi3B', 'platform': PLATFORM_SPECIFIC
    },
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Raspberry Pi Zero W', 'model': 'PiZeroW', 'platform': PLATFORM_SPECIFIC
    },
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Raspberry Pi Zero', 'model': 'PiZero', 'platform': PLATFORM_SPECIFIC
    }
]

SUPPORTED_MODELS = [x.get('model', 'n/a') for x in MODEL_IDENTIFIER]

SERIAL_NUMBER = '/sys/firmware/devicetree/base/serial-number'
