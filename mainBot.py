# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 23:51:15 2020

@author: Dinh-Vien.BUI
"""
import time
from Basi_Bot import*


load_model()
#move_Servo(1100)

question = ""                         

print('Hello')
inputText = input()
#inputText = recognizeSpeech()

while (inputText != "exit"):
    if inputText.find("Alex")>0:
        
        #call function find the face (di chuyen camera trong pham vi phia truoc de tim khuan mat, hoi ban la ai neu chua biet ten, chao ban neu da biet ten)
#        name = scan_face()
#        if (name!='')and(name!='Unknown'):
#            convertText2Audio('hello '+name)
            
        convertText2Audio('hello ')
#        print('Welcome')
        inputText = input()
        # thoi gian de lang nge menh lenh la 60s 
        now = time.time()
        future = now + 60 # time to listen after "Kim" was called
        while time.time() < future:
            # do stuff
            if len(inputText)>0: 
                tags = classify(inputText)     
                print (tags)
                if (len(tags)>0)and(tags[0][1]>0.7): ## nur für den fall es gibt nur eine ergebnis
                    question = inputText
                    print('tags[0][0]: ',tags[0][0])
                    print('question_1: ', question)
                    
#                    print('response: ',response(inputText))
                    convertText2Audio(str(response(inputText)))
                    
                    future = time.time() + 60
                    
                    # goi ham defition_noun neu nhan dc cau hoi ve dinh nghia danh tu
                    if (tags[0][0]=='definition'):
                        (_,_,nouns,_,_)=abkurzenP(inputText)
                        if (len(nouns)==1):
                            inputText = '' # xoa input 
                            definition(nouns[0][0])
                            future = time.time() + 60
#                            continue
                        else:
                            print('not found which noun to define: ', nouns)
                    if (tags[0][0]=='forward')or(tags[0][0]=='backward')or(tags[0][0]=='left')or(tags[0][0]=='right')or(tags[0][0]=='stop'):
                        
#                        move_Fahrzeug(50, tags[0][0], 1)
                        print(tags[0][0])
                        future = time.time() + 60

                    # kiem tra xem co loi gioi thieu ten nao khong?
                    if (tags[0][0]=='introduction'):
                        # tim kiem khuon mat trong mot pham vi nhat dinh
                        print('introduction')
                        # tim va nhan dang khuan mat
                        # neu ket qua tra ve la None thi hoi where are you?
                        # neu ket qua tra ve la Unknow thi hoi who are you
#                        name = scan_face()
#                        if (name!='')and(name!='Unknown'):
                    
#                            convertText2Audio('hello '+name)
                    # tiep tuc lang nghe xem nguoi dung co dong y voi response khong 
                    # neu khong dong y thi dat cau hoi ve de tai nguoi dung muon nhac den
                    # neu dong y thi tiep tuc lang nghe 
                    inputText = input()
#                    inputText = recognizeSpeech()
                    
                    tags = classify(inputText)     
                    print (tags)
                    if (tags[0][0]=='discontentment'):
                        inputText = '' # xoa input
                        createQuestion1(question,[''],1)
                        future = time.time() + 60
                else:
                    # save the first question of user to variable question
                    question = inputText
                    print('question_2:', question)
                    # create a bot question to verify user mind in their question
                    Array_Themas = [tag[0] for tag in tags]
                    inputText = '' # xoa input
                    createQuestion1(question,Array_Themas)
                    future = time.time() + 60

            else:
                inputText = input()
#                inputText = recognizeSpeech()
                
            print("you have said: ",inputText)
            print("future: ",future)
            
        print("out of time!")
        
    else: # he thong se doi cho den khi nguoi dung noi den tu khoa "Kim"
        inputText = input()
#        inputText = recognizeSpeech()
        print('inputText: ',inputText)