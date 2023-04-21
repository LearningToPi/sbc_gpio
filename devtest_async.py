from logging_handler import create_logger, INFO
import gpiod
from threading import Thread, Lock
from time import sleep, time
from datetime import timedelta
from RPLCD.i2c import CharLCD
from bmx280_spi import Bmx280Spi, Bmx280Readings, MODE_NORMAL
from dht11_spi import DHT11_Spi, DhtReadings, DHT22_Spi
import lirc
from lirc.exceptions import LircError
import socket
from serial import Serial
import string
import random
import asyncio


LED_CHIP = 0
LED_GPIO = 24 # Rock5B GPIO3_C1, GPIO 113 - PI4 GPIO0_23

BUTTON_CHIP = 0
BUTTON_GPIO = 23 # Rock5B GPIO3_B6, GPIO 110 - PI4 GPIO0_25

BMX280_SPI_BUS = 1
BMX280_SOFT_CS_PIN = 13
BMX280_SOFT_CS_CHIP = 0

DHT11_SPI_BUS = 0
DHT11_SOFT_CS_PIN = 26
DHT11_SOFT_CS_CHIP = 0
DHT22 = True

I2C_CONFIG = {
    'i2c_expander': 'PCF8574', 
    'port': 1,  # Rock 5B port 7 - PI4 1
    'address': 0x27, 
    'cols': 16, 
    'rows': 2, 
    'charmap': 'A00', 
    'auto_linebreaks': True, 
    'backlight_enabled': True
}

IR_SEND_SOCK = '/var/run/lirc/lircd'
IR_RECV_SOCK = '/var/run/lirc/lircd1'

SER_1_DEV = '/dev/ttyS0'
SER_2_DEV = '/dev/ttyUSB0'
SER_BAUDRATES = [9600, 115200, 230400, 460800, 576000, 921600]
SER_BLOCK_SIZES = [64, 128, 256, 512, 1024, 2048]
SER_SEND_DELAY_ADD = .20

RUN_TIME = 300

logger = create_logger(INFO)

# DHT11 - temp and humidity

# BMP280 SPI - pressure and temp


# Serial in/out

# IR Transmitter

# IR Receiver

class I2cDisplay:
    ''' Class to manage and update the I2C display '''
    def __init__(self):
        i2c_config = I2C_CONFIG
        self.i2c_display = CharLCD(**i2c_config)
        self.i2c_display.clear()
        self.i2c_display.write_string('LearningToPi.com')
        self._lock = Lock()
        self._data = {}

    def led_set(self, value):
        Thread(target=self.set_thread, kwargs={'param': 'led', 'value': value}).start()

    def button_set(self, value):
        Thread(target=self.set_thread, kwargs={'param': 'button', 'value': value}).start()

    def bmx280_set(self, temp, press):
        Thread(target=self.set_thread, kwargs={'param': 'bmp280-temp', 'value': temp}).start()
        Thread(target=self.set_thread, kwargs={'param': 'bmp280-press', 'value': press}).start()

    def dht_set(self, temp, humidity):
        Thread(target=self.set_thread, kwargs={'param': 'dht11-temp', 'value': temp}).start()
        Thread(target=self.set_thread, kwargs={'param': 'dht11-humidity', 'value': humidity}).start()
        
    def set_thread(self, param:str, value):
        with self._lock:
            self._data[param] = value
        self.update_display()

    def update_display(self):
        ''' Update the display data '''
        with self._lock:
            self.i2c_display.cursor_pos = (0, 0)
            self.i2c_display.write(0xff if self._data.get('led') == 1 else 0x02)


async def run_tests():
    tasks = []
    # init i2c Display
    display = I2cDisplay()

    # start the LED flashing
    new_task = asyncio.create_task(flash_LED(run_for=RUN_TIME, display=display))
    tasks.append(new_task)

    # start the button press polling
    #new_task = asyncio.create_task(button_press_edge(run_for=RUN_TIME, display=display))
    #tasks.append(new_task)

    # start BME280 SPI polling
    new_task = asyncio.create_task(sensor_bmx_280_spi(run_for=RUN_TIME, display=display))
    tasks.append(new_task)

    # start DHT polling
    new_task = asyncio.create_task(sensor_dht11_spi(run_for=RUN_TIME, display=display))
    tasks.append(new_task)

    # start IR Transmitter
    new_task = asyncio.create_task(ir_transmit(run_for=RUN_TIME, display=display))
    tasks.append(new_task)

    # start Serial
    new_task = asyncio.create_task(ser_send_receive(run_for=RUN_TIME, display=display))
    tasks.append(new_task)

    # wait for threads
    for task in tasks:
        await task

async def flash_LED(run_for=30, display=None):
    ''' Flash the LED for x seconds '''
    chip = gpiod.chip(str(LED_CHIP), gpiod.chip.OPEN_BY_NUMBER)
    led = chip.get_line(LED_GPIO)
    led_config = gpiod.line_request()
    led_config.consumer = 'Test-LED'
    led_config.request_type = gpiod.line_request.DIRECTION_OUTPUT
    led.request(led_config)
    stop_time = time() + run_for
    logger.info('Starting LED Flash...')
    while time() < stop_time:
        led.set_value(0 if led.get_value() else 1)
        if display is not None:
            display.led_set(led.get_value())
        await asyncio.sleep(.5)
    logger.info('Ending LED Flash.')

async def button_press_polling(run_for=30, display=None):
    ''' Wait for a button press and log a message '''
    chip = gpiod.chip(str(BUTTON_CHIP), gpiod.chip.OPEN_BY_NUMBER)
    button = chip.get_line(BUTTON_GPIO)
    button_config = gpiod.line_request()
    button_config.consumer = 'Test-Button'
    button_config.request_type = gpiod.line_request.DIRECTION_INPUT
    button_config.flags = gpiod.line_request.FLAG_BIAS_PULL_DOWN
    button.request(button_config)
    press_counter = 0
    stop_time = time() + run_for
    logger.info('Starting Button press polling...')
    while time() < stop_time:
        if button.get_value() > 0:
            logger.info('Button Pressed!')
            press_counter += 1
            if display is not None:
                display.button_set(1)
            while button.get_value() > 0 and time() < stop_time:
                # wait until the button is released before checking for a button press again
                await asyncio.sleep(.1)
            display.button_set(0)
        await asyncio.sleep(.1)
    logger.info(f'Ending Button press polling.  Button pressed {press_counter} times.')

async def button_press_edge(run_for=30, display=None):
    ''' Use edge notification for processing a button press as opposed to polling '''
    chip = gpiod.chip(str(BUTTON_CHIP), gpiod.chip.OPEN_BY_NUMBER)
    button = chip.get_line(BUTTON_GPIO)
    button_config = gpiod.line_request()
    button_config.consumer = 'Test-Button-Edge'
    button_config.request_type = gpiod.line_request.EVENT_BOTH_EDGES
    button_config.flags = gpiod.line_request.FLAG_BIAS_PULL_DOWN
    button.request(button_config)
    press_counter = 0
    stop_time = time() + run_for
    button_state = button.get_value()
    logger.info('Starting button press rising/falling edge...')
    while time() < stop_time:
        event_triggered = button.event_wait(timedelta(seconds=(stop_time - time())))
        if event_triggered:
            event = button.event_read()
            if event.event_type == gpiod.line_event.RISING_EDGE and button_state != event.event_type:
                logger.info('Button Rising Edge Triggered!')
                if display is not None:
                    display.button_set(1)
                button_state = event.event_type
            elif event.event_type == gpiod.line_event.FALLING_EDGE and button_state != event.event_type:
                logger.info('Button Falling Edge Triggered!')   
                press_counter += 1
                if display is not None:
                    display.button_set(0)
                button_state = event.event_type
    logger.info(f'Ending button press rising/falling edge. Button pressed {press_counter} times.')

async def sensor_bmx_280_spi(run_for=30, display=None):
    ''' Start monitoring the BME280 SPI sensor '''
    bmx = Bmx280Spi(spiBus=BMX280_SPI_BUS, cs_pin=BMX280_SOFT_CS_PIN, cs_chip=BMX280_SOFT_CS_CHIP, logger=logger)
    bmx.set_power_mode(MODE_NORMAL)
    bmx.set_sleep_duration_value(3)
    bmx.set_temp_oversample(1)
    bmx.set_pressure_oversample(1)
    bmx.set_filter(0)
    success_count = 0
    total_count = 0
    stop_time = time() + run_for
    logger.info('Starting BMX sensor polling...')
    while time() < stop_time:
        total_count += 1
        try:
            reading = bmx.update_readings()
            logger.info(f"BMX Sensor: {str(reading)}")
            if reading is not None:
                success_count += 1
            if display is not None and reading is not None:
                display.bmx280_set(temp=round(reading.temp_f,1), press=round(reading.pressure_psi,1))
        except Exception as e:
            logger.error(f'Error reading BMX: {e}')
        await asyncio.sleep(1)
    logger.info(f'Ending BMX sensor polling. {success_count}/{total_count} reads successful.')

async def sensor_dht11_spi(run_for=30, display=None):
    ''' Start monitoring the DHT11 sensor using the SPI bus '''
    dht = DHT11_Spi(spiBus=DHT11_SPI_BUS, cs_pin=DHT11_SOFT_CS_PIN, cs_chip=DHT11_SOFT_CS_CHIP, logger=logger, dht22=DHT22)
    success_count = 0
    total_count = 0
    stop_time = time() + run_for
    logger.info('Starting DHT11 sensor polling...')
    while time() < stop_time:
        total_count += 1
        try:
            reading = dht.read()
            logger.info(f"DHT11 Sensor: {str(reading)}")
            if reading is not None:
                success_count += 1
            if display is not None and reading is not None:
                display.dht_set(temp=round(reading.temp_f,1), humidity=round(reading.humidity,0))
        except Exception as e:
            logger.error(f'Error reading DHT: {e}')
        await asyncio.sleep(1)
    logger.info(f'Ending DHT11 sensor polling. {success_count}/{total_count} reads successful.')

async def ir_transmit(run_for=30, display=None, ir_timeout=1):
    ''' Start the IR transmitter and receiver '''
    lirc_tx = lirc.Client(lirc.LircdConnection(address=IR_SEND_SOCK))
    remotes = lirc_tx.list_remotes()
    remote = remotes[0] if isinstance(remotes, list) else remotes
    keys = lirc_tx.list_remote_keys(remote)
    send_count = 0
    receive_count = 0
    stop_time = time() + run_for
    logger.info(f'Starting IR TX/RX (remote {remote}...')
    lirc_rx_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    lirc_rx_socket.connect(IR_RECV_SOCK)
    lirc_rx = lirc.LircdConnection(socket=lirc_rx_socket)
    i = 0
    while time() < stop_time:
        if i >= len(keys):
            i = 0
        command = keys[i].split(' ')[1]
        command_received = False
        logger.info(f"Sending IR Command {command} for remote {remote}")
        lirc_tx.send_start(remote, command)
        await asyncio.sleep(1)
        lirc_tx.send_stop(remote, command)
        send_count += 1
        data = ''
        ir_break_time = time() + ir_timeout
        while time() < ir_break_time and time() < stop_time:
            sleep(.05)
            try:
                data += lirc_rx.readline()
            except Exception as e:
                logger.error(f"Failed reading IR Receiver: {e}")
            if command in data:
                command_received = True
                break
        if command_received:
            logger.info(f"Received IR command {command}")
            receive_count += 1
        else:
            logger.error(f"Failed to receive IR command {command}")
        i += 1
        await asyncio.sleep(.5)
    logger.info(f'Stopping IR TX/RX. {receive_count}/{send_count} IR TX signals were received.')


async def ser_send_receive(run_for=30, display=None):
    ''' Start initialize 2 serial ports to send and receive data at different speeds and multiple block sizes '''
    ser1 = Serial(SER_1_DEV, baudrate=SER_BAUDRATES[0])
    ser2 = Serial(SER_2_DEV, baudrate=SER_BAUDRATES[0])
    # clear receive queues
    ser1.read_all()
    ser2.read_all()
    random_chars = string.ascii_letters + string.digits
    sent_rates = [[0] * len(SER_BAUDRATES), [0] * len(SER_BAUDRATES)]   # [sent using ser1, send using ser2]
    sent_sizes = [[0] * len(SER_BLOCK_SIZES), [0] * len(SER_BLOCK_SIZES)]   # [sent using ser1, send using ser2]
    recv_rates = [[0] * len(SER_BAUDRATES), [0] * len(SER_BAUDRATES)]  # [received on ser2, received on ser1]
    recv_sizes = [[0] * len(SER_BLOCK_SIZES), [0] * len(SER_BLOCK_SIZES)]  # [received on ser2, received on ser1]
    stop_time = time() + run_for
    logger.info(f'Starting UART TX/RX {SER_1_DEV} <--> {SER_2_DEV}, rates: {SER_BAUDRATES}, blocksizes: {SER_BLOCK_SIZES}...')
    while time() < stop_time:
        for baudrate in SER_BAUDRATES:
            for block_size in SER_BLOCK_SIZES:
                ser1.baudrate = ser2.baudrate = baudrate
                data_send = ''.join([random.choice(random_chars) for x in range(block_size)]).encode() + b'\n'
                ser1.write(data_send)
                sent_rates[0][SER_BAUDRATES.index(baudrate)] += 1
                sent_sizes[0][SER_BLOCK_SIZES.index(block_size)] += 1
                await asyncio.sleep((block_size * 8 / baudrate) + SER_SEND_DELAY_ADD)
                data_recv = ser2.read_all()
                if data_send == data_recv:
                    recv_rates[0][SER_BAUDRATES.index(baudrate)] += 1
                    recv_sizes[0][SER_BLOCK_SIZES.index(block_size)] += 1
                    logger.info(f"Sent {SER_1_DEV} ({baudrate}baud)/({block_size}bytes) OK")
                else:
                    logger.warning(f"Sent {SER_1_DEV} ({baudrate}baud)/({block_size}bytes) FAILED")
                if time() > stop_time:
                    break
                data_send = ''.join([random.choice(random_chars) for x in range(block_size)]).encode() + b'\n'
                ser2.write(data_send)
                sent_rates[1][SER_BAUDRATES.index(baudrate)] += 1
                sent_sizes[1][SER_BLOCK_SIZES.index(block_size)] += 1
                await asyncio.sleep((block_size * 8 / baudrate) + SER_SEND_DELAY_ADD)
                data_recv = ser1.read_all()
                if data_send == data_recv:
                    recv_rates[1][SER_BAUDRATES.index(baudrate)] += 1
                    recv_sizes[1][SER_BLOCK_SIZES.index(block_size)] += 1
                    logger.info(f"Sent {SER_2_DEV} ({baudrate}baud)/({block_size}bytes) OK")
                else:
                    logger.warning(f"Sent {SER_2_DEV} ({baudrate}baud)/({block_size}bytes) FAILED")
                if time() > stop_time:
                    break
            if time() > stop_time:
                break
        if time() > stop_time:
            break
    ser1.close()
    ser2.close()
    logger.info(f"{SER_1_DEV}: ({sum(recv_rates[0])}/{sum(sent_rates[0])}) (baud:recv/sent): {', '.join([f'{SER_BAUDRATES[i]}:{recv_rates[0][i]}/{sent_rates[0][i]}' for i in range(len(SER_BAUDRATES))])}")
    logger.info(f"{SER_2_DEV}: ({sum(recv_rates[1])}/{sum(sent_rates[1])}) (baud:recv/sent): {', '.join([f'{SER_BAUDRATES[i]}:{recv_rates[1][i]}/{sent_rates[1][i]}' for i in range(len(SER_BAUDRATES))])}")
    logger.info(f"{SER_1_DEV}: ({sum(recv_rates[0])}/{sum(sent_rates[0])}) (bs:recv/sent): {', '.join([f'{SER_BLOCK_SIZES[i]}:{recv_sizes[0][i]}/{sent_sizes[0][i]}' for i in range(len(SER_BLOCK_SIZES))])}")
    logger.info(f"{SER_2_DEV}: ({sum(recv_rates[1])}/{sum(sent_rates[1])}) (bs:recv/sent): {', '.join([f'{SER_BLOCK_SIZES[i]}:{recv_sizes[1][i]}/{sent_sizes[1][i]}' for i in range(len(SER_BLOCK_SIZES))])}")


if __name__ == '__main__':
    asyncio.run(run_tests())