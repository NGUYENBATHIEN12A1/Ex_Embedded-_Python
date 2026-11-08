import time

import dht
from machine import Pin, SoftI2C

import config
from bh1750 import BH1750
from bmp280 import BMP280

DHT_RETRIES = 3


class Sensors:
    def __init__(self):
        self.dht = dht.DHT22(Pin(config.DHT_PIN))
        self.i2c = SoftI2C(scl=Pin(config.I2C_SCL), sda=Pin(config.I2C_SDA), freq=config.I2C_FREQ)
        self.bmp = None
        self.bh = None
        self._init_i2c()

    def _init_i2c(self):
        if self.bmp is None:
            try:
                self.bmp = BMP280(self.i2c, config.BMP280_ADDR)
            except OSError as e:
                print("BMP280 init error:", e)
        if self.bh is None:
            try:
                self.bh = BH1750(self.i2c, config.BH1750_ADDR)
            except OSError as e:
                print("BH1750 init error:", e)

    def scan(self):
        return [hex(a) for a in self.i2c.scan()]

    def _read_dht(self):
        for i in range(DHT_RETRIES):
            try:
                self.dht.measure()
                return self.dht.temperature(), self.dht.humidity()
            except OSError:
                if i < DHT_RETRIES - 1:
                    time.sleep_ms(2100)
        return None

    def read_all(self):
        self._init_i2c()
        data = {
            "temperature": None,
            "humidity": None,
            "pressure": None,
            "light": None,
        }
        errors = []

        th = self._read_dht()
        if th is None:
            errors.append("dht22")
        else:
            data["temperature"] = round(th[0], 1)
            data["humidity"] = round(th[1], 1)

        if self.bmp is None:
            errors.append("bmp280")
        else:
            try:
                _, p = self.bmp.read()
                data["pressure"] = round(p, 2)
            except OSError:
                errors.append("bmp280")
                self.bmp = None

        if self.bh is None:
            errors.append("bh1750")
        else:
            try:
                data["light"] = round(self.bh.read(), 1)
            except OSError:
                errors.append("bh1750")
                self.bh = None

        data["errors"] = errors
        return data
