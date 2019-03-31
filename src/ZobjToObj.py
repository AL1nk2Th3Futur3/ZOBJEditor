import ctypes
import argparse

if __name__ == '__main__':
    # Command line parsing. Will probably remove in the future
    parser = argparse.ArgumentParser()
    parser.add_argument("ifile", help="Input File (.zobj)", type=str)
    parser.add_argument("-o", "--ofile", help="Output File (.obj)", type=str)
    args = parser.parse_args()

    if args.ofile == None:
        inputFilename = args.ifile.split(".")[0] + ".zobj"
        outputFilename = args.ifile.split(".")[0] + ".obj"
    else:
        inputFilename = args.ifile.split(".")[0] + ".zobj"
        outputFilename = args.ofile.split(".")[0] + ".obj"

    # Open the .zobj
    with open(inputFilename, 'rb') as fil:
        data = fil.read()

    # Initialize lists for storing data and their locations
    dataPoints = []
    locations = []

    # Go through the data in the file and pick out every byte that equals 01
    # and the next 7 bytes after it
    for num, byte in enumerate(data):
        if byte == 1:
            locations.append(hex(num))
            dataPoints.append({"vertex": data[num:num+8], "start": hex(num), "end": hex(num+8)})

    vertexPoints = []

    # If the fifth byte equals 06 then it's part of the zobj, append it to
    # the vertexPoints list
    # TODO: Allow for grabbing data outside of the zobj
    for dataPoint in dataPoints:
        if dataPoint["vertex"][4] == 6:
            vertexPoints.append(dataPoint)

    # Grab the face data for each set of vertexPoints. This data continues until
    # the end of the next vertexPoint
    for num, vertex in enumerate(vertexPoints):
        try:
            vertex['faces'] = data[int(vertex['end'], 16):int(vertexPoints[num+1]['start'], 16)]
        # If there is no next vertexPoint then go until it reaches the DF command
        except:
            i = 0
            vertex['faces'] = b''
            while data[i+int(vertex['end'], 16): i+int(vertex['end'], 16) + 8] != b'\xdf\x00\x00\x00\x00\x00\x00\x00':
                vertex['faces'] += data[i+int(vertex['end'], 16): i+int(vertex['end'], 16) + 8]
                i += 8

    line = 1
    lineCount = 0
    # Here we actually convert to an .obj
    for num, vertex in enumerate(vertexPoints):
        # Break the vertex up into it's different pieces
        start = int.from_bytes(vertex['vertex'][0:1], byteorder="big")
        length = int.from_bytes(vertex['vertex'][1:3], byteorder="big")
        halfLength = int.from_bytes(vertex['vertex'][3:4], byteorder="big")
        bank = int.from_bytes(vertex['vertex'][4:5], byteorder="big")
        dataStart = hex(int.from_bytes(vertex['vertex'][5:], byteorder="big"))

        # Grab all the vertex data from the file
        vertexData = data[int(dataStart, 16):int(dataStart, 16)+length]
        # Go through the data, 16 bytes at a time
        for i in range(0, len(vertexData), 16):
            vertexPoint = vertexData[i:i+16]
            # Grab the XYZ of the vertex
            x = ctypes.c_int16(int.from_bytes(vertexPoint[:2], byteorder="big")).value
            y = ctypes.c_int16(int.from_bytes(vertexPoint[2:4], byteorder="big")).value
            z = ctypes.c_int16(int.from_bytes(vertexPoint[4:6], byteorder="big")).value
            unused = vertexPoint[6:8]
            # Grab the texture coordinate
            sCoordinate = vertexPoint[8:10]
            # Grab the RGBA value
            r = vertexPoint[12]
            g = vertexPoint[13]
            b = vertexPoint[14]
            a = vertexPoint[15]
            # Write the vertex to the output file
            with open(outputFilename, 'a') as fil:
                fil.write("v {} {} {}\n".format(float(x), float(y), float(z)))
                lineCount += 1

        # Using the face data obtained earlier, write the faces to the obj
        with open(outputFilename, 'a') as fil:
            fil.write("\n")
            for i in range(0, len(vertex['faces']), 4):
                one = int(int(vertex['faces'][i+1] / 2) + line)
                two = int(int(vertex['faces'][i+2] / 2) + line)
                three = int(int(vertex['faces'][i+3] / 2) + line)
                if +one > lineCount or +two > lineCount or +three > lineCount:
                    continue
                if one == two == three:
                    continue
                fil.write("f {}/{} {}/{} {}/{}\n".format(one, one, two, one, three, one))
            fil.write("\n")

        line = lineCount + 1
