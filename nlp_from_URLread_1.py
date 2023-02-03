# -*- coding: utf-8 -*-
"""
Created on Fri Jun  5 22:48:46 2020

@author: Dinh-Vien.BUI
"""
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from newspaper import Article
#url = 'https://vnexpress.net/12-000-nguoi-do-ve-cua-lo-4092705.html'
DEF_QUELL = 'https://en.wikipedia.org/wiki/'
##url = 'https://dictionary.cambridge.org/de/worterbuch/englisch-deutsch/car'
#
#Noun = 'tomorow' # --> this str duoc nhap vao tu nguoi dung 
#Noun = Noun.capitalize()
#
#url = DEF_QUELL + Noun
#article = Article(url)
#article.download()
#article.parse()
## cut Text data from website: 
#rawText = article.text
##print(rawText)
## vi du:  tim dinh nghia cua mot danh tu nao do tren internet (wiki)
##   - them danh tu do vao cuoi duong dan
##   - loc cac cau co tu bat dau la danh tu can tim
#lines = rawText.splitlines()
#paragraphts = [line for line in lines if len(line)!=0]
#definitions = [paragrapht for paragrapht in paragraphts if (Noun+' is' in paragrapht)or((Noun+'s'+' are')in paragrapht)and(paragrapht.index(Noun)<2)]
#if len(definitions)==0:
#    # truong hop khong the tim thay dinh nghia cua danh tu thi chuyen chu cai dau tien thanh dang viet thuong 
#    Noun = Noun.lower()
#    definitions = [paragrapht for paragrapht in paragraphts if (Noun+' is' in paragrapht)or((Noun+'s'+' are')in paragrapht)and(paragrapht.index(Noun)<2)]
#
#if len(definitions)==0:
#    Noun = Noun.upper()
#    definitions = [paragrapht for paragrapht in paragraphts if (Noun+' is' in paragrapht)or((Noun+'s'+' are')in paragrapht)and(paragrapht.index(Noun)<2)]
#
#def_noun = definitions[0]
#first_sent = sent_tokenize(def_noun)[0]

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
          first_sent = str('can not find the definition of '+Noun)  
#    convertText2Audio(first_sent)
    print(first_sent)

definition('tomorow')