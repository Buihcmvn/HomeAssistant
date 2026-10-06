# -*- coding: utf-8 -*-
import eventlet
eventlet.monkey_patch()  # Required for asynchronous Flask-SocketIO

import cv2
import imutils
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
# HARDWARE CONTROL FUNCTIONS (MOTOR & SERVO)
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
# CAMERA STREAM GENERATOR (RAW MJPEG)
# ---------------------------------------------------------
def generate_frames():
    camera = cv2.VideoCapture(0)
    
    # Force MJPEG format to ensure stable streaming on Linux/Raspberry Pi
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
                # Resize frame for smooth network bandwidth on mobile devices
                frame = imutils.resize(frame, width=480)

                # Compress and encode directly as JPEG without any image processing overhead
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                if not ret:
                    eventlet.sleep(0.01)
                    continue
                    
                frame_bytes = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            except Exception as e:
                print("Stream error: {}".format(e))
                
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
# WEBSOCKET EVENTS (MOBILE CONTROLS)
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

@socketio.on('servo_canon')
def handle_servo_canon(data):
    global GPos
    position = data.get('position')
    if position == 'left':
        GPos = 500
    elif position == 'right':
        GPos = 2500
    elif position == 'center':
        GPos = 1400
        
    servo_canon.runServo(GPos)
    emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos}, broadcast=True)

if __name__ == '__main__':
    print("=====================================================")
    print(" ROBOT STREAM & CONTROL SERVER STARTED!")
    print(" Access from phone browser: http://<IP_RASPBERRY_PI>:5000")
    print("=====================================================")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)