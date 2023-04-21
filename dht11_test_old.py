import src.dht11_spi
from time import sleep

src.dht11_spi.DEBUG = True

dht22 = src.dht11_spi.DHT22_Spi(spiBus=0, cs_chip=0, cs_pin=26)

while True:
    print(dht22.read())
    sleep(30)

#dht11 = src.dht11_spi.DHT11_Spi(spiBus=0, cs_chip=0, cs_pin=26)
