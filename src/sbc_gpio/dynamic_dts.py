'''
These classes are used to represent a dynamic overlay.  The dynamic overlay is a workaround
for SBC's that use extlinux for bootng.  Unlike the typical method you may be used to with a
Raspberry Pi, extlinux doesn't support passing parameters to an overlay.  All overlays must be
compiled as complete DTB files.  The Dynamic Overlay will compile a DTB after generating a
DTS file using the parameters from the /boot/config.txt (default for most platforms) file.

Only a limited number of drivers are supported.  Check the platform specific configuration
for the list of supported dynamic overlays.

For comparison:

RPI-4 overlay to enable gpio-ir-tx on a GPIO:
============================================
(in /boot/config.txt)
dtoverlay=gpio-ir-tx,gpio_pin=18

Using dynamic overlay on a extlinux system: (Rock Pi 5B used as an example)
==========================================
(in /boot/config.txt)
dynamic_overlay=gpio-ir-tx,gpio=3b3

After adding the dynamic Overlay to the /boot/config.txt file, run "update_dynamic_overlay.py"
to generate the DTS and DTBO files.  For each platform, before editing the extlinux.conf file
we need to run the platform specific tool to run their update on extlinux.conf first.  For
exeample, "sudo update_extlinux.sh" is used to regenerate the extlinux.conf file from the
/boot/config.txt parameters.  THIS WILL REMOVE ALL DYNAMIC OVERLAYS!  The 
"update_dynamic_overlay.py" tool will run "update_extlinux.sh" first, then add the dynamic
overlays after the extlinux.conf file is updated.

NOTE:  When using dynamic overlays, be sure to use "update_dynamic_overlay.py" INSTEAD of
the platform specific "update_extlinux.sh" command, otherwise your dynamic overlays will be
lost on next boot.

NOTE!!!  "update_dynamic_overlay,py" MUST be run as root or with sudo!  This will read the
contents of the /boot/config.txt file, create DTS/DTBO files in "/boot/dynamic_overlay" and
write changes to "/boot/extlinux/extlinux.conf".

How to run:
==========
sudo update_dynamic_overlay.py
(this is installed in your path as a script with the install. If you installed the package
using a venv, be sure to active the venv first!)
'''

import logging

class OverlayParam:
    ''' Represent a parameter in an overlay '''
    def __init__(self, name:str, param_type:str, number_as_str=False, param_help='No additional help available', values=None, default_value=None, set_value=None):
        self.name = name
        if param_type in ['str', 'string']:
            self.param_type = str
        elif param_type in ['int', 'integer']:
            self.param_type = int
        elif param_type in ['bool', 'boolean']:
            self.param_type = bool
        elif param_type in ['float', 'decimal']:
            self.param_type = float
        else:
            self.param_type = None
        self.number_as_str = number_as_str
        self.param_help = param_help
        self.values = values if values is not None else []
        self.default_value = default_value
        self.set_value = default_value if set_value is None else set_value

    def __str__(self):
        ''' Print the parameter help as a line '''
        return f"({'required' if self.default_value is None else 'optional'}) " +  \
                str(self.values) if self.values else '' + \
                f"(DEFAULT: {self.default_value})" if self.default_value else '' + \
                self.param_help

    def update_value(self, value):
        ''' Update the set value.  Verify type and if in values list '''
        if self.param_type is not None:
            if self.number_as_str and isinstance(value, int) or isinstance(value, float):
                value = str(value)
            if not isinstance(value, self.param_type):
                raise ValueError(f"Unable to set value for {self.name} to {value}. Does not match type {self.param_type}")
        if len(self.values) != 0:
            if value not in self.values:
                raise ValueError(f"Unable to set value for {self.name} to {value}. Supported values: {self.values}")
        self.set_value = value

    @property
    def ok(self):
        ''' Return True if parameter value is set '''
        return self.set_value is not None


class DynamicOverlay:
    ''' Represent an overlay '''
    def __init__(self, name:str, template='gpio_basic.dts.j2', params=None):
        ''' Create overlay instance from the configuration file '''
        self.name = name
        self.template = template
        self.params = []
        if isinstance(params, list):
            for _param in params:
                try:
                    self.params.append(OverlayParam(**_param))
                except Exception as ex:
                    logging.error('Unable to import parameter for %s: %s', self.name, _param)
                    raise ex
        else:
            raise ValueError(f"Expecting a list of parameters and received {type(params)}")

    @property
    def ok(self) -> bool:
        ''' Return True if all required parameters are configured, else False '''
        return len(self.missing_params) == 0

    @property
    def missing_params(self) -> list:
        ''' Return a list of required parameters that are missing '''
        missing_params = []
        for _param in self.params:
            if not _param.ok:
                missing_params.append(_param.name)
        return missing_params

    @property
    def param_name_list(self) -> list:
        ''' Return a list of all available parameters '''
        return [_overlay_param.name for _overlay_param in self.params]

    def get_param(self, param_name:str) -> OverlayParam:
        ''' Return a specific parameter '''
        for _param in self.params:
            if _param.name == param_name:
                return _param
        raise ValueError(f'Unknown parameter {param_name}.  Parameters are {self.param_name_list}')

    def set_params(self, params:dict):
        ''' Update the params for the overlay.  Verify all params set '''
        for item, value in params.items():
            if item not in self.param_name_list:
                logging.error('Parameter %s not a valid parameter', item)
                raise ValueError(f"Paramter {item} not a valid parameter")
            self.get_param(item).update_value(value)
        for _param in self.params:
            if not _param.ok:
                raise ValueError(f"Not all required parameters configured. {_param} is required")
