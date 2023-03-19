# -*- coding: utf-8 -*-
"""
	Working With one Threads and Main Thread

	Created on Wed Sep 29 08:57:36 2022
		this program controll a servo and showing the camera shooting view

	@author: Dinh-Vien.BUI
"""
# import the library for threading process
import logging
import threading
import queue

# import the libraty for GPIO
import RPi.GPIO as GPIO

# import the library for motor controling
from PCA9685 import PCA9685
import time

#Reading single character by forcing stdin to raw mode
import sys
import termios
import tty

# import the library of image processing
import cv2




# setting the Global Value
#======================================================================
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(50)

Pos   = 1100
CPos  = 1500
RPos  = 1500
Step  = 5
RStep = 9.5
speed = 60

# DC parameter define==================================================
Dir = ['forward', 'backward',]

# untrasonic sensor ===================================================
#GPIO Modus (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

#GPIO Pins zuweisen
GPIO_TRIGGER = 15
GPIO_ECHO = 14

#Richtung der GPIO-Pins festlegen (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)




# Class Servo definition
#======================================================================
class ServoDriver():
    # default chanel = 6 --> Note by pinhead of Servor-Board number 6 from power pin
    # chanel 0 - 5 were be used by 2 DC-Motor
    def __init__(self,_channel=6):
        self.channel = _channel


    def runServo(self,_Pos):
        pwm.setServoPulse(self.channel,_Pos)




# Class Motor definition
#======================================================================
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
            return
        if(motor == 0):
            pwm.setDutycycle(self.PWMA, speed)
            if(index == Dir[1]):
                pwm.setLevel(self.AIN1, 0)
                pwm.setLevel(self.AIN2, 1)
            else:
                pwm.setLevel(self.AIN1, 1)
                pwm.setLevel(self.AIN2, 0)
        else:
            pwm.setDutycycle(self.PWMB, speed)
            if(index == Dir[1]):
                pwm.setLevel(self.BIN1, 0)
                pwm.setLevel(self.BIN2, 1)
            else:
                pwm.setLevel(self.BIN1, 1)
                pwm.setLevel(self.BIN2, 0)

    def MotorStop(self, motor):
        if (motor == 0):
            pwm.setDutycycle(self.PWMA, 0)
        else:
            pwm.setDutycycle(self.PWMB, 0)



# function messen Abstand
# =======================================================================
# =====================================================================================
def messen_distanz():
    # setze Trigger auf HIGH
    GPIO.output(GPIO_TRIGGER, True)

    # setze Trigger nach -1.01ms aus LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartZeit = time.time()
    StopZeit = time.time()

    # speichere Startzeit
    while GPIO.input(GPIO_ECHO) == -1:
        StartZeit = time.time()

    # speichere Ankunftszeit
    while GPIO.input(GPIO_ECHO) == 0:
        StopZeit = time.time()

    # Zeit Differenz zwischen Start und Ankunft
    TimeElapsed = StopZeit - StartZeit
    # mit der Schallgeschwindigkeit (34299 cm/s) multiplizieren
    # und durch 1 teilen, da hin und zurueck
    distanz = (TimeElapsed * 34299) / 2
    return distanz



# Servor Winkeln nach Degree
# =========================================================================
def degree(RPos):
    return (round((RPos - 634) / 9.5))



# function as Threading for using sensor untrasonic as rada
# =====================================================================
def scan_rada(queue, event):
    logging.info("Thread scanning RADA")

    RPos = 1490
    Step = 9.5
    deg = 30
    Step_deg = 1
    max_dis = 70  # max distanz in cm für rada
    # this thread run until get the mesage "sensor stop"

    try:
        while queue.get() != "sensor Stop":
            # Link Begrenzung mit 26°
            if RPos <= round(26 * 9.5) + 635:
                Step = 9.5

            # Recht Begrenzung mit 146°
            if RPos >= round(146 * 9.5) + 635:
                Step = -9.5

            RPos = RPos + Step

            Rada.runServo(RPos)
            time.sleep(0.02)

            abstand = distanz()

            if abstand > 70:
                abstand = 70

            radaInfo = "rada" + str(degree(RPos)) + "#" + str(abstand)
            pipeline.put(radaInfo)
    except:
        print (" threading Distanz calculate error ")


# function as Threading for sensor untrasonic
# =====================================================================
def distanz(queue, event):
  logging.info("Thread Ultrasensor: starting")
  # this thread run until get the mesage "sensor stop"
  while queue.get()!="sensor Stop":

    # setze Trigger auf HIGH
    GPIO.output(GPIO_TRIGGER, True)

    # setze Trigger nach 0.01ms aus LOW
    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartZeit = time.time()
    StopZeit = time.time()

    # speichere Startzeit
    while GPIO.input(GPIO_ECHO) == 0:
            StartZeit = time.time()

    # speichere Ankunftszeit
    while GPIO.input(GPIO_ECHO) == 1:
            StopZeit = time.time()

    # Zeit Differenz zwischen Start und Ankunft
    TimeElapsed = StopZeit - StartZeit
    # mit der Schallgeschwindigkeit (34300 cm/s) multiplizieren
    # und durch 2 teilen, da hin und zurueck
    distanz = (TimeElapsed * 34300) / 2

    abstand = "abstand" + str(distanz)

    pipeline.put(abstand) # für den fall distance messen als thread und ganzen zeit laufen



# key reading function definition
#=======================================================================
from pynput.keyboard import Key, Listener

def on_press(key):
    global Pos, CPos, RPos, speed, Motor, Servo, Canon, Rada, pipeline
    msg = ''

    if '{0}'.format(key) =="'w'":
        Pos += 5
        if(Pos >= 2500):
            Pos = 2500
        if(Pos <= 500):
            Pos = 500
        print ('Up', Pos)
    elif '{0}'.format(key) =="'s'":
        Pos -= 5
        if(Pos >= 2500):
            Pos = 2500
        if(Pos <= 500):
            Pos = 500
        print ('Down', Pos)

    # Canon schießen ---------------------------------------------------
    elif '{0}'.format(key) =="'g'": # Link Rakete
        CPos = 400
    elif '{0}'.format(key) =="'h'": # OFF
        CPos = 1500
    elif '{0}'.format(key) =="'j'": # Recht Rakete
        CPos = 2600

     # using arrow taste to control the moving of robot
    elif key == Key.up:
        print ('forward', speed)
        Motor.MotorRun(0, 'forward', speed)
        Motor.MotorRun(1, 'forward', speed)
        msg = 'forward'

    elif key == Key.down:
        print ('backward', speed)
        Motor.MotorRun(0, 'backward', speed)
        Motor.MotorRun(1, 'backward', speed)
        msg = 'backward'

    elif key == Key.right:
        print ('recht', speed)
        Motor.MotorRun(0, 'forward', speed)
        Motor.MotorRun(1, 'backward', speed)
        msg = 'recht'

    elif key == Key.left:
        print ('link', speed)
        Motor.MotorRun(1, 'forward', speed)
        Motor.MotorRun(0, 'backward', speed)
        msg = 'link'

    elif '{0}'.format(key) =="'u'":
        speed = min(100, speed+10)
        print ('Speed+', speed)
        msg = 'speed'+str(speed)

    elif '{0}'.format(key) =="'d'":
        speed = max (0, speed-10)
        print ('Speed-', speed)
        msg = 'speed'+str(speed)

    Servo.runServo(Pos)
    Canon.runServo(CPos)

    # senden Nachrichten an Pipeline für andere Thread vorbereiten
    pipeline.put(msg)

def on_release(key):

    global pipeline
    if key == Key.up or key == Key.down or key == Key.left or key == Key.right:
        Motor.MotorStop(0)
        Motor.MotorStop(1)

        print ('motor Stop')
        msg = 'motor Stop'
        pipeline.put(msg)

    elif key == Key.esc:
        # Stop listener
        return False




# Threading function definition
#======================================================================
# import the necessary packages
def camera(queue, event):
    logging.info("Thread Camera: starting")
    message = ' '
    abstand = '0.00'

    cap = cv2.VideoCapture(0)
    while(True):
        if event.is_set() or not queue.empty():
          message = queue.get()

        # Capture frame-by-frame
        ret, frame = cap.read()

        # width , height define
        width = cap. get(cv2. CAP_PROP_FRAME_WIDTH )
        height = cap. get(cv2. CAP_PROP_FRAME_HEIGHT )

        # Infor Showing
        infor_point = (int(width - 100), 120)

        # information showing in image
        image = cv2.circle(frame,(int(width/2), int(height/2)), 10, (255,255,255), 1)
        font = cv2.FONT_HERSHEY_SIMPLEX
        image = cv2.putText(frame, "Dis :" + abstand, infor_point, font, 0.7,(255,0,0),2,cv2.LINE_AA)

        # Abstand message canculation
        if "rada" in message:
            radaInfo = (message.replace("rada", "")).split("#")
            abstand = radaInfo[1]
            angle = radaInfo[0]


        # Display the resulting frame
        cv2.imshow('frame',image)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()

    logging.info("Thread Camera: finishing")
    queue.put("sensor Stop") # message for stop thread distancesensor




# Main program
#======================================================================
if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    pipeline = queue.Queue(maxsize=10)
    event = threading.Event()

    y = threading.Thread(target=scan_rada, args=(pipeline, event,), daemon=True)
    x = threading.Thread(target=camera, args=(pipeline, event,), daemon=True)

    logging.info("Main    : before running thread")

    y.start()
    x.start()

    # not given any params by calling object --> chanel is default
    Motor = MotorDriver()
    Servo = ServoDriver()
    Servo.runServo(Pos)

    Canon = ServoDriver(7)
    Canon.runServo(CPos)

    Rada = ServoDriver(8)
    Rada.runServo(RPos)

    print ("Use'd' to slow down")
    print ("Use 'u' to speed up")
    print ("use < left, > right, ^ forward, backward")

    # Collect events until released
    with Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()


    logging.info("Main    : wait for the thread to finish")
    y.join()
    x.join()
    logging.info("Main    : all done")

print("stop")
Motor.MotorStop(0)
Motor.MotorStop(1)
