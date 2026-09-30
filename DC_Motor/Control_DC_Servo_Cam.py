# -*- coding: utf-8 -*-
"""
Raspberry Pi Robot Control Program (Python 3.5+ Compatible):
- PCA9685: Controls DC Motors and Servos (Pan/Tilt, Canon)
- Threading + Queue: High-FPS camera stream without blocking keyboard input
- OpenCV GUI: Hardware-accelerated window scaling (1024px display)
- Pynput: Keyboard event listener (WASD, Arrow Keys) with I2C anti-spam state management
"""

import logging
import threading
import queue
import time
import sys
import numpy as np
import cv2
import imutils
from imutils.video import VideoStream
from pynput.keyboard import Key, Listener

# PCA9685 Driver Library
from PCA9685 import PCA9685

# ---------------------------------------------------------
# 1. GLOBAL CONFIGURATION & PCA9685 INITIALIZATION
# ---------------------------------------------------------
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(50)

# Initial Hardware States
Pos = 1100          # Main Servo position
GPos = 1500         # Canon Servo position
speed = 60          # DC Motor speed (0 - 100)

# State variable to track motor direction and prevent duplicate I2C commands
current_dir = "STOP"

Dir = ['forward', 'backward']


# ---------------------------------------------------------
# 2. SERVO & MOTOR DRIVER CLASSES
# ---------------------------------------------------------
class ServoDriver():
    def __init__(self, _channel=6):
        self.channel = _channel

    def runServo(self, _Pos):
        pwm.setServoPulse(self.channel, _Pos)


class MotorDriver():
    def __init__(self):
        self.PWMA = 0
        self.AIN1 = 1
        self.AIN2 = 2
        self.PWMB = 5
        self.BIN1 = 3
        self.BIN2 = 4

    def MotorRun(self, motor, index, speed):
        if speed > 100:
            speed = 100
        if motor == 0:
            pwm.setDutycycle(self.PWMA, speed)
            if index == Dir[1]:
                pwm.setLevel(self.AIN1, 0)
                pwm.setLevel(self.AIN2, 1)
            else:
                pwm.setLevel(self.AIN1, 1)
                pwm.setLevel(self.AIN2, 0)
        else:
            pwm.setDutycycle(self.PWMB, speed)
            if index == Dir[1]:
                pwm.setLevel(self.BIN1, 0)
                pwm.setLevel(self.BIN2, 1)
            else:
                pwm.setLevel(self.BIN1, 1)
                pwm.setLevel(self.BIN2, 0)

    def MotorStop(self, motor):
        if motor == 0:
            pwm.setDutycycle(self.PWMA, 0)
        else:
            pwm.setDutycycle(self.PWMB, 0)

    def StopAll(self):
        self.MotorStop(0)
        self.MotorStop(1)


# ---------------------------------------------------------
# 3. CAMERA THREAD FUNCTION (FPS OPTIMIZED)
# ---------------------------------------------------------
def camera_thread(msg_queue, stop_event):
    logging.info("Camera Thread: Starting Optimized FPS Mode")
    
    # Initialize camera with optimal capture resolution
    vs = VideoStream(src=0, resolution=(640, 480)).start()
    time.sleep(2.0)  # Allow camera sensor to warm up

    status_msg = "STOP"

    # Create resizable OpenCV window (GPU/hardware scaled to 1024px width)
    win_name = "Raspberry Pi - Camera Stream"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(win_name, 1024, 768)

    # FPS counter variables
    fps_count = 0
    fps_display = 0
    start_time = time.time()

    while not stop_event.is_set():
        # Non-blocking check for keyboard control messages
        try:
            status_msg = msg_queue.get_nowait()
        except queue.Empty:
            pass

        frame = vs.read()
        if frame is None:
            continue

        # Keep processing width at 600px to reduce CPU workload
        frame = imutils.resize(frame, width=600)

        # Calculate actual FPS
        fps_count += 1
        if (time.time() - start_time) > 1.0:
            fps_display = fps_count
            fps_count = 0
            start_time = time.time()

        # Render overlay text onto frame
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, "Status: {}".format(status_msg), (20, 30), font, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Speed : {}".format(speed), (20, 60), font, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "Servo : {}".format(Pos), (20, 90), font, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "FPS   : {}".format(fps_display), (20, 120), font, 0.7, (0, 255, 255), 2)

        # Show frame (OpenCV handles hardware upscaling)
        cv2.imshow(win_name, frame)
        
        # Press 'q' on OpenCV window for emergency stop
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    vs.stop()
    cv2.destroyAllWindows()
    logging.info("Camera Thread: Stopped")


# ---------------------------------------------------------
# 4. KEYBOARD EVENT LISTENER (STATE-MANAGED & ANTI-SPAM)
# ---------------------------------------------------------
def on_press(key):
    global Pos, GPos, speed, Motor, Servo, Canon, pipeline, current_dir

    msg = ''

    # A. Servo Position and Speed Control
    try:
        if hasattr(key, 'char') and key.char == 'w':
            Pos = min(2500, Pos + 25)
            Servo.runServo(Pos)
            msg = "Servo Up ({})".format(Pos)

        elif hasattr(key, 'char') and key.char == 's':
            Pos = max(500, Pos - 25)
            Servo.runServo(Pos)
            msg = "Servo Down ({})".format(Pos)

        elif hasattr(key, 'char') and key.char == 'g':
            GPos = 500
            Canon.runServo(GPos)
            msg = "Canon Left"

        elif hasattr(key, 'char') and key.char == 'h':
            GPos = 1400
            Canon.runServo(GPos)
            msg = "Canon Center"

        elif hasattr(key, 'char') and key.char == 'j':
            GPos = 2700
            Canon.runServo(GPos)
            msg = "Canon Right"

        elif hasattr(key, 'char') and key.char == 'u':
            speed = min(100, speed + 10)
            msg = "Speed: {}".format(speed)

        elif hasattr(key, 'char') and key.char == 'd':
            speed = max(0, speed - 10)
            msg = "Speed: {}".format(speed)

    except AttributeError:
        pass

    # B. DC Motor Direction Control (State Checked to Prevent I2C Spam)
    new_dir = None

    if key == Key.up:
        new_dir = "FORWARD"
    elif key == Key.down:
        new_dir = "BACKWARD"
    elif key == Key.left:
        new_dir = "LEFT"
    elif key == Key.right:
        new_dir = "RIGHT"

    # Only send I2C commands when direction state actually changes
    if new_dir and new_dir != current_dir:
        current_dir = new_dir
        
        if current_dir == "FORWARD":
            Motor.MotorRun(0, 'forward', speed)
            Motor.MotorRun(1, 'forward', speed)
        elif current_dir == "BACKWARD":
            Motor.MotorRun(0, 'backward', speed)
            Motor.MotorRun(1, 'backward', speed)
        elif current_dir == "LEFT":
            Motor.MotorRun(0, 'backward', speed)
            Motor.MotorRun(1, 'forward', speed)
        elif current_dir == "RIGHT":
            Motor.MotorRun(0, 'forward', speed)
            Motor.MotorRun(1, 'backward', speed)
        
        msg = current_dir

    # Safely push notification message to Queue without blocking
    if msg:
        try:
            pipeline.put_nowait(msg)
        except queue.Full:
            pass


def on_release(key):
    global pipeline, current_dir
    
    # Stop motors when navigation arrow key is released
    if key in [Key.up, Key.down, Key.left, Key.right]:
        Motor.StopAll()
        current_dir = "STOP"
        try:
            pipeline.put_nowait("STOP")
        except queue.Full:
            pass

    # Exit application when ESC key is released
    elif key == Key.esc:
        print("\nStopping program...")
        event.set()
        return False


# ---------------------------------------------------------
# 5. MAIN PROGRAM ENTRY
# ---------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")

    pipeline = queue.Queue(maxsize=10)
    event = threading.Event()

    # Hardware Initialization
    Motor = MotorDriver()
    Servo = ServoDriver(6)
    Canon = ServoDriver(7)

    # Move Servos to initial positions
    Servo.runServo(Pos)
    Canon.runServo(GPos)

    # Start Camera Thread
    cam_thread = threading.Thread(target=camera_thread, args=(pipeline, event), daemon=True)
    cam_thread.start()

    print("==================================================")
    print(" ROBOT CONTROL STARTED (PYTHON 3.5 READY)")
    print(" - Arrow Keys UP/DOWN/LEFT/RIGHT : Navigation")
    print(" - Keys W / S                    : Tilt Servo Up/Down")
    print(" - Keys G / H / J                : Rotate Canon Servo")
    print(" - Keys U / D                    : Speed Up/Down")
    print(" - Key ESC                       : Exit Program")
    print("==================================================")

    # Start Listening to Keyboard Events
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    # Clean up resources on exit
    event.set()
    cam_thread.join()
    Motor.StopAll()
    print("All motors stopped and hardware resources released successfully!")