# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 00:07:54 2020

@author: Dinh-Vien.BUI
"""
# using recognize_sphinx for Rasp -->
# 1. sudo apt-get install -qq python python-dev python-pip build-essential swig libpulse-dev
# 2. sudo pip install pocketsphinx

# using recognize_sphinx for Win --> but google recognize more better than that
# 1. conda install swig
# 2. pip install pocketsphinx


import speech_recognition as sr  

# get audio from the microphone                                                                       
r = sr.Recognizer() 
                                                                                 
with sr.Microphone() as source:                                                                       
    print("Speak:")                                                                                   
    audio = r.listen(source) 

    with open('speech.wav', 'wb') as f:
        f.write(audio.get_wav_data())

try:
    audio.get_wav_data()
    
    print("You said " + r.recognize_google(audio))#--> default for english
#    print("Sie haben gesagt: " + r.recognize_google(audio, language="de-DE"))
#    print("You said " + r.recognize_sphinx(audio))#--> default for english, work offline
except sr.UnknownValueError:
    print("Entschuldigen Ich verstehe nicht was Sie gesagt haben.")
except sr.RequestError as e:
    print("Could not request results; {0}".format(e))