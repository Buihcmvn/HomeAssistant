# -*- coding: utf-8 -*-
"""
Created on Sun May 17 23:32:42 2020

@author: https://www.pyimagesearch.com/2018/06/25/raspberry-pi-face-recognition/
"""

# import the necessary packages
from DC_Motor.PCA9685 import PCA9685

from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2

cascade = "/home/pi/opencv-3.3.0/data/haarcascades_cuda/haarcascade_frontalface_default.xml"
encodings = "/home/pi/Desktop/CODE/Face_reg/encodings.pickle" 

Dir = ['forward', 'backward',]
pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(50)

speed = 30
Pos = 1100  
Step = 5


class ServoDriver():
    def __init__(self,_channel=0):
        self.channel = _channel
  

    def runServo(self,_Pos):
        pwm.setServoPulse(self.channel,_Pos)
        
        
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

# chuong trinh vua di chuyen camera vua nhan dien khuan mat
# camera di chuyen len xuong qua trai qua phai
# --> su dung thread 
def scan_face():
    data = pickle.loads(open(encodings, "rb").read())
    detector = cv2.CascadeClassifier(cascade)
    # initialize the video stream and allow the camera sensor to warm up
    vs = VideoStream(src=0).start() # --> use a USB camera
    # vs = VideoStream(usePiCamera=True).start() # --> to use a PiCamera 
    time.sleep(2.0)
    # start the FPS counter
    fps = FPS().start()
    
    # capturing frames from the camera and recognizing faces:
    # loop over frames from the video file stream
    while True:    
        # grab the frame from the threaded video stream and resize it
        # to 500px (to speedup processing)
        frame = vs.read()
        frame = imutils.resize(frame, width=500)
        
        # convert the input frame from (1) BGR to grayscale (for face
        # detection) and (2) from BGR to RGB (for face recognition)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # detect faces in the grayscale frame
        rects = detector.detectMultiScale(gray, scaleFactor=1.1, 
            minNeighbors=5, minSize=(30, 30))
        # OpenCV returns bounding box coordinates in (x, y, w, h) order
        # but we need them in (top, right, bottom, left) order, so we
        # need to do a bit of reordering
        boxes = [(y, x + w, y + h, x) for (x, y, w, h) in rects]
        # compute the facial embeddings for each face bounding box
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []
        
        # loop over the face encodings and check for matches:
        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(data["encodings"],
                encoding)
            name = "Unknown"
            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}
                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1
                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
                
                # neu phat hien ra khuan mat thi lap tuc nghung di chuyen camera va nhan dien khuon mat mot lan nua 
                # neu ket qua giong nhu lan mot thi tra ve ket qua va thoat ra 
                if name!="":
                    return name










