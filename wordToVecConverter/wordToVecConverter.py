
# coding: utf-8


import numpy as np
import gensim
import os
import json
import enchant
import pymorphy2

import os

# class to provide saving and loading mechanism for classes inherited from base class
class SaveAndLoadMechanismForInheritedClasses:
    def save(self, destinationFolder):
        if os.path.isdir(destinationFolder) == False:
            os.mkdir(destinationFolder)
        with open(destinationFolder + "/realClassName.txt", "w") as outputFile:
            outputFile.write(self.__class__.__name__)
    @staticmethod
    def load(destinationFolder):
        with open(destinationFolder + "/realClassName.txt", "r") as inputFile:
            childClassName = inputFile.readline()
            childClass = eval(childClassName)
            return childClass.load(destinationFolder)

# interface for word convertion (word -> vector) class
class WordToVecConverter(SaveAndLoadMechanismForInheritedClasses):
    def convert(self, word, defaultResult = None):
        pass
    def getWordVectorSize(self):
        pass
    @staticmethod
    def getDtype():
        pass
    
class WordToVecConverterOneHotEncoder(WordToVecConverter):
    def __init__(self):      
        self.__wordIdentificators = dict()
    def getWordVectorSize(self):
        return 1
    def fit(self, listOfWords, minFrequency=None, maxFrequency=None):
        wordFrequencies = dict()
        for word in listOfWords:
            word = word.lower()
            if word in wordFrequencies:
                wordFrequencies[word] += 1
            else:
                wordFrequencies[word] = 1
            
        wordsToRemove = set()
        
        if minFrequency is not None:
            keys = wordFrequencies.keys()
            for key in keys:
                if wordFrequencies[key] < minFrequency:
                    wordsToRemove.add(key)
                    
        if maxFrequency is not None:
            keys = wordFrequencies.keys()
            for key in keys:
                if wordFrequencies[key] > maxFrequency:
                    wordsToRemove.add(key)
                    
        for key in wordsToRemove:
                del wordFrequencies[key]
                    
        keys = wordFrequencies.keys()
        self.__wordIdentificators = dict()
        maxIndex = 0
        for key in keys:
            self.__wordIdentificators[key] = maxIndex + 1
            maxIndex += 1
                    
    def convert(self, word, defaultResult = None):
        if word in self.__wordIdentificators:
            return self.__wordIdentificators[word]
        else:
            return defaultResult
    def getWordIdentificators(self):
        return self.__wordIdentificators
    def getVocabularyLength(self):
        return len(self.__wordIdentificators)
    def save(self, destinationFolder):
        SaveAndLoadMechanismForInheritedClasses.save(self, destinationFolder)
        wordIdentificatorsFilename = os.path.join(destinationFolder, "wordIdentificators.json")
        with open(wordIdentificatorsFilename, "w") as fp:
            json.dump(self.__wordIdentificators, fp)
    @staticmethod
    def load(destinationFolder):
        obj = WordToVecConverterOneHotEncoder()
        wordIdentificatorsFilename = os.path.join(destinationFolder, "wordIdentificators.json")
        with open(wordIdentificatorsFilename, "r") as fp:
            obj.__wordIdentificators = json.load(fp)
        return obj
    @staticmethod
    def getDtype():
        return np.int32
    __wordIdentificators = None


class WordToVecConverterKeyedVectorsBased(WordToVecConverter):
    def convert(self, word, defaultResult = None):
        try:
            res = self.__model[word]
            return res
        except:
            return defaultResult
    def getWordVectorSize(self):
        return self.__model.vector_size
    def setModel(self, model):
        self.__model = model
    def save(self, destinationFolder):
        SaveAndLoadMechanismForInheritedClasses.save(self, destinationFolder)
        self.__model.save(destinationFolder + "/model.vec")
    @staticmethod
    def load(destinationFolder):
        obj = WordToVecConverterKeyedVectorsBased()
        obj.__model = gensim.models.KeyedVectors.load(destinationFolder + "/model.vec")
        return obj
    @staticmethod
    def getDtype():
        return np.float32
    __model = None

