# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 21:11:39 2022

@author: Dinh-Vien.BUI
"""

import RPi.GPIO as GPIO
import time

# import library for drawing rada
import numpy as np
import cv2

# calculate math
import math

# import the library for motor controling
from PCA9685 import PCA9685

#====================================================================================
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(50)

#GPIO Modus (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

#GPIO Pins zuweisen
GPIO_TRIGGER = 15
GPIO_ECHO = 14

#Richtung der GPIO-Pins festlegen (IN / OUT)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)

# Class Servo definition
#=====================================================================================
class ServoDriver():
    # default chanel = 6 --> Note by pinhead of Servor-Board number 6 from power pin
    # chanel 0 - 5 were be used by 2 DC-Motor
    def __init__(self,_channel=6):
        self.channel = _channel


    def runServo(self,_Pos):
        pwm.setServoPulse(self.channel,_Pos)

#=====================================================================================
def distanz():

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

  return distanz

def degree(GPos):
    return(round((GPos - 635)/9.5))

if __name__ == '__main__':

    Canon = ServoDriver(8)
    Canon.runServo(1490)

    r = 480
    h = 480
    w = 960

    # drawing rada ----------------------------------------------------------------------------
    # Create a black image
    img = np.zeros((480,960,3), np.uint8)

    # Drawing circle
    cv2.circle(img,(480,480),480,(255,255,255),5)

    try:
        GPos = 1490
        Step = 9.5
        deg = 30
        Step_deg = 1
        max_dis = 70 # max distanz in cm für rada

        while(1):

            # showing image
            cv2.imshow('image',img)

            # Link Begrenzung mit 30°
            if GPos <= round(30*9.5) + 635:
                Step = 9.5

            # Recht Begrenzung mit 150°
            if GPos >= round(150*9.5) + 635:
                Step = -9.5

            GPos = GPos + Step

            Canon.runServo(GPos)
            time.sleep(0.02)

            abstand = distanz()

            if abstand > 70:
                abstand = 70
            print ("Degree " + str(degree(GPos)) + " Gemessene Entfernung = %.1f cm"  % abstand)

            r_dis = round(r*(abstand/70))

            # drawing line rada
            x_max = round(r + r*(math.cos(math.radians(degree(GPos)))))
            y_max = round(r - r*(math.sin(math.radians(degree(GPos)))))

            x_dis = round(r + r_dis*(math.cos(math.radians(degree(GPos)))))
            y_dis = round(r - r_dis*(math.sin(math.radians(degree(GPos)))))
            img = cv2.line(img,(r,r),(x_dis,y_dis),(0,255,0),2)
            img = cv2.line(img,(x_dis,y_dis),(x_max,y_max),(0,0,255),2)

            if cv2.waitKey(1) & 0xFF == 27:
                break
#        # --------------------------------------------------------------------------------------
        cv2.destroyAllWindows()

    # Beim Abbruch durch STRG+C resetten
    except KeyboardInterrupt:
        print("Messung vom User gestoppt")
#        cv2.destroyAllwindows()
        GPIO.cleanup()
