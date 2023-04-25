from ._test_base import DevTest_Base, DevTest_Results, DEBUG, INFO, ERROR, WARNING, CRITICAL
from time import time, sleep
from sbc_gpio.gpio_libs._generic_gpio import GpioIn
from threading import Lock

TEST_NAME = 'Button GPIOD'
TEST_DESCRIPTION = 'Test an button connected to a GPIO'
PASS_THRESHOLD = 0

class DevTest_Button(DevTest_Base):
    ''' Class for a button using gpiod with edge monitoring.
        Requires a GpioPin class for cross platform support. 
        Calling class should pass platform appropriate derivitive '''
    def __init__(self, gpio:GpioIn, log_level=INFO):
        super().__init__(log_level)
        self._pin = gpio
        self._pin.callback = self.__button_callback
        self._events = []
        self._event_lock = Lock()

    def close(self):
        self._pin.close()
        
    @property
    def is_test_ok(self):
        return True

    def __button_callback(self, event, **kwargs):
        with self._event_lock:
            self._logger.info(f"Input event {event}, state: {kwargs.get('state')}")
            self.__events.append((kwargs.get('time'), event))

    def _start_thread_iterations(self, run_secs=10, iterations=None, interval=.5):
        ''' Run the thread checking for button events '''
        with self._testing_lock:
            with self._event_lock:
                # clear any events
                self.__events = []
            stop_time = time() + run_secs
            start_time = time()
            while time() < stop_time and not self._stop_tests:
                with self._event_lock:
                    if iterations is not None and len(self.__events) >= iterations:
                        break
                sleep(interval)
            end_time = time()
            with self._event_lock:
                iter_run = len(self.__events)
            self.test_results = DevTest_Results(iterations=iter_run, iter_success=iter_run,
                                                parameters={'run_secs': run_secs, 'iterations': iterations, 'interval': interval},
                                                start_time=start_time, end_time=end_time, pass_threshold=PASS_THRESHOLD,
                                                name=TEST_NAME, description=TEST_DESCRIPTION, pass_on_zero=True)
        
    def _start_thread_time(self, *args, **kwargs):
        self._start_thread_iterations(*args, **kwargs)
