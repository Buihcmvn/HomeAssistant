# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 17:48:06 2020

@author: Dinh-Vien.BUI
muc dich la doc cac thong tin dang van ban trong website 

- kho khan o buoc loc thong tin trong website --> tach loc thong tin dang text tu HTML-Code  
    + results =soup.find_all("span",{"class":"short-desc"}) ### o moi trang web khac nhau thi 
    ta phai dua vao cac thong so khac nhau de loc cac thong tin can thiet
"""
#from selenium import webdriver
#from bs4 import BeautifulSoup
#import pandas as pd

import requests 
from bs4 import BeautifulSoup 
  
def news(): 
    # the target we want to open     
    url='https://www.nytimes.com/interactive/2017/06/23/opinion/trumps-lies.html'
#    url='https://www.parent24.com/Child_7-12/Development/health_safety/these-9-safety-tips-will-keep-your-child-safe-in-dangerous-situations-20180531'
      
    #open with GET method 
    resp=requests.get(url) 
#    print(resp.text[0:500])
    
    # we need a parser,Python built-in HTML parser is enough . 
    soup=BeautifulSoup(resp.text,'html.parser')
#    print(soup)
    
    # results is the list which contains all the text i.e news  
    results =soup.find_all("span",{"class":"short-desc"})
#    print(len(results))
#    print(results[0:3])
    first_result = results[0]
#    print(first_result)
#    print(first_result.contents[1])
    
    print(first_result.find('a').text)
    
#    date = first_result.find('strong')
#    print(date.text)
    
    
      
#    #http_respone 200 means OK status 
#    if resp.status_code==200: 
#        print("Successfully opened the web page") 
#        print("The news are as follow :-\n") 
#      
#        # we need a parser,Python built-in HTML parser is enough . 
#        soup=BeautifulSoup(resp.text,'html.parser') 
#        print(soup)
#  
#        # l is the list which contains all the text i.e news  
#        l=soup.find_all("ul",{"class":"News"}) 
##        l=soup.find(attrs={'new'}) 
##        print(l)
#        #now we want to print only the text part of the anchor. 
#        #find all the elements of a, i.e anchor 
##        for i in l.findall("a"): 
##            print(i.text) 
#    else: 
#        print("Error") 
          
news()