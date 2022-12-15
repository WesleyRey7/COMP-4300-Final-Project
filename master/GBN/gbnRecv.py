"""
Author: Wesley Reynolds
Student #: 7842362
Course: COMP 4300
Prof: Dr. Rouhani

Description:
    Server side for the GBN protocol
    Open a tcp socket and wait for a connection
    Once a client is connected, sent acknowledgments for received packets
    When we receive a packet:
        Validate it:
            if it's not corrupt, make and send positive acknowledgment
            otherwise, make and send negative acknowledgment
"""
import socket, pickle, random
from gbnPacket import Packet
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
    Validatess a received packets checksum
    """
    checksumInt = 0
    checksumReverse = 0
    splitChecksum = ""

    checksum = (' '.join(format(ord(x), 'b') for x in packet.message))
    splitChecksum = checksum.split(" ")
    for y in splitChecksum:
        checksumInt += int(y, 2)
    checksumReverse = (~checksumInt)

    #return results of the checksum validation
    if(checksumReverse == packet.checksum):
        return True
    return False
#-----------------------------------------------------------------------------------------------------------------------
def sendPacket(packet, conn):
    '''
    Sends our packets over the TCP socket to the receiver
    '''
    percent = random.randint(1,101)
    conn.send(pickle.dumps(packet))



#-----------------------------------------------------------------------------------------------------------------------
def makePacket(seqNum, acknowledgment, checksum):
    """
    Make a new gbnPacket object
    """
    packet = Packet(SERVER_PORT, SERVER_PORT, len(acknowledgment),
                    checksum, acknowledgment, seqNum)
    return packet
#-----------------------------------------------------------------------------------------------------------------------
def makeChecksum(message):
    """
    Generates a checksum for a given packet
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
def handleClient(conn):
    """
    Wait for packets to be sent from the sender
        If they are in a valid range and not corrumpted, send and ACK
        otherwise, discard or send NAK, resectfully
    """
    base = 0
    try:
        while True:
            #wait for packet
            packet = conn.recv(1024)
            packetVariables = pickle.loads(packet)
            #validate with checksum
            if validate(packetVariables):
                #make and send packet
                checksum = makeChecksum("ACK")
                packet = makePacket(packetVariables.seqNum, "ACK", checksum)
                sendPacket(packet, conn)
                #increase the base if we receive the base
                if packetVariables.seqNum == base:
                    base += 1
            #corrupted packet, send a NAK
            else:
                checksum = makeChecksum("NAK")
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
    serverSocket.listen()
    print(f"Listening for conenction on {ADDR}")

    #waiting for incoming clients
    conn, addr = serverSocket.accept()
    print(f"connected to {conn}:{addr}")
    handleClient(conn)
#-----------------------------------------------------------------------------------------------------------------------
#Comment out to run unit test
main()