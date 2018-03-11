# gsg.py
#
# Graph Stream Generator v1.0
#
# Usage: gsg <input_file>
#
# See readme.txt for description of input and output files.
#
# Written by Larry Holder (holder@eecs.wsu.edu).
#
# Copyright (c) 2017, Washington State University.

import sys
import json
from datetime import datetime
from datetime import timedelta
import random
from gsgClasses import *
import scipy.stats as ss
import numpy as np


# ----- Global variables -----

global gParameters
global gPatterns
global gSeedPatterns
global gStreamFiles
global gInstancesFile
global gWroteAnInstance # True if wrote at least one instance already
global gStreamVertices  # list where gStreamVertices[i] = list of vertices in stream i+1
global gStreamVerticesDeg  # list where gStreamVertices[i] = list of degree of vertices in stream i+1
global gStreamSchedules # list of streams, where gStreamSchedules[i] = list of scheduled vertices and edges for stream i+1
global gStreamWrittenTo # list of Booleans, where gStreamWrittenTo[i] = True if some vertex written to stream
global gNumVertices     # total number of unique vertices written to streams
global gNumEdges        # total number of edges written to streams


# ----- Parsing Functions -----

def ParseVertices(jsonData):
    vertices = []
    for jsonVertex in jsonData:
        vertex = Vertex()
        vertex.id = jsonVertex['id']
        if (jsonVertex['new'] == "true"):
            vertex.new = True
            vertex.attributes = jsonVertex['attributes']
        else:
            vertex.new = False 
            vertex.attributes = [] # attributes ignored if new=false, i.e., referring to old vertex (and will use its attributes)
        vertices.append(vertex)
    return vertices

def ParseEdges(jsonData, vertices, streamNum=None):
    global gParameters
    edges = []
    for jsonEdge in jsonData:
        edge = Edge()
        edge.id = jsonEdge['id']
        edge.source = jsonEdge['source']
        if (GetVertexById(edge.source, vertices) == None):
            print("Error: Source vertex in edge " + edge.id + " not defined")
            sys.exit()
        edge.target = jsonEdge['target']
        if (GetVertexById(edge.target, vertices) == None):
            print("Error: Target vertex in edge " + edge.id + " not defined")
            sys.exit()
        if (jsonEdge['directed'] == "true"):
            edge.directed = True
        else:
            edge.directed = False
        edge.minOffset = int(jsonEdge['minOffset'])
        edge.maxOffset = int(jsonEdge['maxOffset'])
        if ((edge.minOffset < 0) or (edge.minOffset > edge.maxOffset)):
            print("Error: Incorrect offsets in edge " + edge.id)
            sys.exit()
        if streamNum is None:
            edge.streamNum = int(jsonEdge['streamNum'])
        else:
            edge.streamNum = int(streamNum)
        if ((edge.streamNum < 1) or (edge.streamNum > gParameters.numStreams)):
            print("Error: streamNum out of range in edge " + edge.id)
            sys.exit()
        edge.attributes = jsonEdge['attributes']
        edges.append(edge)
    return edges

def ParsePatterns(jsonData,baseJsonData=None):
    print('Parsing patterns...')
    global gPatterns
    global gSeedPatterns
    gPatterns = []
    gSeedPatterns = []

    for jsonPattern in baseJsonData:
        pattern = Pattern()
        pattern.id = jsonPattern['id']
        if (jsonPattern['track'] == "true"):
            pattern.track = True
        else:
            pattern.track = False
        pattern.probability = float(jsonPattern['probability'])
        if ((pattern.probability < 0.0) or (pattern.probability > 1.0)):
            print("Error: probability out of range for pattern " + pattern.id)
            sys.exit()
        pattern.vertices = ParseVertices(jsonPattern['vertices'])
        pattern.edges = ParseEdges(jsonPattern['edges'], pattern.vertices)
        if ValidPattern(pattern):
            gSeedPatterns.append(pattern)

    for jsonPattern in jsonData:
        pattern = Pattern()
        pattern.id = jsonPattern['id']
        if (jsonPattern['track'] == "true"):
            pattern.track = True
        else:
            pattern.track = False
        pattern.probability = float(jsonPattern['probability'])
        if ((pattern.probability < 0.0) or (pattern.probability > 1.0)):
            print("Error: probability out of range for pattern " + pattern.id)
            sys.exit()
        pattern.vertices = ParseVertices(jsonPattern['vertices'])
        pattern.edges = ParseEdges(jsonPattern['edges'], pattern.vertices)
        if ValidPattern(pattern):
            gPatterns.append(pattern)

def ParseBackgroundPatterns(streamBackGroundModelsList):
    print('Parsing patterns...')
    global gPatterns
    for index, modelKey in enumerate(streamBackGroundModelsList):
        inputFileName = str(modelKey) + ".json"
        with open(inputFileName) as inputFile:
            jsonData = json.load(inputFile)
            ParseAppendPatterns(jsonData['patterns'], int(index) +1)

def ParseAppendPatterns(jsonData, streamNum):
    print('Parsing patterns...')
    global gPatterns
    for jsonPattern in jsonData:
        pattern = Pattern()
        pattern.id = jsonPattern['id']
        if (jsonPattern['track'] == "true"):
            pattern.track = True
        else:
            pattern.track = False
        pattern.probability = float(jsonPattern['probability'])
        if ((pattern.probability < 0.0) or (pattern.probability > 1.0)):
            print("Error: probability out of range for pattern " + pattern.id)
            sys.exit()
        pattern.vertices = ParseVertices(jsonPattern['vertices'])
        pattern.edges = ParseEdges(jsonPattern['edges'], pattern.vertices,streamNum)
        if ValidPattern(pattern):
            gPatterns.append(pattern)


def ValidPattern(pattern):
    # Check that all edges to an old vertex in same stream
    # NOTE : SUMIT: should we allow to use old vertex in each specified stream ? Ex:
    # a 4-node ring graph where each edge is in different stream .
    for vertex in pattern.vertices:
        if (not vertex.new):
            oldVertexStreamNum = -1
            for edge in pattern.edges:
                if ((edge.source == vertex.id) or (edge.target == vertex.id)):
                    if (oldVertexStreamNum == -1):
                        oldVertexStreamNum = edge.streamNum # first edge using old vertex
                    else:
                        if (oldVertexStreamNum != edge.streamNum):
                            print("Error: Invalid pattern " + pattern.id + ": two edges to same old vertex have different streams")
                            sys.exit()
    return True


# ----- File I/O -----

def OpenFiles():
    global gStreamFiles
    global gInstancesFile
    global gWroteAnInstance
    gStreamFiles = []
    for streamNum in range(0,gParameters.numStreams):
        outputFileName = gParameters.outputFilePrefix + '-s' + str(streamNum+1)
        outputFile = open(outputFileName, 'w')
        outputFile.write('[\n') # array of vertices and edges
        gStreamFiles.append(outputFile)
    instancesFileName = gParameters.outputFilePrefix + '-insts'
    gInstancesFile = open(instancesFileName, 'w')
    gInstancesFile.write('[\n') # array of pattern instances
    gWroteAnInstance = False
    
def CloseFiles():
    global gStreamFiles
    global gInstancesFile
    for streamFile in gStreamFiles:
        streamFile.write('\n]\n')
        streamFile.close()
    gInstancesFile.write('\n]\n')
    gInstancesFile.close()
        
    
# ----- Main Functions -----

def AddPatternInstance(pattern, timeUnit):
    global gNumEdges
    #print("Adding instance of pattern " + pattern.id + " at time " + str(timeUnit))
    vertexInstancesDict = {}
    edgeInstances = []
    patternCreated = True
    for edge in pattern.edges:
        edgeInstance = EdgeInstance()
        edgeInstance.directed = edge.directed
        edgeInstance.attributes = edge.attributes
        edgeInstance.streamNum = edge.streamNum
        edgeInstance.creationTime = timeUnit + random.randint(edge.minOffset, edge.maxOffset)
        sourceVertex = GetVertexById(edge.source, pattern.vertices)
        edgeInstance.source = GetVertexInstanceId(sourceVertex, edgeInstance, vertexInstancesDict)
        targetVertex = GetVertexById(edge.target, pattern.vertices)
        edgeInstance.target = GetVertexInstanceId(targetVertex, edgeInstance, vertexInstancesDict)
        if ((edgeInstance.source == 0) or (edgeInstance.target == 0)):
            patternCreated = False
            break # break out of loop over pattern.edges
        else:
            gNumEdges += 1
            edgeInstance.id = gNumEdges
            edgeInstances.append(edgeInstance)
    if patternCreated:
        patternInstance = PatternInstance()
        patternInstance.id = pattern.id
        patternInstance.vertices = vertexInstancesDict.values()
        patternInstance.edges = edgeInstances
        # Write instance if pattern track'ed
        if (pattern.track):
            WritePatternInstance(patternInstance)
        SchedulePatternInstance(patternInstance)   
    else:
        print("  Instance not added: not enough old vertices available in stream")

# Add pattern instance's vertices and edges to appropriate stream schedules
def SchedulePatternInstance(patternInstance):
    global gStreamSchedules
    for vertexInstance in patternInstance.vertices:
        for streamNum in vertexInstance.streamCreationTimes.keys():
            gStreamSchedules[streamNum-1].append(vertexInstance)
    for edgeInstance in patternInstance.edges:
        gStreamSchedules[edgeInstance.streamNum-1].append(edgeInstance)

def WritePatternInstance(patternInstance):
    global gWroteAnInstance
    global gInstancesFile
    global gWroteAnInstance
    if gWroteAnInstance:
        gInstancesFile.write(',\n')
    else:
        gWroteAnInstance = True
    gInstancesFile.write('  {"patternId": "'+ patternInstance.id + '",\n')
    gInstancesFile.write('   "vertexIds": [')
    firstTime = True
    for vertexInstance in patternInstance.vertices:
        if firstTime:
            firstTime = False
        else:
            gInstancesFile.write(', ')
        gInstancesFile.write('"' + str(vertexInstance.id) + '"')
    gInstancesFile.write('],\n')
    gInstancesFile.write('   "edgeIds": [')
    firstTime = True
    for edgeInstance in patternInstance.edges:
        if firstTime:
            firstTime = False
        else:
            gInstancesFile.write(', ')
        gInstancesFile.write('"' + str(edgeInstance.id) + '"')
    gInstancesFile.write(']\n  }')

# If returns 0, then it was unable to create vertex instance
def GetVertexInstanceId(vertex, edgeInstance, vertexInstancesDict):
    global gNumVertices
    if (vertex.id in vertexInstancesDict):
        # Vertex instance already created
        vertexInstance = vertexInstancesDict[vertex.id]
        if (vertex.new):
            streamCreationTimes = vertexInstance.streamCreationTimes
            # Make sure new vertex instance appears no later than any incident edges
            if (edgeInstance.streamNum in streamCreationTimes):
                if (edgeInstance.creationTime < streamCreationTimes[edgeInstance.streamNum]):
                        streamCreationTimes[edgeInstance.streamNum] = edgeInstance.creationTime
            else:
                streamCreationTimes[edgeInstance.streamNum] = edgeInstance.creationTime
        # else old vertex instance already exists and no need to change streamCreationTimes
    else:
        # Create new vertex instance
        vertexInstance = VertexInstance()
        vertexInstance.attributes = vertex.attributes
        if (vertex.new):
            gNumVertices += 1
            vertexInstance.id = gNumVertices
            vertexInstance.streamCreationTimes[edgeInstance.streamNum] = edgeInstance.creationTime
        else:
            # Get random old vertex that has not already been used for a different old vertex in this pattern
            usedVertexIds = [vi.id for vi in vertexInstancesDict.values()]
            vertexInstance.id = GetRandomVertexIdOnStream(edgeInstance.streamNum, usedVertexIds)
        vertexInstancesDict[vertex.id] = vertexInstance
    return vertexInstance.id # If zero, then edge left hanging; should abort creating this pattern instance

def GetVertexById(id, vertices):
    for vertex in vertices:
        if (vertex.id == id):
            return vertex # Should always exist (unless incorrect input)
    return None

# Return id of random vertex already written to given stream number (and not already used).
# Returns 0 if none exists.
def GetRandomVertexIdOnStream(streamNum, usedVertexIds):
    global gStreamVertices
    global gStreamVerticesDeg
    streamVertices = gStreamVertices[streamNum-1]
    streamVerticesDeg = gStreamVerticesDeg[streamNum - 1]
    numStreamVertices = len(streamVertices)
    if (numStreamVertices > 0):
        # Get a random starting point
        randomVertexIndex = random.randint(0,numStreamVertices-1)
        #randomVertexIndex = int(ss.powerlaw.rvs(.3, loc = 0, scale = numStreamVertices-1, size = 1))
        # get randomVertexIndex proportional to its degree
        # print "this stream deg is "
        # print gStreamVerticesDeg
        sumOfDegree = sum(streamVerticesDeg)
        # print "sum is " + str(sumOfDegree)
        streamVerticesProb = list(map((lambda x: x/float(sumOfDegree)), streamVerticesDeg))
        streamVerticesProbAccum = np.cumsum(streamVerticesProb)
        # print streamVerticesProbAccum
        drwaProb = random.uniform(0, 1)
        #randomVertexIndex = (x for x in range(len(streamVerticesProbAccum)) if streamVerticesProbAccum[x] >= drwaProb).next()
        # print "deg list"
        # print gStreamVerticesDeg
        # print "used vertex is "
        # print usedVertexIds
        # print "draw prob " + str(drwaProb)
        # print "selected : " + str(randomVertexIndex)
        numTries = 0
        while (numTries < numStreamVertices):
            # Keep incrementing from random starting point until non-used vertex id found, or tried them all
            randomVertexId = streamVertices[randomVertexIndex]
            if (randomVertexId not in usedVertexIds):
                return randomVertexId
            randomVertexIndex += 1
            #randomVertexIndex = int(ss.powerlaw.rvs(.3, loc=0, scale=numStreamVertices - 1, size=1))
            if (randomVertexIndex == numStreamVertices):
                randomVertexIndex = 0
            numTries += 1
    return 0
    
def GenerateStreams():
    print('Generating streams...')
    global gParameters
    global gPatterns
    global gSeedPatterns
    global gNumVertices
    global gNumEdges
    global gStreamVertices
    global gStreamVerticesDeg
    global gStreamSchedules
    global gStreamWrittenTo
    gNumVertices = 0
    gNumEdges = 0
    gStreamVertices = [[] for x in xrange(gParameters.numStreams)] # list of numStreams empty lists
    gStreamVerticesDeg = [[] for x in xrange(gParameters.numStreams)]  # list of numStreams empty lists
    gStreamSchedules = [[] for x in xrange(gParameters.numStreams)] # list of numStreams empty lists
    gStreamWrittenTo = [False for x in xrange(gParameters.numStreams)]
    #Add base graph first with probability = 1
    for pattern in gSeedPatterns:
            AddPatternInstance(pattern, 0)
    for timeUnit in range(0,gParameters.duration):
        for pattern in gPatterns:
            if (pattern.probability >= random.uniform(0,1)):
                AddPatternInstance(pattern, timeUnit)
        ProcessStreamSchedules(timeUnit)
    # Continue until all scheduled vertices and edges processed
    timeUnit = gParameters.duration
    while not SchedulesEmpty():
        ProcessStreamSchedules(timeUnit)
        timeUnit += 1

def SchedulesEmpty():
    global gStreamSchedules
    for streamSchedule in gStreamSchedules:
        if streamSchedule: # not empty
            return False
    return True

# Write scheduled vertices and edges to streams for creationTime = timeUnit.
# Add new vertices to gStreamVertices.
def ProcessStreamSchedules(timeUnit):
    global gParameters
    global gStreamVertices
    global gStreamVerticesDeg
    global gStreamSchedules
    for streamIndex in range(0,gParameters.numStreams):
        for item in list(gStreamSchedules[streamIndex]):
            if isinstance(item, VertexInstance):
                vertexInstance = item
                if (vertexInstance.streamCreationTimes[streamIndex+1] == timeUnit):
                    WriteVertexInstanceToStream(vertexInstance, streamIndex+1)
                    gStreamVertices[streamIndex].append(vertexInstance.id)
                    # initialized the degree of node by zero;
                    # vertex index should be found in gStreamVertices[streamIndex]
                    #print "adding new vertex "
                    gStreamVerticesDeg[streamIndex].append(0)
                    #print gStreamVerticesDeg
                    gStreamSchedules[streamIndex].remove(vertexInstance)
            else: # item must be an edge instance
                edgeInstance = item
                if (edgeInstance.creationTime == timeUnit):
                    WriteEdgeInstanceToStream(edgeInstance, streamIndex+1)
                    gStreamSchedules[streamIndex].remove(edgeInstance)
                    #update degree of sourc and destination
                    # get degree of source vertex
                    # first get is index
                    # print "adding new edge. now updating deg"
                    srcIndex = gStreamVertices[streamIndex].index(edgeInstance.source)
                    # print "src index is " + str(srcIndex)
                    gStreamVerticesDeg[streamIndex][srcIndex] = gStreamVerticesDeg[streamIndex][srcIndex] + 1
                    dstIndex = gStreamVertices[streamIndex].index(edgeInstance.target)
                    # print "dst index is " + str(dstIndex)
                    gStreamVerticesDeg[streamIndex][dstIndex] = gStreamVerticesDeg[streamIndex][dstIndex] + 1
                    # print "udpated gdeg list"
                    # print gStreamVerticesDeg

def WriteVertexInstanceToStreamBkp(vertexInstance, streamNum):
    global gStreamFiles
    global gStreamWrittenTo
    streamFile = gStreamFiles[streamNum-1]
    if gStreamWrittenTo[streamNum-1]:
        streamFile.write(',\n')
    else:
        gStreamWrittenTo[streamNum-1] = True
    streamFile.write('  {"vertex": {\n')
    streamFile.write('     "id": "' + str(vertexInstance.id) + '",\n')
    streamFile.write('     "attributes": ' + DictToJSONString(vertexInstance.attributes) + ',\n')
    streamFile.write('     "timestamp": "' + TimeStr(vertexInstance.streamCreationTimes[streamNum]) + '"}}')

def WriteVertexInstanceToStream(vertexInstance, streamNum):
    global gStreamFiles
    global gStreamWrittenTo
    streamFile = gStreamFiles[streamNum-1]
    #if gStreamWrittenTo[streamNum-1]:
        #streamFile.write(',\n')
    #else:
        #gStreamWrittenTo[streamNum-1] = True
    #streamFile.write('  {"vertex": {\n')
    #streamFile.write('     "id": "' + str(vertexInstance.id) + '",\n')
    #streamFile.write('     "attributes": ' + DictToJSONString(vertexInstance.attributes) + ',\n')
    #streamFile.write('     "timestamp": "' + TimeStr(vertexInstance.streamCreationTimes[streamNum]) + '"}}')


def WriteEdgeInstanceToStream(edgeInstance, streamNum):
    global gStreamFiles
    global gStreamWrittenTo
    streamFile = gStreamFiles[streamNum-1]
    streamFile.write('\n') # some vertices must have already been written
    #streamFile.write('  {"edge": {\n')
    #streamFile.write('     "id": "' + str(edgeInstance.id) + '",\n')
    streamFile.write(str(edgeInstance.source) + ' ' + DictToJSONString(edgeInstance.attributes) + ' ' + str(edgeInstance.target) + ' ' + TimeStr(edgeInstance.creationTime) )
    #streamFile.write('     "source": "' + str(edgeInstance.source) + '",\n')
    #streamFile.write('     "target": "' + str(edgeInstance.target) + '",\n')
    #streamFile.write('     "attributes": ' + DictToJSONString(edgeInstance.attributes) + ',\n')
    #if edgeInstance.directed:
    #    streamFile.write('     "directed": "true",\n')
    #else:
    #    streamFile.write('     "directed": "false",\n')
    #streamFile.write('     "timestamp": "' + TimeStr(edgeInstance.creationTime) + '"}}')

def WriteEdgeInstanceToStreamBkp(edgeInstance, streamNum):
    global gStreamFiles
    global gStreamWrittenTo
    streamFile = gStreamFiles[streamNum-1]
    streamFile.write(',\n') # some vertices must have already been written
    streamFile.write('  {"edge": {\n')
    streamFile.write('     "id": "' + str(edgeInstance.id) + '",\n')
    streamFile.write('     "source": "' + str(edgeInstance.source) + '",\n')
    streamFile.write('     "target": "' + str(edgeInstance.target) + '",\n')
    streamFile.write('     "attributes": ' + DictToJSONString(edgeInstance.attributes) + ',\n')
    if edgeInstance.directed:
        streamFile.write('     "directed": "true",\n')
    else:
        streamFile.write('     "directed": "false",\n')
    streamFile.write('     "timestamp": "' + TimeStr(edgeInstance.creationTime) + '"}}')

# Convert timeUnit to string according to output time format
def TimeStr(timeUnit):
    global gParameters
    result = str(timeUnit) # i.e., outputTimeFormat = "units"
    if (gParameters.outputTimeFormat == "seconds"):
        result = str(timeUnit * gParameters.secondsPerUnitTime)
    if (gParameters.outputTimeFormat == "datetime"):
        secs = timeUnit * gParameters.secondsPerUnitTime
        dateTime = gParameters.startTime + timedelta(seconds=secs)
        result = dateTime.strftime('%Y-%m-%d %H:%M:%S')
    return result

def main():
    global gParameters
    global gPatterns
    global gSeedPatterns
    inputFileName = sys.argv[1]
    with open(inputFileName) as inputFile:
        jsonData = json.load(inputFile)
    with open("seedGraph.json") as seedGraphFile:
        baseJsonData = json.load(seedGraphFile)
    gParameters = Parameters()
    gParameters.parseFromJSON(jsonData)
    print('Graph Stream Generator v1.0\n')
    gParameters.prettyprint()
    ParsePatterns(jsonData['patterns'],baseJsonData['patterns'])
    ParseBackgroundPatterns(jsonData['streamBackGroundModels'])
    for pattern in gPatterns:
        pattern.prettyprint()
    OpenFiles()
    GenerateStreams()
    CloseFiles()
    
if __name__ == "__main__":
    main()