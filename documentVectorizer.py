
# coding: utf-8

from polyglot.detect import Detector

from .offlineWordTranslator.offlineWordTranslator import OfflineWordTranslator

from .textPreprocessorForConcreteLanguage.eng.textPreprocessorEng import TextPreprocessorEng
from .textPreprocessorForConcreteLanguage.rus.textPreprocessorRus import TextPreprocessorRus

from .onlineMultilanguageTranslator.onlineMultilanguageTranslator import OnlineMultilanguageTranslator

import json

import os

class DocumentVectorizer:
    def __init__(self):
        langSys = {"preprocessor" : TextPreprocessorEng()}
        self.__languageSystems = {"English" : langSys}
        
        pathToDictionary = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "offlineWordTranslator", 
                                        "dictionaries", 
                                        "custom", 
                                        "rusToEngExtendedDict.json")
        offlineWordTranslator = None
        with open(pathToDictionary, "r") as fp:
            rusToEngDictionary = json.load(fp)
            offlineWordTranslator = OfflineWordTranslator(rusToEngDictionary)
        langSys = {"preprocessor" : TextPreprocessorRus(), "offlineWordTranslator" : offlineWordTranslator}
        self.__languageSystems["Russian"] = langSys
        
        self.__onlineMultilanguageTranslator = OnlineMultilanguageTranslator()
    # lang: "Russian", "English"
    def vectorizeDocument(self, doc, lang = None, useOfflineTranslation = True, useOnlineTranslation = False):
        translatedWords = None
        
        if useOnlineTranslation == True:
            translatedWords = self._onlineWordSeparationAndTranslation(doc, maxNumberOfAttempts = 4)
            
        if translatedWords == None:
            if useOfflineTranslation == True:
                translatedWords = self._offlineWordSeparationAndTranslation(doc, lang)
            elif useOnlineTranslation == True and len(translatedWords) == 0:
                translatedWords = self._onlineWordSeparationAndTranslation(doc, maxNumberOfAttempts=None)
                
        if translatedWords == None:
            return None
            
        res = []
        for word in translatedWords:
            vector = self.__wordToConverter.convert(word)
            if vector is not None:
                res.append(vector)
        return res
        
    # setters and getters
    
    def setWordToVecConverter(self, converter):
        self.__wordToConverter = converter
    def getWordToVecConverter(self):
        return self.__wordToConverter
    
    def _offlineWordSeparationAndTranslation(self, doc, lang):
        # if lang == None detect language of doc automatically
        if lang is None:
            try:
                d = Detector(doc)
                lang = d.language.name
            except:
                lang = "English"
        
        # if language is supported then preprocess, translate and vectorize words
        if lang in self.__languageSystems:
            wordList = self.__languageSystems[lang]["preprocessor"].prepareDocument(doc)
            # translate words if they are not in English
            if lang != "English":
                translatedWords = []
                i = 0
                while i < len(wordList):
                    translation = self.__languageSystems[lang]["offlineWordTranslator"].translate(wordList[i])
                    if translation is not None:
                        translatedWords += self.__languageSystems["English"]["preprocessor"].prepareDocument(translation, normalize = False, fixMisspellings = False, removeUnsignificantSentenceParts = True, removeNamedEntities = False)
                    i += 1
                return translatedWords
            else:
                return wordList
        else:
            raise ValueError("Unsupported language of document")
            
    def _onlineWordSeparationAndTranslation(self, doc, maxNumberOfAttempts):
        res = None
        translation = self.__onlineMultilanguageTranslator.translate(doc, dest="en", maxNumberOfAttempts=maxNumberOfAttempts)
        # If online translation succeed
        if translation != None:
            res = self.__languageSystems["English"]["preprocessor"].prepareDocument(translation, normalize = False, fixMisspellings = False, removeUnsignificantSentenceParts = True, removeNamedEntities = False)
        return res
        
    __wordToConverter = None
    __languageSystems = None
    __onlineMultilanguageTranslator = None

