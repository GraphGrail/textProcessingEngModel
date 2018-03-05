# class to provide saving and loading mechanism for classes inherited from base class
class SaveAndLoadMechanismForInheritedClasses:
    def save(self, destinationFolder):
        with open(destinationFolder + "/realClassName.txt", "w") as outputFile:
            outputFile.write(self.__class__.__name__)
    @staticmethod
    def load(destinationFolder):
        with open(destinationFolder + "/realClassName.txt", "r") as inputFile:
            childClassName = inputFile.readline()
            childClass = eval(childClassName)
            return childClass.load(destinationFolder)