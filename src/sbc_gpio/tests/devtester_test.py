import unittest
from logging_handler import create_logger, INFO, DEBUG
from time import time, sleep

from sbc_gpio import SBCPlatform, EVENT

from sbc_gpio.device_tests.ir import DevTest_IR
from sbc_gpio.device_tests.led_gpiod import DevTest_LED
from sbc_gpio.device_tests.button_gpiod import DevTest_Button
from sbc_gpio.device_tests.dht_spi import DevTest_DHT
from sbc_gpio.device_tests.bmx_spi import DevTest_BMX
from sbc_gpio.device_tests.i2c_display import DevTest_I2CDisp
from sbc_gpio.device_tests.uart import DevTest_UART

logger = create_logger(INFO, name='tester')

gpio_tests = {
    'Rock5B': {
        'led': '3A7',
        'btn': '3B6',
        'dht': '1D7',
        'dht_spi': 0,
        "dht22": True,
        'bmx': '3B5',
        'bmx_spi': 1,
        'i2c': 7,
        "ir": True,
        "uart_dev": "ttyS2",
        "usb_dev": "ttyUSB1"
    },
    'Pi4B': {
        "led": 17,
        "btn": 27,
        "dht": 5,
        "dht22": True,
        "dht_spi": 0,
        "bmx": 16,
        "bmx_spi": 1,
        "i2c": 1,
        "ir": True,
        "uart_dev": "ttyS0",
        "usb_dev": "ttyUSB0"
    }
}

platform = SBCPlatform()
test_vars = dict(gpio_tests.get(platform.model, {}))


class devtesterTest(unittest.TestCase):
    def test_1_ir_test(self):
        logger.info('===================================== %s', self._testMethodName)
        dev_tester = DevTest_IR(log_level=INFO)
        self.assertTrue(dev_tester.is_test_ok)
        logger.info('----------------- Test 10 iterations blocking')
        dev_tester.start(iterations=10, wait=True)
        logger.info(f'{dev_tester.test_results}')
        self.assertTrue(dev_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        dev_tester.start(run_secs=30, wait=True)
        logger.info(f'{dev_tester.test_results}')
        self.assertTrue(dev_tester.test_results.passed)

    def test_2_led_test(self):
        logger.info('===================================== %s', self._testMethodName)
        pin = platform.get_gpio_out(test_vars.get('led'))
        led_tester = DevTest_LED(pin, log_level=INFO)
        logger.info('----------------- Test 10 iterations blocking')
        led_tester.start(iterations=10, wait=True, on_ms=250, off_ms=750)
        logger.info(f'{led_tester.test_results}')
        self.assertTrue(led_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        led_tester.start(run_secs=10, wait=True, on_ms=750, off_ms=250)
        logger.info(f'{led_tester.test_results}')
        self.assertTrue(led_tester.test_results.passed)

    def test_3_button_test(self):
        logger.info('===================================== %s', self._testMethodName)
        pin = platform.get_gpio_in(test_vars.get('btn'), event=EVENT.RISING)
        button_tester = DevTest_Button(pin, log_level=INFO)
        logger.info('----------------- Test 10 iterations blocking')
        button_tester.start(iterations=10, run_secs=10, wait=True)
        logger.info(f'{button_tester.test_results}')
        self.assertTrue(button_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        button_tester.start(run_secs=10, wait=True)
        logger.info(f'{button_tester.test_results}')
        self.assertTrue(button_tester.test_results.passed)
        pin.close()

    def test_4_dht(self):
        logger.info('===================================== %s', self._testMethodName)
        pin = platform.convert_gpio_tuple(test_vars.get('dht'))
        dht_tester = DevTest_DHT(int(test_vars.get('dht_spi', 0)), pin, log_level=INFO, dht22=test_vars.get('dht22', False))
        logger.info('----------------- Test 10 iterations blocking')
        dht_tester.start(iterations=10, wait=True)
        logger.info(f'{dht_tester.test_results}')
        self.assertTrue(dht_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        dht_tester.start(run_secs=10, wait=True)
        logger.info(f'{dht_tester.test_results}')
        self.assertTrue(dht_tester.test_results.passed)

    def test_5_bmx(self):
        logger.info('===================================== %s', self._testMethodName)
        pin = platform.convert_gpio_tuple(test_vars.get('bmx'))
        bmx_tester = DevTest_BMX(int(test_vars.get('bmx_spi', 1)), pin, log_level=INFO)
        logger.info('----------------- Test 10 iterations blocking')
        bmx_tester.start(iterations=10, wait=True)
        logger.info(f'{bmx_tester.test_results}')
        self.assertTrue(bmx_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        bmx_tester.start(run_secs=10, wait=True)
        logger.info(f'{bmx_tester.test_results}')
        self.assertTrue(bmx_tester.test_results.passed)

    def test_6_i2c(self):
        logger.info('===================================== %s', self._testMethodName)
        i2c_tester = DevTest_I2CDisp(test_vars.get('i2c', 1), log_level=INFO)
        logger.info('----------------- Test 10 iterations blocking')
        i2c_tester.start(iterations=10, wait=True)
        logger.info(f'{i2c_tester.test_results}')
        self.assertTrue(i2c_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        i2c_tester.start(run_secs=10, wait=True)
        logger.info(f'{i2c_tester.test_results}')
        self.assertTrue(i2c_tester.test_results.passed)

    def test_7_uart(self):
        logger.info('===================================== %s', self._testMethodName)
        uart_tester = DevTest_UART(test_vars.get('uart_dev'), test_vars.get('usb_dev'), log_level=DEBUG)
        logger.info('----------------- Test 10 iterations blocking')
        uart_tester.start(iterations=10, wait=True)
        logger.info(f'{uart_tester.test_results}')
        for detail in uart_tester.test_results.details:
            logger.info(f"    {detail}")
        self.assertTrue(uart_tester.test_results.passed)
        logger.info('----------------- Test 10 seconds blocking')
        uart_tester.start(run_secs=120, wait=True)
        logger.info(f'{uart_tester.test_results}')
        for detail in uart_tester.test_results.details:
            logger.info(f"    {detail}")
        self.assertTrue(uart_tester.test_results.passed)

    def test_7_threading(self):
        logger.info('===================================== %s', self._testMethodName)
        bmx_pin = platform.convert_gpio_tuple(test_vars.get('bmx'))
        bmx_tester = DevTest_BMX(1, bmx_pin, log_level=INFO)
        dht_pin = platform.convert_gpio_tuple(test_vars.get('dht'))
        dht_tester = DevTest_DHT(0, dht_pin, log_level=INFO, dht22=True)
        btn_pin = platform.get_gpio_in(test_vars.get('btn'), event=EVENT.RISING)
        btn_tester = DevTest_Button(btn_pin, log_level=INFO)
        led_pin = platform.get_gpio_out(test_vars.get('led'))
        led_tester = DevTest_LED(led_pin, log_level=INFO)
        ir_tester = DevTest_IR(log_level=INFO)
        uart_tester = DevTest_UART(test_vars.get('uart_dev'), test_vars.get('usb_dev'), log_level=INFO)
        i2c_tester = DevTest_I2CDisp(test_vars.get('i2c'), log_level=INFO)
        # verify all tests are ok to run
        self.assertTrue(bmx_tester.is_test_ok and dht_tester.is_test_ok and btn_tester.is_test_ok and led_tester.is_test_ok and ir_tester.is_test_ok and i2c_tester.is_test_ok)
        # start all the threads for 30 seconds
        run_secs=30
        bmx_tester.start(run_secs=run_secs)
        dht_tester.start(run_secs=run_secs)
        btn_tester.start(run_secs=run_secs)
        led_tester.start(run_secs=run_secs)
        ir_tester.start(run_secs=run_secs)
        i2c_tester.start(run_secs=run_secs)
        uart_tester.start(run_secs=run_secs)
        stop_time = time() + run_secs
        while time() < stop_time:
            logger.info(f'Tasks Running:  BMX: {bmx_tester.is_running}, DHT: {dht_tester.is_running}, BTN: {btn_tester.is_running}, LED: {led_tester.is_running}, IR: {ir_tester.is_running}, I2C: {i2c_tester.is_running}')
            sleep(1)
        while bmx_tester.is_running or dht_tester.is_running or btn_tester.is_running or led_tester.is_running or ir_tester.is_running or i2c_tester.is_running:
            logger.info(f'Tasks Running:  BMX: {bmx_tester.is_running}, DHT: {dht_tester.is_running}, BTN: {btn_tester.is_running}, LED: {led_tester.is_running}, IR: {ir_tester.is_running}, I2C: {i2c_tester.is_running}')
            sleep(1)
        self.assertFalse(bmx_tester.is_running and dht_tester.is_running and btn_tester.is_running and led_tester.is_running and ir_tester.is_running and i2c_tester.is_running)
        logger.info(f"BMX results:  {bmx_tester.test_results}")
        logger.info(f"DHT results:  {dht_tester.test_results}")
        logger.info(f"BTN results:  {btn_tester.test_results}")
        logger.info(f"LED results:  {led_tester.test_results}")
        logger.info(f"IR  results:  {ir_tester.test_results}")
        logger.info(f"I2C results:  {i2c_tester.test_results}")
        logger.info(f"UART Results: {uart_tester.test_results}")
        for detail in uart_tester.test_results.details:
            logger.info(f"    {detail}")
        self.assertTrue(bmx_tester.test_results.passed and dht_tester.test_results.passed and btn_tester.test_results.passed and led_tester.test_results.passed and ir_tester.test_results.passed and i2c_tester.test_results.passed and uart_tester.test_results.passed)
