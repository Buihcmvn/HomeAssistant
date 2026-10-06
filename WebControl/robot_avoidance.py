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

# Obstacle detection restricted to the middle 1/3 horizontal strip (ROI)
def detect_obstacle(frame):
    h, w, _ = frame.shape
    
    # Crop to the middle 1/3 horizontal strip of the frame based on user markup
    roi_top = int(h * 0.35)
    roi_bottom = int(h * 0.65)
    roi = frame[roi_top:roi_bottom, :]
    rh, rw, _ = roi.shape
    third_w = rw // 3
    
    # Convert ROI to grayscale and apply slight blur
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    # Use adaptive thresholding to isolate objects inside the strip
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 5)
    
    # Remove noise using morphological operations
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Find contours safely across different OpenCV versions (3.x and 4.x)
    contours_result = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours_result) == 3:
        _, contours, _ = contours_result
    else:
        contours, _ = contours_result
    
    obstacle_left = False
    obstacle_center = False
    obstacle_right = False
    
    min_contour_area = 1000  # Minimum pixel area for detection in the strip
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_contour_area:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                
                # Check which zone the obstacle centroid falls into
                if cx < third_w:
                    obstacle_left = True
                elif cx < 2 * third_w:
                    obstacle_center = True
                else:
                    obstacle_right = True
                    
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
                eventlet.sleep(0.05)
                continue

            try:
                frame = imutils.resize(frame, width=480)
                h, w, _ = frame.shape
                third_w = w // 3
                
                roi_top = int(h * 0.35)
                roi_bottom = int(h * 0.65)

                # If obstacle detection display mode is enabled, analyze and draw visual alerts
                if auto_mode:
                    c_obs, l_obs, r_obs = detect_obstacle(frame)
                    
                    # Draw visual rectangle representing the scanning strip (matching user requirement)
                    cv2.rectangle(frame, (0, roi_top), (w, roi_bottom), (0, 255, 255), 1)
                    
                    # Draw vertical grid lines dividing 3 zones inside the strip
                    cv2.line(frame, (third_w, roi_top), (third_w, roi_bottom), (255, 255, 0), 1)
                    cv2.line(frame, (2 * third_w, roi_top), (2 * third_w, roi_bottom), (255, 255, 0), 1)

                    # Draw visual warnings based on detected obstacles
                    if c_obs:
                        cv2.rectangle(frame, (third_w, roi_top), (2 * third_w, roi_bottom), (0, 0, 255), 2)
                        cv2.putText(frame, "OBSTACLE CENTER!", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    if l_obs:
                        cv2.rectangle(frame, (0, roi_top), (third_w, roi_bottom), (0, 165, 255), 2)
                        cv2.putText(frame, "OBSTACLE LEFT", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
                    if r_obs:
                        cv2.rectangle(frame, (2 * third_w, roi_top), (w, roi_bottom), (0, 165, 255), 2)
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
            
            except Exception as e:
                print("Frame processing error: {}".format(e))
                
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
    
    if canon_timer and canon_timer.is_alive():
        canon_timer.cancel()

    if position == 'left':
        GPos = 500
    elif position == 'right':
        GPos = 2500
        
    servo_canon.runServo(GPos)
    print("Servo Canon Position: {}".format(GPos))
    emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

    canon_timer = threading.Timer(3.0, reset_canon_to_center)
    canon_timer.start()

if __name__ == '__main__':
    print("=====================================================")
    print(" ROBOT WEB SERVER (STRIP ROI DETECTION) STARTED!")
    print(" Access from browser: http://<IP_RASPBERRY_PI>:5000")
    print("=====================================================")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)