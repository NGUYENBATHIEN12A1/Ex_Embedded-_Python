from machine import Pin
from time import sleep_ms
led = Pin(2, Pin.OUT)
button = Pin(4, Pin.IN, Pin.PULL_UP)
total_presses = 0
last_state = 1
while True:
    current_state = button.value()
    if current_state == 0:
        led.value(1)
        print("Button Pressed")
        sleep_ms(50)
        while button.value() == 0:
            sleep_ms(10)
        led.value(0)
        total_presses += 1
        print("Button Released")
        print("Total Presses:", total_presses)
        sleep_ms(50)
    else:
        led.value(0)

    sleep_ms(10)