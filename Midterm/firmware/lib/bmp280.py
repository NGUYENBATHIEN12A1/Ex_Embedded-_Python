import struct
import time

_REG_CALIB = 0x88
_REG_ID = 0xD0
_REG_RESET = 0xE0
_REG_STATUS = 0xF3
_REG_CTRL = 0xF4
_REG_CONFIG = 0xF5
_REG_DATA = 0xF7
_CHIP_IDS = (0x56, 0x57, 0x58, 0x60)
_OSRS_T = 2
_OSRS_P = 5
_MODE_FORCED = 1
_CTRL_FORCED = (_OSRS_T << 5) | (_OSRS_P << 2) | _MODE_FORCED
_MAX_WAIT_MS = 100


def _div(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


def compensate(cal, adc_t, adc_p):
    t1, t2, t3, p1, p2, p3, p4, p5, p6, p7, p8, p9 = cal
    var1 = (((adc_t >> 3) - (t1 << 1)) * t2) >> 11
    var2 = (((((adc_t >> 4) - t1) * ((adc_t >> 4) - t1)) >> 12) * t3) >> 14
    t_fine = var1 + var2
    temp = ((t_fine * 5 + 128) >> 8) / 100

    var1 = t_fine - 128000
    var2 = var1 * var1 * p6
    var2 = var2 + ((var1 * p5) << 17)
    var2 = var2 + (p4 << 35)
    var1 = ((var1 * var1 * p3) >> 8) + ((var1 * p2) << 12)
    var1 = (((1 << 47) + var1) * p1) >> 33
    if var1 == 0:
        raise OSError("BMP280 bad calibration")
    p = 1048576 - adc_p
    p = _div(((p << 31) - var2) * 3125, var1)
    var1 = (p9 * (p >> 13) * (p >> 13)) >> 25
    var2 = (p8 * p) >> 19
    p = ((p + var1 + var2) >> 8) + (p7 << 4)
    return temp, p / 256


class BMP280:
    def __init__(self, i2c, addr=0x76):
        self.i2c = i2c
        self.addr = addr
        chip = self.i2c.readfrom_mem(addr, _REG_ID, 1)[0]
        if chip not in _CHIP_IDS:
            raise OSError("BMP280 not found (id=0x%02x)" % chip)
        self.i2c.writeto_mem(addr, _REG_RESET, b"\xb6")
        time.sleep_ms(5)
        self.cal = struct.unpack("<HhhHhhhhhhhh", self.i2c.readfrom_mem(addr, _REG_CALIB, 24))
        self.i2c.writeto_mem(addr, _REG_CONFIG, b"\x00")

    def _raw(self):
        self.i2c.writeto_mem(self.addr, _REG_CTRL, bytes([_CTRL_FORCED]))
        start = time.ticks_ms()
        time.sleep_ms(5)
        while self.i2c.readfrom_mem(self.addr, _REG_STATUS, 1)[0] & 0x08:
            if time.ticks_diff(time.ticks_ms(), start) > _MAX_WAIT_MS:
                raise OSError("BMP280 timeout")
            time.sleep_ms(5)
        d = self.i2c.readfrom_mem(self.addr, _REG_DATA, 6)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        if adc_p == 0x80000 or adc_t == 0x80000:
            raise OSError("BMP280 no data")
        return adc_t, adc_p

    def read(self):
        temp, pa = compensate(self.cal, *self._raw())
        return temp, pa / 100
