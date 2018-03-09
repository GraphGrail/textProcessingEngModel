
# coding: utf-8

# In[3]:

from offlineWordTranslator import *
import json


# In[1]:

class SmartOfflineWordTranslator:
    def __init__(self):
        self.__pathToCustomDictionary = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "dictionaries", 
                                        "custom", 
                                        "rusEngDictionary.json")
        rusToEngDict = None
        with open(self.__pathToCustomDictionary, "r") as fp:
            rusToEngDict = json.load(fp)
        __customTranslator = OfflineWordTranslator(rusToEngDict)
        
        pathToDictionary = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "dictionaries", 
                                        "Wiktionary Russian-English", 
                                        "Wiktionary Russian-English")
        self.__wiktionaryTranslator = OfflineWordTranslatorForWiktionary(Dictionary(pathToDictionary))
        
        pathToDictionary = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "dictionaries", 
                                        "stardict-quick_rus-eng-2.4.2", 
                                        "quick_russian-english")
        self.__starDictQuickTranslator = OfflineWordTranslatorForStarDictQuick(Dictionary(pathToDictionary))
    
    def translate(self, word):
        translation = self.__customTranslator.translate(word)
        if translation is not None:
            return translation
        
        translation = self.__wiktionaryTranslator.translate(word)
        if translation is not None:
            return translation
        
        translation = self.__starDictQuickTranslator.translate(word)
        if translation is not None:
            return translation
    
    def addNewWordTranslation(self, word, translation):
        customDict = self.__customTranslator.getDictionary()
        if word in customDict:
            customDict[word].append(translation)
        else:
            customDict[word] = [translation]
        
    __pathToCustomDictionary = None
    __customTranslator = None
    __wiktionaryTranslator = None
    __starDictQuickTranslator = None


# In[ ]:



