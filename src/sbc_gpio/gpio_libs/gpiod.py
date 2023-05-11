'''
GPIO library:  gpiod
Supported platforms: Most modern SBC devices that support the libgpiod kernel driver
'''
import gpiod
from threading import Thread
from time import time
from datetime import timedelta
from sbc_gpio import PULL, EVENT
from ._generic_gpio import GpioIn as Generic_GpioIn, GpioOut as Generic_GpioOut
from logging_handler import INFO


class GpioOut(Generic_GpioOut):
    ''' Class to represent an abstracted GPIO pin using the gpiod '''
    def __init__(self, gpio_pin, gpio_chip, name=None, pull=PULL.NONE, log_level=INFO, initial_state=0):
        super().__init__(name=name, log_level=log_level, pull=pull)
        self.name = name if name is not None else f"chip:{gpio_chip},pin:{gpio_pin}"
        self.gpio_pin, self.gpio_chip = gpio_pin, gpio_chip
        # initialize the chip and pin
        chip = gpiod.chip(int(gpio_chip), gpiod.chip.OPEN_BY_NUMBER)
        self._pin = chip.get_line(int(self.gpio_pin))
        pin_config = gpiod.line_request()
        pin_config.consumer = name if name is not None else f'{self.info_str}-OUT'
        pin_config.request_type = gpiod.line_request.DIRECTION_OUTPUT
        if pull == PULL.UP:
            pin_config.flags = gpiod.line_request.FLAG_BIAS_PULL_UP
        elif pull == PULL.DOWN:
            pin_config.flags = gpiod.line_request.FLAG_BIAS_PULL_DOWN
        else:
            pin_config.flags = gpiod.line_request.FLAG_BIAS_DISABLE
        self._logger.info(f"{self.info_str}: Requesting GPIO...")
        self._pin.request(pin_config)

        if initial_state == 0:
            self.set_0()
        else:
            self.set_1()

    def close(self):
        self._logger.info(f"{self.info_str}: Releasing GPIO...")
        self._pin.release()

    @property
    def state(self):
        ''' Return current CS state '''
        return self._pin.get_value()

    def set_high(self):
        ''' Set the pin to on/high '''
        self._pin.set_value(1)
    
    def set_low(self):
        ''' Set the pin to off/low '''
        self._pin.set_value(0)

class GpioIn(Generic_GpioIn):
    ''' Class to represent an abstracted GPIO pin using the gpiod '''
    def __init__(self, gpio_pin, gpio_chip, name=None, pull=PULL.DOWN, event=EVENT.BOTH, debounce_ms=100, callback=None, log_level=INFO, start_polling=True):
        super().__init__(name=name, log_level=log_level, event=event, callback=callback, debounce_ms=debounce_ms, pull=pull)
        self.name = name if name is not None else f"chip:{gpio_chip},pin:{gpio_pin}"
        self.gpio_pin, self.gpio_chip = gpio_pin, gpio_chip
        # initialize the chip and pin
        chip = gpiod.chip(str(gpio_chip), gpiod.chip.OPEN_BY_NUMBER)
        self._pin = chip.get_line(int(self.gpio_pin))
        pin_config = gpiod.line_request()
        pin_config.consumer = name if name is not None else f'{self.info_str}-IN'
        pin_config.request_type = gpiod.line_request.DIRECTION_INPUT
        if pull == PULL.UP:
            pin_config.flags = gpiod.line_request.FLAG_BIAS_PULL_UP
        elif pull == PULL.DOWN:
            pin_config.flags = gpiod.line_request.FLAG_BIAS_PULL_DOWN
        else:
            pin_config.flags = gpiod.line_request.FLAG_BIAS_DISABLE
        # set edge request - filter in loop
        pin_config.request_type = gpiod.line_request.EVENT_BOTH_EDGES
        self._logger.info(f"{self.info_str}: Requesting GPIO...")
        self._pin.request(pin_config)
        self._stop_thread = False
        self._edge_thread = None
        if start_polling:
            self.start()

    def close(self):
        self.stop()
        self._logger.info(f"{self.info_str}: Releasing GPIO...")
        self._pin.release()

    @property
    def state(self):
        ''' Return current CS state '''
        return self._pin.get_value()
    
    def _event_thread(self): # type: ignore
        ''' Background thread to watch for rising or falling edge '''
        triggered = False

        def call_event(event, triggered):
            if self.callback is not None:
                self._logger.debug(f"{self.info_str}: {EVENT.RISING.upper() if event.event_type == gpiod.line_event.RISING_EDGE else EVENT.FALLING.upper()} state: {triggered}")
                Thread(target=self.callback, kwargs={'event': EVENT.RISING if event.event_type == gpiod.line_event.RISING_EDGE else EVENT.FALLING,
                      'time': time(), 'state': triggered}).start()
            else:
                self._logger.info(f"{self.info_str}: {EVENT.RISING.upper() if event.event_type == gpiod.line_event.RISING_EDGE else EVENT.FALLING.upper()} state: {triggered}")

        while True and not self._stop_thread:
            try:
                event_triggered = self._pin.event_wait(timedelta(seconds=1))
                if event_triggered:
                    event = self._pin.event_read()
                    # check for another event within the debounce interval
                    bounce_event_triggered = self._pin.event_wait(timedelta(milliseconds=self.debounce_ms))
                    if not bounce_event_triggered:
                        # if monitoring for event rising or event falling ONLY, just send the event
                        if self.event != EVENT.BOTH:
                            if (self.event == EVENT.RISING and event.event_type == gpiod.line_event.RISING_EDGE) or (self.event == EVENT.FALLING and event.event_type == gpiod.line_event.FALLING_EDGE):
                                triggered = True
                                call_event(event, triggered)
                        # otherwise need to track when we are triggered so we don't alert to a release if there was no press!
                        else:
                            if (event.event_type == gpiod.line_event.RISING_EDGE and self.pull == PULL.DOWN) or (event.event_type == gpiod.line_event.FALLING_EDGE and self.pull != PULL.DOWN):
                                triggered = True
                                call_event(event, triggered)
                            elif triggered:
                                triggered = False
                                call_event(event, triggered)
                            
                    event = None
            except Exception as e:
                self._logger.error(f"{self.info_str}: Error in event thread: {e}. Restarting...")
                triggered = False
        # reset the stop thread variable
        self._stop_thread = False
