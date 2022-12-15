class Packet():
    srcPort = 0
    dstPort = 0
    length = 0
    checksum = 0
    message = 0
    seqNum = 0
    def __init__(self, srcPort, dstPort, length, checksum, message, seqNum):
        self.srcPort = srcPort
        self.dstPort = dstPort
        self.length = length
        self.checksum = checksum
        self.message = message
        self.seqNum = seqNum