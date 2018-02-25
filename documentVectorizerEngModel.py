
# coding: utf-8

from polyglot.detect import Detector

from pystardict import Dictionary
from offlineWordTranslator.offlineWordTranslator import OfflineWordTranslatorForWiktionary

from textPreprocessorForConcreteLanguage.eng.textPreprocessorEng import TextPreprocessorEng
from textPreprocessorForConcreteLanguage.rus.textPreprocessorRus import TextPreprocessorRus

class DocumentVectorizerEngModel:
    def __init__(self):
        langSys = {"preprocessor" : TextPreprocessorEng()}
        self.__languageSystems = {"English" : langSys}
        
        offlineTranslator = OfflineWordTranslatorForWiktionary(Dictionary(".offlineWordTranslator/dictionaries/Wiktionary Russian-English/Wiktionary Russian-English"))
        langSys = {"preprocessor" : TextPreprocessorRus(), "offlineTranslator" : offlineTranslator}
        self.__languageSystems["Russian"] = langSys
    # lang: "Russian", "English"
    def vectorizeDocument(self, doc, lang = None):
        # lang == None detect language of doc automatically
        if lang is None:
            d = Detector(doc)
            lang = d.language.name
            
        # if language is supported then preprocess, translate and vectorize words
        if lang in self.__languageSystems:
            wordList = self.__languageSystems[lang]["preprocessor"].prepareDocument(doc)
            translatedWords = []
            # translate words if they are not in English
            if lang != "English":
                i = 0
                while i < len(wordList):
                    translation = self.__languageSystems[lang]["offlineTranslator"].translate(wordList[i])
                    if translation is not None:
                        translatedWords += translation.split(" ")
                        #translatedWords.append(translation)
                    i += 1
            else:
                translatedWords = wordList
            res = []
            for word in translatedWords:
                try:
                    res.append(self.__wordToVecEngModel[word])
                except:
                    pass
            return res
        # if language is not supported
        else:
            return None
        
    # setters and getters
    
    def setWordToVecEngModel(self, model):
        self.__wordToVecEngModel = model
    def getWordToVecEngModel(self):
        return self.__wordToVecEngModel
            
        
    __wordToVecEngModel = None
    __languageSystems = None

