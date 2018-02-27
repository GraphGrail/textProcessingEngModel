
# coding: utf-8

from polyglot.detect import Detector

from pystardict import Dictionary
from offlineWordTranslator.offlineWordTranslator import OfflineWordTranslatorForWiktionary

from textPreprocessorForConcreteLanguage.eng.textPreprocessorEng import TextPreprocessorEng
from textPreprocessorForConcreteLanguage.rus.textPreprocessorRus import TextPreprocessorRus

from onlineMultilanguageTranslator.onlineMultilanguageTranslator import OnlineMultilanguageTranslator

class DocumentVectorizerEngModel:
    def __init__(self):
        langSys = {"preprocessor" : TextPreprocessorEng()}
        self.__languageSystems = {"English" : langSys}
        
        offlineWordTranslator = OfflineWordTranslatorForWiktionary(Dictionary("./offlineWordTranslator/dictionaries/Wiktionary Russian-English/Wiktionary Russian-English"))
        langSys = {"preprocessor" : TextPreprocessorRus(), "offlineWordTranslator" : offlineWordTranslator}
        self.__languageSystems["Russian"] = langSys
        
        self.__onlineMultilanguageTranslator = OnlineMultilanguageTranslator()
    # lang: "Russian", "English"
    def vectorizeDocument(self, doc, lang = None, useOfflineTranslation = True, useOnlineTranslation = False):
        translatedWords = None
        
        if tryToUseOnlineTranslation == True:
            translatedWords = self._onlineWordSeparationAndTranslation(doc, maxNumberOfAttempts = 4)
            
        if translatedWords == None:
            if useOfflineTranslation == True:
                translatedWords = self._offlineWordSeparationAndTranslation(doc, lang)
            else:
                translatedWords = self._onlineWordSeparationAndTranslation(doc)
                
        if translatedWords == None:
            return None
            
        res = []
        for word in translatedWords:
            try:
                res.append(self.__wordToVecEngModel[word])
            except:
                pass
        return res
        
    # setters and getters
    
    def setWordToVecEngModel(self, model):
        self.__wordToVecEngModel = model
    def getWordToVecEngModel(self):
        return self.__wordToVecEngModel
    
    def _offlineWordSeparationAndTranslation(self, doc, lang):
        # if lang == None detect language of doc automatically
        if lang is None:
            d = Detector(doc)
            lang = d.language.name
        
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
        
    __wordToVecEngModel = None
    __languageSystems = None
    __onlineMultilanguageTranslator = None

