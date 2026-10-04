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
auto_mode = False  # Flag to toggle auto obstacle avoidance mode
Pos = 1100
GPos = 1400

# Hardware motor control function
def set_motor_control(direction, speed):
    if not HAS_HARDWARE:
        print(f"[SIMULATION] Motor Drive: {direction} at speed {speed}")
        return
    
    # Convert speed level (0-100) to PWM pulse width (0-4095)
    pwm_val = int(speed * 40.95)
    
    if direction == "FORWARD":
        # Example motor pin configuration for forward movement (depends on your hardware setup)
        pwm.setPWM(0, 0, pwm_val)  # Replace with your actual pin configuration
        print(f"Motor Moving FORWARD with speed {speed}")
    elif direction == "BACKWARD":
        print(f"Motor Moving BACKWARD with speed {speed}")
    elif direction == "LEFT":
        print(f"Motor Turning LEFT")
    elif direction == "RIGHT":
        print(f"Motor Turning RIGHT")
    else:
        # STOP
        print(f"Motor STOP")

# Simple obstacle detection image processing algorithm (based on contrast/edge detection)
def detect_obstacle(frame):
    # Convert to grayscale and blur to reduce noise
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    
    # Divide the frame into 3 regions: Left, Center, Right
    h, w = blurred.shape
    third_w = w // 3
    
    left_region = blurred[:, :third_w]
    center_region = blurred[:, third_w:2*third_w]
    right_region = blurred[:, 2*third_w:]
    
    # Calculate obstacle level based on edge amplitude (Canny Edge)
    edges = cv2.Canny(blurred, 50, 150)
    
    left_val = np.sum(edges[:, :third_w])
    center_val = np.sum(edges[:, third_w:2*third_w])
    right_val = np.sum(edges[:, 2*third_w:])
    
    # Obstacle detection threshold (can be fine-tuned based on actual lighting conditions)
    THRESHOLD = 2000000 
    
    obstacle_center = center_val > THRESHOLD
    obstacle_left = left_val > THRESHOLD
    obstacle_right = right_val > THRESHOLD
    
    return obstacle_center, obstacle_left, obstacle_right

# Camera stream and parallel obstacle avoidance logic thread
def generate_frames():
    global current_dir, current_speed, auto_mode
    camera = cv2.VideoCapture(0)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        success, frame = camera.read()
        if not success:
            eventlet.sleep(0.01)
            continue

        frame = imutils.resize(frame, width=480)
        
        # If auto avoidance mode is enabled
        if auto_mode:
            c_obs, l_obs, r_obs = detect_obstacle(frame)
            
            if c_obs:
                # If obstacle is in the center -> Reverse and turn toward a clearer direction
                current_dir = "BACKWARD"
                set_motor_control("BACKWARD", current_speed)
                cv2.putText(frame, "OBSTACLE CENTER! REVERSING...", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            elif l_obs:
                # If obstacle is on the left -> Turn right to avoid
                current_dir = "RIGHT"
                set_motor_control("RIGHT", current_speed)
                cv2.putText(frame, "OBSTACLE LEFT -> TURNING RIGHT", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            elif r_obs:
                # If obstacle is on the right -> Turn left to avoid
                current_dir = "LEFT"
                set_motor_control("LEFT", current_speed)
                cv2.putText(frame, "OBSTACLE RIGHT -> TURNING LEFT", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
            else:
                # Path clear -> Move forward
                current_dir = "FORWARD"
                set_motor_control("FORWARD", current_speed)
                cv2.putText(frame, "PATH CLEAR -> MOVING FORWARD", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Display status parameters on the video stream frame
        cv2.putText(frame, "MODE: {} | STATUS: {}".format("AUTO" if auto_mode else "MANUAL", current_dir), (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, "SPD: {} | TILT: {}".format(current_speed, Pos), (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        eventlet.sleep(0.01)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Socket.IO event handler for receiving commands from the web GUI
@socketio.on('move')
def handle_move(data):
    global current_dir, current_speed, auto_mode
    if auto_mode:
        return  # Ignore manual web commands if in auto mode
    
    current_dir = data.get('dir', 'STOP')
    current_speed = data.get('speed', 60)
    set_motor_control(current_dir, current_speed)
    socketio.emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos})

@socketio.on('stop')
def handle_stop():
    global current_dir, auto_mode
    current_dir = "STOP"
    set_motor_control("STOP", 0)
    socketio.emit('status_update', {'dir': current_dir, 'speed': current_speed, 'pos': Pos, 'gpos': GPos})

@socketio.on('toggle_auto')
def handle_toggle_auto(data):
    global auto_mode
    auto_mode = data.get('auto', False)
    print(f"Auto Avoidance Mode set to: {auto_mode}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)