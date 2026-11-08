import _thread, time
from machine import Pin

def blink(pin_no, delay_ms):
    led = Pin(pin_no, Pin.OUT)
    while True:
        led.value(not led.value())
        time.sleep_ms(delay_ms)

_thread.start_new_thread(blink, (26, 500))  
_thread.start_new_thread(blink, (27, 100)) 
blink(2, 1000)                              

# chill vậy ???