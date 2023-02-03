from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy as np
import tflearn
import tensorflow as tf
import random
import json
import nltk
from nltk.corpus import stopwords#(nltk.download('stopwords'))
stop_words = set(stopwords.words('english'))


words = []
classes = []
documents = []

with open('BasiBot.json',encoding='utf8') as json_data:
    intents = json.load(json_data)

# --> convert intents to 'utf-8'


for intent in intents['intents']:
    for pattern in intent['patterns']:

        w = nltk.word_tokenize(pattern)
        words.extend(w)
        documents.append((w, intent['tag']))
        if intent['tag'] not in classes:
            classes.append(intent['tag'])

words = [stemmer.stem(w.lower()) for w in words if w not in stop_words]
words = sorted(list(set(words)))

classes = sorted(list(set(classes)))

# create our training data
training = []
output = []
output_empty = [0] * len(classes)

# training set, bag of words for each sentence
for doc in documents:
    bag = []
    pattern_words = doc[0]
    pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]

    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)

    # output is a '0' for each tag and '1' for current tag
    output_row = list(output_empty)
    output_row[classes.index(doc[1])] = 1

    training.append([bag, output_row])
random.shuffle(training)
training = np.array(training)

# create train and test lists
train_x = list(training[:,0])
train_y = list(training[:,1])


tf.reset_default_graph()
# Build neural network
net = tflearn.input_data(shape=[None, len(train_x[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(train_y[0]), activation='softmax')
net = tflearn.regression(net, optimizer='adam', loss='categorical_crossentropy')

# Define model and setup tensorboard
model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
# Start training
model.fit(train_x, train_y, n_epoch=1000, batch_size=8, show_metric=True)
model.save('model.tflearn')

import pickle
pickle.dump( {'words':words, 'classes':classes, 'train_x':train_x, 'train_y':train_y}, open( "training_data", "wb" ) )

##=====================================================================================================================>>
## if the under code doesnt work --> try the code over again to create new model ()
## bevor to do that you have (should) delete all files from the folder of directory containst this python file (.py) 
## "C:\Users\Dinh-Vien.BUI\Desktop\Phase_1_Jan_Maerz\ChatBot"
##=====================================================================================================================>>