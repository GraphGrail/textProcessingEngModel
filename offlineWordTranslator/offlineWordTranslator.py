# coding: utf-8

import re

# interface for word translators
class OfflineWordTranslator:
    def __init__(self, dictionary):
        self.__dictionary = dictionary
    # word should be in lower case
    def translate(self, word):
        translationResult = self.__dictionary.get(word, d = None)
        if translationResult == None:
            return None
        return self._parseTranslationResult(translationResult)
    
    def getDictionary(self):
        return self.__dictionary
    
    # Result of translation using dictionary could be in unappropriate form (raw string with descriptions).
    # This function returns string (word could be translated to phrase) which is the result of translation.
    def _parseTranslationResult(self, translationResult):
        return translationResult
    
    __dictionary = None

class OfflineWordTranslatorForStarDictQuick(OfflineWordTranslator):
    def _parseTranslationResult(self, translationResult):
        translatedWords = translationResult.split(", ")
        return translatedWords[0]
    
class OfflineWordTranslatorForWiktionary(OfflineWordTranslator):
    def _parseTranslationResult(self, translationResult):
        translationResult = translationResult.replace("\t", "")
        translationResult = translationResult.split("\n")
        
        translatedWord = translationResult[1].split(", ")[0]
        translatedWord = re.sub("</?.*?>", "",  translatedWord)
        translatedWord = re.sub("\(.*?\)", "",  translatedWord)
        translatedWord = re.sub("\'\'.*?\'\'", "",  translatedWord)
        match = re.search("{{.*\|.*\|(.*?)}}", translatedWord)
        if match:
            translatedWord = match.group(1)
        translatedWord = re.sub(" {2,}", " ",  translatedWord)
        translatedWord = re.sub("^ ", "",  translatedWord)
        translatedWord = re.sub(" $", "",  translatedWord)
        
        return translatedWord
    
    


