import sbc_gpio
from logging_handler import create_logger, INFO, DEBUG

logger = create_logger(DEBUG, name='tester')

platform = sbc_gpio.SBCPlatform(DEBUG)
print(platform.model)

platform.write_dynamic_overlays()
print('test123')