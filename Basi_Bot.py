# -*- coding: utf-8 -*-
"""
Created on Sun May 31 07:28:05 2020

@author: Dinh-Vien.BUI

- Listen_NLP active in 1 minute wenn das Wort "Alex" angerufen wird
    (phan biet cau lenh dang chatbot thong thuong hay cau lenh dieu khien hanh dong cua robot)
    + Befehlen verstehen (vorfahren, rückfahren, recht-link abbiegen, umdrehen, shauen nach oben, unten Stop)
    + Name der personen finden (erstellen Ordner dafür)
    
* Fall: 
    Face recognition command: 
        ich würde gern meine Kollegen, ... vorstellen. das ist Kimmy
        hallo, mein Name ist Kimmy. ich bin K, ich heiß K
        

start: 
    hört "Alex" --> activate 1 minute NLP_task
        chatbot --> warte für classify
            Bot --> entsprechende response
            Befehle --> do sthing
    hört das wort nicht --> wiederholen von start 
            
"""
import nltk #(nltk.download('punkt'))
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from newspaper import Article
from nltk.corpus import stopwords#(nltk.download('stopwords'))
stop_words = set(stopwords.words('english'))

from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

#from DC_Motor.PCA9685 import PCA9685
#from imutils.video import VideoStream
#from imutils.video import FPS
#import face_recognition
#import imutils
#import pickle
#import cv2

import numpy as np
import tflearn
import tensorflow as tf
import random
import json
import time

cascade = "/home/pi/opencv-3.3.0/data/haarcascades_cuda/haarcascade_frontalface_default.xml"
encodings = "/home/pi/Desktop/CODE/Face_reg/encodings.pickle" 

DEF_QUELL = 'https://en.wikipedia.org/wiki/'
JSON_TRAING_DATA  = 'BasiBot.json'

#Dir = ['forward', 'backward',]
#pwm = PCA9685(0x40, debug=False)
#pwm.setPWMFreq(50)
#
#speed = 50 

words = []
classes = []
documents = []

#
##################################################################################################
#class ServoDriver():
#    def __init__(self,_channel=0):
#        self.channel = _channel
#  
#
#    def runServo(self,_Pos):
#        pwm.setServoPulse(self.channel,_Pos)
#        
#        
##################################################################################################        
#class MotorDriver():
#    def __init__(self):
#        self.PWMA = 0
#        self.AIN1 = 1
#        self.AIN2 = 2
#        self.PWMB = 5
#        self.BIN1 = 3
#        self.BIN2 = 4
#
#    def MotorRun(self, motor, index, speed):
#        if speed > 100:
#            return
#        if(motor == 0):
#            pwm.setDutycycle(self.PWMA, speed)
#            if(index == Dir[1]):
#                pwm.setLevel(self.AIN1, 0)
#                pwm.setLevel(self.AIN2, 1)
#            else:
#                pwm.setLevel(self.AIN1, 1)
#                pwm.setLevel(self.AIN2, 0)
#        else:
#            pwm.setDutycycle(self.PWMB, speed)
#            if(index == Dir[1]):
#                pwm.setLevel(self.BIN1, 0)
#                pwm.setLevel(self.BIN2, 1)
#            else:
#                pwm.setLevel(self.BIN1, 1)
#                pwm.setLevel(self.BIN2, 0)
#
#    def MotorStop(self, motor):
#        if (motor == 0):
#            pwm.setDutycycle(self.PWMA, 0)
#        else:
#            pwm.setDutycycle(self.PWMB, 0)
#
#
##################################################################################################
#def move_Servo(Pos):
#    Servo = ServoDriver()
#    
#    Servo.runServo(Pos)
#
##################################################################################################
#def move_Fahrzeug(Speed, Direction, MoveTime):
#    Motor = MotorDriver()
#    
#    if Direction=='right':
#        Motor.MotorRun(0, 'forward', Speed)
#        Motor.MotorRun(1, 'backward', Speed)
#        time.sleep(MoveTime)
#        # dung lai 
#        Motor.MotorStop(0)
#        Motor.MotorStop(1)
#    
#    if Direction=='left':
#        Motor.MotorRun(0, 'backward', Speed)
#        Motor.MotorRun(1, 'forward', Speed)
#        time.sleep(MoveTime)
#        # dung lai 
#        Motor.MotorStop(0)
#        Motor.MotorStop(1)
#        
#    if Direction=='straight':
#        Motor.MotorRun(0, 'forward', Speed)
#        Motor.MotorRun(1, 'forward', Speed)
#        time.sleep(MoveTime)
#        # dung lai 
#        Motor.MotorStop(0)
#        Motor.MotorStop(1)
#        
#    if Direction=='back':
#        Motor.MotorRun(0, 'backward', Speed)
#        Motor.MotorRun(1, 'backward', Speed)
#        time.sleep(MoveTime)
#        # dung lai 
#        Motor.MotorStop(0)
#        Motor.MotorStop(1)
#
#    if Direction=='stop':
#        # dung lai 
#        Motor.MotorStop(0)
#        Motor.MotorStop(1)
#                
#
##################################################################################################
#def move_Camera(Direction):
#    Servo = ServoDriver()
#    
#    if Direction=='up':
#        Servo.runServo(1500)
#         
#    if Direction=='down':
#        Servo.runServo(1100)
#    
#    if (Direction=='left')or(Direction=='right'):
#        move_Fahrzeug(50, Direction, 1)

#################################################################################################
def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [stemmer.stem(word.lower()) for word in sentence_words]
    return sentence_words


#################################################################################################  
# bag of words
def bow(sentence, words, show_details=False):
    sentence_words = clean_up_sentence(sentence)
    # bag of words
    bag = [0]*len(words)  
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s: 
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)

    return(np.array(bag))
    
    
################################################################################################# 
# data structure to hold user context
context = {}
ERROR_THRESHOLD = 0.25
def classify(sentence):
    results = model.predict([bow(sentence, words)])[0]
    results = [[i,r] for i,r in enumerate(results) if r>ERROR_THRESHOLD]
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append((classes[r[0]], r[1]))
    return return_list

def response(sentence, userID='1', show_details=False):
    results = classify(sentence)
    if results:
        while results:
            for i in intents['intents']:
                if i['tag'] == results[0][0]:
                    if 'context_set' in i:
                        if show_details: print ('context:', i['context_set'])
                        context[userID] = i['context_set']
                    if not 'context_filter' in i or \
                        (userID in context and 'context_filter' in i and i['context_filter'] == context[userID]):
                        if show_details: print ('tag:', i['tag'])
                        return random.choice(i['responses'])
#                        return print(random.choice(i['responses']))

            results.pop(0)
            
            
#################################################################################################
def chunkTreeNLTK(tag_tokenSentence):
    #Using a Tagger
    import nltk 
    
    #In this case, we will define a simple grammar with a single regular expression rule
    grammar = r"""
                NP: {<DT>*<IN>*<DT>*<RB>*<JJ>*<NN|NNP|NNS>+<IN>*<DT>*<RB>*<JJ>*<NN|NNP|NNS>*}
                VP: {<VERB|VBN|VBP|VBD|VBG|VB>*} 
              """    
    '''
    This rule says that an NP chunk should be formed whenever the
    chunker finds an optional (ADP), determiner (DT) followed by any number of adjectives (JJ)
    and then any number of noun (NN).
    '''
    
    #Using this grammar, we create a chunk parser
    cp = nltk.RegexpParser(grammar)
    
    #test it on our example sentence
    tree = cp.parse(tag_tokenSentence)
    result = tree.subtrees()
#    tree.draw()
    return result


#################################################################################################  
def abkurzenP(Sentence):
    VTokens = []
    NTokens = []
    NETokens = []
    abtext = ''
    foundVerb = False 
    i= 0
    
    tokenSentence = nltk.word_tokenize(Sentence)
    tag_tokenSentence = nltk.pos_tag(tokenSentence)
    
    print(tag_tokenSentence)## <----------------------------------------------------------------
    
    subtrees = chunkTreeNLTK(tag_tokenSentence)
    namedEnt = nltk.ne_chunk(tag_tokenSentence, binary=True)
    result = namedEnt.subtrees()
    
    for subtree in result:
        if subtree.label() == 'NE':
            print ('NE: ',subtree.leaves())  
            NP_Root = subtree.leaves()[len(subtree.leaves())-1]
#            print ('the last word of NP subtree: ',NP_Root[0])
            NETokens.append(NP_Root)
            abtext = abtext+NP_Root[0]+' '
            
    for subtree in subtrees:
        if subtree.label() == 'NP':
            print ('NP: ',subtree.leaves())  
            NP_Root = subtree.leaves()[len(subtree.leaves())-1]
#            print ('the last word of NP subtree: ',NP_Root[0])
            NTokens.append(NP_Root)
            abtext = abtext+NP_Root[0]+' '
        if subtree.label() == 'VP':
            foundVerb = True
            print ('VP: ',subtree.leaves()) 
#            print ('len(subtree.leaves())-1: ',len(subtree.leaves())-1)
            VP_Root = subtree.leaves()[len(subtree.leaves())-1]
#            print ('the last word of NP subtree: ',VP_Root[0])
            VTokens.append(VP_Root[0])
            abtext = abtext+VP_Root[0]+' '
        i+=1
    return (foundVerb,VTokens,NTokens,NETokens,abtext)


#abkurzenP('that is about the weather')


# this function change add some more text to json training data 
#################################################################################################
def changeTrainingData(tag,pattern,respons=""):
    with open(JSON_TRAING_DATA,encoding='utf8') as json_data:
        TraningData_Dict = json.load(json_data)
    # change the intent of training data (adding more training data to make your bot clever)
    for intent in TraningData_Dict['intents']:
        if (intent["tag"] ==tag):
            intent["patterns"].append(pattern)
#            intent["responses"].append(respons)
    
    # convert the new training data to json file   
    with open(JSON_TRAING_DATA, 'w',encoding='utf-8') as f:
        json.dump(TraningData_Dict, f, ensure_ascii=False, indent=4)    

# For the current working directory:
#import pathlib
#print(pathlib.Path().absolute())
        
#################################################################################################        
# this update function should run in background *************
def updateModel():
    #delete the old files and folder before create new files (this step is just for safe because by creating new model sometime be brokendown during overwrite process)
    import os
    import shutil
    # check if folder exists
    if os.path.exists("tflearn_logs"):
         # remove if exists
         shutil.rmtree("tflearn_logs")
    else:
         print("Pfad not found: 'tflearn_logs'") 
         
    myfiles=["checkpoint","model.tflearn.data-00000-of-00001","model.tflearn.index","model.tflearn.meta","training_data"]
    
    for i in myfiles:
        ## If file exists, delete it ##
        if os.path.isfile(i):
            os.remove(i)
        else:    ## Show an error ##
            print("Error: %s file not found" % i)

    # run createTrainingModel.py to create new model
    os.system('python createTrainingModel.py')


#################################################################################################
#this function convert text to audio
def convertText2Audio(inputText,language='en'):
    # Import the required module for text  
    # to speech conversion 
    from gtts import gTTS  
    import os 
    import mpg123 #download mpg123.exe and paste to project folder
      
    # Passing the text and language to the engine,  
    # here we have marked slow=False. Which tells  
    # the module that the converted audio should  
    # have a high speed 
    myobj = gTTS(text=inputText, lang=language, slow=False) 
      
    # Saving the converted audio in a mp3 file named 
    # welcome  
    myobj.save("bot.mp3") 
    # Playing the converted file 
    #os.system('mpg123 bot.mp3')
    os.system('P:\Desktop\Arbeitplatz\Phase_1_Jan_Maerz\BasiBot\mpg123.exe P:\Desktop\Arbeitplatz\Phase_1_Jan_Maerz\BasiBot/bot.mp3')
    # delete the mp3 file to prepare for next time 
    os.remove('bot.mp3')


#################################################################################################
def recognizeSpeech():
    import speech_recognition as sr  

    # get audio from the microphone                                                                       
    r = sr.Recognizer() 
                                                                                     
    with sr.Microphone() as source:                                                                       
        print("Speak:")                                                                                   
        audio = r.listen(source) 
    
    try:
    #    print("You said " + r.recognize_google(audio))#--> default for english
#        print("Sie haben gesagt: " + r.recognize_google(audio, language="de-DE"))
        return r.recognize_google(audio, language="en-EN")
    except sr.UnknownValueError:
#        print("Entschuldigen Ich verstehe nicht was Sie gesagt haben.")
#        return ("sorry i am not understand what did you say.")
        return("")
    except sr.RequestError as e:
#        print("Could not request results; {0}".format(e))
        return ("Could not request results; {0}".format(e))


#################################################################################################
def respone_tag(tag):
    import json
    with open('BasiBot.json',encoding='utf8') as json_data:
        TraningData_Dict = json.load(json_data)
    for intent in TraningData_Dict['intents']:
        if (intent["tag"] ==tag):
            return(random.choice(intent["responses"]))
          
            
#################################################################################################
def create_theme(Noun):
    #   tao moi file trainingData.json moi de luu cac thema moi
    #   loc file trainingData.json
    #       giu lai nhung cau noi duoc lap lai nhieu lan 
    #       xoa nhung cau noi chi xuat hien mot lan
    
    strText = Noun+" is a new theme for me."
    
#    convertText2Audio(strText)
    print(strText)


##################################################################################################
#def detect_face_infront():
#    import Face_reg.FaceRecognition as fr
#    
#    name = fr.scan_face()
#    # neu name == Unknow --> hoi ten who are you?
#    # neu name != Unknow --> nice to meet you 'name'
#    # neu name =='' --> hoi where are you. sorry i dont see you. 
#
##################################################################################################           
# this function look for the definition of parameter Noun on website en.wikipedia.org 
# and speak out the first sentence of that
def definition(Noun):
    Noun = Noun.capitalize()

    url = DEF_QUELL + Noun
    
    try:
        article = Article(url)
        article.download()
        article.parse()
        # cut Text data from website: 
        rawText = article.text
        #print(rawText)
        # vi du:  tim dinh nghia cua mot danh tu nao do tren internet (wiki)
        #   - them danh tu do vao cuoi duong dan
        #   - loc cac cau co tu bat dau la danh tu can tim
        lines = rawText.splitlines()
        paragraphts = [line for line in lines if len(line)!=0]
        definitions = [paragrapht for paragrapht in paragraphts if (Noun+' is' in paragrapht)or((Noun+'s'+' are')in paragrapht)and(paragrapht.index(Noun)<2)]
        if len(definitions)==0:
            # truong hop khong the tim thay dinh nghia cua danh tu thi chuyen chu cai dau tien thanh dang viet thuong 
            Noun = Noun.lower()
            definitions = [paragrapht for paragrapht in paragraphts if (Noun+' is' in paragrapht)or((Noun+'s'+' are')in paragrapht)and(paragrapht.index(Noun)<2)]
        
        if len(definitions)==0:
            Noun = Noun.upper()
            definitions = [paragrapht for paragrapht in paragraphts if (Noun+' is' in paragrapht)or((Noun+'s'+' are')in paragrapht)and(paragrapht.index(Noun)<2)]
    
        def_noun = definitions[0]
        first_sent = sent_tokenize(def_noun)[0]
    except:
          first_sent = str('can not find the definition of the word '+Noun)
          
#    convertText2Audio(first_sent)
    print(first_sent)


#definition('gun')
#################################################################################################
# tao ra cau hoi ve nhieu de tai va loc cac de tai trong cau tra loi cua nguoi dung
def createQuestion1(Question,Array_themas, discontentment=0):
    import json
    with open('BasiBot.json',encoding='utf8') as json_data:
        TraningData_Dict = json.load(json_data)
    tags = [intent["tag"] for intent in TraningData_Dict['intents']]
    
    
    disc_theme = ['Sorry for misunderstanding, but what is your theme?']
    chose_theme = ["sorry I'm not really understand. what do you talk about?", "I'm sorry, Could you tell me which theme do you talk about?",
                   "Sorry, I'm afraid I don't follow you. what is your theme?", "Could you say it again? which theme do you talk about?", 
                   "I didn't hear you. in which theme do you talk about?"]
    repeat_question = ["Sorry, I'm afraid I don't follow you.","Excuse me, could you repeat it?", 
                       "I'm sorry, I don't understand. Could you say it again?", "I'm sorry, I didn't catch that. Would you mind speaking more slowly?",
                       "I'm confused. Could you tell me again?", "I'm sorry, I didn't understand.", 
                       "I didn't hear you."]
    repeat_commands = ["could you tell me your command in difference way?"]
    
    
    repeat_time = 0
    
    if discontentment ==1:
        
#        convertText2Audio(random.choice(disc_theme))
        print(random.choice(disc_theme))
        
    else:
        strThemas = '   or about  '.join(Array_themas)
        
#        convertText2Audio(random.choice(chose_theme) + '    about ' + strThemas)
        print(random.choice(chose_theme) + '    about ' + strThemas)
        
    # neu cau tra loi la ja hoac tuong tu thi luu cau hoi vao phan patterns cua tag[firstClassify[0][0]]
    # lam sao de xac dinh cau tra loi la dong y hay khong --> tim tu "ja" hoac (dong nghia)
    while (repeat_time < 2):
        repeat_time +=1
        inputText = input()
#        inputText = recognizeSpeech()
        
        # neu ham speechrecognition() nhan biet sai thi co the dung tag(nothing) de ngung viec hoi ve de tai gi.
        tag = classify(inputText)     
        print (tag)
        if (tag[0][0]=='nothing')and(tag[0][1]>0.7):
            break
        # neu cau tra loi cua nguoi dung co chua mot danh tu nao do thi thuc hien update training data
        print("inputText: ", inputText)
        (_,_,nouns,_,_)=abkurzenP(inputText)
        print("nouns: ", nouns)
        # neu co key_word hoac nouns --> 
        if (len(nouns)>0 ):
            print('nouns: ',nouns)
            # neu khong co trong Array_Themas thi tim trong intent['tags']
            for noun in nouns:
                print('noun[0]: ',noun[0])
                if noun[0] in tags:
                    print("found noun in tags: ", noun[0])
                    # neu co thi goi ham respone_tag(tag) --> viet ham nay
                    
#                    convertText2Audio(respone_tag(noun[0]))
                    print(respone_tag(noun[0]))
                    
                    # them cau hoi vao Training_Data (changeTrainingData(noun[0],Question))
                    changeTrainingData(noun[0],Question)
                    # --> update dataset (updateModel())
                    updateModel()
                    load_model()
                    return # neu co cau tra loi thi khong can tao thema moi
                
                else:
                    continue # --> duyet het cac danh tu tim duoc trong cau tra loi
            # neu khong co trong intent['tags'] --> return False ('tra google, thong tin can dc cap nhat')
            # co the noi them voi nguoi dung day la de tai moi
            # goi mo chuong trinh huan luyen de tai moi -->
            print("nouns are not in tags: ", noun[0])
            create_theme(noun[0])
            return
        # neu khong tim thay key_word hoac noun nao thi hoi lai cau hoi tren
        
#        convertText2Audio(random.choice(repeat_question))
        print(random.choice(repeat_question))
        
        # ket thuc ham va quay lai chatbot
        
#    convertText2Audio(random.choice(repeat_commands))
    print(random.choice(repeat_commands))


#################################################################################################
def scan_face():
    global encodings, cascade
    router = ('up','down','right','up','down','left','up','down','left','up','down','right')
    move_router = (i for i in router)
    
    data = pickle.loads(open(encodings, "rb").read())
    detector = cv2.CascadeClassifier(cascade)
    # initialize the video stream and allow the camera sensor to warm up
    vs = VideoStream(src=0).start() # --> use a USB camera
    # vs = VideoStream(usePiCamera=True).start() # --> to use a PiCamera 
    time.sleep(2.0)
    # start the FPS counter
    fps = FPS().start()
    
    
    # thoi gian de lang nge menh lenh la 60s 
    now = time.time()
    future = now + 100 # time to listen after "Kim" was called
    # capturing frames from the camera and recognizing faces:
    # loop over frames from the video file stream
    while time.time() < future:
        try:
            # di chuyen camera
            move_Camera(next(move_router))
        except:
            pass
        
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
 
#============================================================================================
# restore our data structures
def load_model():
    import pickle
    global words, classes, intents, model
    
    data = pickle.load( open( "training_data", "rb" ) )
    words = data['words']
    classes = data['classes']
    train_x = data['train_x']
    train_y = data['train_y']
    
    # import intents file
    with open(JSON_TRAING_DATA,encoding='utf8') as json_data:
        intents = json.load(json_data) #### --> need to change the font of json file to german 
        
    
    tf.reset_default_graph() 
    #tf.compat.v1.get_default_graph()
    # Build neural network
    net = tflearn.input_data(shape=[None, len(train_x[0])])
    net = tflearn.fully_connected(net, 8)
    net = tflearn.fully_connected(net, 8)
    net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
    net = tflearn.regression(net, optimizer='adam', loss='categorical_crossentropy')
    
    # Define model and setup tensorboard
    model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
    
    model.load('./model.tflearn')
#============================================================================================




    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

