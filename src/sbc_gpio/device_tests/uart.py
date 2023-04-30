from ._test_base import DevTest_Base, DevTest_Results, DEBUG, INFO, ERROR, WARNING, CRITICAL
import os
from serial import Serial
import string
from time import time, sleep
import random

TEST_NAME = 'UART'
TEST_DESCRIPTION = 'Uses CP2102 connected to USB and UART RX/TX pins to test serial communication'
PASS_THRESHOLD = 0.75

SER_BAUDRATES = [9600, 115200, 230400, 460800, 576000, 921600]
SER_BLOCK_SIZES = [64, 128, 256, 512, 1024, 2048]
SER_SEND_DELAY_ADD = .20

class DevTest_UART(DevTest_Base):
    ''' Class for a serial test using UART and a CP2102 '''
    def __init__(self, uart_interface, usb_interface, log_level=INFO, baud_rates=SER_BAUDRATES, block_sizes=SER_BLOCK_SIZES, 
                 send_delay=SER_SEND_DELAY_ADD):
        super().__init__(log_level)
        self._uart_interface = uart_interface
        self._usb_interface = usb_interface
        self._uart_ok = None
        self._uart_dev = None
        self._usb_dev = None
        self.baud_rates = baud_rates
        self.block_sizes = block_sizes
        self.send_delay = send_delay

    def close(self):
        if isinstance(self._uart_dev, Serial):
            self._logger.info(f"{self.info_str}: Closing {self._uart_interface}...")
            self._uart_dev.close()
        if isinstance(self._usb_dev, Serial):
            self._logger.info(f"{self.info_str}: Closing {self._usb_interface}...")
            self._usb_dev.close()

    @property
    def is_test_ok(self):
        if self._uart_ok is not None:
            return self._uart_ok
        try:
            dev_folder = os.listdir('/dev')            
            # check if uart and usb interfaces are present
            if self._uart_interface in dev_folder:
                self._uart_dev = Serial(port='/dev/' + self._uart_interface)
            else:
                raise NameError(f"Device {self._uart_interface} not found!")
                
            if self._usb_interface in dev_folder:
                self._usb_dev = Serial(port='/dev/' + self._usb_interface)
            else:
                raise NameError(f"Device {self._usb_interface} not found!")

            if not isinstance(self._uart_dev, Serial) or not isinstance(self._usb_dev, Serial):
                raise TypeError(f"Unable to initiate Serial interfaces!")
        except Exception as e:
            self._logger.error(f"{self.info_str}: {e}")
            self._uart_dev = None
            self._usb_dev = None
            return False
        return True

    

    def _start_thread_time(self, run_secs, iterations=None):
        if isinstance(self._uart_dev, Serial) and isinstance(self._usb_dev, Serial):
            with self._testing_lock:
                # clear receive queues
                self._uart_dev.read_all()
                self._usb_dev.read_all()
                random_char_list = string.ascii_letters + string.digits
                sent_rates = [[0] * len(SER_BAUDRATES), [0] * len(SER_BAUDRATES)]   # [sent using ser1, send using ser2]
                sent_sizes = [[0] * len(SER_BLOCK_SIZES), [0] * len(SER_BLOCK_SIZES)]   # [sent using ser1, send using ser2]
                recv_rates = [[0] * len(SER_BAUDRATES), [0] * len(SER_BAUDRATES)]  # [received on ser2, received on ser1]
                recv_sizes = [[0] * len(SER_BLOCK_SIZES), [0] * len(SER_BLOCK_SIZES)]  # [received on ser2, received on ser1]
                iter_run = 0
                iter_success = 0
                start_time = time()
                stop_time = time() + run_secs
                while time() < stop_time and not self._stop_tests:
                    for baud_rate in self.baud_rates:
                        # set the serial baud rates
                        self._uart_dev.baudrate = baud_rate
                        self._usb_dev.baudrate = baud_rate
                        
                        for block_size in self.block_sizes:
                            # generate random data and send on both serial interfaces
                            random_data = ''.join([random.choice(random_char_list) for x in range(block_size)]).encode() + b'\n'
                            self._uart_dev.write(random_data)
                            sent_rates[0][self.baud_rates.index(baud_rate)] += 1
                            sent_sizes[0][self.block_sizes.index(block_size)] += 1
                            self._usb_dev.write(random_data)
                            sent_rates[1][self.baud_rates.index(baud_rate)] += 1
                            sent_sizes[1][self.block_sizes.index(block_size)] += 1
                            iter_run += 2
                            sleep((block_size * 8 / baud_rate) + self.send_delay)

                            # read the serial data
                            usb_recv_data = self._usb_dev.read_all()
                            uart_recv_data = self._uart_dev.read_all()

                            # record success / failures
                            if usb_recv_data == random_data:
                                recv_rates[0][self.baud_rates.index(baud_rate)] += 1
                                recv_sizes[0][self.block_sizes.index(block_size)] += 1
                                self._logger.debug(f"{self.info_str}: Sent from {self._uart_interface} ({baud_rate}baud/{block_size}chars) OK")
                                iter_success += 1
                            else:
                                self._logger.warning(f"{self.info_str}: Sent from {self._uart_interface} ({baud_rate}baud/{block_size}chars) FAILED")
                            if uart_recv_data == random_data:
                                recv_rates[1][self.baud_rates.index(baud_rate)] += 1
                                recv_sizes[1][self.block_sizes.index(block_size)] += 1
                                self._logger.debug(f"{self.info_str}: Sent from {self._usb_interface} ({baud_rate}baud/{block_size}chars) OK")
                                iter_success += 1
                            else:
                                self._logger.warning(f"{self.info_str}: Sent from {self._usb_interface} ({baud_rate}baud/{block_size}chars) FAILED")

                            if time() >= stop_time or self._stop_tests:
                                break
                        if time() >= stop_time or self._stop_tests:
                            break
                end_time = time()

                test_details = []
                test_details.append(f"{self._uart_interface}: ({sum(recv_rates[0])}/{sum(sent_rates[0])}) (baud:recv/sent): {', '.join([f'{self.baud_rates[i]}:{recv_rates[0][i]}/{sent_rates[0][i]}' for i in range(len(self.baud_rates))])}")
                test_details.append(f"{self._usb_interface}: ({sum(recv_rates[1])}/{sum(sent_rates[1])}) (baud:recv/sent): {', '.join([f'{self.baud_rates[i]}:{recv_rates[1][i]}/{sent_rates[1][i]}' for i in range(len(self.baud_rates))])}")
                test_details.append(f"{self._uart_interface}: ({sum(recv_sizes[0])}/{sum(sent_sizes[0])}) (bs:recv/sent): {', '.join([f'{self.block_sizes[i]}:{recv_sizes[0][i]}/{sent_sizes[0][i]}' for i in range(len(self.block_sizes))])}")
                test_details.append(f"{self._usb_interface}: ({sum(recv_sizes[1])}/{sum(sent_sizes[1])}) (bs:recv/sent): {', '.join([f'{self.block_sizes[i]}:{recv_sizes[1][i]}/{sent_sizes[1][i]}' for i in range(len(self.block_sizes))])}")
                self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success,
                                                    parameters={'run_secs': run_secs, 'baud_rates': self.baud_rates, 'block_sizes': self.block_sizes},
                                                    start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD, name=TEST_NAME,
                                                    description=TEST_DESCRIPTION, details=test_details)


    _start_thread_iterations = _start_thread_time # type: ignore
    
