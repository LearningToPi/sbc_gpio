'''
Any scripts created during the install of the sbc_gpio package will execute from here.

How to run update_dynamic_overlay():
====================================
sudo update_dynamic_overlay.py
(this is installed in your path as a script with the install)
NOTE: If you installed this module in a venv, sudo will fail.  You will need to install the
module under root to make sure the script is available to run.
'''

from . import SBCPlatform



def update_dynamic_overlay():
    ''' Initiate a call to start the dynamic overlay generation '''
    device = SBCPlatform()
    device.write_dynamic_overlays()
