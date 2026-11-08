# Part 1 — ESP32 firmware (MicroPython)

The firmware runs on the ESP32. When the board powers up, MicroPython runs `boot.py` first and then `main.py`.
`main.py` uses `sensors.py` to read the sensors, and `sensors.py` uses the two drivers in `lib/`.

```
boot.py ──► wifi.py                      (connect Wi-Fi, sync the clock)
main.py ──► wifi.py, sensors.py, umqtt   (main loop)
sensors.py ──► lib/bmp180.py, lib/bh1750.py, dht (built in)
config.py  ◄── every file reads its settings from here
```

> Click a line number (for example [L14](../../firmware/main.py#L14)) to open that exact line in VS Code. In the HTML version, VS Code may ask once to allow opening the link.

---

## 1.1. `config.py` — settings

This file only holds constants. Keeping them separate means changing the Wi-Fi network or the broker IP never touches the program logic.

| Lines | Code | Explanation |
|---|---|---|
| [L1–2](../../firmware/config.py#L1) | `# ...` | Comment: do not commit the real password to Git. |
| [L4–5](../../firmware/config.py#L4) | `WIFI_SSID`, `WIFI_PASSWORD` | Wi-Fi name and password. The ESP32 only supports 2.4 GHz Wi-Fi. |
| [L6](../../firmware/config.py#L6) | `WIFI_TIMEOUT_S = 15` | Wait at most 15 s for each Wi-Fi connection attempt. |
| [L8](../../firmware/config.py#L8) | `MQTT_HOST` | IP address of the computer running Mosquitto. |
| [L9](../../firmware/config.py#L9) | `MQTT_PORT = 1883` | Default (unencrypted) MQTT port. |
| [L10–11](../../firmware/config.py#L10) | `MQTT_USER`, `MQTT_PASSWORD` | MQTT credentials. `None` means the broker allows anonymous clients. |
| [L12](../../firmware/config.py#L12) | `MQTT_KEEPALIVE = 60` | Keep-alive of 60 s: if the broker hears nothing from the ESP32 for about 1.5 × 60 = 90 s, it treats the device as dead and publishes its Last Will. |
| [L13](../../firmware/config.py#L13) | `TOPIC_PREFIX` | Common start of every topic: `vku/weather`. |
| [L15](../../firmware/config.py#L15) | `DEVICE_ID` | Device name. It appears in the topics and is the MQTT `client_id`, so every ESP32 needs a unique one. |
| [L16](../../firmware/config.py#L16) | `INTERVAL_S = 10` | Default sampling interval: 10 s. |
| [L17–18](../../firmware/config.py#L17) | `MIN_INTERVAL_S`, `MAX_INTERVAL_S` | Allowed interval range 2–3600 s. The minimum is 2 s because the DHT22 cannot measure faster. |
| [L21](../../firmware/config.py#L21) | `DHT_PIN = 4` | DHT22 data pin is wired to GPIO4. |
| [L22–23](../../firmware/config.py#L22) | `I2C_SDA = 21`, `I2C_SCL = 22` | The two I2C bus pins, shared by the BMP180 and BH1750. |
| [L24](../../firmware/config.py#L24) | `I2C_FREQ = 100000` | I2C at 100 kHz (standard mode, reliable with longer wires). |
| [L25–26](../../firmware/config.py#L25) | `BH1750_ADDR`, `BMP180_ADDR` | I2C addresses of the two sensors: 0x23 and 0x77. |
| [L27](../../firmware/config.py#L27) | `LED_PIN = 2` | The on-board LED is on GPIO2. |
| [L29](../../firmware/config.py#L29) | `SEA_LEVEL_HPA = 1013.25` | Standard sea-level pressure, used to compute altitude. |
| [L30](../../firmware/config.py#L30) | `WDT_TIMEOUT_MS = 60000` | Watchdog: if the program does not signal "I'm alive" within 60 s, the board restarts itself. |

---

## 1.2. `wifi.py` — Wi-Fi connection

| Lines | Explanation |
|---|---|
| [L1–4](../../firmware/wifi.py#L1) | Imports: `time` for timing, `network` (MicroPython's Wi-Fi module), `config` for the SSID and password. |
| [L6](../../firmware/wifi.py#L6) | Create the Wi-Fi interface in **STA (station)** mode, meaning the ESP32 joins a router (as opposed to AP mode, where it would create its own network). The leading `_` marks it as private to this file. |
| [L9–10](../../firmware/wifi.py#L9) | `is_connected()`: `True` if Wi-Fi is connected. |
| [L13–17](../../firmware/wifi.py#L13) | `rssi()`: Wi-Fi signal strength in dBm (closer to 0 is stronger: −50 is good, −80 is weak). Wrapped in `try` because the call fails when not connected; it then returns `None`. |
| [L20](../../firmware/wifi.py#L20) | `connect()` optionally takes `wdt` and `led`, so it can feed the watchdog and blink the LED while waiting. |
| [L22](../../firmware/wifi.py#L22) | Turn the Wi-Fi radio on. |
| [L23–24](../../firmware/wifi.py#L23) | Already connected: return straight away. |
| [L25](../../firmware/wifi.py#L25) | Print a log line to the serial port (visible over USB). |
| [L26–29](../../firmware/wifi.py#L26) | Drop any old connection to start clean; ignore errors here. |
| [L30](../../firmware/wifi.py#L30) | Start connecting. This call **does not wait**: it returns immediately and the connection happens in the background. |
| [L31](../../firmware/wifi.py#L31) | Remember the start time in milliseconds. |
| [L32](../../firmware/wifi.py#L32) | Loop until connected. |
| [L33–35](../../firmware/wifi.py#L33) | Give up and return `False` after `timeout_s` seconds. `ticks_diff` is used instead of plain subtraction because the `ticks_ms` counter wraps back to 0 after a long time; `ticks_diff` stays correct across the wrap. |
| [L36–37](../../firmware/wifi.py#L36) | Feed the watchdog so the board does not reset while waiting. |
| [L38–39](../../firmware/wifi.py#L38) | Toggle the LED: blinking means "connecting". |
| [L40](../../firmware/wifi.py#L40) | Wait 250 ms, then check again. |
| [L41–42](../../firmware/wifi.py#L41) | Connected: print the assigned IP and the RSSI, return `True`. |

---

## 1.3. `boot.py` — runs first at power-up

| Lines | Explanation |
|---|---|
| [L3–5](../../firmware/boot.py#L3) | Import `gc` (garbage collector) and the `wifi` module. |
| [L7–9](../../firmware/boot.py#L7) | Try Wi-Fi up to 3 times; `break` on success. If all 3 fail the program continues anyway, because `main.py` keeps retrying. |
| [L11](../../firmware/boot.py#L11) | Only sync the clock if there is a network. |
| [L13–14](../../firmware/boot.py#L13) | `ntptime.settime()` asks an Internet NTP server for the time and sets the ESP32 clock to **UTC**. The ESP32 has no battery-backed clock, so this is needed after every power-up. The dashboard converts to Vietnam time (UTC+7). |
| [L15–17](../../firmware/boot.py#L15) | Print the result; on failure (no Internet) just print the error and carry on. |
| [L19](../../firmware/boot.py#L19) | Free memory before `main.py` starts. The ESP32 has only a few hundred KB of RAM, so this is done often. |

---

## 1.4. `sensors.py` — the three sensors in one place

| Lines | Explanation |
|---|---|
| [L2–9](../../firmware/sensors.py#L2) | Imports: `dht` (built-in DHT22 driver), `Pin`, `SoftI2C` (software I2C that works on any pins), the settings and the two custom drivers. |
| [L11](../../firmware/sensors.py#L11) | A failed DHT22 read is retried up to 3 times. |
| [L14](../../firmware/sensors.py#L14) | The `Sensors` class manages all three sensors. |
| [L16](../../firmware/sensors.py#L16) | DHT22 object on GPIO4. |
| [L17](../../firmware/sensors.py#L17) | I2C bus on GPIO21 (SDA) and GPIO22 (SCL) at 100 kHz. |
| [L18–19](../../firmware/sensors.py#L18) | The BMP180 and BH1750 start as `None` (not set up yet). |
| [L20](../../firmware/sensors.py#L20) | Try to set up the two I2C sensors. |
| [L22–33](../../firmware/sensors.py#L22) | `_init_i2c()`: set up any sensor that is still `None`. On failure (sensor unplugged, bad wiring) just print and move on. It is called again **on every read** ([L49](../../firmware/sensors.py#L49)), so a sensor that is unplugged and plugged back in starts working again without resetting the ESP32. |
| [L35–36](../../firmware/sensors.py#L35) | `scan()`: scan the I2C bus and list addresses in hex. Correct wiring shows `['0x23', '0x77']`. |
| [L38–46](../../firmware/sensors.py#L38) | `_read_dht()`: `measure()` takes a reading, then temperature and humidity are read out. The DHT22 fails randomly now and then (`OSError`), so on failure wait 2.1 s (it needs ≥ 2 s between reads) and retry. After 3 failures return `None`. |
| [L48–57](../../firmware/sensors.py#L48) | `read_all()`: prepare the result dict with every value set to `None`. |
| [L58](../../firmware/sensors.py#L58) | List of sensors that failed in this read. |
| [L60–65](../../firmware/sensors.py#L60) | Read the DHT22. On failure add `"dht22"` to `errors`; otherwise round to 1 decimal. |
| [L67–77](../../firmware/sensors.py#L67) | Read the BMP180: secondary temperature, pressure (2 decimals) and altitude computed from pressure. On failure add `"bmp180"` and set `self.bmp = None` so it is set up again next time. |
| [L79–86](../../firmware/sensors.py#L79) | Same for the BH1750 (light). |
| [L88–89](../../firmware/sensors.py#L88) | Attach the error list and return. **Key idea:** one broken sensor never loses the data from the other two. |

---

## 1.5. `lib/bmp180.py` — pressure sensor driver

The BMP180 does not output °C and Pa directly. It returns **raw values** (UT, UP) that must be converted with the datasheet formulas and 11 **calibration coefficients** unique to each chip (written into it at the factory).

| Lines | Explanation |
|---|---|
| [L2–3](../../firmware/lib/bmp180.py#L2) | `struct` to unpack bytes into numbers, `time` for delays. |
| [L5–8](../../firmware/lib/bmp180.py#L5) | Register addresses: `0xAA` calibration data, `0xD0` chip ID, `0xF4` measurement command, `0xF6` result. |
| [L9](../../firmware/lib/bmp180.py#L9) | The BMP180 chip ID is always `0x55`. |
| [L10–11](../../firmware/lib/bmp180.py#L10) | "Measure temperature" (`0x2E`) and "measure pressure" (`0x34`) commands. |
| [L12](../../firmware/lib/bmp180.py#L12) | Pressure conversion time for oversampling modes 0–3: more precise means slower, 5 → 26 ms. |
| [L15–18](../../firmware/lib/bmp180.py#L15) | `_div()`: integer division that **rounds toward zero**, like C. Python's `//` rounds down (`-7 // 2 = -4`, while C gives `-3`). The datasheet formulas are written in C, so this is needed to get identical results. |
| [L21–23](../../firmware/lib/bmp180.py#L21) | `compensate()`: unpack the 11 coefficients (`ac1` … `md`; `_mb` is unused). |
| [L24–27](../../firmware/lib/bmp180.py#L24) | Temperature, per the datasheet. `>> 15` shifts right 15 bits, i.e. divides by 2¹⁵. `b5` is an intermediate value reused for pressure. The result is in 0.1 °C, hence `/ 10`. |
| [L29–46](../../firmware/lib/bmp180.py#L29) | Pressure, following the datasheet steps exactly (section 3.5): `b6` → `b3` → `b4` → `b7` → `p`. [L39–42](../../firmware/lib/bmp180.py#L39) splits two cases to avoid 32-bit overflow, as in the C original. [L43–46](../../firmware/lib/bmp180.py#L43) is the final non-linear correction. The result `p` is in Pa. |
| [L47](../../firmware/lib/bmp180.py#L47) | Return (°C, Pa). A unit test checks this against the datasheet example: exactly 15.0 °C and 69 964 Pa. |
| [L50–51](../../firmware/lib/bmp180.py#L50) | `altitude()`: barometric formula h = 44330 × (1 − (p/p₀)^(1/5.255)). |
| [L54–58](../../firmware/lib/bmp180.py#L54) | `BMP180` class: stores the I2C bus, the address and `oss = 3` (highest precision, lowest noise). |
| [L59–61](../../firmware/lib/bmp180.py#L59) | Read the chip ID; anything other than `0x55` raises "BMP180 not found". |
| [L62](../../firmware/lib/bmp180.py#L62) | Read 22 bytes of calibration data and unpack them into 11 16-bit numbers. In `">hhhHHHhhhhh"`, `>` means big-endian (high byte first), `h` is signed and `H` unsigned. |
| [L64–68](../../firmware/lib/bmp180.py#L64) | `_raw_temp()`: start a temperature conversion, wait 5 ms, read 2 bytes and combine them into a 16-bit number (`high << 8 \| low`). |
| [L70–74](../../firmware/lib/bmp180.py#L70) | `_raw_pressure()`: start a pressure conversion with the `oss` setting, wait, read 3 bytes and combine them into a 19-bit number. |
| [L76–79](../../firmware/lib/bmp180.py#L76) | `read()`: read raw values, run `compensate()`, convert Pa to hPa (÷ 100). |

---

## 1.6. `lib/bh1750.py` — light sensor driver

| Lines | Explanation |
|---|---|
| [L4–6](../../firmware/lib/bh1750.py#L4) | Three BH1750 commands: power on (`0x01`), reset the data register (`0x07`), continuous high-resolution 1 lux mode (`0x10`). |
| [L10–15](../../firmware/lib/bh1750.py#L10) | Setup: send the three commands in order. From then on the sensor **measures continuously**; the code only has to read. |
| [L16](../../firmware/lib/bh1750.py#L16) | Wait 180 ms for the first measurement (each one takes about 120 ms). |
| [L18–21](../../firmware/lib/bh1750.py#L18) | `read()`: read 2 bytes, combine into 16 bits, **divide by 1.2** to get lux (the factor comes from the datasheet). |

---

## 1.7. `main.py` — the main loop

### Declarations

| Lines | Explanation |
|---|---|
| [L2–12](../../firmware/main.py#L2) | Imports: `gc`, `json` (packaging data), `time`, `machine` (board reset), `WDT` (watchdog), `Pin`, the MQTT client `umqtt.simple`, and the project modules. |
| [L14–18](../../firmware/main.py#L14) | Build the 4 topics: `vku/weather/esp32-01/data`, `/status`, `/cmd`, `/ack`. |
| [L19](../../firmware/main.py#L19) | File in flash that stores the sampling interval. |
| [L22](../../firmware/main.py#L22) | Some older MicroPython builds count time from 2000 instead of 1970 (the Unix standard). If so, add 946 684 800 s (30 years) to get standard Unix time. |
| [L24](../../firmware/main.py#L24) | GPIO2 LED as an output. |
| [L25](../../firmware/main.py#L25) | **Start the 60 s watchdog.** Once started it cannot be stopped. If the program hangs for 60 s without calling `wdt.feed()`, the chip restarts. |
| [L26–27](../../firmware/main.py#L26) | Set up the sensors and print the I2C scan to check the wiring. |
| [L29–33](../../firmware/main.py#L29) | Global state: `client` (MQTT connection, `None` = not connected), `seq` (message counter), `read_now` flag (measure immediately), `reboot_pending` flag, `last_io` (time of the last packet sent). |

### Helper functions

| Lines | Explanation |
|---|---|
| [L36–37](../../firmware/main.py#L36) | `clamp_interval()`: force the interval into 2–3600 s. Sending 1 gives 2; sending 99999 gives 3600. |
| [L40–45](../../firmware/main.py#L40) | `load_interval()`: read the saved interval from `state.json`. Missing file, bad JSON or missing key falls back to the default in `config`. |
| [L48–53](../../firmware/main.py#L48) | `save_interval()`: write the new interval to flash, so a reboot keeps the interval the user chose. |
| [L56](../../firmware/main.py#L56) | Load the interval once at start-up. |
| [L59–61](../../firmware/main.py#L59) | `unix_time()`: current Unix time (seconds since 1 Jan 1970). A value below 1.7 billion (before 2023) means NTP never synced, so return `None` and **let the receiver stamp the time** instead (Node-RED then uses the arrival time). |
| [L64–69](../../firmware/main.py#L64) | `sleep_feed()`: sleep N seconds in 250 ms steps, feeding the watchdog and blinking the LED. A single `time.sleep(60)` would trigger the watchdog. |
| [L72–75](../../firmware/main.py#L72) | `publish()`: send with **QoS 1** (the broker must acknowledge; lost messages are resent) and record the time in `last_io`. |
| [L78–80](../../firmware/main.py#L78) | `ack()`: reply on `/ack`, e.g. `{"cmd": "read_now", "ok": true, "ts": ...}`. `**extra` allows extra fields such as `value` or `msg`. |

### Handling commands — `on_cmd()`

umqtt calls this automatically whenever a message arrives on `/cmd`.

| Lines | Explanation |
|---|---|
| [L84](../../firmware/main.py#L84) | `global` because the function changes global variables. |
| [L85–90](../../firmware/main.py#L85) | Decode the JSON. Malformed commands are printed and ignored instead of crashing. |
| [L92–99](../../firmware/main.py#L92) | `set_interval`: clamp the value, save it to flash, ack with the new value. A non-numeric `value` gets an `"invalid value"` error ack. |
| [L100–102](../../firmware/main.py#L100) | `read_now`: only **set a flag** and let the main loop measure. Measuring here would take seconds and block MQTT. |
| [L103–105](../../firmware/main.py#L103) | `reboot`: also just a flag, so the ack can be sent before the reset. |
| [L106–107](../../firmware/main.py#L106) | Unknown command: ack with `"unknown command"`. |

### MQTT connection

| Lines | Explanation |
|---|---|
| [L112–119](../../firmware/main.py#L112) | Create the MQTT client with `client_id` = device name, broker address, credentials and keep-alive. |
| [L120](../../firmware/main.py#L120) | **Last Will and Testament (LWT):** tell the broker in advance: *"if I disconnect unexpectedly, publish `offline` on my `/status` topic for me."* `retain=True` so anyone who subscribes later still sees the last state. This is how the dashboard knows the device lost power. |
| [L121](../../firmware/main.py#L121) | Register `on_cmd` as the incoming-message handler. |
| [L122–125](../../firmware/main.py#L122) | Connect with a 10 s timeout. Older umqtt versions have no `timeout` parameter (raising `TypeError`), so fall back to the old call. |
| [L126](../../firmware/main.py#L126) | Only after success is the client stored in the global `client`. |
| [L127](../../firmware/main.py#L127) | Publish `online` (retained) on `/status`, replacing the old `offline`. |
| [L128](../../firmware/main.py#L128) | Subscribe to `/cmd` to receive commands. |
| [L129–130](../../firmware/main.py#L129) | LED on = connected; print a log line. |
| [L133–140](../../firmware/main.py#L133) | `mqtt_close()`: close the old socket (ignore errors if it is already dead) and set `client = None`. The main loop sees `None` and reconnects. |

### Sending one reading — `send_reading()`

| Lines | Explanation |
|---|---|
| [L145](../../firmware/main.py#L145) | Read all three sensors. |
| [L146–150](../../firmware/main.py#L146) | Add device name, timestamp, sequence number `seq`, RSSI and the current interval. |
| [L151–153](../../firmware/main.py#L151) | LED off, publish the JSON on `/data`, LED on: a quick blink for every message sent. |
| [L154](../../firmware/main.py#L154) | Increment `seq`. A gap in `seq` on the receiving side means lost packets (the dashboard shows the latest `seq`). |
| [L155–156](../../firmware/main.py#L155) | Print sensor errors, if any. |

### Main loop — `run()`

The loop runs forever. Each pass checks, in order: **Wi-Fi → MQTT → incoming commands → time to measure? → need a ping?**

| Lines | Explanation |
|---|---|
| [L161](../../firmware/main.py#L161) | `backoff = 1`: seconds to wait before the next MQTT reconnect attempt, starting at 1. |
| [L162](../../firmware/main.py#L162) | `last_send = None`: nothing sent yet, so the first reading goes out immediately. |
| [L164](../../firmware/main.py#L164) | Feed the watchdog on every pass. |
| [L165–169](../../firmware/main.py#L165) | **Wi-Fi lost:** close MQTT and reconnect Wi-Fi; on failure wait 2 s. `continue` jumps back to the top of the loop. |
| [L171–180](../../firmware/main.py#L171) | **No MQTT connection:** try to connect. On success reset `backoff` to 1. On failure wait `backoff` seconds and **double** it (1 → 2 → 4 → … up to 60 s). This is **exponential backoff**: it avoids hammering a broker that is down. |
| [L183](../../firmware/main.py#L183) | `check_msg()`: check for incoming commands without waiting; if there is one, `on_cmd` runs. |
| [L184–188](../../firmware/main.py#L184) | Reboot requested: publish `offline` ourselves, disconnect cleanly, wait 0.5 s, reset the board. |
| [L189–194](../../firmware/main.py#L189) | If a reading was requested, or it is the first pass, or `interval` seconds have passed since the last send: measure, send, free memory. This **avoids `sleep(interval)`**, so commands are still received while waiting. |
| [L195–197](../../firmware/main.py#L195) | Nothing sent for half the keep-alive (30 s): send a PING so the broker knows the device is alive. Needed when the interval is long, e.g. 10 minutes. |
| [L198–201](../../firmware/main.py#L198) | Any network error (broker down, socket broken) lands here: LED off, close the connection. The next pass reconnects. |
| [L202](../../firmware/main.py#L202) | Pause 50 ms per pass so the CPU is not at 100 %. |
| [L205](../../firmware/main.py#L205) | Call `run()` to start. |

---

## 1.8. `lib/umqtt/simple.py`

This is the official MicroPython MQTT library (micropython-lib, MIT licence), **not code written for this project**.
It only needs copying to the board if the firmware does not already include it. The functions the project uses:

| Function | What it does |
|---|---|
| `set_last_will()` | Registers the "last will" (LWT) message. |
| `connect()` | Opens a TCP socket to the broker and sends CONNECT. |
| `publish()` | Sends a message; with QoS 1 it waits for the PUBACK confirmation. |
| `subscribe()` | Subscribes to a topic. |
| `check_msg()` | Checks for an incoming message without waiting; calls the callback if there is one. |
| `ping()` | Sends PINGREQ to keep the connection alive. |
| `disconnect()` | Disconnects cleanly (the broker then does **not** publish the LWT). |
