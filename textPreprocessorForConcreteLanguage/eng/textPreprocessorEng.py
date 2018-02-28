
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
        
        self.__wordTags = set(['ADJ', 
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
                             'NUM'])
        
        
        
        self.__wordPattern = "^[a-z]+-?[a-z]+(\'t)?$"
        
    # return a list of words 
    # NOTE: normalizing not working
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
                                            removeNamedEntities))
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
            
        resWordList = self.handleCorrectedWordList(tempWordList, removeUnsignificantSentenceParts, removeNamedEntities)
        return resWordList
        
    # return word list without unsignificant sentence parts, named entities and words which is in stoplist
    def handleCorrectedWordList(self, wordList, normalize = True, removeUnsignificantSentenceParts = True, removeNamedEntities = True):
        
        if self.__stoplist is not None:
            i = len(wordList) - 1
            while i >= 0:
                if wordList[i] in self.__stoplist:
                    del wordList[i]
                i -= 1
                
        # if insignificant words and named entities should not be removed then return wordList
        if removeUnsignificantSentenceParts == False and removeNamedEntities == False:
            return wordList
        
        resWordList = []
        
        parsedText = Text(" ".join(wordList))
        
        # significant_POS is sentece parts that we want to keep
        significant_POS = None
        
        if removeUnsignificantSentenceParts == True:
            significant_POS = self.__significantSentenceParts
        else:
            significant_POS = self.__wordTags
            
        if removeNamedEntities == True:
            # proper noun is not significant if we want to remove named entities
            significant_POS = significant_POS.difference({"PROPN"})
            
        try:
            wordTags = parsedText.pos_tags
            for t in wordTags:
                if t[1] in significant_POS:
                    resWordList.append(t[0])
        except:
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
        resWordList = []
        i = 0
        while i < len(tokens):
            if isWordList[i] == True:
                if self.wordIsCorrect(tokens[i]) == False:
                    corrected = self.tryToCorrectWord(tokens[i])
                    if corrected is not None:
                        correctedWordList = self.__tokenizer.tokenize(corrected)
                        resWordList += correctedWordList
                else:
                    resWordList.append(tokens[i])
            i += 1
        return resWordList
        
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
    
    __tokenizer = None
    
    __significantSentenceParts = None
    __stoplist = None
    __wordTags = None
    
    __wordPattern = None
    
    testMode = False

