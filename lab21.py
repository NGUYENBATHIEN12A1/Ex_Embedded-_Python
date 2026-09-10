from machine import Pin
from time import sleep

# Cấu hình GPIO 2 làm output
led = Pin(2, Pin.OUT)


# Hàm nhấp nháy LED
def blink_led(number_of_blinks, delay_time):
    for i in range(number_of_blinks):
        led.value(1)       # LED ON
        sleep(delay_time)

        led.value(0)       # LED OFF
        sleep(delay_time)


# =========================
# CHƯƠNG TRÌNH CHÍNH
# =========================

while True:

    # 1. Nhấp nháy chậm: 1 giây
    blink_led(1, 1)

    # 2. Nhấp nháy nhanh: 200 ms
    blink_led(1, 0.2)

    # 3. Nhấp nháy 3 lần
    blink_led(3, 0.2)

    # Nghỉ 2 giây
    sleep(2)