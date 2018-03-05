
# coding: utf-8


import numpy as np
import gensim
import os
import json
import enchant
import pymorphy2

from .saveAndLoadMechanismForInheritedClasses import SaveAndLoadMechanismForInheritedClasses

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
        self.__vocabularyLength = 0
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
                
        if minFrequency is not None:
            keys = wordFrequencies.keys()
            wordsToRemove = []
            for key in keys:
                if wordFrequencies[key] < minFrequency:
                    wordsToRemove.append(key)
                    #del wordFrequencies[key]
            for key in wordsToRemove:
                del wordFrequencies[key]
                    
        if maxFrequency is not None:
            keys = wordFrequencies.keys()
            for key in keys:
                if wordFrequencies[key] > maxFrequency:
                    del wordFrequencies[key]
                    
        keys = wordFrequencies.keys()
        self.__wordIdentificators = dict()
        self.__vocabularyLength = 0
        for key in keys:
            self.__wordIdentificators[key] = self.__vocabularyLength + 1
            self.__vocabularyLength += 1
                    
    def convert(self, word, defaultResult = None):
        if word in self.__wordToId:
            return self.__wordToId[word]
        else:
            return defaultResult
    def getWordIdentificators(self):
        return self.__wordIdentificators
    def getVocabularyLength(self):
        return len(self.__wordIdentificators)
    def save(self, destinationFile):
        SaveAndLoadMechanismForInheritedClasses.save(destinationFolder)
        with open(destinationFile, "w") as outputFile:
            state = json.dumps([self.__wordIdentificators, self.__vocabularyLength], separators=(',',':'))
            outputFile.write(state)
            outputFile.close()
    @staticmethod
    def load(destinationFolder):
        obj = WordToVecConverterOneHotEncoder()
        with open(destinationFile, "r") as inputFile:
            state = json.load(inputFile)
            obj.__wordIdentificators = state[0]
            obj.__vocabularyLength = state[1]
        return obj
    @staticmethod
    def getDtype():
        return np.int32
    __wordIdentificators = None
    __vocabularyLength = None


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
        SaveAndLoadMechanismForInheritedClasses.save(destinationFolder)
        self.__model.save(destinationFolder + "/model.vec")
    @staticmethod
    def load(destinationFolder):
        obj = WordToVecConverterProximityBased()
        obj.__model = gensim.models.KeyedVectors.load(destinationFolder + "/model.vec")
        return obj
    @staticmethod
    def getDtype():
        return np.float32
    __model = None

