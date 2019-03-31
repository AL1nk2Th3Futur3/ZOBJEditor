import re
import ctypes
import pprint

class ZobjFile:
    def __init__(self, fileData, filename="untitled"):
        self.fileData = fileData
        self.displayLists = []
        self.filename = "untitled"

        # Grab display lists
        for data in re.compile(
            b'\xE7\x00\x00\x00\x00\x00\x00\x00[^\xE7^\xDF]*'
        ).finditer(self.fileData):
            self.displayLists.append({
                "start": data.start(),
                "displayListData": data.group(),
                "end": data.start() + len(data.group()),
                "vertexData": []
            })

        # Grab vertex data
        for displayList in self.displayLists:
            for data in re.compile(
                b'\x01[\x00-\xFF][\x00-\xFF][\x00-\xFF][\x02\x03\x04\x05\x06][\x00-\xFF][\x00-\xFF][\x00-\xFF]'
            ).finditer(displayList['displayListData']):
                end = data.start() + len(data.group()) + displayList['start']
                vertexStart = int.from_bytes(data.group()[5:], byteorder='big')
                vertexEnd = int.from_bytes(data.group()[1:3], byteorder='big') + vertexStart
                displayList["vertexData"].append({
                    "vertexPointer": data.group(),
                    "start": data.start() + displayList['start'],
                    "end": end,
                    "vertices": self.fileData[vertexStart:vertexEnd]
                })

        # Grab object faces
        for displayList in self.displayLists:
            for num, vertex in enumerate(displayList['vertexData']):
                try:
                    vertex['faces'] = self.fileData[vertex['end']:displayList['vertexData'][num+1]['start']]
                except:
                    vertex['faces'] = self.fileData[vertex['end']:displayList['end']]

    # Return a list of formatted F3DEX2 data points
    def generateF3DEX2Dict(self, F3DEX2Data):
        assert len(F3DEX2Data) % 16 == 0, "Invalid F3DEX2 data provided"
        toReturn = []
        # Go through the data, 16 bytes at a time
        for i in range(0, len(F3DEX2Data), 16):
            toReturn.append({
                "x": ctypes.c_int16(int.from_bytes(F3DEX2Data[i:i+16][:2], byteorder="big")).value,
                "y": ctypes.c_int16(int.from_bytes(F3DEX2Data[i:i+16][2:4], byteorder="big")).value,
                "z": ctypes.c_int16(int.from_bytes(F3DEX2Data[i:i+16][4:6], byteorder="big")).value,
                "sCoordinate": F3DEX2Data[i:i+16][8:10],
                "r": F3DEX2Data[i:i+16][12],
                "g": F3DEX2Data[i:i+16][13],
                "b": F3DEX2Data[i:i+16][14],
                "a": F3DEX2Data[i:i+16][15],
            })
        return toReturn

    # Genereate and return the face data
    def generateFaceData(self, faces):
        toReturn = []
        for i in range(0, len(faces), 4):
            one = int(int(faces[i+1] / 2) + self.line)
            two = int(int(faces[i+2] / 2) + self.line)
            three = int(int(faces[i+3] / 2) + self.line)
            if +one > self.lineCount or +two > self.lineCount or +three > self.lineCount:
                continue
            if one == two == three:
                continue
            toReturn.append("f {}/{} {}/{} {}/{}".format(one, one, two, one, three, one))
        return toReturn

    # Create an OBJ from the ZOBJ file
    def createObj(self):
        obj = []
        self.line = 1
        self.lineCount = 0
        for displayList in self.displayLists:
            if len(displayList['vertexData']) != 0:
                for vertexData in displayList['vertexData']:
                    for vertex in self.generateF3DEX2Dict(vertexData['vertices']):
                        obj.append("v {} {} {}".format(
                            float(vertex['x']),
                            float(vertex['y']),
                            float(vertex['z']))
                        )
                        self.lineCount += 1
                    obj.append("")

                    for face in self.generateFaceData(vertexData['faces']):
                        obj.append(face)
                    obj.append("")
                    self.line = self.lineCount + 1

        with open("{}.obj".format(self.filename), 'w') as fil:
            for line in obj:
                fil.write("{}\n".format(line))


if __name__ == '__main__':
    with open("object_gi_ki_tan_mask.zobj", 'rb') as fil:
        zobj = ZobjFile(fil.read())

    zobj.createObj()
