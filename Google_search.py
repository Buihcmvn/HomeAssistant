# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 08:31:39 2020

@author: Dinh-Vien.BUI

chuong trinh dat cau hoi tren Google ket qua tra ve la mot danh sach cac trang web lien quan 
tu cac trang web thu duoc ta se loc cac cau tra loi dc lap lai nhieu lan nhat va co tinh logic voi
cau hoi dc dat ra
"""

try: 
    from googlesearch import search 
except ImportError:  
    print("No module named 'google' found") 
  
# to search 
query = "Geeksforgeeks"
#query = "was ist wallbox?"
  
for j in search(query, tld="co.in", num=10, stop=10, pause=2): 
    print(j) 