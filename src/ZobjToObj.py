import ctypes
import argparse

if __name__ == '__main__':
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

    with open(inputFilename, 'rb') as fil:
        data = fil.read()
    dataPoints = []
    locations = []
    for num, byte in enumerate(data):
        if byte == 1:
            locations.append(hex(num))
            dataPoints.append({"vertex": data[num:num+8], "start": hex(num), "end": hex(num+8)})

    vertexPoints = []

    for dataPoint in dataPoints:
        if dataPoint["vertex"][4] == 6:
            vertexPoints.append(dataPoint)

    for num, vertex in enumerate(vertexPoints):
        try:
            vertex['faces'] = data[int(vertex['end'], 16):int(vertexPoints[num+1]['start'], 16)]
        except:
            i = 0
            vertex['faces'] = b''
            while data[i+int(vertex['end'], 16): i+int(vertex['end'], 16) + 8] != b'\xdf\x00\x00\x00\x00\x00\x00\x00':
                vertex['faces'] += data[i+int(vertex['end'], 16): i+int(vertex['end'], 16) + 8]
                i += 8

    line = 1
    lineCount = 0
    for num, vertex in enumerate(vertexPoints):
        start = int.from_bytes(vertex['vertex'][0:1], byteorder="big")
        length = int.from_bytes(vertex['vertex'][1:3], byteorder="big")
        halfLength = int.from_bytes(vertex['vertex'][3:4], byteorder="big")
        bank = int.from_bytes(vertex['vertex'][4:5], byteorder="big")
        dataStart = hex(int.from_bytes(vertex['vertex'][5:], byteorder="big"))


        vertexData = data[int(dataStart, 16):int(dataStart, 16)+length]
        for i in range(0, len(vertexData), 16):
            # vertexCount += 1
            vertexPoint = vertexData[i:i+16]
            x = ctypes.c_int16(int.from_bytes(vertexPoint[:2], byteorder="big")).value
            y = ctypes.c_int16(int.from_bytes(vertexPoint[2:4], byteorder="big")).value
            z = ctypes.c_int16(int.from_bytes(vertexPoint[4:6], byteorder="big")).value
            unused = vertexPoint[6:8]
            sCoordinate = vertexPoint[8:10]
            r = vertexPoint[12]
            g = vertexPoint[13]
            b = vertexPoint[14]
            a = vertexPoint[15]
            # print(vertexPoint)
            with open(outputFilename, 'a') as fil:
                fil.write("v {} {} {}\n".format(float(x), float(y), float(z)))
                lineCount += 1

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
