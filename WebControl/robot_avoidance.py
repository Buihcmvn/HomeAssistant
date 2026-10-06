# -*- coding: utf-8 -*-
import eventlet
eventlet.monkey_patch()  # Required for asynchronous Flask-SocketIO

import time
import threading
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

# ---------------------------------------------------------
# GLOBAL STATE & CONTROL OBJECTS
# ---------------------------------------------------------
current_speed = 60
current_dir = "STOP"
Pos = 1100   # Servo Tilt position (Camera) - Default center
GPos = 1400  # Servo Canon position - Default center
auto_mode = False  # Flag to toggle obstacle detection display mode on video feed

# Global variable for managing Canon servo auto-center timer
canon_timer = None

class ServoDriver():
    def __init__(self, _channel=6):
        self.channel = _channel

    def runServo(self, _Pos):
        if HAS_HARDWARE:
            pwm.setServoPulse(self.channel, _Pos)

# Initialize 2 Servos (Channel 6 for Camera Tilt, Channel 7 for Canon)
servo_cam = ServoDriver(6)
servo_canon = ServoDriver(7)

# ---------------------------------------------------------
# 1. HARDWARE CONTROL FUNCTIONS (MOTOR & SERVO)
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

# Simple obstacle detection image processing algorithm
def detect_obstacle(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    h, w = blurred.shape
    third_w = w // 3
    
    edges = cv2.Canny(blurred, 50, 150)
    
    left_val = np.sum(edges[:, :third_w])
    center_val = np.sum(edges[:, third_w:2*third_w])
    right_val = np.sum(edges[:, 2*third_w:])
    
    THRESHOLD = 500000 
    
    obstacle_center = center_val > THRESHOLD
    obstacle_left = left_val > THRESHOLD
    obstacle_right = right_val > THRESHOLD
    
    return obstacle_center, obstacle_left, obstacle_right

# ---------------------------------------------------------
# 2. CAMERA STREAM GENERATOR (MJPEG)
# ---------------------------------------------------------
def generate_frames():
    global auto_mode
    camera = cv2.VideoCapture(0)
    
    # Force MJPEG format to prevent OpenCV V4L2 unsupported pixel format errors on Linux
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

            # If obstacle detection display mode is enabled, draw warning boxes and grid lines on screen
            if auto_mode:
                c_obs, l_obs, r_obs = detect_obstacle(frame)
                
                # Draw vertical grid lines dividing 3 zones (Left, Center, Right)
                cv2.line(frame, (third_w, 0), (third_w, h), (255, 255, 0), 1)
                cv2.line(frame, (2 * third_w, 0), (2 * third_w, h), (255, 255, 0), 1)

                # Draw visual warnings based on detected obstacles
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

            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if not ret:
                eventlet.sleep(0.01)
                continue
                
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Yield CPU slightly after each frame so WebSocket commands are received promptly
            eventlet.sleep(0.01)
    finally:
        camera.release()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------------------------------------
# 3. WEBSOCKET EVENTS (ZERO-LATENCY CONTROL)
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

@socketio.on('toggle_auto')
def handle_toggle_auto(data):
    global auto_mode
    auto_mode = data.get('auto', False)
    print("Obstacle Detection Display Mode set to: {}".format(auto_mode))

# Camera Servo control event (Tilt Up/Down)
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

# Helper function to reset Canon servo to center
def reset_canon_to_center():
    global GPos, canon_timer
    GPos = 1400
    servo_canon.runServo(GPos)
    print("Canon Servo auto-reset to Center (1400)")
    socketio.emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos})

# Canon Servo control event (Left / Right with auto-center after 3s)
@socketio.on('servo_canon')
def handle_servo_canon(data):
    global GPos, canon_timer
    position = data.get('position')
    
    # Cancel previous timer if active (to reset the 3s timeout on consecutive clicks)
    if canon_timer and canon_timer.is_alive():
        canon_timer.cancel()

    if position == 'left':
        GPos = 500
    elif position == 'right':
        GPos = 2500
        
    servo_canon.runServo(GPos)
    print("Servo Canon Position: {}".format(GPos))
    emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

    # Set a 3-second timer to automatically reset to center (1400)
    canon_timer = threading.Timer(3.0, reset_canon_to_center)
    canon_timer.start()

if __name__ == '__main__':
    print("=====================================================")
    print(" ROBOT WEB SERVER (OBSTACLE OVERLAY & CANON) STARTED!")
    print(" Access from browser: http://<IP_RASPBERRY_PI>:5000")
    print("=====================================================")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)