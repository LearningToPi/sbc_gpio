'''
PyPi Package: sbc_gpio
Homepage: https://www.learningtopi.com/python-modules-applications/sbc_gpio/
Git: https://github.com/LearningToPi/sbc_gpio

Description:
===========
Calling the module directly can be used for either printing the model and serial number
of the SBC device as it is identified, or executing a series of tests based on test classes
available in the sbc_gpio/device_tests folder.

Executing tests requires a config file that includes the GPIO info needed for each of the tests.
A sample configuration file can be generated using the CLI options outlined below:


Usage Example:
=============

>> Output the platform info
$ python3 -m sbc_gpio
2023-04-30 22:59:55,337 - SBCPlatform - INFO - SBCPlatform: Platform identified as Rock5B (Radxa ROCK 5B)
###################################
SBC Model:        Rock5B
SBC Description:  Radxa ROCK 5B
SBC Serial:       ***************
SPI Buses:        1, 0
I2C Buses:        7, 6, 4, 1, 0, 9
###################################

>> Create a configuration file
$ python3 -m sbc_gpio --write-config --config configs/test.json
Sample configuration written to 'configs/test.json'.

>> Execute a test using a configuration file
$ python3 -m sbc_gpio --config configs/rock5b.json  --time 30
2023-04-30 23:05:19,705 - SBCPlatform - INFO - SBCPlatform: Platform identified as Rock5B (Radxa ROCK 5B)
2023-04-30 23:05:19,706 - GpioOut - INFO - GpioOut (chip:3,pin:7): Requesting GPIO...
2023-04-30 23:05:19,707 - GpioIn - INFO - GpioIn (chip:3,pin:14): Requesting GPIO...
2023-04-30 23:05:19,707 - GpioIn - INFO - GpioIn (chip:3,pin:14): Starting event thread...
2023-04-30 23:05:19,708 - dht11_spi - INFO - DHT22_Spi (SPI0-500.0kHz): Opening
2023-04-30 23:05:19,708 - dht11_spi - INFO - DHT22_Spi (SPI0-500.0kHz): Setting SPI bus speed from 50000000 to 500000
2023-04-30 23:05:19,709 - root - INFO - Bmx280Spi (SPI1.13): Opening
<...>
2023-04-30 23:05:53,880 - SBC_Tester - INFO - Test LED Flash GPIOD PASSED: 15 / 15 iterations successful. 100.0%, pass theshold is 100%
2023-04-30 23:05:53,882 - SBC_Tester - INFO - Test Button GPIOD PASSED: 0 / 0 iterations successful. 100%, pass theshold is 0%
2023-04-30 23:05:53,882 - SBC_Tester - INFO - Test DHT11 over SPI PASSED: 13 / 14 iterations successful. 93.0%, pass theshold is 75.0%
2023-04-30 23:05:53,882 - SBC_Tester - INFO - Test BMP280/BME280 over SPI PASSED: 28 / 28 iterations successful. 100.0%, pass theshold is 75.0%
2023-04-30 23:05:53,883 - SBC_Tester - INFO - Test I2C Display PASSED: 27 / 27 iterations successful. 100.0%, pass theshold is 100%
2023-04-30 23:05:53,883 - SBC_Tester - INFO - Test IR GPIO TX/RX PASSED: 22 / 22 iterations successful. 100.0%, pass theshold is 75.0%
2023-04-30 23:05:53,883 - SBC_Tester - INFO - Test UART PASSED: 108 / 108 iterations successful. 100.0%, pass theshold is 75.0%
2023-04-30 23:05:53,883 - SBC_Tester - INFO -     ttyS2: (54/54) (baud:recv/sent): 9600:12/12, 115200:12/12, 230400:12/12, 460800:6/6, 576000:6/6, 921600:6/6
2023-04-30 23:05:53,884 - SBC_Tester - INFO -     ttyUSB1: (54/54) (baud:recv/sent): 9600:12/12, 115200:12/12, 230400:12/12, 460800:6/6, 576000:6/6, 921600:6/6
2023-04-30 23:05:53,884 - SBC_Tester - INFO -     ttyS2: (54/54) (bs:recv/sent): 64:9/9, 128:9/9, 256:9/9, 512:9/9, 1024:9/9, 2048:9/9
2023-04-30 23:05:53,884 - SBC_Tester - INFO -     ttyUSB1: (54/54) (bs:recv/sent): 64:9/9, 128:9/9, 256:9/9, 512:9/9, 1024:9/9, 2048:9/9
2023-04-30 23:05:53,884 - SBC_Tester - INFO - Completed test run for 30 seconds.
2023-04-30 23:05:53,963 - DevTest_IR - INFO - DevTest_IR: lircd TX process pid: 282170 stopping...
2023-04-30 23:05:54,071 - DevTest_IR - INFO - DevTest_IR: lircd RX process pid: 282187 stopping...
2023-04-30 23:05:55,243 - GpioOut - INFO - GpioOut (chip:3,pin:7): Releasing GPIO...
2023-04-30 23:05:55,244 - GpioOut - INFO - GpioOut (chip:3,pin:7): Releasing GPIO...
2023-04-30 23:05:55,244 - DevTest_UART - INFO - DevTest_UART: Closing ttyS2...
2023-04-30 23:05:55,244 - DevTest_UART - INFO - DevTest_UART: Closing ttyUSB1...

    
MIT License

Copyright (c) 2022 LearningToPi <contact@learningtopi.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
import argparse
import os
import json
import sys
from time import sleep
from logging_handler import create_logger, INFO, WARNING
from sbc_gpio.device_tests.led_gpiod import DevTest_LED
from sbc_gpio.device_tests.button_gpiod import DevTest_Button
from sbc_gpio.device_tests.i2c_display import DevTest_I2CDisp
from sbc_gpio.device_tests.ir import DevTest_IR
from sbc_gpio.device_tests.dht_spi import DevTest_DHT
from sbc_gpio.device_tests.bmx_spi import DevTest_BMX
from sbc_gpio.device_tests.uart import DevTest_UART
from . import SBCPlatform


def run_test(run_secs=60, led=None, btn=None, dht=None, ir=None, dht_spi=None, dht22=False, bmx=None, bmx_spi=None, i2c=None, log_level=INFO,
             uart_dev=None, usb_dev=None):
    ''' Run a basic set of tests on the specified devices.  All tests are run in parallel for a number of seconds.'''
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
    platform = SBCPlatform(log_level=WARNING)
    print('#' * 35)
    print('SBC Model:       ', platform.model)
    print('SBC Description: ', platform.description)
    print('SBC Serial:      ', platform.serial)
    print('SPI Buses:       ', ', '.join([str(x) for x in platform.spi_buses()]))
    print('I2C Buses:       ', ', '.join([str(x) for x in platform.i2c_buses()]))
    print('#' * 35)
