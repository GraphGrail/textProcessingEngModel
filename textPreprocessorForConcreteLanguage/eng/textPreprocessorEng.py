
# coding: utf-8

import spacy
import re
import json
import enchant
import threading

from nltk.corpus import stopwords

import psutil

import os

from .saveAndLoadMechanismForInheritedClasses import SaveAndLoadMechanismForInheritedClasses

class TextPreprocessorEng(SaveAndLoadMechanismForInheritedClasses):
    def __init__(self):
        #self.__languageDict = enchant.Dict("en_EN")
        
        pathToWordListFromGoogle = os.path.join(os.path.dirname(os.path.abspath(__file__)), "google_numberOfWords_737236.txt")
        
        self.__languageDict = enchant.DictWithPWL("en_EN", pathToWordListFromGoogle)
        
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
        
        self.setStopList(stopwords.words('english'))
        
        
        
        self.__wordPattern = "([a-z]+-)?[a-z]+|n\'t|\'s|\'m|\'ve"
        
    # return a list of words 
    def prepareDocument(self, doc, normalize = True, fixMisspellings = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        processedDoc = self.__nlp(doc)
        return self.prepareProcessedDocument(processedDoc, 
                                      normalize, 
                                      fixMisspellings, 
                                      removeUnsignificantSentenceParts, 
                                      removeNamedEntities)
    
    def prepareProcessedDocument(self, processedDoc, normalize = True, fixMisspellings = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        # correct words in tokens and write them to tempWordList list 
        # if function fixMisspellings is deactivated just write words from tokens list to tempWordList list
        tempTokenList = []
        if fixMisspellings == True:
            tempTokenList = self._correctMisspellingsInListOfWords(processedDoc)
        else:
            for token in processedDoc:
                if self._tokenIsWord(token):
                    tempTokenList.append(token)
            
        resWordList = self.handleCorrectedWordList(tempTokenList, normalize, removeUnsignificantSentenceParts, removeNamedEntities)
        return resWordList
        
    def prepareSequenceOfDocuments(self, docSeq, normalize = True, removeUnsignificantSentenceParts = True, fixMisspellings = True, removeNamedEntities = True):
        
        res = [None] * len(docSeq)
        
        curPos = 0
        curPosMutex = threading.Lock()
        
        numberOfThreads = 4
        try:
            numberOfThreads = psutil.cpu_count(logical=False)
        except:
            pass
        
        dataPieceLength = 10
        
        def prepareDocumentsInOneThread():
            nonlocal curPos
            nonlocal curPosMutex
            nonlocal dataPieceLength
            
            nonlocal normalize
            nonlocal removeUnsignificantSentenceParts
            nonlocal fixMisspellings
            nonlocal removeNamedEntities
            
            while True:
                curPosMutex.acquire()
                beginIndex = curPos
                curPos += dataPieceLength
                curPosMutex.release()
                
                if self.testMode == True and beginIndex % 200 == 0:
                    print("Current position of parsed document: " + str(beginIndex))
                
                if beginIndex >= len(docSeq):
                    break
                
                endIndex = beginIndex + dataPieceLength
                if endIndex >= len(docSeq):
                    endIndex = len(docSeq) - 1
                
                i = beginIndex
                while i <= endIndex:
                    res[i] = self.prepareDocument(docSeq[i], 
                                                    normalize,
                                                    removeUnsignificantSentenceParts, 
                                                    fixMisspellings, 
                                                    removeNamedEntities)
                    i += 1
            
        threadList = []
        for r in range(numberOfThreads):
            threadList.append(threading.Thread(target=prepareDocumentsInOneThread, args=()))
        
        for thr in threadList:
            thr.start()
        
        for thr in threadList:
            thr.join()

        return res
    
    def prepareWord(self, word, normalize = True, removeUnsignificantSentenceParts = True, fixMisspellings = True, removeNamedEntities = True):
        return prepareDocument(word, normalize, removeUnsignificantSentenceParts, fixMisspellings, removeNamedEntities)
        
    # return word list without unsignificant sentence parts, named entities and words which is in stoplist
    def handleCorrectedWordList(self, tokenList, normalize = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        resWordList = []
                
        # if insignificant words and named entities should not be removed then return wordList
        if normalize == False and removeUnsignificantSentenceParts == False and removeNamedEntities == False:
            for token in tokenList:
                resWordList.append(token.text)
            return resWordList
        
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
                tokenText = token.text
                if tokenText == "'s":
                    tokenText = "is"
                elif tokenText == "n't":
                    tokenText = "not"
                elif tokenText == "'ve":
                    tokenText = "have"
                elif tokenText == "'m":
                    tokenText = "am"
                if normalize == True:
                    if token.lemma_ == "-PRON-":
                        resWordList.append(tokenText)
                    else:
                        resWordList.append(token.lemma_)
                else:
                    resWordList.append(tokenText)
                    
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
    
    def _tokenIsWord(self, token):
        pattern = re.compile(self.__wordPattern)
        if pattern.match(token.text.lower()):
            return True
        return False
    
    def _correctMisspellingsInListOfWords(self, parsedDoc):
        res = []
        for token in parsedDoc:
            if self._tokenIsWord(token):
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
    def setStopList(self, stoplist):
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

