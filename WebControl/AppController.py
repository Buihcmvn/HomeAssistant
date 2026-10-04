# -*- coding: utf-8 -*-
import eventlet
eventlet.monkey_patch()  # Tối ưu luồng Asynchronous cho Flask-SocketIO

import time
import threading
import cv2
import imutils
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

# Tích hợp thư viện PCA9685 của phần cứng
try:
    from PCA9685 import PCA9685
    pwm = PCA9685(0x40, debug=False)
    pwm.setPWMFreq(50)
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False
    print("Warning: PCA9685 library not found. Running in simulation mode.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'robot_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ---------------------------------------------------------
# TRẠNG THÁI TOÀN CỤC & ĐỐI TƯỢNG ĐIỀU KHIỂN
# ---------------------------------------------------------
current_speed = 60
current_dir = "STOP"
Pos = 1100   # Vị trí Servo Tilt (Camera) - Mặc định giữa
GPos = 1400  # Vị trí Servo Canon - Mặc định giữa

# Biến toàn cục quản lý luồng hẹn giờ tự động về giữa của Canon Servo
canon_timer = None

class ServoDriver():
    def __init__(self, _channel=6):
        self.channel = _channel

    def runServo(self, _Pos):
        if HAS_HARDWARE:
            pwm.setServoPulse(self.channel, _Pos)

# Khởi tạo 2 Servo (Channel 6 cho Camera Tilt, Channel 7 cho Canon)
servo_cam = ServoDriver(6)
servo_canon = ServoDriver(7)

# ---------------------------------------------------------
# 1. HÀM ĐIỀU KHIỂN HARDWARE (MOTOR & SERVO)
# ---------------------------------------------------------
def set_motor(direction, speed):
    global current_dir
    current_dir = direction
    print("Motor Command: {} | Speed: {}".format(direction, speed))
    
    if not HAS_HARDWARE:
        return

    PWMA, AIN1, AIN2 = 0, 1, 2
    PWMB, BIN1, BIN2 = 5, 3, 4

    if direction == "STOP":
        pwm.setDutycycle(PWMA, 0)
        pwm.setDutycycle(PWMB, 0)
    elif direction == "FORWARD":
        pwm.setDutycycle(PWMA, speed); pwm.setLevel(AIN1, 1); pwm.setLevel(AIN2, 0)
        pwm.setDutycycle(PWMB, speed); pwm.setLevel(BIN1, 1); pwm.setLevel(BIN2, 0)
    elif direction == "BACKWARD":
        pwm.setDutycycle(PWMA, speed); pwm.setLevel(AIN1, 0); pwm.setLevel(AIN2, 1)
        pwm.setDutycycle(PWMB, speed); pwm.setLevel(BIN1, 0); pwm.setLevel(BIN2, 1)
    elif direction == "LEFT":
        pwm.setDutycycle(PWMA, speed); pwm.setLevel(AIN1, 0); pwm.setLevel(AIN2, 1)
        pwm.setDutycycle(PWMB, speed); pwm.setLevel(BIN1, 1); pwm.setLevel(BIN2, 0)
    elif direction == "RIGHT":
        pwm.setDutycycle(PWMA, speed); pwm.setLevel(AIN1, 1); pwm.setLevel(AIN2, 0)
        pwm.setDutycycle(PWMB, speed); pwm.setLevel(BIN1, 0); pwm.setLevel(BIN2, 1)

# ---------------------------------------------------------
# 2. GENERATOR CAMERA STREAM (MJPEG)
# ---------------------------------------------------------
def generate_frames():
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        success, frame = camera.read()
        if not success:
            eventlet.sleep(0.01) # Dùng eventlet.sleep thay vì time.sleep để không nghẽn luồng
            continue

        frame = imutils.resize(frame, width=480)

        # Hiển thị thông số lên màn hình stream
        cv2.putText(frame, "STATUS: {} | SPD: {}".format(current_dir, current_speed), (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, "CAM TILT: {} | CANON: {}".format(Pos, GPos), (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        # Nhường CPU nhẹ nhàng sau mỗi khung hình để WebSocket nhận lệnh kịp thời
        eventlet.sleep(0.001)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------------------------------------
# 3. WEBSOCKET EVENTS (ĐIỀU KHIỂN KHÔNG ĐỘ TRỄ)
# ---------------------------------------------------------
@socketio.on('move')
def handle_move(data):
    global current_speed
    direction = data.get('dir', 'STOP')
    speed_val = data.get('speed', current_speed)
    current_speed = speed_val
    set_motor(direction, current_speed)
    emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

@socketio.on('stop')
def handle_stop():
    set_motor('STOP', 0)
    emit('status_update', {'dir': 'STOP', 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

# Sự kiện điều khiển Servo Camera (Tilt Up/Down)
@socketio.on('servo_tilt')
def handle_servo_tilt(data):
    global Pos
    action = data.get('action')
    if action == 'up':
        Pos = min(2500, Pos + 100)
    elif action == 'down':
        Pos = max(500, Pos - 100)
    servo_cam.runServo(Pos)
    emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

# Hàm phụ trợ đặt lại Canon về giữa
def reset_canon_to_center():
    global GPos, canon_timer
    GPos = 1400
    servo_canon.runServo(GPos)
    print("Canon Servo auto-reset to Center (1400)")
    # Gửi cập nhật giao diện web qua WebSocket
    socketio.emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos})

# Sự kiện điều khiển Servo Canon (Left / Right với cơ chế tự động về giữa sau 3s)
@socketio.on('servo_canon')
def handle_servo_canon(data):
    global GPos, canon_timer
    position = data.get('position')
    
    # Hủy bộ đếm thời gian trước đó nếu có (để reset thời gian 3s khi bấm liên tục)
    if canon_timer and canon_timer.is_alive():
        canon_timer.cancel()

    if position == 'left':
        GPos = 500
    elif position == 'right':
        GPos = 2500
        
    servo_canon.runServo(GPos)
    print("Servo Canon Position: {}".format(GPos))
    emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

    # Đặt bộ đếm thời gian 3 giây để tự động về giữa (1400)
    canon_timer = threading.Timer(3.0, reset_canon_to_center)
    canon_timer.start()

if __name__ == '__main__':
    print("=====================================================")
    print(" ROBOT WEB SERVER (AUTO-CENTER CANON) STARTED!")
    print(" Truy cap tu trinh duyet: http://<IP_RASPBERRY_PI>:5000")
    print("=====================================================")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)