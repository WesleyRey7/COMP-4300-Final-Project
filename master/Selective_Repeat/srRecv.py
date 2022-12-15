"""
Author: Wesley Reynolds
Student #: 7842362
Course: COMP 4300
Prof: Dr. Rouhani

Description:
    Selective_Repeat Protocol:
    Opens a TCP socket and waits for a connection
    Once connected, send acknowledgments for receivec packets
    Steps:
        Receive packet and validate it
            if validated, make and send ACK packet
            if not validated, make and send NAK packet
        If we receive a packet out of order, buffer it
            Once we received the base packet, remove all buffered packets
        Ignore any packets that are out of range of the window
"""
import socket, pickle
from srPacket import Packet

#---------------------------------GLOBALS-------------------------------------------------------------------------------
#Socket global constants
SERVER_NAME = 'localhost'
SERVER_PORT = 1234
ADDR = (SERVER_NAME, SERVER_PORT)
DISCONNECT = "!QUIT"

WINDOW_SIZE = 5
bufferedPacket = []
#-----------------------------------------------------------------------------------------------------------------------
def validate(packet):
    checksumInt = 0
    checksumReverse = 0
    splitChecksum = ""

    checksum = (' '.join(format(ord(x), 'b') for x in packet.message))
    splitChecksum = checksum.split(" ")
    for y in splitChecksum:
        checksumInt += int(y, 2)
    checksumReverse = (~checksumInt)
    if(checksumReverse == packet.checksum):
        return True
    return False
#-----------------------------------------------------------------------------------------------------------------------
def sendPacket(packet, conn):
    conn.send(pickle.dumps(packet))
#-----------------------------------------------------------------------------------------------------------------------
def makePacket(packet, acknowledgment, checksum):
    packet = Packet(SERVER_PORT, SERVER_PORT, len(acknowledgment),
                    checksum, acknowledgment, packet.seqNum)
    return packet
#-----------------------------------------------------------------------------------------------------------------------
def makeChecksum(message):
    checksumInt = 0
    checksumReverse = 0
    splitChecksum = ""

    checksum = (' '.join(format(ord(x), 'b') for x in message))
    splitChecksum = checksum.split(" ")
    for y in splitChecksum:
        checksumInt += int(y, 2)
    checksumReverse = (~checksumInt)

    return (checksumReverse)
#-----------------------------------------------------------------------------------------------------------------------
def addFromBuffer(currSeqNum):
    match = True
    found = False
    addedNumber = 0
    while match:
        for x in bufferedPacket:
            if x.seqNum == currSeqNum+addedNumber+1:
                addedNumber += 1
                bufferedPacket.remove(x)
                found = True
                break
        if found:
            found = False
        else:
            match = False
    return addedNumber
#-----------------------------------------------------------------------------------------------------------------------
def handleClient(conn):
    base = 0

    try:
        while True:
            expectedSeqNum = base
            packet = conn.recv(1024)
            packetVariables = pickle.loads(packet)
            #make sure it's within the range [base, base+windowSize-1]
            if (packetVariables.seqNum in range(base-WINDOW_SIZE, WINDOW_SIZE+base)):
                #checksum validation
                if validate(packetVariables):
                    #create and send the ACK
                    checksum = makeChecksum("ACK")
                    packet = makePacket(packetVariables, "ACK", checksum)
                    sendPacket(packet, conn)
                    #If this packet is the base, increase our base and check buffer
                    if packetVariables.seqNum == expectedSeqNum:
                        base += addFromBuffer(expectedSeqNum) + 1
                    #if this packet is not the base, add it to the buffer
                    elif packetVariables.seqNum in range(base, base+WINDOW_SIZE):
                        bufferedPacket.append(packetVariables)
                #checksum failed, send a NAK
                else:
                    checksum = makeChecksum("NAK")
                    packet = makePacket(packetVariables, "NAK", checksum)
                    sendPacket(packet, conn)
            else:
                print(f"Ignored {packetVariables.seqNum}. Not in range 0-{WINDOW_SIZE+base-1}")

    finally:
        print("Connection Closed")
        conn.close()
        return False
#-----------------------------------------------------------------------------------------------------------------------
def main():
    '''
    Accepts incoming connections over the TCP socket
    '''
    # create Socket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(ADDR)
    serverSocket.listen()
    print(f"Listening for conenction on {ADDR}")

    #waiting for incoming clients
    conn, addr = serverSocket.accept()
    print(f"connected to {conn}:{addr}")
    handleClient(conn)
#-----------------------------------------------------------------------------------------------------------------------
#Comment out to run unit test
main()