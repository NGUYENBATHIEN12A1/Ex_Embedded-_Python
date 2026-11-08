# Part 2 — Tests, simulator and configuration files

Run the tests from the project root with:

```powershell
pip install -r requirements.txt
python -m pytest -q tests
```

**pytest** finds every `test_*.py` file and runs every `test_*` function in it. A test passes if its `assert` lines are all true.

---

## 2.1. `tests/test_bmp280.py` — firmware maths on a PC

The BMP280 compensation formula is the most error-prone code in the firmware, so it is tested on the computer, without hardware.

| Lines | Explanation |
|---|---|
| [L4](../../tests/test_bmp280.py#L4) | Add `firmware/lib` to Python's import path so the firmware's `bmp280.py` can be imported on a PC. This works because `compensate()` uses no ESP32-only features. |
| [L8](../../tests/test_bmp280.py#L8) | The 12 calibration values (`dig_T1…dig_P9`) from the worked example in the Bosch datasheet. |
| [L11–14](../../tests/test_bmp280.py#L11) | With the datasheet's raw values (adc_T = 519888, adc_P = 415148) the result must be 25.08 °C and 100 653.27 Pa, as printed in the datasheet. |

---

## 2.2. `tools/fake_device.py` — ESP32 simulator

Pretends to be one or more ESP32 boards, so the Node-RED dashboard can be developed and demonstrated without hardware. It speaks exactly the same MQTT protocol.

| Lines | Explanation |
|---|---|
| [L12–21](../../tools/fake_device.py#L12) | One `FakeDevice` per simulated board: name, topic base, interval, `seq`, a `wake` event (to interrupt the wait when a command arrives) and a random `phase` so several devices don't show identical curves. |
| [L23–29](../../tools/fake_device.py#L23) | Create a paho client with the **Last Will** `offline` (retained), like the real firmware, and automatic reconnect (1–30 s). |
| [L31–34](../../tools/fake_device.py#L31) | On connect: publish `online` (retained) and subscribe to its `/cmd` topic. |
| [L36–37](../../tools/fake_device.py#L36) | `_ack()`: reply on `/ack`. |
| [L39–62](../../tools/fake_device.py#L39) | Handle commands exactly like `on_cmd` in the firmware: `set_interval` (clamped 2–3600), `read_now`, `reboot`, unknown command. `wake.set()` cuts the current wait short so the change applies immediately. `reboot` runs in a separate thread so it doesn't block the MQTT thread. |
| [L64–73](../../tools/fake_device.py#L64) | `_reboot()`: publish `offline`, disconnect, wait 3 s, restart from `seq = 0` with a new connection, the same as a real reset. |
| [L75–92](../../tools/fake_device.py#L75) | `reading()`: realistic fake values. A sine wave over 24 hours gives a day/night cycle: about 24–32 °C, humidity falling as temperature rises, pressure gently varying around 1009 hPa, light near 0 at night and up to ~20 000 lux at noon, plus small random noise (`random.gauss`). `--hot` forces 36–38 °C; `--sensor-fail` sometimes simulates an unplugged DHT22 (`null` + `errors: ["dht22"]`). |
| [L94–101](../../tools/fake_device.py#L94) | `bad_payload()`: one of five deliberately broken messages (bad JSON, 999 °C, negative humidity, wrong device, text instead of a number). Node-RED's `mqtt in` node drops the bad JSON and the flow ignores other devices, but out-of-range values are shown as they are: the flow does no range checks. |
| [L103–105](../../tools/fake_device.py#L103) | `start()`: connect in the background and start the network thread. |
| [L107–125](../../tools/fake_device.py#L107) | `run()`: wait for the connection, then loop forever: maybe send a bad message (`--bad`), maybe **skip** a reading on purpose (`--drop`; `seq` still increases, so the gap shows in the dashboard's seq field), otherwise send a reading. Then wait `interval` seconds, or less if a command wakes it up. |
| [L129–140](../../tools/fake_device.py#L129) | Command-line options (`argparse`): broker host/port, prefix, number of devices, first device number, interval, drop %, bad %, sensor-fail %, hot. |
| [L142–145](../../tools/fake_device.py#L142) | Create the devices (`esp32-01`, `esp32-02`, … — `:02d` pads to 2 digits) and run each in its own thread. The Node-RED dashboard only shows `esp32-01`. |
| [L146–150](../../tools/fake_device.py#L146) | Keep the program alive until Ctrl+C. Exiting without a clean disconnect makes the broker publish each device's Last Will (`offline`), which is a handy way to test the offline status. |

---

## 2.3. `broker/mosquitto.conf` — MQTT broker

| Lines | Explanation |
|---|---|
| [L1](../../broker/mosquitto.conf#L1) | Listen on port 1883 on every network interface (`0.0.0.0`), so the ESP32 can connect over Wi-Fi. |
| [L2](../../broker/mosquitto.conf#L2) | Plain MQTT protocol (not WebSockets). |
| [L4](../../broker/mosquitto.conf#L4) | Anonymous access allowed during development (requiring a username and password is an optional extension in `task.md`). |
| [L6](../../broker/mosquitto.conf#L6) | Up to 10 000 queued QoS 1 messages per client (default 1 000). Raised after testing showed a burst of messages being dropped. |
| [L8–9](../../broker/mosquitto.conf#L8) | `persistence`: save retained messages (online/offline status) to disk so they survive a broker restart. |
| [L11–15](../../broker/mosquitto.conf#L11) | Print errors, warnings, notices and information to the console. |

---

## 2.4. Other configuration files

| File | Purpose |
|---|---|
| [requirements.txt](../../requirements.txt) | Python packages for the PC side: `paho-mqtt` (simulator) and `pytest` (tests). |
| [broker/docker-compose.yml](../../broker/docker-compose.yml) | (Optional) Starts Mosquitto in Docker with one command. Written but not tested (Docker is not installed on this machine). |
| [broker/mosquitto.docker.conf](../../broker/mosquitto.docker.conf) | Broker settings used inside the Docker container. |
| [node-red/package.json](../../node-red/package.json) | Node-RED project: `npm start` runs Node-RED with this folder as its user directory; depends on `node-red-dashboard`. |
| [node-red/settings.js](../../node-red/settings.js) | Port 1880 (or `PORT`), flow file `flows.json`, dashboard served at `/ui`. |
