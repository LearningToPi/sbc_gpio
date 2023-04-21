MODEL_IDENTIFIER = [
    {
        'type': 'file', 'file': '/sys/firmware/devicetree/base/model', 'contents': 'Raspberry Pi 4 Model B'
    }
]

MODEL_DESCRIPTION = 'Raspberry Pi 4 Model B'
MODEL_SHORT = 'Pi4B'

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
I2C_DISPLAY_PORT = 1
SER_1_DEV = '/dev/ttyS0'
SER_2_DEV = '/dev/ttyUSB0'