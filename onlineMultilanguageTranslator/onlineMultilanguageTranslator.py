
# coding: utf-8

from googletrans import Translator
import time

import json


class OnlineMultilanguageTranslator:
    def __init__(self):
        self.__translator = Translator()
        self.__maxStringLength = 3000
        
        self.testMode = False
    def translate(self, document, dest="en", src="auto", maxNumberOfAttempts=None):
        stringtoTranslate = ""
        if len(document) <= self.__maxStringLength:
            stringtoTranslate = document
        else:
            stringtoTranslate = document[:self.__maxStringLength]
            
        errorNumber = 0
        while errorNumber != maxNumberOfAttempts:
            try:
                translation = self.__translator.translate(stringtoTranslate, dest=dest, src=src)
                res = translation.text
                return res
            except json.decoder.JSONDecodeError:
                errorNumber += 1
                if self.testMode == True:
                    print("Error number: " + errorNumber)
                    print("JSONDecodeError occured!")
                time.sleep(10)
        
        # Didn't translate document
        return None
    
    def getMaxStringLength(self):
        return self.__maxStringLength
    
    __translator = None
    __maxStringLength = None
    
    testMode = None

