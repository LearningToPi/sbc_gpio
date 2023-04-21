from ._test_base import DevTest_Base, DevTest_Results, DEBUG, INFO, ERROR, WARNING, CRITICAL
from time import time, sleep
from sbc_gpio.gpio_libs._generic_gpio import GpioOut

TEST_NAME = 'LED Flash GPIOD'
TEST_DESCRIPTION = 'Flash an LED connected to a GPIO using the GPIOD library'
PASS_THRESHOLD = 1

class DevTest_LED(DevTest_Base):
    ''' Class for an LED flash using gpiod 
        Requires a GpioPin class for cross platform support.
        Calling class should pass platform appropriate derivitive '''
    def __init__(self, gpio:GpioOut, log_level=INFO):
        super().__init__(log_level)
        self.__pin = gpio

    def close(self):
        self.__pin.set_low()
        self.__pin.close()
    
    @property
    def is_test_ok(self):
        return True

    def _start_thread_iterations(self, iterations, on_ms=1000, off_ms=1000, run_secs=None):
        ''' Run the blink test for a specified number of iterations '''
        with self._testing_lock:
            iter_run, iter_success = 0, 0
            start_time = time()
            while iter_run < iterations and not self._stop_tests:
                try:
                    self.__pin.set_high()
                    sleep(on_ms / 1000)
                    self.__pin.set_low()
                    sleep(off_ms / 1000)
                    iter_success += 1
                except Exception as e:
                    self._logger.error(f"{self.info_str}: Error flashing LED: {e}")
                finally:
                    iter_run += 1
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'iterations': iterations, 'on_ms': on_ms, 'off_ms': off_ms,
                                                            'gpio': str(self.__pin)},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)

    def _start_thread_time(self, run_secs=10, iterations=None, on_ms=1000, off_ms=1000):
        ''' Run the blink test for a specified number of seconds '''
        with self._testing_lock:
            iter_run, iter_success = 0, 0
            start_time = time()
            stop_time = time() + run_secs
            while time() < stop_time and not self._stop_tests:
                try:
                    self.__pin.set_high()
                    sleep(on_ms / 1000)
                    self.__pin.set_low()
                    sleep(off_ms / 1000)
                    iter_success += 1
                except Exception as e:
                    self._logger.error(f"{self.info_str}: Error flashing LED: {e}")
                finally:
                    iter_run += 1
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'run_secs': run_secs, 'on_ms': on_ms, 'off_ms': off_ms,
                                                            'gpio': str(self.__pin)},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)