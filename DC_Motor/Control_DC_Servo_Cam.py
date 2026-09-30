# -*- coding: utf-8 -*-
"""
Chương trình điều khiển Robot Raspberry Pi:
- PCA9685: Điều khiển DC Motor và Servo (Pan/Tilt, Canon)
- Threading + Queue: Đọc Camera mượt mà không bị nghẽn bàn phím
- Pynput: Nhận sự kiện bàn phím (WASD, Phím mũi tên)
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

# Thư viện điều khiển PCA9685
from PCA9685 import PCA9685

# ---------------------------------------------------------
# 1. CẤU HÌNH BIẾN TOÀN CỤC & PCA9685
# ---------------------------------------------------------
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(50)

# Trạng thái ban đầu
Pos = 1100      # Vị trí Servo chính
GPos = 1500     # Vị trí Servo Canon
speed = 60      # Tốc độ động cơ DC (0 - 100)
current_status = "STOP"

Dir = ['forward', 'backward']


# ---------------------------------------------------------
# 2. LỚP ĐIỀU KHIỂN SERVO & MOTOR
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
# 3. LUỒNG ĐỌC CAMERA (CAMERA THREAD)
# ---------------------------------------------------------
def camera_thread(msg_queue, stop_event):
    logging.info("Thread Camera: Đang khởi chạy")
    
    vs = VideoStream(src=0).start()
    time.sleep(2.0)  # Chờ camera khởi động

    status_msg = "STOP"

    while not stop_event.is_set():
        # Đọc tin nhắn từ bàn phím không bị nghẽn (Non-blocking queue)
        try:
            status_msg = msg_queue.get_nowait()
        except queue.Empty:
            pass

        frame = vs.read()
        if frame is None:
            continue

        # Resize khung hình để tăng tốc độ hiển thị
        frame = imutils.resize(frame, width=600)

        # Hiển thị thông tin điều khiển lên góc màn hình Video
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, f"Status: {status_msg}", (20, 30), font, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Speed : {speed}", (20, 60), font, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Servo : {Pos}", (20, 90), font, 0.7, (0, 255, 0), 2)

        # Hiển thị Cửa sổ Video
        cv2.imshow("Raspberry Pi - Camera Stream", frame)
        
        # Bấm 'q' trên cửa sổ cv2 để thoát khẩn cấp
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break

    vs.stop()
    cv2.destroyAllWindows()
    logging.info("Thread Camera: Đã dừng")


# ---------------------------------------------------------
# 4. BỘ HỨNG SỰ KIỆN BÀN PHÍM (KEYBOARD LISTENER)
# ---------------------------------------------------------
def on_press(key):
    global Pos, GPos, speed, Motor, Servo, Canon, pipeline

    msg = ''

    try:
        # Điều khiển góc Servo (Phím W / S)
        if hasattr(key, 'char') and key.char == 'w':
            Pos = min(2500, Pos + 25)
            Servo.runServo(Pos)
            print(f"Servo UP: {Pos}")
            msg = f"Servo Up ({Pos})"

        elif hasattr(key, 'char') and key.char == 's':
            Pos = max(500, Pos - 25)
            Servo.runServo(Pos)
            print(f"Servo DOWN: {Pos}")
            msg = f"Servo Down ({Pos})"

        # Điều khiển Canon Servo (Phím G, H, J)
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

        # Tăng/Giảm Tốc độ (Phím U / D)
        elif hasattr(key, 'char') and key.char == 'u':
            speed = min(100, speed + 10)
            print(f"Speed +: {speed}")
            msg = f"Speed: {speed}"
        elif hasattr(key, 'char') and key.char == 'd':
            speed = max(0, speed - 10)
            print(f"Speed -: {speed}")
            msg = f"Speed: {speed}"

    except AttributeError:
        pass

    # Điều khiển hướng Động cơ DC (Phím mũi tên)
    if key == Key.up:
        Motor.MotorRun(0, 'forward', speed)
        Motor.MotorRun(1, 'forward', speed)
        msg = "FORWARD"
    elif key == Key.down:
        Motor.MotorRun(0, 'backward', speed)
        Motor.MotorRun(1, 'backward', speed)
        msg = "BACKWARD"
    elif key == Key.left:
        Motor.MotorRun(0, 'backward', speed)
        Motor.MotorRun(1, 'forward', speed)
        msg = "TURN LEFT"
    elif key == Key.right:
        Motor.MotorRun(0, 'forward', speed)
        Motor.MotorRun(1, 'backward', speed)
        msg = "TURN RIGHT"

    if msg:
        pipeline.put(msg)


def on_release(key):
    global pipeline
    # Khi thả phím mũi tên thì dừng động cơ
    if key in [Key.up, Key.down, Key.left, Key.right]:
        Motor.StopAll()
        pipeline.put("STOP")

    # Nhấn ESC để dừng chương trình
    elif key == Key.esc:
        print("\nĐang dừng chương trình...")
        event.set()
        return False


# ---------------------------------------------------------
# 5. VÒNG LẶP CHÍNH (MAIN PROGRAM)
# ---------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.INFO, datefmt="%H:%M:%S")

    pipeline = queue.Queue(maxsize=10)
    event = threading.Event()

    # Khởi tạo phần cứng
    Motor = MotorDriver()
    Servo = ServoDriver(6)
    Canon = ServoDriver(7)

    # Đưa Servo về vị trí ban đầu
    Servo.runServo(Pos)
    Canon.runServo(GPos)

    # Khởi chạy Thread Camera
    cam_thread = threading.Thread(target=camera_thread, args=(pipeline, event), daemon=True)
    cam_thread.start()

    print("==================================================")
    print(" BẮT ĐẦU ĐIỀU KHIỂN ROBOT")
    print(" - Phím mũi tên UP/DOWN/LEFT/RIGHT : Điều khiển di chuyển")
    print(" - Phím W / S                      : Nâng / Hạ Servo")
    print(" - Phím G / H / J                  : Xoay Servo Canon")
    print(" - Phím U / D                      : Tăng / Giảm tốc độ")
    print(" - Phím ESC                        : Thoát chương trình")
    print("==================================================")

    # Bắt sự kiện bàn phím
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

    # Dọn dẹp sau khi thoát
    event.set()
    cam_thread.join()
    Motor.StopAll()
    print("Đã dừng toàn bộ động cơ và giải phóng tài nguyên!")