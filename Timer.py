# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 23:51:15 2020

@author: Dinh-Vien.BUI
"""
import time
from Basi_Bot import recognizeSpeech

# listen --> all the time until found the text " Alex "
inputText = input()
#inputText = recognizeSpeech()
while (inputText != "exit"):
    if inputText.find("Kim")>0:
        now = time.time()
        future = now + 60 # time to listen after "Kim" was called
        while time.time() < future:
            # do stuff
            inputText = input()
#            inputText = recognizeSpeech()
            if len(inputText)>0: 
                print("you have said: ",inputText)
                future = time.time() + 60
            print("future: ",future)
            pass
        print("out of time!")
    inputText = input()
#    inputText = recognizeSpeech()
    print(inputText)

# define the function in local repository
def show_text_local(text2show):
  print(text2show)

# define the function in remote repository
def read_text_remote(text2read):
    print('read the text' + text2read)
