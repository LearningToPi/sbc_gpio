'''
Platform specific file for Raspberry Pi devices.  This system does NOT use extlinux for boot so
dynamic overlays are not needed or supported.  GPIO's are provided as a simple GPIO # (i.e. 14, 21).
This configuration should also apply to other Raspberry Pi family devices and may be updated in
the future to include other platforms.
'''

from ._base import SbcPlatform_Base

# select the gpio library for the platform
gpiod = None
rpi_gpio = None
try:
    # try using The RPi.GPIO library
    import sbc_gpio.gpio_libs.rpi_gpio as rpi_gpio #pylint: disable=W0611
except ImportError:
    # fallback to gpiod
    import  sbc_gpio.gpio_libs.gpiod as gpiod #pylint: disable=W0611,C0411

GPIO_VALID_VALUES = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27]
MODEL_FILE = '/sys/firmware/devicetree/base/model'
SERIAL_FILE = '/sys/firmware/devicetree/base/serial-number'

# List of dict - platforms supported by this definition
SUPPORTED_PLATFORMS = [
    {
        'model': 'Pi4B',
        'description': 'Raspberry Pi 4 Model B',
        'gpio_valid_values': GPIO_VALID_VALUES,
        'gpio_lib': rpi_gpio if rpi_gpio is not None else gpiod,
        'identifiers': [{'type': 'file', 'file': MODEL_FILE, 'contents': '^Raspberry Pi 4 Model B'}],
        '_serial_location': {'type': 'file', 'file': SERIAL_FILE, 'contents': '.*'}
    },
    {
        'model': 'Pi4B',
        'description': 'Raspberry Pi 3 Model B',
        'gpio_valid_values': GPIO_VALID_VALUES,
        'gpio_lib': rpi_gpio if rpi_gpio is not None else gpiod,
        'identifiers': [{'type': 'file', 'file': MODEL_FILE, 'contents': '^Raspberry Pi 3 Model B'}],
        '_serial_location': {'type': 'file', 'file': SERIAL_FILE, 'contents': '.*'}
    },
    {
        'model': 'Pi4B',
        'description': 'Raspberry Pi Zero W',
        'gpio_valid_values': GPIO_VALID_VALUES,
        'gpio_lib': rpi_gpio if rpi_gpio is not None else gpiod,
        'identifiers': [{'type': 'file', 'file': MODEL_FILE, 'contents': '^Raspberry Pi Zero W$'}],
        '_serial_location': {'type': 'file', 'file': SERIAL_FILE, 'contents': '.*'}
    },
    {
        'model': 'Pi4B',
        'description': 'Raspberry Pi Zero',
        'gpio_valid_values': GPIO_VALID_VALUES,
        'gpio_lib': rpi_gpio if rpi_gpio is not None else gpiod,
        'identifiers': [{'type': 'file', 'file': MODEL_FILE, 'contents': '^Raspberry Pi Zero$'}],
        '_serial_location': {'type': 'file', 'file': SERIAL_FILE, 'contents': '.*'}
    }


]
class SbcPlatformClass(SbcPlatform_Base):
    ''' SBC Platform representing an Allwinner based SBC '''
    _platforms = SUPPORTED_PLATFORMS
