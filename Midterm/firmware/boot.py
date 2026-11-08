import gc

import wifi

for _attempt in range(3):
    if wifi.connect():
        break

if wifi.is_connected():
    try:
        import ntptime
        ntptime.settime()   
        print("NTP: time synced")
    except Exception as e:
        print("NTP: failed", e)

gc.collect()
