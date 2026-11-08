# KẾ HOẠCH THỰC HIỆN ĐỀ TÀI

## Hệ thống quan trắc nhiệt độ, độ ẩm, áp suất và ánh sáng sử dụng ESP32 và giao thức MQTT

---

## 1. Mục tiêu

Xây dựng một hệ thống IoT hoàn chỉnh gồm:

1. **Nút cảm biến (ESP32)** đọc định kỳ nhiệt độ, độ ẩm (DHT22), áp suất khí quyển (BMP180) và cường độ ánh sáng (BH1750), đóng gói dữ liệu dạng JSON và gửi lên **MQTT Broker** qua Wi-Fi.
2. **Node-RED** đăng ký (subscribe) topic MQTT, xử lý dữ liệu và kiểm tra ngưỡng.
3. **Dashboard Node-RED** hiển thị giá trị thời gian thực, biểu đồ 1 giờ gần nhất, trạng thái thiết bị online/offline và cảnh báo khi vượt ngưỡng.
4. Có thể **điều khiển ngược** thiết bị qua MQTT (đổi chu kỳ đo, yêu cầu đọc ngay, khởi động lại).

### Tiêu chí hoàn thành sản phẩm

- [ ] ESP32 gửi dữ liệu đủ 4 đại lượng (nhiệt độ, độ ẩm, áp suất, ánh sáng) đều đặn theo chu kỳ cấu hình được.
- [ ] Mất Wi-Fi / mất broker thì ESP32 tự kết nối lại, không treo.
- [x] Dashboard cập nhật real-time (độ trễ < 2 giây).
- [x] Hiển thị đúng trạng thái online/offline của thiết bị (dùng MQTT Last Will).
- [x] Có cảnh báo khi giá trị vượt ngưỡng.
- [ ] Có báo cáo, sơ đồ nối dây, video demo.

---

## 2. Thiết bị phần cứng

| STT | Thiết bị | Chức năng | Giao tiếp | Điện áp | Ghi chú |
|-----|----------|-----------|-----------|---------|---------|
| 1 | ESP32 DevKit V1 (ESP32-WROOM-32) | Vi điều khiển trung tâm, kết nối Wi-Fi | — | 5V qua USB / 3.3V logic | |
| 2 | DHT22 (AM2302) | Nhiệt độ (-40…80 °C, ±0.5 °C), độ ẩm (0…100 %RH, ±2 %) | 1-Wire riêng (Digital) | 3.3V | Chu kỳ đọc tối thiểu **2 giây**; cần điện trở kéo lên 10kΩ nếu là cảm biến trần (module thường đã có sẵn) |
| 3 | BMP180 (GY-68) | Áp suất (300…1100 hPa) | I2C, địa chỉ `0x77` | 3.3V | |
| 4 | BH1750 (GY-302) | Cường độ ánh sáng (1…65535 lux) | I2C, địa chỉ `0x23` (chân ADDR = GND) / `0x5C` (ADDR = VCC) | 3.3V | |
| 5 | Breadboard, dây cắm, cáp Micro-USB | Lắp ráp, cấp nguồn, nạp code | | | |
| 6 | (Tuỳ chọn) LED + điện trở 220Ω | Báo trạng thái kết nối | GPIO | | |

### 2.1. Sơ đồ nối dây

BMP180 và BH1750 dùng **chung bus I2C** (khác địa chỉ nên không xung đột).

| Cảm biến | Chân cảm biến | Chân ESP32 |
|----------|---------------|------------|
| DHT22 | VCC (+) | 3V3 |
| DHT22 | DATA (OUT) | GPIO4 |
| DHT22 | GND (-) | GND |
| BMP180 | VIN | 3V3 |
| BMP180 | GND | GND |
| BMP180 | SDA | GPIO21 |
| BMP180 | SCL | GPIO22 |
| BH1750 | VCC | 3V3 |
| BH1750 | GND | GND |
| BH1750 | SDA | GPIO21 |
| BH1750 | SCL | GPIO22 |
| BH1750 | ADDR | GND (→ địa chỉ 0x23) |
| LED (tuỳ chọn) | Anode (qua 220Ω) | GPIO2 (LED onboard) |

```
            +-----------------------+
            |        ESP32          |
  DHT22 ----| GPIO4                 |
            |                       |
  BMP180 ---| GPIO21 (SDA) ---+     |
  BH1750 ---| GPIO22 (SCL) ---+-- bus I2C chung
            |                       |
            | 3V3 ---- VCC tất cả cảm biến
            | GND ---- GND tất cả cảm biến
            +-----------------------+
```

---

## 3. Kiến trúc hệ thống

```
+------------------+     Wi-Fi / MQTT      +------------------+
|  ESP32 + 3 cảm   | --- publish data ---> |  MQTT Broker     |
|  biến (Node)     | <-- subscribe cmd --- |  (Mosquitto)     |
+------------------+                       +------------------+
                                              |          ^
                                   subscribe  |          | publish cmd
                                              v          |
                                    +----------------------------+
                                    |  Node-RED (:1880)          |
                                    |  - mqtt in / mqtt out      |
                                    |  - function: tách số đo,   |
                                    |    kiểm tra ngưỡng         |
                                    +----------------------------+
                                                 |
                                                 v
                                    +----------------------------+
                                    |  Dashboard Node-RED (/ui)  |
                                    |  gauge, chart, toast       |
                                    +----------------------------+
```

### 3.1. Công nghệ sử dụng

| Thành phần | Công nghệ | Lý do chọn |
|------------|-----------|------------|
| Firmware ESP32 | **MicroPython** (v1.2x) | Đồng bộ ngôn ngữ Python với môn học; có sẵn module `dht`, `machine.I2C`, `umqtt.simple` |
| Driver cảm biến | `dht` (có sẵn), `bmp180.py`, `bh1750.py` (thư viện ngoài) | |
| Công cụ nạp | `esptool`, `mpremote` hoặc Thonny IDE | |
| MQTT Broker | **Eclipse Mosquitto** (cài trên máy tính / Docker) | Miễn phí, nhẹ, chạy local; dự phòng: `broker.hivemq.com` |
| Xử lý + Dashboard | **Node-RED** + `node-red-dashboard` | Kéo thả node, có sẵn MQTT, gauge, biểu đồ, nút điều khiển |
| Giả lập + kiểm thử | **Python 3.11+**, `paho-mqtt` 2.x, `pytest` | `tools/fake_device.py`, `tests/` |
| Công cụ test MQTT | MQTT Explorer / `mosquitto_sub`, `mosquitto_pub` | |

> **Phương án thay thế:** Có thể viết firmware bằng Arduino C++ (thư viện `DHT sensor library`, `Adafruit BMP085`, `BH1750`, `PubSubClient`) và dashboard bằng Streamlit nếu cần làm nhanh.

---

## 4. Thiết kế giao thức MQTT

### 4.1. Cấu trúc topic

`<device_id>` ví dụ: `esp32-01`

| Topic | Chiều | QoS | Retain | Mô tả |
|-------|-------|-----|--------|-------|
| `vku/weather/<device_id>/data` | ESP32 → Node-RED | 1 | Không | Dữ liệu đo định kỳ (JSON) |
| `vku/weather/<device_id>/status` | ESP32 → Node-RED | 1 | **Có** | `online` khi kết nối; `offline` qua **Last Will (LWT)** khi mất kết nối |
| `vku/weather/<device_id>/cmd` | Node-RED → ESP32 | 1 | Không | Lệnh điều khiển |
| `vku/weather/<device_id>/ack` | ESP32 → Node-RED | 1 | Không | Phản hồi đã thực hiện lệnh |

### 4.2. Định dạng bản tin dữ liệu

```json
{
  "device_id": "esp32-01",
  "ts": 1761200000,
  "seq": 1024,
  "temperature": 29.4,
  "humidity": 71.2,
  "pressure": 1009.6,
  "light": 356.7,
  "rssi": -58,
  "errors": []
}
```

- Đơn vị: nhiệt độ `°C`, độ ẩm `%RH`, áp suất `hPa`, ánh sáng `lux`, RSSI `dBm`.
- `seq`: số thứ tự tăng dần → phát hiện mất gói.
- `errors`: danh sách cảm biến đọc lỗi (vd: `["dht22"]`), giá trị tương ứng gửi `null` thay vì làm hỏng cả bản tin.
- `ts`: thời gian Unix, ESP32 đồng bộ qua NTP (`ntptime`).

### 4.3. Định dạng lệnh điều khiển

```json
{ "cmd": "set_interval", "value": 10 }   // đổi chu kỳ đo (giây, tối thiểu 2)
{ "cmd": "read_now" }                     // đo và gửi ngay
{ "cmd": "reboot" }                       // khởi động lại ESP32
```

---

## 5. Cấu trúc thư mục dự án

```
mid/
├── task.md                     # File kế hoạch này
├── README.md                   # Hướng dẫn cài đặt & chạy
├── docs/
│   ├── wiring.png              # Sơ đồ nối dây (Fritzing/Wokwi)
│   ├── architecture.png        # Sơ đồ kiến trúc
│   └── report.docx             # Báo cáo
├── firmware/                   # Code chạy trên ESP32 (MicroPython)
│   ├── boot.py                 # Kết nối Wi-Fi
│   ├── main.py                 # Vòng lặp chính: đọc cảm biến, publish, nhận lệnh
│   ├── config.py               # SSID, mật khẩu, broker, device_id, chu kỳ (KHÔNG commit mật khẩu thật)
│   ├── sensors.py              # Lớp đọc DHT22, BMP180, BH1750
│   └── lib/
│       ├── bmp180.py
│       ├── bh1750.py
│       └── umqtt/simple.py     # nếu firmware chưa có sẵn
├── node-red/                   # Xử lý + dashboard
│   ├── flows.json              # Flow: mqtt in/out, function, gauge, chart, toast
│   ├── settings.js
│   └── package.json            # npm start; phụ thuộc node-red-dashboard
├── tools/
│   └── fake_device.py          # Giả lập ESP32 publish dữ liệu để test không cần phần cứng
├── tests/
│   └── test_bmp280.py          # pytest: công thức bù BMP280 của firmware
├── requirements.txt            # paho-mqtt, pytest
└── broker/
    ├── mosquitto.conf
    └── docker-compose.yml      # (tuỳ chọn) chạy Mosquitto bằng Docker
```

---

## 6. Các giai đoạn thực hiện

### Giai đoạn 0 — Chuẩn bị (Tuần 1)

- [ ] Mua/kiểm tra linh kiện: ESP32, DHT22, BMP180, BH1750, breadboard, dây.
- [ ] Cài driver USB-UART cho ESP32 (CP210x hoặc CH340) và xác định cổng COM.
- [ ] Cài Python 3.11+, Thonny (hoặc `pip install esptool mpremote`).
- [ ] Nạp firmware MicroPython cho ESP32:
  ```
  esptool --chip esp32 --port COMx erase_flash
  esptool --chip esp32 --port COMx --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-xxx.bin
  ```
- [x] Cài Mosquitto, chạy được broker trên cổng 1883; test bằng `mosquitto_sub -t "#" -v` và `mosquitto_pub`.
- [ ] Cài MQTT Explorer để quan sát topic.
- [x] Tạo cấu trúc thư mục dự án như mục 5.

**Kết quả:** ESP32 chạy được REPL MicroPython, broker hoạt động.

### Giai đoạn 1 — Lắp mạch và đọc từng cảm biến (Tuần 1–2)

- [ ] Lắp mạch theo sơ đồ mục 2.1 (tắt nguồn khi cắm dây).
- [ ] Quét bus I2C, phải thấy `0x23` (BH1750) và `0x77` (BMP180):
  ```python
  from machine import Pin, SoftI2C
  i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
  print([hex(a) for a in i2c.scan()])
  ```
- [ ] Đọc DHT22 bằng module `dht` có sẵn, xử lý ngoại lệ `OSError` khi đọc lỗi.
- [ ] Đọc BMP180 (áp suất).
- [ ] Đọc BH1750 ở chế độ Continuous High-Resolution (1 lux, ~120 ms).
- [x] Viết `sensors.py` gom 3 cảm biến thành một hàm `read_all()` trả về dict; cảm biến nào lỗi thì trả `None` và ghi vào `errors`.
- [ ] Kiểm tra tính hợp lý: thổi hơi vào DHT22 (độ ẩm tăng), che/chiếu đèn BH1750 (lux thay đổi), so sánh nhiệt độ DHT22 với BMP180 (chênh lệch ≤ ~1–2 °C).

**Kết quả:** In ra Serial đủ các giá trị đo đúng, ổn định.

### Giai đoạn 2 — Firmware kết nối Wi-Fi và MQTT (Tuần 2)

- [x] `boot.py`: kết nối Wi-Fi có timeout, thử lại nếu thất bại.
- [x] Đồng bộ giờ qua NTP (`ntptime.settime()`), lưu ý múi giờ UTC+7 khi hiển thị.
- [x] `main.py`:
  - [x] Kết nối broker bằng `umqtt.simple.MQTTClient` với `client_id = device_id`, `keepalive = 60`.
  - [x] Đặt **Last Will**: topic `.../status`, payload `offline`, retain.
  - [x] Sau khi kết nối publish `online` (retain) lên `.../status`.
  - [x] Subscribe `.../cmd`, xử lý lệnh trong callback (`set_interval`, `read_now`, `reboot`), gửi phản hồi lên `.../ack`.
  - [x] Vòng lặp chính không chặn: dùng `check_msg()` + so sánh `time.ticks_ms()` để đến chu kỳ thì đọc cảm biến và publish JSON.
  - [x] Đảm bảo chu kỳ đo ≥ 2 giây (giới hạn của DHT22).
- [x] Xử lý lỗi và tự phục hồi:
  - [x] Mất Wi-Fi → kết nối lại; mất broker → kết nối lại với thời gian chờ tăng dần (backoff).
  - [x] Bật **Watchdog Timer** (`machine.WDT`) để tự reset nếu treo.
  - [x] LED onboard GPIO2: nháy khi đang kết nối, sáng khi đã kết nối, nháy nhanh khi gửi dữ liệu.
- [x] Tách cấu hình ra `config.py` (SSID, password, broker host/port, device_id, interval).
- [ ] Kiểm tra bằng MQTT Explorer: dữ liệu đến đều, rút điện ESP32 thì status chuyển `offline`.

**Kết quả:** ESP32 publish dữ liệu ổn định lên broker, nhận được lệnh từ xa.

### Giai đoạn 3 — Xử lý dữ liệu bằng Node-RED (Tuần 3)

- [x] Cài Node-RED và `node-red-dashboard` (`node-red/package.json`, chạy bằng `npm start`).
- [x] Node `mqtt in` subscribe `vku/weather/+/data` (JSON), `vku/weather/esp32-01/status` và `vku/weather/esp32-01/ack`.
- [x] Function **Split readings**: chỉ nhận thiết bị `esp32-01`, tách từng đại lượng ra gauge và biểu đồ, bỏ qua giá trị `null` khi cảm biến lỗi.
- [x] Function **Check thresholds**: nhiệt độ > 35 °C, độ ẩm < 30 % hoặc > 90 %, ánh sáng < 50 lux. Chống spam: cùng một đại lượng không cảnh báo lại trong 5 phút.
- [x] Node `mqtt out` publish lệnh lên `vku/weather/esp32-01/cmd`; kết quả lệnh đọc từ topic `ack`.
- [x] **tools/fake_device.py** — script giả lập ESP32 publish dữ liệu ngẫu nhiên hợp lý, để làm dashboard khi chưa có phần cứng.
- [x] Unit test công thức bù BMP280 của firmware (`pytest`).

**Kết quả:** Node-RED nhận dữ liệu từ broker, kiểm tra ngưỡng và gửi lệnh xuống ESP32.

### Giai đoạn 4 — Dashboard Node-RED (Tuần 3–4)

- [x] Tab **Monitoring Station** tại `http://localhost:1880/ui` gồm:
  - [x] 4 gauge giá trị hiện tại: Temperature, Humidity, Pressure, Light.
  - [x] 4 biểu đồ đường, giữ dữ liệu 1 giờ gần nhất.
  - [x] Bảng thiết bị: Online/Offline (LWT), thời điểm cập nhật, cảm biến lỗi, RSSI Wi-Fi, chu kỳ đo, `seq`.
  - [x] Thông báo (toast) khi vượt ngưỡng và khi ESP32 phản hồi lệnh.
  - [x] Điều khiển: nút **Read now**, danh sách **Change interval** (5 / 10 / 30 / 60 s).
- [x] Xem được trên điện thoại trong cùng mạng LAN.

**Kết quả:** Dashboard hiển thị dữ liệu thật từ ESP32.

### Giai đoạn 5 — Tích hợp, kiểm thử, hoàn thiện (Tuần 4)

- [ ] Chạy toàn hệ thống: ESP32 → Mosquitto → Node-RED → Dashboard.
- [ ] Thực hiện các kịch bản kiểm thử ở mục 7, ghi lại kết quả.
- [ ] Chạy liên tục ≥ 24 giờ, kiểm tra tỷ lệ mất gói và ESP32 không bị treo.
- [ ] (Nâng cao, tuỳ chọn) Bật xác thực username/password cho Mosquitto (`password_file`, `allow_anonymous false`).
- [ ] (Nâng cao, tuỳ chọn) Gửi cảnh báo qua Telegram Bot.
- [ ] (Nâng cao, tuỳ chọn) Chế độ deep sleep giữa các lần đo để tiết kiệm năng lượng (khi chạy pin).
- [ ] (Nâng cao, tuỳ chọn) Đóng gói broker + Node-RED bằng Docker Compose.

### Giai đoạn 6 — Báo cáo và demo (Tuần 5)

- [x] Viết `README.md`: yêu cầu, cách nối dây, cách nạp firmware, cách chạy broker và Node-RED.
- [x] Vẽ sơ đồ nối dây (Fritzing hoặc Wokwi) và sơ đồ kiến trúc.
- [ ] Viết báo cáo gồm:
  1. Giới thiệu đề tài, lý do chọn
  2. Cơ sở lý thuyết: ESP32, DHT22, BMP180, BH1750, giao thức I2C, giao thức MQTT (publish/subscribe, QoS, retain, LWT)
  3. Thiết kế hệ thống: phần cứng, sơ đồ nối dây, kiến trúc, thiết kế topic
  4. Cài đặt: firmware (trích đoạn code chính), flow Node-RED, dashboard
  5. Kết quả thực nghiệm: ảnh mạch, ảnh dashboard, bảng số liệu, kết quả kiểm thử
  6. Kết luận và hướng phát triển
- [ ] Quay video demo (2–5 phút): mạch thật, dữ liệu thay đổi khi tác động cảm biến, dashboard real-time, gửi lệnh, rút điện → offline.
- [ ] Chuẩn bị slide thuyết trình.

---

## 7. Kịch bản kiểm thử

| # | Kịch bản | Cách thực hiện | Kết quả mong đợi |
|---|----------|----------------|-------------------|
| 1 | Đọc cảm biến | Chạy `read_all()` 50 lần | Không crash; giá trị nằm trong khoảng hợp lý |
| 2 | Thay đổi nhiệt độ/độ ẩm | Thổi hơi / để gần nguồn nhiệt vào DHT22 | Giá trị tăng, dashboard cập nhật |
| 3 | Thay đổi ánh sáng | Che tay / chiếu đèn pin vào BH1750 | Lux giảm gần 0 / tăng mạnh |
| 4 | Áp suất | So sánh với số liệu thời tiết Đà Nẵng | Sai lệch nhỏ (vài hPa) |
| 5 | Lỗi một cảm biến | Rút dây DATA của DHT22 | Bản tin vẫn gửi, `temperature/humidity = null`, `errors = ["dht22"]` |
| 6 | Mất Wi-Fi | Tắt router 1 phút rồi bật lại | ESP32 tự kết nối lại, tiếp tục gửi |
| 7 | Mất broker | Dừng Mosquitto rồi chạy lại | ESP32 và Node-RED đều tự kết nối lại |
| 8 | Thiết bị offline | Rút điện ESP32 | Sau ≤ 1.5 × keepalive, dashboard hiện Offline (nhờ LWT) |
| 9 | Lệnh điều khiển | Gửi `set_interval = 5` từ dashboard | ESP32 phản hồi ack, chu kỳ gửi đổi thành 5 s |
| 10 | Dữ liệu sai | Dùng `mosquitto_pub` gửi JSON lỗi | Node-RED bỏ qua bản tin, không crash |
| 11 | Cảnh báo | Làm nóng DHT22 vượt 35 °C | Xuất hiện cảnh báo, không bị spam lặp |
| 12 | Chạy dài hạn | Chạy 24 giờ, chu kỳ 10 s | Tỷ lệ mất gói < 1 % (dựa trên `seq`) |

---

## 8. Tiến độ tổng quát

| Tuần | Công việc chính | Sản phẩm bàn giao |
|------|-----------------|-------------------|
| 1 | Giai đoạn 0 + bắt đầu Giai đoạn 1 | Môi trường sẵn sàng, mạch lắp xong |
| 2 | Hoàn thành Giai đoạn 1 + Giai đoạn 2 | Firmware gửi dữ liệu MQTT |
| 3 | Giai đoạn 3 + bắt đầu Giai đoạn 4 | Flow Node-RED hoạt động |
| 4 | Hoàn thành Giai đoạn 4 + Giai đoạn 5 | Hệ thống hoàn chỉnh, đã kiểm thử |
| 5 | Giai đoạn 6 | Báo cáo, video, slide |

---

## 9. Rủi ro và cách khắc phục

| Rủi ro | Cách khắc phục |
|--------|----------------|
| DHT22 trả lỗi `OSError` / đọc sai | Đọc lại tối đa 3 lần, chu kỳ ≥ 2 s, kiểm tra điện trở kéo lên, dây ngắn |
| `i2c.scan()` không thấy thiết bị | Kiểm tra nối SDA/SCL, nguồn 3.3V, thử giảm `freq` xuống 50 kHz, kiểm tra chân ADDR của BH1750 |
| Nhiệt độ đo bị cao do nhiệt toả ra từ ESP32 | Đặt cảm biến cách xa ESP32, dùng dây nối dài; có thể hiệu chỉnh offset |
| ESP32 không vào được Wi-Fi trường | ESP32 chỉ hỗ trợ 2.4 GHz, không hỗ trợ Wi-Fi có trang đăng nhập → dùng hotspot điện thoại |
| Không cài được Mosquitto trên máy | Dùng Docker hoặc broker công cộng `broker.hivemq.com` (đổi prefix topic cho riêng tư) |
| ESP32 và máy chạy broker không cùng mạng | Đặt IP tĩnh cho máy chạy broker, mở cổng 1883 trên Windows Firewall |
| Thiếu bộ nhớ trên ESP32 khi chạy MicroPython | Gọi `gc.collect()` định kỳ, tránh tạo chuỗi lớn trong vòng lặp |
| Chưa có phần cứng khi làm dashboard | Dùng `fake_device.py` để giả lập |
