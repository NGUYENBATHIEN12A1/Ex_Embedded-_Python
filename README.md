Ex_Embedded-_Python

Repository tổng hợp các bài thực hành môn Embedded Python.

📚 Labs
Lab 1: OOP

Thực hành lập trình hướng đối tượng (Object-Oriented Programming) bằng Python.

Nội dung:

Class và Object
Constructor
Attribute và Method
Inheritance
Encapsulation
Lab 2: LED Matrix

Điều khiển LED Matrix bằng Python/MicroPython để hiển thị:

Lớp
Mã sinh viên

Thiết bị sử dụng:

Microcontroller
LED Matrix
Module điều khiển LED Matrix
Lab 3: Interrupt, Timer, PWM & RGB LED

Thực hành điều khiển LED bằng Interrupt, Hardware Timer và PWM trên MicroPython.

Chức năng:

Sử dụng nút nhấn để chuyển đổi giữa 3 chế độ.
Mode 1: LED đơn nhấp nháy sử dụng Hardware Timer.
Mode 2: Điều khiển độ sáng LED bằng PWM với hiệu ứng Fading.
Mode 3: Điều khiển LED RGB chuyển đổi tuần tự nhiều màu.
Sử dụng Software Debounce để chống dội nút nhấn.

Kiến thức sử dụng:

GPIO
Interrupt
Hardware Timer
PWM
RGB LED
Software Debounce
Lab 4: ESP32 IoT Web Server

Xây dựng hệ thống IoT sử dụng ESP32, kết nối Wi-Fi và điều khiển thiết bị thông qua giao diện Web.

Chức năng:

Kết nối ESP32 với Wi-Fi.
Tự động kiểm tra và kết nối lại khi mất Wi-Fi.
Xây dựng Web Server trên ESP32.
Điều khiển LED từ trình duyệt Web.
Gửi HTTP Request đến Open-Meteo API.
Lấy thông tin thời tiết:
Nhiệt độ
Độ ẩm
Tốc độ gió
Hiển thị địa chỉ IP và trạng thái Wi-Fi trên Web.
Tự động cập nhật dữ liệu thời tiết mỗi 30 giây.

Kiến thức sử dụng:

ESP32
Wi-Fi
HTTP
Socket
REST API
JSON
HTML/CSS
Web Server
Lab 5: DHT11 Web Monitoring

Xây dựng hệ thống giám sát nhiệt độ và độ ẩm realtime sử dụng ESP8266 và cảm biến DHT11.

Chức năng:

Kết nối ESP8266 với Wi-Fi.
Đọc nhiệt độ và độ ẩm từ cảm biến DHT11.
Xây dựng Web Server trên ESP8266.
Cung cấp dữ liệu cảm biến thông qua HTTP Endpoint /data.
Trả dữ liệu cảm biến dưới dạng JSON.
Hiển thị nhiệt độ và độ ẩm trên biểu đồ realtime.
Tự động cập nhật dữ liệu mỗi 5 giây.
Sử dụng Chart.js để trực quan hóa dữ liệu.

Thiết bị sử dụng:

ESP8266
DHT11
Wi-Fi

Kết nối:

DHT11 DATA → GPIO14

Kiến thức sử dụng:

ESP8266
DHT11
Wi-Fi
HTTP
Socket
JSON
HTML/CSS
JavaScript
Chart.js
🛠️ Technologies
Python
MicroPython
Embedded Systems
ESP32 / ESP8266
GPIO
SPI
PWM
Interrupt
Hardware Timer
Wi-Fi
HTTP
REST API
JSON
HTML/CSS
JavaScript
Chart.js
📂 Repository Structure
Ex_Embedded-_Python/
│
├── Lab1/
│   └── OOP/
│
├── Lab2/
│   └── LED_Matrix/
│
├── Lab3/
│   └── Interrupt_Timer_PWM_RGB/
│
├── Lab4/
│   └── ESP32_IoT_WebServer/
│
├── Lab5/
│   └── ESP8266_DHT11/
│
└── README.md
