from . import SBCPlatform
import argparse
import os
import json
import sys
from time import sleep
from logging_handler import create_logger, INFO
from sbc_gpio.device_tests.led_gpiod import DevTest_LED
from sbc_gpio.device_tests.button_gpiod import DevTest_Button
from sbc_gpio.device_tests.i2c_display import DevTest_I2CDisp
from sbc_gpio.device_tests.ir import DevTest_IR
from sbc_gpio.device_tests.dht_spi import DevTest_DHT
from sbc_gpio.device_tests.bmx_spi import DevTest_BMX
from sbc_gpio.device_tests.uart import DevTest_UART


def run_test(run_secs=60, led=None, btn=None, dht=None, ir=None, dht_spi=None, dht22=False, bmx=None, bmx_spi=None, i2c=None, log_level=INFO,
             uart_dev=None, usb_dev=None):
    logger = create_logger(console_level=log_level, name='SBC_Tester')

    # loop through and start each test
    platform = SBCPlatform()
    # only run a test if passed values are not None or empty string
    tests = []
    if led is not None and led != '':
        if platform.gpio_is_valid(led):
            tests.append(DevTest_LED(gpio=platform.get_gpio_out(led), log_level=log_level))
    if btn is not None and btn != '':
        if platform.gpio_is_valid(btn):
            tests.append(DevTest_Button(gpio=platform.get_gpio_in(btn), log_level=log_level))
    if dht is not None and dht != '' and isinstance(dht_spi, int):
        if platform.gpio_is_valid(dht):
            tests.append(DevTest_DHT(spi_bus=dht_spi, dht22=dht22, gpio_tuple=platform.convert_gpio_tuple(dht), log_level=log_level))
    if bmx is not None and bmx != '' and isinstance(bmx_spi, int):
        if platform.gpio_is_valid(bmx):
            tests.append(DevTest_BMX(spi_bus=bmx_spi, gpio_tuple=platform.convert_gpio_tuple(bmx), log_level=log_level))
    if isinstance(i2c, int) and i2c in platform.i2c_buses():
        tests.append(DevTest_I2CDisp(port=i2c, log_level=log_level))
    if isinstance(ir, bool) and ir:
        tests.append(DevTest_IR(log_level=log_level))
    if uart_dev is not None and usb_dev is not None:
        tests.append(DevTest_UART(uart_dev, usb_dev, log_level=log_level))

    # start the tests
    for test in tests:
        logger.info(f'Starting test {test.info_str}')
        test.start(run_secs=run_secs)

    try:
        logger.info('Waiting for tests to complete...')
        sleep(run_secs)

        # check to make sure all tests complete before continuing
        for x in range(10):
            for test in tests:
                if test.is_running:
                    sleep(1)
                    continue

        # print out if any tests failed to complete and results for the completed tests
        for test in tests:
            if test.is_running:
                logger.error(f"Test {test.infostr} failed to complete!  Results not available.")
            else:
                logger.info(test.test_results)
                if test.test_results.details is not None:
                    for line in test.test_results.details:
                        logger.info(f"    {line}")

        logger.info(f'Completed test run for {run_secs} seconds.')
    except KeyboardInterrupt:
        # if Ctrl+C stop all tests
        logger.warning('Keyboard Interrupt caught. Stopping all tests. This may take a few seconds to complete...')
        for test in tests:
            test.stop()
        for x in range(10):
            for test in tests:
                if test.is_running:
                    sleep(1)
                    continue


if __name__ == '__main__':
    # setup the argument parser
    parser = argparse.ArgumentParser(description="Execute a sequence of tests on the SBC GPIO's or if no arguments print the SBC system data.")
    parser.add_argument('--time', required=False, type=int, default=60, help="(60) Number of seconds to run the test")
    parser.add_argument('--config', required=False, type=str, help="Config file to read from or write to")
    parser.add_argument('--output', required=False, type=str, help="Output file for results of the test run")
    parser.add_argument('--write-config', required=False, action='store_true', default=False, help="(False) Write a sample config file (requires config parameter)")
    parser.add_argument('--log-level', dest='log_level', required=False, type=str, default='INFO', help='(INFO) Specify the logging level for the console (DEBUG, INFO, WARN, CRITICAL)')

    args = vars(parser.parse_args())

    print(args)

    if args.get('write_config', False) and args.get('config') is None:
        sys.tracebacklimit=0
        raise ValueError('Parameter "write-config" requires parameter "config"')
    
    if args.get('write_config', False):
        sample_config = {
            'led': '3A7',
            'btn': '3B6',
            'dht': '1D7',
            'dht22': True,
            'dht_spi': 0,
            'bmx': '3B5',
            'bmx_spi': 1,
            'i2c': 7,
            'ir': True,
            "uart_dev": "ttyS0",
            "usb_dev": "ttyUSB0"
        }
        if os.path.isfile(args.get('config', 'sample-config.json')):
            print(f"Config file '{args.get('config', 'sample-config.json')}' already exists")
            overwrite = input("Overwrite file? (N)o/(Y)es: ")
            if overwrite != "Y":
                print("Quitting without writing configuration file.")
                quit(1)
        with open(args.get('config', 'sample-config.json'), 'w', encoding='utf-8') as output_file:
            output_file.write(json.dumps(sample_config, indent=4, default=str))
            print(f"Sample configuration written to '{args.get('config', 'sample-config.json')}'.")
            quit(0)

    if args.get('config', None) is not None:
        with open(args.get('config', 'sample-config.json'), 'r', encoding='utf-8') as input_file:
            config = json.loads(input_file.read())
        run_test(run_secs=args.get('time', 60), **config)
        quit()

    # print the SBC data to the screen
    platform = SBCPlatform()
    print('#' * 35)
    print('SBC Model:       ', platform.model)
    print('SBC Description: ', platform.description)
    print('SBC Serial:      ', platform.serial)
    print('SPI Buses:       ', ', '.join([str(x) for x in platform.spi_buses()]))
    print('I2C Buses:       ', ', '.join([str(x) for x in platform.i2c_buses()]))
    print('#' * 35)

