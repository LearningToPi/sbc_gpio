import unittest
from logging_handler import create_logger, INFO, DEBUG
from time import sleep

import sbc_gpio

logger = create_logger(INFO, name='tester')

gpio_tests = {
    'Rock5B': {
        'gpio_string': ['4B3', '3C2', '3A4', '0B5', '1B1'],
        'gpio_out': '3A7',
        'gpio_in': '3B6'
    }
}


class devtesterTest(unittest.TestCase):
    def test_1_get_platform(self):
        logger.info('===================================== %s', self._testMethodName)
        platform = sbc_gpio.SBCPlatform(INFO)
        logger.info(f"Device Platform: {platform}")
        self.assertTrue(isinstance(platform, sbc_gpio.SBCPlatform))
        logger.info(f"Valid GPIO's: {platform.gpio_valid_values}")
        platform_tests = gpio_tests[platform.model]
        for gpio_string in platform_tests['gpio_string']:
            gpio_val = platform.convert_gpio(gpio_string)
            logger.info(f"GPIO {gpio_string} converts to {gpio_val}. GPIO Valid? {gpio_val in platform.gpio_valid_values}")
            self.assertTrue(gpio_val in platform.gpio_valid_values)
        # test gpio output and input
        gpio_in_events = 0
        def in_callback(**kwargs):
            nonlocal gpio_in_events
            logger.info(f"Event: {kwargs.get('event')} State: {kwargs.get('state')}")
            gpio_in_events += 1
        gpio_in = platform.get_gpio_in(platform_tests['gpio_in'], event='rising', callback=in_callback)
        gpio_out = platform.get_gpio_out(platform_tests['gpio_out'])
        logger.info('Press the input button >= 5 times...')
        logger.info('LED Output will run for 15 seconds...')
        for i in range(15):
            gpio_out.set_high()
            sleep(.5)
            gpio_out.set_low()
            sleep(.5)
        self.assertGreaterEqual(gpio_in_events, 5)
        gpio_in.stop()
        del gpio_in
        del gpio_out
