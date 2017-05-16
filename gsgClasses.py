# gsgClasses.py
#
# Graph Stream Generator v1.0
#
# Class definitions.
#
# Written by Larry Holder (holder@eecs.wsu.edu).
#
# Copyright (c) 2017, Washington State University.

from datetime import datetime

class Parameters:
    def __init__(self):
        self.numStreams = 1
        self.secondsPerUnitTime = 1
        self.startTime = datetime.now()
        self.duration = 100
        self.outputTimeFormat = "units"
        self.outputFilePrefix = "out"
    
    def parseFromJSON(self,jsonData):
        self.numStreams = int(jsonData['numStreams'])
        self.secondsPerUnitTime = int(jsonData['secondsPerUnitTime'])
        self.startTime = datetime.strptime(jsonData['startTime'], '%Y-%m-%d %H:%M:%S')
        self.duration = int(jsonData['duration'])
        self.outputTimeFormat = jsonData['outputTimeFormat']
        self.outputFilePrefix = jsonData['outputFilePrefix']
    
    def prettyprint(self, tab = ''):
        print(tab + 'Parameters:')
        print(tab + '  Number of streams = ' + str(self.numStreams))
        print(tab + '  Seconds per unit time = ' + str(self.secondsPerUnitTime))
        print(tab + '  Start time = ' + self.startTime.strftime('%Y-%m-%d %H:%M:%S'))
        print(tab + '  Duration = ' + str(self.duration))
        print(tab + '  Output time format = ' + self.outputTimeFormat)
        print(tab + '  Output file prefix = ' + self.outputFilePrefix + '\n')

class Pattern:
    def __init__(self):
        self.id = ""
        self.track = False
        self.probability = 0.0
        self.vertices = [] # list of Vertex class objects
        self.edges = [] # list of Edge class objects
    
    def prettyprint(self, tab = ''):
        print(tab + 'Pattern:')
        print(tab + '  id = ' + self.id)
        if (self.track):
            print(tab + '  track = true')
        else:
            print(tab + '  track = false')
        print(tab + '  probability = ' + str(self.probability))
        print(tab + '  vertices = [')
        for vertex in self.vertices:
            vertex.prettyprint(tab + '    ')
        print(tab + '  ]')
        print(tab + '  edges = [')
        for edge in self.edges:
            edge.prettyprint(tab + '    ')
        print(tab + '  ]')

class Vertex:
    def __init__(self):
        self.id = ""
        self.new = True
        self.attributes = {} # dictionary
    
    def prettyprint(self, tab = ''):
        print(tab + 'Vertex:')
        print(tab + '  id = ' + self.id)
        if (self.new):
            print(tab + '  new = true')
        else:
            print(tab + '  new = false')
        attrStr = DictToString(self.attributes)
        print(tab + '  attributes = ' + attrStr)

class Edge:
    def __init__(self):
        self.id = ""
        self.source = ""
        self.target = ""
        self.directed = False
        self.minOffset = 0
        self.maxOffset = 0
        self.streamNum = 1
        self.attributes = {} # dictionary
    
    def prettyprint(self, tab = ''):
        print(tab + 'Edge:')
        print(tab + '  id = ' + self.id)
        print(tab + '  source = ' + self.source)
        print(tab + '  target = ' + self.target)
        if (self.directed):
            print(tab + '  directed = true')
        else:
            print(tab + '  directed = false')
        print(tab + '  minOffset = ' + str(self.minOffset))
        print(tab + '  maxOffset = ' + str(self.maxOffset))
        print(tab + '  streamNum = ' + str(self.streamNum))
        attrStr = DictToString(self.attributes)
        print(tab + '  attributes = ' + attrStr)

class PatternInstance:
    def __init__(self):
        self.id = ""
        self.vertices = [] # list of VertexInstance class objects
        self.edges = [] # list of EdgeInstance class objects

class VertexInstance:
    def __init__(self):
        self.id = 0
        self.attributes = []
        self.streamCreationTimes = {} # dictionary with entries {streamNum: creationTime} in time units; one for each stream needing new vertex (empty means exists)

class EdgeInstance:
    def __init__(self):
        self.id = 0
        self.source = 0
        self.target = 0
        self.directed = False
        self.attributes = []
        self.streamNum = 0
        self.creationTime = 0 # in time units
        
        
# ----- Class Utility Functions -----

def DictToString(dict):
    dictStr = '{'
    if dict:
        first = True
        for key,value in dict.items():
            if first:
                first = False
            else:
                dictStr += ', '
            dictStr += (str(key) + '=' + str(value))
    dictStr += '}'
    return dictStr

def DictToJSONString(dict):
    dictStr = '{'
    if dict:
        first = True
        for key,value in dict.items():
            if first:
                first = False
            else:
                dictStr += ', '
            dictStr += ('"' + str(key) + '": "' + str(value) + '"')
    dictStr += '}'
    return dictStr
