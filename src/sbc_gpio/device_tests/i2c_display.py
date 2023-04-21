from ._test_base import DevTest_Base, DevTest_Results, DEBUG, INFO, ERROR, WARNING, CRITICAL
from time import time, sleep
from RPLCD.i2c import CharLCD

TEST_NAME = 'I2C Display'
TEST_DESCRIPTION = 'Connect to an I2C display and print data to the screen'
PASS_THRESHOLD = 1

class DevTest_I2CDisp(DevTest_Base):
    ''' Class for an I2C display. 
        Required Parameters:
            port (int) - I2C bus where the display is located
         '''
    def __init__(self, port, address=0x27, cols=16, rows=2, charmap='A00', auto_linebreaks=True, backlight_enabled=True, i2c_expander='PCF8574', log_level=INFO):
        super().__init__(log_level)
        self._params = {
            'port': port,
            'address': address,
            'cols': cols,
            'rows': rows,
            'charmap': charmap,
            'auto_linebreaks': auto_linebreaks,
            'backlight_enabled': backlight_enabled,
            'i2c_expander': i2c_expander
        }
        self._i2c_display = CharLCD(**self._params)
        
    def close(self):
        self._i2c_display.close()
    
    @property
    def is_test_ok(self):
        return True

    def _start_thread_iterations(self, iterations, interval=1, run_secs=None):
        ''' Run the i2c display test for a specified number of iterations '''
        with self._testing_lock:
            iter_run, iter_success = 0, 0
            start_time = time()
            self._i2c_display.clear()
            self._i2c_display.write_string('LearningToPi.com\n\rIteration: ')
            while iter_run < iterations and not self._stop_tests:
                try:
                    self._i2c_display.cursor_pos = (0, 0)
                    self._i2c_display.write_string(f'LearningToPi.com\n\rIteration: {iter_run + 1}')
                    iter_success += 1
                except Exception as e:
                    self._logger.error(f"{self.info_str}: Error Writing to I2C Display: {e}")
                finally:
                    iter_run += 1
                    sleep(interval)
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'iterations': iterations, 'interval': interval}.update(self._params),
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)

    def _start_thread_time(self, run_secs=10, iterations=None, interval=1):
        ''' Run the i2c display test for a specified number of seconds '''
        with self._testing_lock:
            iter_run, iter_success = 0, 0
            start_time = time()
            stop_time = start_time + run_secs
            self._i2c_display.clear()
            self._i2c_display.write_string('LearningToPi.com\n\rIteration: ')
            while time() < stop_time and not self._stop_tests:
                try:
                    self._i2c_display.cursor_pos = (0, 0)
                    self._i2c_display.write_string(f'LearningToPi.com\n\rIteration: {iter_run + 1}')
                    iter_success += 1
                except Exception as e:
                    self._logger.error(f"{self.info_str}: Error Writing to I2C Display: {e}")
                finally:
                    iter_run += 1
                    sleep(interval)
            end_time = time()
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_success, 
                                                parameters={'run_secs': run_secs, 'interval': interval}.update(self._params),
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION)