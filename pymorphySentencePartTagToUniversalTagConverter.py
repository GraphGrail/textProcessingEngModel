
# coding: utf-8

class PymorphySentencePartTagToUniversalTagConverter(dict):
    def __init__(self):
        self["ADJF"] = "ADJ"
        self["ADJS"] = "ADJ"

        self["COMP"] = "ADV"
        self["ADVB"] = "ADV"

        self["INFN"] = "VERB"
        self["PRTF"] = "VERB"
        self["PRTS"] = "VERB"
        self["GRND"] = "VERB"

        self["NPRO"] = "NOUN"
