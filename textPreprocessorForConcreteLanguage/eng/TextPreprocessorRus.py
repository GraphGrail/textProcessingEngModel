
# coding: utf-8

from nltk.tokenize import TweetTokenizer
from polyglot.text import Text
import re
import json
import enchant

from .saveAndLoadMechanismForInheritedClasses import SaveAndLoadMechanismForInheritedClasses

class TextPreprocessorEng(SaveAndLoadMechanismForInheritedClasses):
    def __init__(self):
        self.__languageDict = enchant.Dict("en_EN")
        
        self.__tokenizer = TweetTokenizer()
        
        self.setSignificantSentenceParts(set(['ADJ', 
                                              'ADV', 
                                              'AUX', 
                                              'INTJ', 
                                              'NOUN', 
                                              'PROPN', 
                                              'VERB']))
        
        self.__wordTags(set(['ADJ', 
                             'ADV', 
                             'AUX', 
                             'INTJ', 
                             'NOUN', 
                             'PROPN', 
                             'VERB', 
                             'CONJ', 
                             'SCONJ', 
                             'ADP', 
                             'DET', 
                             'NUM']))
        
        
        
        self.__wordPattern = "^[a-z]+-?[a-z]+\'t$"
        
    # return a list of words 
    def prepareDocument(self, doc, normalize = True, fixMisspellings = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        tokens = self.__tokenizer.tokenize(doc)
        
        # search for positions where words is placed
        isWordList = self._findOutWhichTokenIsWord(tokens) # returns list of booleans
            
        # correct words in tokens and write them to tempWordList list 
        # if function fixMisspellings is deactivated just write words from tokens list to tempWordList list
        tempWordList = []
        if fixMisspellings == True:
            tempWordList = self._correctMisspellingsInListOfWords(tokens, isWordList)
        else:
            i = 0
            while i < len(tokens):
                if isWordList[i] == True:
                    tempWordList.append(tokens[i])
                i += 1
            
        resWordList = self.handleCorrectedWordList(tempWordList, normalize, removeUnsignificantSentenceParts, removeNamedEntities)
        return resWordList
        
    def prepareSequenceOfDocuments(self, docSeq, normalize = True, removeUnsignificantSentenceParts = True, fixMisspellings = True, removeNamedEntities = True):
        res = []
        for doc in docSeq:
            res.append(self.prepareDocument(doc, 
                                            normalize,
                                            removeUnsignificantSentenceParts, 
                                            fixMisspellings, 
                                            removeNamedEntities, 
                                            stoplist))
        return res
    
    def prepareWord(self, word, normalize = True, removeUnsignificantSentenceParts = True, fixMisspellings = True, removeNamedEntities = True):
        resWordList = []
        
        # correct words in tokens and write them to tempWordList list 
        # if function fixMisspellings is deactivated just write words from tokens list to tempWordList list
        tempWordList = []
        if fixMisspellings == True:
            if self.wordIsCorrect(word) == False:
                corrected = self.tryToCorrectWord(word)
                if corrected is not None:
                    correctedWordList = self.__tokenizer.tokenize(corrected)
                    tempWordList += correctedWordList
        else:
            tempWordList.append(word)
            
        resWordList = self.handleCorrectedWordList(tempWordList, removeUnsignificantSentenceParts, removeNamedEntities, stoplist)
        return resWordList
        
    # return word list without unsignificant sentence parts, named entities and words which is in stoplist
    def handleCorrectedWordList(self, wordList, normalize = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        resWordList = []
        
        # if we should remove some words first we need to find out their POS tags
        if normalize == True or removeUnsignificantSentenceParts == True or removeNamedEntities == True:
            if normalize == False:
                wordTags = [None] * len(wordList)
                i = 0
                while i < len(wordList):
                    wordTags[i] = self.__morph.tag(wordList[i])[0]
                    i += 1

                # remove unsignificant sentence parts if needed
                if removeUnsignificantSentenceParts == True:
                    i = len(wordList)
                    while i >= 0:
                        if self._isSignificantSentencePartTag(wordTags[i]) == True:
                            del wordList[i]
                            del wordTags[i]
                        i -= 1

                # remove named entities if needed
                if removeNamedEntities == True:
                    i = len(wordList)
                    while i >= 0:
                        if self._isNamedEntitieTag(wordTags[i]) == True:
                            del wordList[i]
                            del wordTags[i]
                        i -= 1
            else:
                wordParse = [None] * len(wordList)
                i = 0
                while i < len(wordList):
                    wordParse[i] = self.__morph.parse(wordList[i])[0]
                    i += 1

                # remove unsignificant sentence parts if needed
                if removeUnsignificantSentenceParts == True:
                    i = len(wordList)
                    while i >= 0:
                        if self._isSignificantSentencePartTag(wordParse[i].tag) == True:
                            del wordList[i]
                            del wordParse[i]
                        i -= 1

                # remove named entities if needed
                if removeNamedEntities == True:
                    i = len(wordList)
                    while i >= 0:
                        if self._isNamedEntitieTag(wordTags[i].tag) == True:
                            del wordList[i]
                            del wordParse[i]
                        i -= 1
                i = 0
                while i < len(wordList):
                    wordList[i] = wordParse[i].normal_form
                
                
        if stoplist is not None:
            for word in wordList:
                if word.lower() not in self.__stoplist:
                    resWordList.append(word)
        else:
            resWordList = wordList
            
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
    
    def _correctMisspellingsInListOfWords(self, tokens, isWordList):
        tempWordList = []
        i = 0
        while i < len(tokens):
            if isWordList[i] == True:
                if self.wordIsCorrect(tokens[i]) == False:
                    corrected = self.tryToCorrectWord(tokens[i])
                    if corrected is not None:
                        correctedWordList = self.__tokenizer.tokenize(corrected)
                        tempWordList += correctedWordList
            i += 1
        return tempWordList
        
    # returns corrected form of word (could be two words in string) if can't correct the word return None
    def tryToCorrectWord(self, word):
        res = self.__languageDict.suggest(word)
        if len(res) == 0:
            return None
        return res[0]
    def wordIsNamedEntitie(self, word):
        if self.wordIsCorrect(word) == False:
            return False
        tag = self.__morph.tag(word)[0]
        return self._isNamedEntitieTag(tag)
    def wordIsCorrect(self, word):
        return self.__languageDict.check(word.lower()) or self.__languageDict.check(word.title()) # TODO: after creation of appropriate anchane dict remove self.__languageDict.check(word.title())
    def _isNamedEntitieTag(self, tag):
        namedEntitiesTags = ["Name", "Surn", "Patr", "Geox", "Orgn", "Trad"]
        for entitieTag in namedEntitiesTags:
            if entitieTag in tag:
                return True
        return False
    def _isSignificantSentencePartTag(self, tag):
        return tag.POS in self.__significantSentenceParts
            
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
            state = json.dumps([list(self.__significantSentenceParts)], separators=(',',':'))
            outputFile.write(state)
            outputFile.close()
        
    @staticmethod
    def load(destinationFolder):
        obj = TextProcessor()
        with open(destinationFolder + "/state.json", "r") as inputFile:
            state = json.load(inputFile)
            obj.__significantSentenceParts = set(state[0])
        return obj
    
    # class fields
    
    __languageDict = None
    
    __tokenizer = None
    
    __significantSentenceParts = None
    __stoplist = None
    __wordTags = None
    
    __wordPattern = None
    
    testMode = False

