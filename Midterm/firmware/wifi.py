import time
import network

import config

_sta = network.WLAN(network.STA_IF)


def is_connected():
    return _sta.isconnected()


def rssi():
    try:
        return _sta.status("rssi")
    except Exception:
        return None


def connect(timeout_s=config.WIFI_TIMEOUT_S, wdt=None, led=None):
    _sta.active(True)
    if _sta.isconnected():
        return True
    print("WiFi: connecting to", config.WIFI_SSID)
    try:
        _sta.disconnect()
    except OSError:
        pass
    _sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    start = time.ticks_ms()
    while not _sta.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout_s * 1000:
            print("WiFi: timeout")
            return False
        if wdt:
            wdt.feed()
        if led:
            led.value(not led.value())
        time.sleep_ms(250)
    print("WiFi: connected", _sta.ifconfig()[0], "RSSI", rssi())
    return True
