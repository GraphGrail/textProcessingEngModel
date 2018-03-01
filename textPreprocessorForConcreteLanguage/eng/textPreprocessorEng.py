
# coding: utf-8

import spacy
import re
import json
import enchant
import threading

import psutil

from .saveAndLoadMechanismForInheritedClasses import SaveAndLoadMechanismForInheritedClasses

class TextPreprocessorEng(SaveAndLoadMechanismForInheritedClasses):
    def __init__(self):
        #self.__languageDict = enchant.Dict("en_EN")
        self.__languageDict = enchant.DictWithPWL("en_EN", "google_numberOfWords_737236.txt")
        
        self.__nlp = spacy.load('en')
        
        self.setSignificantSentenceParts(set(['ADJ', 
                                              'ADV', 
                                              'AUX', 
                                              'INTJ', 
                                              'NOUN', 
                                              'PROPN', 
                                              'VERB']))
        
        self.__wordTags = set(['ADJ', 
                             'ADV', 
                             'AUX', 
                             'INTJ', 
                             'NOUN', 
                             'PROPN', 
                             'VERB', 
                             'CONJ', 
                             'SCONJ',
                             'CCONJ', 
                             'ADP', 
                             'DET', 
                             'NUM'])
        
        
        
        self.__wordPattern = "^[a-z]+-?[a-z]+(\'t)?$"
        
    # return a list of words 
    def prepareDocument(self, doc, normalize = True, fixMisspellings = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        parsedDoc = self.__nlp(doc)
            
        # correct words in tokens and write them to tempWordList list 
        # if function fixMisspellings is deactivated just write words from tokens list to tempWordList list
        tempTokenList = []
        if fixMisspellings == True:
            tempTokenList = self._correctMisspellingsInListOfWords(parsedDoc)
        else:
            for token in parsedDoc:
                if self._tokenIsWord(token):
                    tempTokenList.append(token)
            
        resWordList = self.handleCorrectedWordList(tempTokenList, normalize, removeUnsignificantSentenceParts, removeNamedEntities)
        return resWordList
        
    def prepareSequenceOfDocuments(self, docSeq, normalize = True, removeUnsignificantSentenceParts = True, fixMisspellings = True, removeNamedEntities = True):
        
        res = [None] * len(docSeq)
        
        curPos = 0
        curPosMutex = threading.Lock()
        
        numberOfCores = 4
        try:
            numberOfCores = psutil.cpu_count(logical=False)
        except:
            pass
        
        dataPieceLength = 10
        
        def prepareDocumentsInOneThread():
            while True:
                curPosMutex.acquire()
                beginIndex = curPos
                curPos += dataPieceLength
                if self.testMode == True:
                    print("Current position of parsed document: " + str(curPos))
                curPosMutex.release()
                
                if beginIndex >= len(docSeq):
                    break
                
                endIndex = beginIndex + dataPieceLength
                if endIndex > len(docSeq):
                    endIndex = len(docSeq)
                
                i = beginIndex
                while i < endIndex:
                    res[i] = self.prepareDocument(docSeq[i], 
                                                    normalize,
                                                    removeUnsignificantSentenceParts, 
                                                    fixMisspellings, 
                                                    removeNamedEntities))
                    i += 1
            
        threadList = [threading.Thread(target=prepareDocumentsInOneThread, args=())] * numberOfCores
        
        for thr in threadList:
            thr.start()
        
        for thr in threadList:
            thr.join()

        return res
    
    def prepareWord(self, word, normalize = True, removeUnsignificantSentenceParts = True, fixMisspellings = True, removeNamedEntities = True):
        return prepareDocument(word, normalize, removeUnsignificantSentenceParts, fixMisspellings, removeNamedEntities)
        
    # return word list without unsignificant sentence parts, named entities and words which is in stoplist
    def handleCorrectedWordList(self, tokenList, normalize = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
                
        # if insignificant words and named entities should not be removed then return wordList
        if normalize == False and removeUnsignificantSentenceParts == False and removeNamedEntities == False:
            return wordList
        
        resWordList = []
        
        # significant_POS is sentece parts that we want to keep
        significant_POS = None
        
        if removeUnsignificantSentenceParts == True:
            significant_POS = self.__significantSentenceParts
        else:
            significant_POS = self.__wordTags
            
        if removeNamedEntities == True:
            # proper noun is not significant if we want to remove named entities
            significant_POS = significant_POS.difference({"PROPN"})
            
        for token in tokenList:
            if token.pos_ in significant_POS:
                if normalize == True:
                    resWordList.append(token.lemma_)
                else:
                    resWordList.append(token.text)
                    
        if self.__stoplist is not None:
            i = len(resWordList) - 1
            while i >= 0:
                if resWordList[i] in self.__stoplist:
                    del resWordList[i]
                i -= 1
        
        return resWordList
    
    def _findOutWhichTokenIsWord(self, tokens):
        isWordList = [False] * len(tokens)
        pattern = re.compile(self.__wordPattern)
        i = 0
        while i < len(tokens):
            if pattern.match(tokens[i].lower()):
                isWordList[i] = True
            i += 1
        return isWordList
    
    def _tokenIsWord(self, tokenText):
        pattern = re.compile(self.__wordPattern)
        if pattern.match(tokenText.lower()):
            return True
        return False
    
    def _correctMisspellingsInListOfWords(self, parsedDoc):
        res = []
        for token in parsedDoc:
            if self._tokenIsWord(token.text):
                if token.pos_ != "PROPN" and self.wordIsCorrect(token.text) == False:
                    corrected = self.tryToCorrectWord(token.text)
                    if corrected is not None:
                        parsedCollocation = self.__nlp(corrected)
                        for correctedWordToken in parsedCollocation:
                            res.append(correctedWordToken)
                else:
                    res.append(token)
        return res
        
    # returns corrected form of word (could be two words in string) if can't correct the word return None
    def tryToCorrectWord(self, word):
        res = self.__languageDict.suggest(word)
        if len(res) == 0:
            return None
        return res[0]
    def wordIsCorrect(self, word):
        return self.__languageDict.check(word.lower()) or self.__languageDict.check(word.title()) # TODO: after creation of appropriate enchant dict remove self.__languageDict.check(word.title())
            
    # getters and setters
            
    def getSignificantSentenceParts(self):
        return self.__significantSentenceParts
    def setSignificantSentenceParts(self, significant_POS):
        self.__significantSentenceParts = set(significant_POS)
        
    def getStopList(self):
        return self.__stoplist
    def setStopList(self, stopList):
        self.__stoplist = stoplist
        
    # save and load functions
        
    def save(self, destinationFolder):
        SaveAndLoadMechanismForInheritedClasses.save(destinationFolder)
        with open(destinationFolder + "/state.json", "w") as outputFile:
            state = json.dumps([list(self.__significantSentenceParts), list(self.__stoplist)], separators=(',',':'))
            outputFile.write(state)
            outputFile.close()
        
    @staticmethod
    def load(destinationFolder):
        obj = TextProcessor()
        with open(destinationFolder + "/state.json", "r") as inputFile:
            state = json.load(inputFile)
            obj.__significantSentenceParts = set(state[0])
            obj.__stoplist = set(state[1])
        return obj
    
    # class fields
    
    __languageDict = None
    
    __nlp = None
    
    __significantSentenceParts = None
    __stoplist = None
    __wordTags = None
    
    __wordPattern = None
    
    testMode = False

