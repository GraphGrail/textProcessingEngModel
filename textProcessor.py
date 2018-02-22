
# coding: utf-8

from nltk.corpus import stopwords
import numpy as np
import pymorphy2
import re
import pandas as pd
import json
import enchant
import copy
import os

from .pymorphySentencePartTagToUniversalTagConverter import PymorphySentencePartTagToUniversalTagConverter

class TextProcessor:
    def __init__(self, fixMisspellings = True, removeNamedEntities = True):
        self.__pymorphySentencePartTagToUniversalTagConverter = PymorphySentencePartTagToUniversalTagConverter()
        self.__morph = pymorphy2.MorphAnalyzer()
        self.__dictRu = enchant.Dict("ru_RU")
        #self.__dictEn = enchant.Dict("en_EN")
        
        self.__fixMisspellings = fixMisspellings
        self.__removeNamedEntities = removeNamedEntities
        
        self.__stoplist = set()
        self.__stoplist = set.union(self.__stoplist, set(stopwords.words('english')))
        self.__stoplist = set.union(self.__stoplist, set(stopwords.words('russian')))
        
        self.setSignificantSentenceParts(set(['NOUN', 'ADJF', 'ADJS', 'COMP', 'VERB', 'INFN', 'PRTF', 'PRTS', 'GRND', 'ADVB']))
        self.setSignificantSentenceParts(set(["ADJ", "ADV", "AUX", "INTJ", "NOUN", "VERB"]))
        
    # convert text to list of words, removing named entities, not significant sentence parts and stopwords
    def convertDocument(self, doc, fixMisspellings = True, removeNamedEntities = True, vectorsAsResult = False):
        if pd.isnull(doc):
            return []
        wordList = self.splitDocumentInListOfWords(doc)
        if self.testMode == True:
            print("After splitting:")
            print(wordList)
        self.removeNotInformativeWordsFromList(wordList)
        if self.__removeNamedEntities == True:
            namedEntitiesSet = self.getEntitiesSet(wordList)
            self.removeSpecificWordsFromList(wordList, namedEntitiesSet)
        i = 0
        res = []
        while i < len(wordList):
            if self.__baseModel == None or self.__baseModel.vector_size > 1:
                res = res + self.tryToHandleWord(wordList[i], vectorsAsResult)
            else:
                res.append(self.tryToHandleWord(wordList[i], vectorsAsResult))
            i += 1
        if self.testMode == True:
            print("After all changes:")
            print(res)
        return res
    def convertSequenceOfDocuments(self, docSeq, vectorsAsResult = False):
        res = []
        for doc in docSeq:
            res.append(self.convertDocument(doc, vectorsAsResult))
        return res
    def tryToHandleWord(self, word, vectorsAsResult = False):
        wordAndItsAlternatives = [word]
        if self.wordIsCorrect(wordAndItsAlternatives[0]) == True:
            wordAndItsAlternatives[0] = self.__morph.parse(wordAndItsAlternatives[0].lower())[0].normal_form
        elif self.__fixMisspellings == True:
            wordAndItsAlternatives = wordAndItsAlternatives + self.suggestCloseDocuments(word)
        if self.__baseModel is not None:
            res = []
            searchResult = self.searchForClosestWordInModels(wordAndItsAlternatives[0], vectorsAsResult) # search in models not normalized word, because it could be a jargon. Jargon normalizing by pymorphy would not bring word to appropriate form (probably)
            if searchResult is None: # if we did not wind word without bringing it to normal form then we try to search for normalized word in models
                originalWordNormalized = self.__morph.parse(wordAndItsAlternatives[0].lower())[0].normal_form
                searchResult = self.searchForClosestWordInModels(originalWordNormalized, vectorsAsResult)
            if searchResult is not None:
                res.append(searchResult)
                return res
            i = 1
            # Trying to find appropriate word among proposed
            while i < len(wordAndItsAlternatives):
                splittedWords = wordAndItsAlternatives[i].split(" ")
                self.removeNotInformativeWordsFromList(splittedWords)
                for splittedWord in splittedWords:
                    splittedWord = self.__morph.parse(splittedWord.lower())[0].normal_form
                    searchResult = self.searchForClosestWordInModels(splittedWord, vectorsAsResult)
                    if searchResult is not None:
                        res.append(searchResult)
                if res != []:
                    return res
                i += 1
            return res
        else:
            resultWordList = None
            if len(wordAndItsAlternatives) > 1:
                resultWordList = wordAndItsAlternatives[1].split(" ")
                self.removeNotInformativeWordsFromList(resultWordList)
            else:
                resultWordList = wordAndItsAlternatives
            i = 0
            size = len(resultWordList)
            while i < size:
                resultWordList[i] = self.__morph.parse(resultWordList[i])[0].normal_form
                i += 1
            return resultWordList
            
    def searchForClosestWordInModels(self, word, vectorsAsResult = False):
        probablePymorphyPOS = str(self.__morph.parse(word.lower())[0].tag.POS)
        probablePOS = None
        if probablePymorphyPOS in list(self.__pymorphySentencePartTagToUniversalTagConverter.keys()): # should POS be transform?
            probablePOS = self.__pymorphySentencePartTagToUniversalTagConverter[str(self.__morph.parse(word.lower())[0].tag.POS)]
        else:
            probablePOS = probablePymorphyPOS
        copiedTags = copy.deepcopy(list(self.__significantModel_POS_Set))
        i = 0
        while i < len(copiedTags):
            if probablePOS == copiedTags[i]:
                del copiedTags[i]
                copiedTags.insert(0, probablePOS)
                break
            i += 1
        res = self._searchForWordInBaseModel(word, copiedTags, vectorsAsResult)
        if res is not None:
            return res
        if self.__supportingModels is not None:
            res = self._searchForSimilarWordInSupportingModels(word, copiedTags, vectorsAsResult)
        return res
    def _searchForWordInBaseModel(self, word, copiedTags, vectorsAsResult):
        for POS in copiedTags:
            try:
                wordWithPOS = word + "_" + POS
                res = self.__baseModel[wordWithPOS]
                if vectorsAsResult == True:
                    return res
                else:
                    return word
            except:
                pass
        return None
    def _searchForSimilarWordInSupportingModels(self, word, copiedTags, vectorsAsResult):
        for POS in copiedTags:
            for supportModel in self.__supportingModels:
                wordWithPOS = word + "_" + POS
                try:
                    res = self.supportModel[wordWithPOS]
                    similarWords = supportModel.similar_by_word(wordWithPOS, topn=3)
                    for similarWord in similarWords:
                        try:
                            res = self.__baseModel[similarWord[0]]
                            if vectorsAsResult == True:
                                return res
                            else:
                                return similarWord[0]
                        except:
                            pass
                except:
                    pass
        return None
    # get list of words from text using regular expressions
    @staticmethod
    def splitDocumentInListOfWords(doc):
        #prog = re.compile(r'[А-Яа-яA-Za-z-]{1,}')
        prog = re.compile(r'[А-Яа-я]{1,}-{0,1}[А-Яа-я]{1,}|[A-Za-z]{1,}-{0,1}[A-Za-z]{1,}')
        wordsIterator = prog.finditer(doc)
        resultList = []
        for word in wordsIterator:
            resultList.append(word.group(0))
        return resultList
    def wordIsCorrect(self, word):
        wordTitle = word.title() # make first letter capital and others make lowercase to check by enchant (it is case-sensitive)
        wordUpper = word.upper() # make all letters capital
        correct = self.__dictRu.check(wordTitle) or self.__dictRu.check(wordUpper)
        if correct == False:
            return self.checkWordByPymorphy(wordTitle)
        return correct
    def checkWordByPymorphy(self, word):
        parseResult = self.__morph.parse(word)[0]
        return TextProcessor._accordingToMethodsStackAnalizeIsCorrect(parseResult.methods_stack)
    @staticmethod   
    def _accordingToMethodsStackAnalizeIsCorrect(methodStack):
        acceptedAnalizerClasses = ["DictionaryAnalyzer", "KnownSuffixAnalyzer", "KnownPrefixAnalyzer"]
        for method in methodStack:
            if method[0].__class__.__name__ not in acceptedAnalizerClasses:
                return False
        return True
    def closestWordAccordingPymorphy(self, word):
        parseResults = self.__morph.parse(word)
        for parseResult in parseResults:
            if parseResult.methods_stack[0][0].__class__.__name__ == "DictionaryAnalyzer":
                return self.__morph.parse(parseResult.methods_stack[0][1])[0].normal_form
        return None
    # return set of words which are named entities in list l
    def getEntitiesSet(self, l):
        res = set()
        for word in l:
            if self.wordIsNamedEntitie(word):
                res.add(word)
        return res
    # can return not single word but document in case of missing space between words
    def suggestCloseDocuments(self, word):
        res = []
        suggestedByEnchant = self.__dictRu.suggest(word)
        for suggested in suggestedByEnchant:
            res = res + [suggested]
        return res
    def wordIsNamedEntitie(self, word):
        if self.wordIsCorrect(word) == False:
            return False
        tag = self.__morph.parse(word)[0].tag
        namedEntitiesTags = ["Name", "Surn", "Patr", "Geox", "Orgn", "Trad"]
        for entitieTag in namedEntitiesTags:
            if entitieTag in tag:
                return True
        return False
    # removes wordsSet from list of words l
    def removeSpecificWordsFromList(self, l, words_set):
        for word in words_set:
            word = word.lower()
            i = len(l) - 1
            while i >= 0:
                if l[i].lower() == word:
                    del l[i]
                i -= 1
    def removeNotInformativeWordsFromList(self, l):
        i = len(l) - 1
        while i >= 0:
            if self.__dictRu.check(l[i]) and self.__morph.parse(l[i])[0].tag.POS not in self.__significantPymorphy_POS_Set:
                del l[i]
            i -= 1
    def getSignificantSentenceParts(self):
        return self.__significantPymorphy_POS_Set
    def setSignificantSentenceParts(self, significant_POS):
        self.__significantPymorphy_POS_Set = significant_POS
        self.__significantModel_POS_Set = set()
        for pos in significant_POS:
            if pos in list(self.__pymorphySentencePartTagToUniversalTagConverter.keys()):
                self.__significantModel_POS_Set.add(self.__pymorphySentencePartTagToUniversalTagConverter[pos])
            else:
                self.__significantModel_POS_Set.add(pos)
    def getStopList(self):
        return self.__stoplist
    def setStopList(self, stopList):
        self.__stoplist = stoplist
    def setBaseModel(self, model):
        self.__baseModel = model
    def setSupportingModels(self, supportingModels):
        self.__supportingModels = supportingModels
    def save(self, destinationFolder):
        with open(destinationFolder + "/state.json", "w") as outputFile:
            state = json.dumps([list(self.__significantPymorphy_POS_Set), 
                                list(self.__stoplist), 
                               self.__fixMisspellings],
                               separators=(',',':'))
            outputFile.write(state)
            outputFile.close()
        if self.__baseModel != None:
            self.__baseModel.save(destinationFolder + "/" + "baseModel")
        if self.__supportingModels != None:
            with open(destinationFolder + "/numberOfSupportingModels.txt", "w") as outputFile:
                outputFile.write(str(len(self.__supportingModels)))
                i = 0
                while i < len(self.__supportingModels):
                    self.__supportingModels[i].save(destinationFolder + "/" + "supModel_" + str(i))
                    i += 1
        
    @staticmethod
    def load(destinationFolder):
        obj = TextProcessor()
        with open(destinationFolder + "/state.json", "r") as inputFile:
            state = json.load(inputFile)
            obj.__significantPymorphy_POS_Set = set(state[0])
            obj.__stoplist = set(state[1])
            obj.__fixMisspellings = state[2]
        if os.path.exists(destinationFolder + "/" + "baseModel"):
            obj.__baseModel = gensim.models.KeyedVectors.load(destinationFolder + "/" + "baseModel")
        if os.path.exists(destinationFolder + "/numberOfSupportingModels.txt"):
            with open(destinationFolder + "/numberOfSupportingModels.txt", "r") as inputFile:
                num = int(inputFile.readline())
            obj.__supportingModels = []
            i = 0
            while i < num:
                obj.__supportingModels.append(gensim.models.KeyedVectors.load(destinationFolder + "/" + "supModel_" + str(i)))
                i += 1
        return obj
    
    __significantPymorphy_POS_Set = None
    __significantModel_POS_Set = None
    __stoplist = None
    __morph = None
    __dictRu = None
    __dictEn = None
    
    __fixMisspellings = None
    __removeNamedEntities = None
    
    __pymorphySentencePartTagToUniversalTagConverter = None
    
    __baseModel = None
    __supportingModels = None
    
    testMode = False


