import sys


def generateGraphML(inputFileName):

    oneIndent = '   '
    twoIndent = '       '
    threeIndent = '         '
    target = open(inputFileName + '.graphml' , 'w')

    target.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    target.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
                 'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')

    target.write('<key id="label" for="node" attr.name="label" attr.type="string"/>\n')
    target.write('<key id="timestamp" for="node" attr.name="timestamp" attr.type="string"/>\n')

    target.write('<key id="label" for="edge" attr.name="label" attr.type="string"/>\n')
    target.write('<key id="timestamp" for="edge" attr.name="timestamp" attr.type="string"/>\n')
    target.write('<key id="directed" for="edge" attr.name="directed" attr.type="string"/>\n')

    target.write('<graph id="GSG_V1" edgedefault="directed">\n')

    with open(inputFileName) as infile:
        for line in infile:
                if line.startswith('  {"vertex": {'):
                    # write a node
                    # use split instead of index+ substring because we
                    idLine = next(infile) #     "id": "27",\n
                    vid = idLine.split('"id": ')[1][:-2] # "27"
                    target.write(oneIndent +'<node id=' + vid + '>\n')

                    #Get Attributes
                    attrLine = next(infile) #    "attributes": {"label": "v8"},\n
                    allAttrs = attrLine.split('"attributes": {')[1][:-3] # "label": "v8"
                    allAttrArray = allAttrs.split(',')
                    for attr in allAttrArray:
                        key, val = attr.split(':') # [0]="label" [1]="v8" with '"'
                        target.write(twoIndent +'<data key='+ key.strip() + '>' + val.strip() + '</data>\n')

                    # Get Timestamp
                    timestampLine = next(infile) #     "timestamp": "5"}},\n
                    vTimestamp = timestampLine.split('"timestamp": ')[1][:-4]
                    # Very last timestamp entry does not end with "," which make the subscript invalid
                    if vTimestamp.endswith('"') == False:
                        vTimestamp = vTimestamp + '"'
                    target.write(twoIndent +'<data key="timestamp">' + vTimestamp + '</data>\n')
                    target.write(oneIndent +'</node>\n')

                elif line.startswith('  {"edge": {'):
                    # Write an edge Node
                    idLine = next(infile)
                    eId = idLine.split('"id": ')[1][:-2]

                    # Get Source
                    srcLine = next(infile)
                    src = srcLine.split('"source": ')[1][:-2]


                    # Get Destination
                    dstLine = next(infile)
                    dst = dstLine.split('"target": ')[1][:-2]

                    target.write(oneIndent +'<edge id='+ eId + ' source=' + src + ' target=' + dst + '>\n')

                    # Get Attributes
                    attrLine = next(infile)  # {"foo": "bar", "label": "e89"},\n
                    allAttrs = attrLine.split('"attributes": {')[1][:-3]  # "label": "v8", "label": "e89"
                    allAttrArray = allAttrs.split(',')
                    for attr in allAttrArray:
                        key, val = attr.split(':')  # [0]="label" [1]="v8" with '"'
                        target.write(twoIndent +'<data key=' + key.strip() + '>' + val.strip() + '</data>\n')

                    # Get Direction
                    edirLine = next(infile)
                    eDir = edirLine.split('"directed": ')[1][:-2]
                    target.write(twoIndent +'<data key="directed">' + eDir + '</data>\n')

                    # Get Timestamp
                    timestampLine = next(infile) #     "timestamp": "5"}},\n
                    eTimestamp = timestampLine.split('"timestamp": ')[1][:-4]

                    # Very last timestamp entry does not end with "," which make the subscript invalid
                    if eTimestamp.endswith('"') == False:
                        eTimestamp = eTimestamp + '"'
                    target.write(twoIndent +'<data key="timestamp">' + eTimestamp + '</data>\n')

                    # End of Edge
                    target.write(oneIndent + '</edge>\n')

                else:
                    continue

    target.write('</graph>\n')
    target.write('</graphml>\n')
    print "****Finish: Export " + inputFileName + " to Format = " + exportFormat + ". " +inputFileName + ".grpahml generated \n"

def main():

    global exportFormat
    exportFormat = "GraphML"

    if len(sys.argv) < 2:
        print "Usage: python gExportGraphML.py <input json file> [exportFormat=GraphMl]"

    if len(sys.argv) > 1:
        inputFileName = sys.argv[1]
    if len(sys.argv) > 2:
        exportFormat = sys.argv[2]

    print "****Start: Export " + inputFileName + " to Format = " + exportFormat + "\n"

    if exportFormat == "GraphML":
        generateGraphML(inputFileName)


if __name__ == '__main__':
    main()
