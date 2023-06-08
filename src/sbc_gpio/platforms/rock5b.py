'''
Platform specific file for the Radxa Rock 5B.  This system uses extlinux for boot and supports
dynamic overlays.  GPIO's are provided in the format <chip><bank><number> (i.e. "0A3", "3B3").
'''
import os
import re
from collections import namedtuple
import jinja2
from sbc_gpio import PLATFORM_INFO
from sbc_gpio.dynamic_dts import DynamicOverlay
from ._generic import set_gpio_flags

# select the gpio library for the platform
from sbc_gpio.gpio_libs.gpiod import GpioIn, GpioOut #pylint: disable=W0611,C0411

MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Radxa ROCK 5B'
    }
]

DYNAMIC_OVERLAYS={
    "gpio-ir-tx": {
        "params": [
            {
                "name": "gpio",
                "param_type": "str",
                "param_help": "String to identify the gpio. i.e. 14, 112, 2A6",
                "number_as_str": True
            },
            {
                "name": "active",
                "param_type": "str",
                "values": ["high", "low"],
                "param_help": "Set active [high|low]",
                "default_value": "high"

            },
            {
                "name": "pull",
                "param_type": "str",
                "values": ["high", "low", "none"],
                "param_help": "Set internal pull-up/pull-down or no bias [high|low|none]",
                "default_value": "none"
            }
        ],
        "template": "gpio-basic.dts"
    },
    "gpio-ir-recv": {}
}

SERIAL_NUMBER = '/sys/firmware/devicetree/base/serial-number'
PLATFORM_LOCAL = namedtuple('PLATFORM_LOCAL', ('gpio_re_format', 'serial_path', 'gpio_prefix'))
PLATFORM_SPECIFIC = PLATFORM_INFO(model='Rock5B',
              description='Radxa ROCK 5B',
              gpio_valid_values=(139,138,115,113,111,112,42,41,43,150,63,47,103,110,13,14,109,100,148,44,45,149,114,105,106,107),
              dynamic_overlay_dir='/boot/dynamic_overlay',
              dynamic_overlays=DYNAMIC_OVERLAYS,
              config_file='/boot/config.txt',
              update_extlinux_script='/usr/local/sbin/update_extlinux.sh',
              extlinux_conf='/boot/extlinux/extlinux.conf',
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
    ''' Take a string representing a GPIO and return it as a Tuple -> ([int chip], [int num])'''
    match = re.search(PLATFORM_SPECIFIC.local.gpio_re_format, gpio_str.upper())
    if not match:
        raise ValueError('GPIO Format for Rock 5B is 0A0-3D8.  GPIO chip (0-4) followed by A-D and 0-8 to identify the pin on the GPIO chip. See https://wiki.radxa.com/Rock5/hardware/5b/gpio')
    if '' in match.groups():
        raise ValueError('GPIO Format for Rock 5B is 0A0-3D8.  GPIO chip (0-4) followed by A-D and 0-8 to identify the pin on the GPIO chip. See https://wiki.radxa.com/Rock5/hardware/5b/gpio')
    return int(match.group('chip')), PLATFORM_SPECIFIC.local.gpio_prefix.index(match.group('pinprefix')) * 8 + int(match.group('pinnum'))


def write_dynamic_overlay(overlay:DynamicOverlay):
    ''' Take an dynamic overlay and write it to the dynamic overlay folder '''
    # write the DTS file from the template
    file_loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates'))
    env = jinja2.Environment(loader=file_loader)
    template = env.get_template(overlay.template)

    # Create dict of flags that need to be set
    gpio_flags = []
    for param_name in overlay.param_name_list:
        _param = overlay.get_param(param_name)
        if _param.name == 'active':
            if _param.set_value == 'high':
                gpio_flags.append('ACTIVE_HIGH')
            elif _param.set_value == 'low':
                gpio_flags.append('ACTIVE_LOW')
        elif _param.name == 'pull':
            if _param.set_value == 'none':
                gpio_flags.append('PULL_NONE')
            elif _param.set_value == 'high':
                gpio_flags.append('PULL_HIGH')
            elif _param.set_value == 'low':
                gpio_flags.append('PULL_LOW')

    with open(os.path.join(PLATFORM_SPECIFIC.dynamic_overlay_dir, f"{overlay.name}-{overlay.get_param('gpio').set_value}.dts"), 'w', encoding='utf-8') as output_file:
        output_file.write(template.render(driver=overlay.name,
                                          gpio_number=convert_gpio(str(overlay.get_param('gpio').set_value)),
                                          gpio_chip=convert_gpio_tuple(str(overlay.get_param('gpio').set_value))[0],
                                          gpio_pin=convert_gpio_tuple(str(overlay.get_param('gpio').set_value))[1],
                                          gpio_pin_ctrl=set_gpio_flags(*gpio_flags)))
