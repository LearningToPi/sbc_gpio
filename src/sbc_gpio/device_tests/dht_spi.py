from ._test_base import DevTest_Base, DevTest_Results, DEBUG, INFO, ERROR, WARNING, CRITICAL
from time import time, sleep
from dht11_spi import DHT11_Spi, DHT22_Spi

TEST_NAME = 'DHT11 over SPI'
TEST_DESCRIPTION = 'Read from a DHT11 or DHT22 sensor using the SPI bus with dht11_spi library'
PASS_THRESHOLD = .75

class DevTest_DHT(DevTest_Base):
    ''' Class for a DHT11 / DHT22 sensor using the dht11_spi library.
        The SPI bus is used to read the signals from the DHT sensor (vastly improved reliability over bit banging gpio library) '''
    def __init__(self, spi_bus:int, gpio_tuple:tuple, dht22=False, log_level=INFO):
        super().__init__(log_level)
        self._gpio_tuple = gpio_tuple
        if dht22:
            self._dht = DHT22_Spi(spiBus=spi_bus, cs_chip=self._gpio_tuple[0], cs_pin=self._gpio_tuple[1])
        else:
            self._dht = DHT11_Spi(spiBus=spi_bus, cs_chip=self._gpio_tuple[0], cs_pin=self._gpio_tuple[1])

    def close(self):
        self._dht.close()
    
    @property
    def is_test_ok(self):
        return True

    def _start_thread_iterations(self, iterations, interval=1, run_secs=None):
        ''' Run the blink test for a specified number of iterations '''
        with self._testing_lock:
            iter_run, iter_success = 0, 0
            if interval < self._dht.min_interval:
                self._logger.info(f"{self.info_str}: interval {interval} less than min interval of {self._dht.min_interval}. Using {self._dht.min_interval}")
                interval = self._dht.min_interval
            start_time = time()
            while iter_run < iterations and not self._stop_tests:
                try:
                    reading = self._dht.read()
                    if reading is not None:
                        iter_success += 1
                        self._logger.info(f"{self.info_str}: {'DHT22' if self._dht.dht22 else 'DHT11'} reading: {reading}")
                    else:
                        self._logger.warning(f"{self.info_str}: Error reading DHT")
                except Exception as e:
                    self._logger.warning(f"{self.info_str}: Error reading DHT: {e}")
                finally:
                    iter_run += 1
                    sleep(interval)
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'iterations': iterations, 'interval': interval,
                                                            'gpio': str(self._gpio_tuple)},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)

    def _start_thread_time(self, run_secs=10, iterations=None, interval=1):
        ''' Run the blink test for a specified number of seconds '''
        with self._testing_lock:
            iter_run, iter_success = 0, 0
            if interval < self._dht.min_interval:
                self._logger.info(f"{self.info_str}: interval {interval} less than min interval of {self._dht.min_interval}. Using {self._dht.min_interval}")
                interval = self._dht.min_interval
            start_time = time()
            stop_time = time() + run_secs
            while time() < stop_time and not self._stop_tests:
                try:
                    reading = self._dht.read()
                    if reading is not None:
                        iter_success += 1
                        self._logger.info(f"{self.info_str}: {'DHT22' if self._dht.dht22 else 'DHT11'} reading: {reading}")
                    else:
                        self._logger.warning(f"{self.info_str}: Error reading DHT")
                except Exception as e:
                    self._logger.error(f"{self.info_str}: Error reading DHT: {e}")
                finally:
                    iter_run += 1
                    sleep(interval)
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'run_secs': run_secs, 'interval': interval,
                                                            'gpio': str(self._gpio_tuple)},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)
