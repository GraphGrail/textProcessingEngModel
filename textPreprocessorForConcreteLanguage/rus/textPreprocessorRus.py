
# coding: utf-8

# In[ ]:

from nltk.tokenize import TweetTokenizer
import pymorphy2
import re
import json
import enchant

from .saveAndLoadMechanismForInheritedClasses import SaveAndLoadMechanismForInheritedClasses

class TextPreprocessorRus(SaveAndLoadMechanismForInheritedClasses):
    def __init__(self):
        self.__languageDict = enchant.Dict("ru_RU")
        
        self.__tokenizer = TweetTokenizer()
        
        self.setSignificantSentenceParts(set(['NOUN', 
                                              'ADJF', 
                                              'ADJS', 
                                              'COMP', 
                                              'VERB', 
                                              'INFN', 
                                              'PRTF', 
                                              'PRTS', 
                                              'GRND', 
                                              'ADVB']))
        self.__morph = pymorphy2.MorphAnalyzer()
        
        self.__wordPattern = "^[а-я]+-?[а-я]+$"
        
    # return a list of words 
    # NOTE:stoplist should be set of words in lower case
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
        resWordList = []
        
        wordParses = None
        wordTags = None
        
        # normilize words if needed
        if normalize == True:
            wordParses = [None] * len(wordList)
            wordTags = [None] * len(wordList)
            i = 0
            while i < len(wordList):
                wordParses[i] = self.__morph.parse(wordList[i])[0]
                wordTags[i] = wordParses[i].tag
                wordList[i] = wordParses[i].normal_form
                i += 1
        
        # if we should remove some words first we need to find out their POS tags
        elif removeUnsignificantSentenceParts == True or removeNamedEntities == True:
            wordTags = [None] * len(wordList)
            i = 0
            while i < len(wordList):
                wordTags[i] = self.__morph.tag(wordList[i])[0]
                i += 1

            # remove unsignificant sentence parts if needed
            if removeUnsignificantSentenceParts == True:
                i = len(wordList) - 1
                while i >= 0:
                    if self._isSignificantSentencePartTag(wordTags[i]) == False:
                        del wordList[i]
                        del wordTags[i]
                    i -= 1

            # remove named entities if needed
            if removeNamedEntities == True:
                i = len(wordList) - 1
                while i >= 0:
                    if self._isNamedEntitieTag(wordTags[i]) == True:
                        del wordList[i]
                        del wordTags[i]
                    i -= 1
                
                
        if self.__stoplist is not None:
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
    def getWordTag(self, word):
        try:
            processedWord = Text(word)
            tag = processedWord.pos_tags[0][1]
        except:
            return None
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
    __morph = None
    
    __wordPattern = None
    
    testMode = False

