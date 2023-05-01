'''
Base GPIO classes used to represent a in and out GPIO and provide common functionality
across all gpio libraries.
'''
from logging_handler import create_logger
from threading import Thread, Lock
from sbc_gpio import EVENT

class Gpio:
    ''' Base GPIO functions that can be used for all input or output GPIO's '''
    def __init__(self, name, log_level):
        self.name = name if name is not None else f"Generic GPIO"
        self._logger = create_logger(console_level=log_level, name=self.__class__.__name__)

    def __del__(self):
        self.close()

    def close(self):
        pass

    @property
    def info_str(self):
        ''' Returns the info string for the class (used in logging commands) '''
        return f"{self.__class__.__name__} ({self.name})"

class GpioOut(Gpio):
    ''' Base GPIO class to represent a GPIO configured for output '''
    def __init__(self, name, log_level, pull):
        super().__init__(name, log_level)
        self.pull = pull

    def state(self):
        pass

    def set_high(self):
        pass

    set_1 = set_high
    set_on = set_high

    def set_low(self):
        pass

    set_0 = set_low
    set_off = set_low


class GpioIn(Gpio):
    ''' Base GPIO class to represent a GPIO configured for input '''
    def __init__(self, name, log_level, event, callback, debounce_ms, pull):
        super().__init__(name, log_level)
        self._edge_thread = None
        self._stop_thread = False
        self.event = event
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.pull = pull

    def stop(self):
        ''' Stop background event polling '''
        if isinstance(self._edge_thread, Thread) and self._edge_thread.is_alive():
            self._logger.info(f"{self.info_str}: Stopping event thread...")
            self._stop_thread = True
            self._edge_thread.join()

    def start(self):
        ''' Start background event polling '''
        self.stop()
        if self.event == EVENT.RISING or self.event == EVENT.FALLING or self.event == EVENT.BOTH:
            self._logger.info(f"{self.info_str}: Starting event thread...")
            self._edge_thread = Thread(target=self._event_thread, name=f'gpiod-in-thread', daemon=True)
            self._edge_thread.start()

    @property
    def state(self):
        ''' Return current state of the input pin '''
        pass

    @property
    def event_thread_running(self):
        ''' Return True/False if the background event thread is running '''
        if isinstance(self._edge_thread, Thread) and self._edge_thread.is_alive():
            return True
        return False
    
    def _event_thread(self):
        ''' Backgroun thread to watch for rising or falling edges '''
        pass