import eventlet
eventlet.monkey_patch()  # Required for asynchronous Flask-SocketIO

import time
import cv2
import imutils
import numpy as np
from flask import Flask, render_template, Response
from flask_socketio import SocketIO, emit

# Integrate PCA9685 hardware library
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

# Global state variables
current_dir = "STOP"
current_speed = 60
auto_mode = False  # Flag to toggle obstacle detection display mode
Pos = 1100
GPos = 1400

# Hardware motor control function (Using .format() for Python 3.5 compatibility)
def set_motor_control(direction, speed):
    if not HAS_HARDWARE:
        print("[SIMULATION] Motor Drive: {} at speed {}".format(direction, speed))
        return
    
    # Convert speed level (0-100) to PWM pulse width (0-4095)
    pwm_val = int(speed * 40.95)
    
    if direction == "FORWARD":
        pwm.setPWM(0, 0, pwm_val)  # Replace with your actual pin configuration
        print("Motor Moving FORWARD with speed {}".format(speed))
    elif direction == "BACKWARD":
        print("Motor Moving BACKWARD with speed {}".format(speed))
    elif direction == "LEFT":
        print("Motor Turning LEFT")
    elif direction == "RIGHT":
        print("Motor Turning RIGHT")
    else:
        print("Motor STOP")

# Simple obstacle detection image processing algorithm
def detect_obstacle(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    h, w = blurred.shape
    third_w = w // 3
    
    left_region = blurred[:, :third_w]
    center_region = blurred[:, third_w:2*third_w]
    right_region = blurred[:, 2*third_w:]
    
    edges = cv2.Canny(blurred, 50, 150)
    
    left_val = np.sum(edges[:, :third_w])
    center_val = np.sum(edges[:, third_w:2*third_w])
    right_val = np.sum(edges[:, 2*third_w:])
    
    THRESHOLD = 2000000 
    
    obstacle_center = center_val > THRESHOLD
    obstacle_left = left_val > THRESHOLD
    obstacle_right = right_val > THRESHOLD
    
    return obstacle_center, obstacle_left, obstacle_right

# Camera stream and obstacle detection display thread
def generate_frames():
    global current_dir, current_speed, auto_mode
    camera = cv2.VideoCapture(0)
    
    # Ép camera xuất ra định dạng MJPEG để OpenCV đọc mượt mà trên Linux và tránh lỗi V4L2
    camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    try:
        while True:
            success, frame = camera.read()
            if not success or frame is None:
                eventlet.sleep(0.01)
                continue

            frame = imutils.resize(frame, width=480)
            h, w, _ = frame.shape
            third_w = w // 3

            # Nếu bật chế độ nhận diện, tiến hành phân tích và đánh dấu vật cản lên màn hình (không điều khiển động cơ)
            if auto_mode:
                c_obs, l_obs, r_obs = detect_obstacle(frame)
                
                # Vẽ các đường phân chia 3 vùng (Trái, Giữa, Phải)
                cv2.line(frame, (third_w, 0), (third_w, h), (255, 255, 0), 1)
                cv2.line(frame, (2 * third_w, 0), (2 * third_w, h), (255, 255, 0), 1)

                # Đánh dấu và thông báo trực quan trên màn hình tùy theo vùng có vật cản
                if c_obs:
                    cv2.rectangle(frame, (third_w, 0), (2 * third_w, h), (0, 0, 255), 2)
                    cv2.putText(frame, "OBSTACLE CENTER!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                if l_obs:
                    cv2.rectangle(frame, (0, 0), (third_w, h), (0, 165, 255), 2)
                    cv2.putText(frame, "OBSTACLE LEFT", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                if r_obs:
                    cv2.rectangle(frame, (2 * third_w, 0), (w, h), (0, 165, 255), 2)
                    cv2.putText(frame, "OBSTACLE RIGHT", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                
                if not c_obs and not l_obs and not r_obs:
                    cv2.putText(frame, "PATH CLEAR", (150, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Hiển thị thông tin trạng thái lên khung hình video stream
            cv2.putText(frame, "DETECT MODE: {} | CMD: {}".format("ON" if auto_mode else "OFF", current_dir), (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            cv2.putText(frame, "SPD: {} | TILT: {}".format(current_speed, Pos), (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if not ret:
                eventlet.sleep(0.01)
                continue
                
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            eventlet.sleep(0.01)
    finally:
        camera.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('move')
def handle_move(data):
    global current_dir, current_speed
    current_dir = data.get('dir', 'STOP')
    current_speed = data.get('speed', 60)
    set_motor_control(current_dir, current_speed)
    socketio.emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos})

@socketio.on('stop')
def handle_stop():
    global current_dir, current_speed
    current_dir = "STOP"
    set_motor_control("STOP", 0)
    socketio.emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos})

@socketio.on('toggle_auto')
def handle_toggle_auto(data):
    global auto_mode
    auto_mode = data.get('auto', False)
    print("Obstacle Detection Display Mode set to: {}".format(auto_mode))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)