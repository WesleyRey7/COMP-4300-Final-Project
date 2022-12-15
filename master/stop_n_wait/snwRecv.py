"""
Author: Wesley Reynolds
Student #: 7842362
Course: COMP 4300
Prof: Dr. Rouhani

Description:
    Stop and wait protocol:
        This is the server side, it opens an TCP socket and waits for a connection
        Once connected, it replies with acknowledgments to received packets
        Steps:
            receive packet
            validate checksum
                if it passes, make and send positive acknowledgment
                if it does, make and send negative acknowledgment
            wait for next packet
"""
import socket, pickle
from snwPacket import Packet
#---------------------------------GLOBALS-------------------------------------------------------------------------------
#Socket global constants
SERVER_NAME = 'localhost'
SERVER_PORT = 1234
ADDR = (SERVER_NAME, SERVER_PORT)

#create Socket
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind(ADDR)
#-----------------------------------------------------------------------------------------------------------------------
def validate(packet):
    """
    Make sure that the received message has not been corrupt
    """
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
    print(f"{packet.seqNum} Failed validation")
    return False
#-----------------------------------------------------------------------------------------------------------------------
def sendPacket(packet, conn):
    conn.send(pickle.dumps(packet))
#-----------------------------------------------------------------------------------------------------------------------
def makePacket(packet, acknowledgment, checksum):
    """
    Make the acknowledgment packet
    """
    packet = Packet(SERVER_PORT, SERVER_PORT, len(acknowledgment),
                    checksum, acknowledgment, packet.seqNum)
    return packet
#-----------------------------------------------------------------------------------------------------------------------
def makeChecksum(message):
    """
    Creates and returns the checksum
        checksum is two compliment of the message
    """
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
def expectedPacket(packet, expectedSeqNum):
    """
    Returns true if we receive the packet with the expected sequence number
    """
    if packet.seqNum == expectedSeqNum:
        return True
    return False
#-----------------------------------------------------------------------------------------------------------------------
def handleClient(conn):
    numPackets = 0
    try:
        while True:
            expectedSeqNum = numPackets % 2
            packet = conn.recv(1024)
            if not packet:
                return False
            else:
                packetVariables = pickle.loads(packet)
                if(validate(packetVariables)):
                    checksum = makeChecksum("ACK")
                    packet = makePacket(packetVariables, "ACK", checksum)
                    sendPacket(packet, conn)
                    if expectedPacket(packetVariables, expectedSeqNum):
                        numPackets += 1
                else:
                    checksum = makeChecksum(packetVariables)
                    packet = makePacket(packetVariables, "NAK", checksum)
                    sendPacket(packet, conn)
    finally:
        print("Connection Closed")
        conn.close()
        return False
#-----------------------------------------------------------------------------------------------------------------------
def main():
    '''
    Accepts incoming connections over the TCP socket
    '''
    print("[STARTING]....")
    serverSocket.listen()
    print(f"Listening for conenction on {ADDR}")
    #waiting for incoming clients

    conn, addr = serverSocket.accept()
    print(f"connected to {conn}:{addr}")
    handleClient(conn)
    print("[ENDING]...")
#-----------------------------------------------------------------------------------------------------------------------
#Comment out to run unit test
main()