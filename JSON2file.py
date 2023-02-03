# -*- coding: utf-8 -*-
"""
Created on Wed Mar 18 22:24:48 2020

@author: Dinh-Vien.BUI

Example 4: Writing JSON to a file
"""


import json

#person_dict = {"name": "Bob",
#"languages": ["English", "Fench"],
#"married": True,
#"age": 32
#}

# mo doc file json duoi dang datype dict (intents)
# open and read file json with dict datatype
# 
with open('TraningData.json',encoding='utf8') as json_data:
    TraningData_Dict = json.load(json_data)


# change the intent of training data (adding more training data to make your bot clever)
for intent in TraningData_Dict['intents']:
#    print(intent["tag"])
    if (intent["tag"] =="greeting"):
        print(intent["patterns"])
        intent["patterns"].append("xin chao")
        print(intent["patterns"])

# convert the new training data to json file   
with open('TraningData.json', 'w',encoding='utf-8') as f:
    json.dump(TraningData_Dict, f, ensure_ascii=False, indent=4)
  



'''
In the above program, we have opened a file named person.txt in writing mode using 'w'. 
If the file doesn't already exist, it will be created. Then, json.dump() transforms person_dict 
to a JSON string which will be saved in the person.txt file.

When you run the program, the person.txt file will be created. The file has following text inside it.
{"name": "Bob", "languages": ["English", "Fench"], "married": true, "age": 32}
'''



#
#'''
################################################################################
#Python Convert to JSON string
#You can convert a dictionary to JSON string using json.dumps() method.
#'''
#person_dict = {'name': 'Bob',
#'age': 12,
#'children': None
#}
#person_json = json.dumps(person_dict)
#
## Output: {"name": "Bob", "age": 12, "children": null}
#print(person_json)