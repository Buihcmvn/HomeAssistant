# -*- coding: utf-8 -*-
"""
Created on Fri Mar 20 10:19:44 2020

@author: Dinh-Vien.BUI
"""

# Import the required module for text  
# to speech conversion 
from gtts import gTTS 
  
# This module is imported so that we can  
# play the converted audio 
import os 
import mpg123 #download mpg123.exe and paste to project folder
  
# The text that you want to convert to audio 
mytext = 'Hallo, danke für Ihre Besuch'
  
# Language in which you want to convert 
language = 'de'
  
# Passing the text and language to the engine,  
# here we have marked slow=False. Which tells  
# the module that the converted audio should  
# have a high speed 
myobj = gTTS(text=mytext, lang=language, slow=False) 
  
# Saving the converted audio in a mp3 file named 
# welcome  
#myobj.save("bot.mp3") 
# Playing the converted file 
#os.system('mpg123 bot.mp3')
os.system('P:\Desktop\Arbeitplatz\Phase_1_Jan_Maerz\BasiBot\mpg123.exe P:\Desktop\Arbeitplatz\Phase_1_Jan_Maerz\BasiBot/bot.mp3')
#os.system('cmd /k "mpg123.exe bot.mp3"')
#os.remove('bot.mp3')