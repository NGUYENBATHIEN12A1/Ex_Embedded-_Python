import machine
import time

# --- 1. ĐỊNH NGHĨA CÁC CHÂN GPIO ---
BTN_PIN = 4
LED_PIN = 2
RGB_R_PIN = 18
RGB_G_PIN = 19
RGB_B_PIN = 21

# --- 2. CẤU HÌNH THIẾT BỊ ---
# Nút nhấn dùng điện trở kéo lên nội (PULL_UP)
btn = machine.Pin(BTN_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# Khởi tạo LED đơn
led = machine.Pin(LED_PIN, machine.Pin.OUT)
pwm_led = None # Sẽ khởi tạo khi vào Mode 2

# Khởi tạo PWM cho RGB LED (mặc định duty = 0 là tắt)
pwm_r = machine.PWM(machine.Pin(RGB_R_PIN), freq=1000, duty=0)
pwm_g = machine.PWM(machine.Pin(RGB_G_PIN), freq=1000, duty=0)
pwm_b = machine.PWM(machine.Pin(RGB_B_PIN), freq=1000, duty=0)

# Timer cho Mode 1
timer = machine.Timer(0)

# --- 3. BIẾN TOÀN CỤC ---
current_mode = 1
last_interrupt_time = 0

# --- 4. CÁC HÀM XỬ LÝ ---
def turn_off_all():
    """Tắt tất cả hiệu ứng và Timer/PWM hiện tại"""
    global pwm_led
    timer.deinit() # Tắt Timer
    
    if pwm_led is not None:
        pwm_led.deinit() # Tắt PWM của LED đơn
        pwm_led = None
        
    led.value(0) # Đảm bảo LED đơn tắt
    pwm_r.duty(0)
    pwm_g.duty(0)
    pwm_b.duty(0)

def mode_1_blink(t):
    """Hàm callback cho Timer - Chớp tắt LED"""
    led.value(not led.value())

def set_mode(mode):
    """Thiết lập chế độ hoạt động và in ra Shell"""
    global current_mode, pwm_led
    turn_off_all() # Reset trạng thái trước khi chuyển chế độ
    current_mode = mode
    
    if mode == 1:
        print("Current Mode: Mode 1 - Timer LED Blink")
        # Nhấp nháy mỗi giây (chu kỳ 1000ms)
        timer.init(period=1000, mode=machine.Timer.PERIODIC, callback=mode_1_blink)
        
    elif mode == 2:
        print("Current Mode: Mode 2 - PWM Brightness Fading")
        # Khởi tạo lại chân LED thành PWM
        pwm_led = machine.PWM(machine.Pin(LED_PIN), freq=1000, duty=0)
        
    elif mode == 3:
        print("Current Mode: Mode 3 - RGB Color Cycling")

def button_isr(pin):
    """Hàm Ngắt (Interrupt Service Routine) xử lý khi bấm nút"""
    global current_mode, last_interrupt_time
    current_time = time.ticks_ms()
    
    # Kỹ thuật Software Debounce: Bỏ qua nếu 2 lần bấm cách nhau < 250ms
    if time.ticks_diff(current_time, last_interrupt_time) > 250:
        next_mode = current_mode + 1
        if next_mode > 3:
            next_mode = 1
        set_mode(next_mode)
        last_interrupt_time = current_time

# Đăng ký ngắt cho nút nhấn (Kích hoạt ở sườn xuống - IRQ_FALLING)
btn.irq(trigger=machine.Pin.IRQ_FALLING, handler=button_isr)

# Khởi động hệ thống ở Mode 1
set_mode(1)


# --- 5. VÒNG LẶP CHÍNH (MAIN LOOP) ---
fade_amount = 15
duty_led = 0

# Danh sách 5 màu cho RGB (Đỏ, Xanh lá, Xanh dương, Vàng, Tím)
colors = [
    (1023, 0, 0),
    (0, 1023, 0),
    (0, 0, 1023),
    (1023, 1023, 0),
    (1023, 0, 1023)
]
color_idx = 0

while True:
    if current_mode == 2:
        # Tác vụ nền cho Mode 2: Fading LED đơn
        if pwm_led is not None:
            pwm_led.duty(duty_led)
            duty_led += fade_amount
            if duty_led >= 1023 or duty_led <= 0:
                fade_amount = -fade_amount # Đổi chiều sáng/tối
            time.sleep_ms(15)
            
    elif current_mode == 3:
        # Tác vụ nền cho Mode 3: Đổi màu RGB
        r, g, b = colors[color_idx]
        pwm_r.duty(r)
        pwm_g.duty(g)
        pwm_b.duty(b)
        color_idx = (color_idx + 1) % len(colors)
        
        # Chia nhỏ thời gian delay (500ms) để không khóa (block) vòng lặp quá lâu
        # Giúp hệ thống phản hồi mượt mà hơn nếu có chuyển mode
        for _ in range(50):
            if current_mode != 3:
                break
            time.sleep_ms(10)
            
    else:
        # Nếu ở Mode 1, Timer đã tự xử lý ngầm, vòng lặp chính chỉ cần ngủ ngắn để giảm tải CPU
        time.sleep_ms(100)