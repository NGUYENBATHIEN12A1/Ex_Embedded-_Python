import time

_POWER_ON = 0x01
_RESET = 0x07
_CONT_HRES = 0x10


class BH1750:
    def __init__(self, i2c, addr=0x23):
        self.i2c = i2c
        self.addr = addr
        self.i2c.writeto(addr, bytes([_POWER_ON]))
        self.i2c.writeto(addr, bytes([_RESET]))
        self.i2c.writeto(addr, bytes([_CONT_HRES]))
        time.sleep_ms(180)

    def read(self):
        d = self.i2c.readfrom(self.addr, 2)
        return ((d[0] << 8) | d[1]) / 1.2
