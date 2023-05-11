'''
GPIO library:  RPi.GPIO
Supported platforms: Raspberry Pi devices only
'''
import RPi.GPIO as GPIO
from sbc_gpio import PULL, EVENT
from ._generic_gpio import GpioIn as Generic_GpioIn, GpioOut as Generic_GpioOut
from logging_handler import INFO
from threading import Thread
from time import time, sleep
from datetime import timedelta


# initialization
GPIO.setmode(GPIO.BCM) # type: ignore
GPIO.setwarnings(False) # type: ignore


class GpioOut(Generic_GpioOut):
    ''' Class to represent an abstracted GPIO pin using the RPi.GPIO library '''
    def __init__(self, gpio_pin, gpio_chip=0, name=None, pull=PULL.NONE, log_level=INFO, initial_state=0):
        super().__init__(name=name, log_level=log_level, pull=pull)
        self.name = name if name is not None else f"pin:{gpio_pin}"
        self.gpio_pin, self.gpio_chip = gpio_pin, gpio_chip
        GPIO.setup(int(gpio_pin), GPIO.OUT) # type: ignore

    def close(self):
        pass

    @property
    def state(self):
        ''' return curent CS state '''
        return GPIO.input(self.gpio_pin) # type: ignore
    
    def set_high(self):
        ''' Set the pin to on/high '''
        GPIO.output(self.gpio_pin, 1) # type: ignore

    def set_low(self):
        ''' Set the pin to off/low '''
        GPIO.output(self.gpio_pin, 0) # type: ignore



class GpioIn(Generic_GpioIn):
    ''' Class to represent an abstracted GPIO pin using the RPi.GPIO '''
    def __init__(self, gpio_pin, gpio_chip=0, name=None, pull=PULL.DOWN, event=EVENT.BOTH, debounce_ms=100, callback=None, log_level=INFO, start_polling=True):
        super().__init__(name=name, log_level=log_level, event=event, callback=callback, debounce_ms=debounce_ms, pull=pull)
        self.name = name if name is not None else f"chip:{gpio_chip},pin:{gpio_pin}"
        self.gpio_pin, self.gpio_chip = gpio_pin, gpio_chip
        # initialize the chip and pin
        GPIO.setup(int(gpio_pin), GPIO.IN, pull_up_down=GPIO.PUD_UP if pull == PULL.UP else (GPIO.PUD_DOWN if pull == PULL.DOWN else None)) # type: ignore

        if start_polling:
            self.start()

    def close(self):
        pass

    @property
    def state(self):
        ''' Return current CS state '''
        return GPIO.input(self.gpio_pin) # type: ignore
    
    def _event_thread(self): # type: ignore
        ''' Background thread to watch for rising or falling edge '''
        # NOTE: The RPi.GPIO library includes a debounce however it doesn't include separate rising and falling
        triggered = False

        def call_event(event, triggered):
            if self.callback is not None:
                self._logger.debug(f"{self.info_str}: {'RISING' if event else 'FALLING'} state: {triggered}")
                Thread(target=self.callback, kwargs={'event': EVENT.RISING if event else EVENT.FALLING,
                        'time': time(), 'state': triggered}).start()
            else:
                self._logger.info(f"{self.info_str}: {'RISING' if event else 'FALLING'} state: triggered")


        while True and not self._stop_thread:
            try:
                event_triggered = GPIO.wait_for_edge(self.gpio_pin, GPIO.BOTH, bouncetime=self.debounce_ms, timeout=1000) # type: ignore
                triggered_state = self.state
                if event_triggered is not None:
                    # if monitoring for event rising or event falling ONLY, just send the event
                    if self.event != EVENT.BOTH:
                        if (self.event == EVENT.RISING and triggered_state) or (self.event == EVENT.FALLING and not triggered_state):
                            triggered = True
                            call_event(triggered_state, triggered)
                    else:
                        if (triggered_state and self.pull == PULL.DOWN) or (not triggered_state and self.pull != PULL.DOWN):
                            triggered = True
                            call_event(triggered_state, triggered)
                        elif triggered:
                            triggered = False
                            call_event(triggered_state, triggered)

            except Exception as e:
                self._logger.error(f"{self.info_str}: Error in rising event thread: {e}. Restarting...")
                triggered = False
                sleep(.5)

        # reset the stop thread variable
        self._stop_thread = False
