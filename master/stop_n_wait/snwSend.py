"""
Author: Wesley Reynolds
Student #: 7842362
Course: COMP 4300
Prof: Dr. Rouhani

Description:
    Stop and Wait protocol:
        Continuously send packets until we receive 100 acknowledgmens from the server
        Step:
            Generate a packet
            Send packet
            Wait for ackowledgment
                if we get one, validate it and send the next packet
                if we don't, re-transmit

"""
import string, random, socket, time, pickle, sys
from snwPacket import Packet
#-----------------------------------------------------------------------------------------------------------------------
#Socket global constants
PORT = 1234
SERVER_NAME = 'localhost'
ADDR = (SERVER_NAME, PORT)

#Constants
NUM_MESSAGES = 500 #Number of randomly generated messages
NUM_ATTEMPTS = 100 #Number of acknowledgments we want to receive
SLEEP_TIME = 0.01

#changes in complexity
#CHANGE THESE TO TEST DIFFERENT COMPLEXITIES                            <---------------------
FAIL_PERCENT = 10 #Chance that a packet is dropped

#List
messages = [] #List of randomly generated messages
ACKList = [] #List of ACK'd packets
NAKList = [] #List of NAK'd packets
lostPackets = [] #List of packets that were dropped

#data variables 
sentPacket = 0
packetSize = -1

#-----------------------------------------------------------------------------------------------------------------------
def generateMessages():
    '''
    Randomly generates NUM_MESSAGES and adds them to the messages array
        each message is of size 10 and has random number and letters
    '''
    #Generates a random lowercase string of size 10
    for i in range(NUM_MESSAGES):
        message = string.ascii_lowercase
        message = (''.join(random.choice(message) for j in range(3)))
        messages.append(message)
#-----------------------------------------------------------------------------------------------------------------------
def makePacket(seqNum, data, checksum):
    '''
    Returns a string in the format [message]:[checksum]:
        This is our packet format
    '''
    packet = Packet(PORT, PORT, len(data), checksum, data, seqNum)
    return (packet)

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
    #covert binary to int
    for y in splitChecksum:
        checksumInt += int(y, 2)
    #take the inverse
    checksumReverse = (~checksumInt)
    return (checksumReverse)
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
def sendPacket(packet,clientSocket):
    '''
    Sends our packets over the TCP socket to the receiver
    '''
    #generate a random value between 1-100 for the packet drop
    global sentPacket
    global packetSize

    value = random.randrange(1, 101)

    #If we don't lose the packet, send it
    if(value > FAIL_PERCENT):
        packetString = pickle.dumps(packet)
        #calculate size of the first packet we send
        if (packetSize == -1):
            packetSize = sys.getsizeof(packetString)
        clientSocket.send(packetString)
    elif(len(lostPackets) == FAIL_PERCENT):
        #send the packet if we have enough lost packets already
        #This is for data collection purposes
        packetString = pickle.dumps(packet)
        if (packetSize == -1):
            packetSize = sys.getsizeof(packetString)
        clientSocket.send(packetString)
    sentPacket += 1
    
#-----------------------------------------------------------------------------------------------------------------------
def receivePacket(expSeqNum, lastPacket,clientSocket):
    """
    Wait for an acknowledgment of the last sent packet from gbnRecv
        - Wait two seconds, if we don't receive one, add it to lost packet list
            - Returns false which resets the nextSeqNum to the lost packet seqNum
        - If we do receive it, add it to the ACK list and return True
            - Returning true causes us to send the next packet
    """
    timer = 2
    while timer > 0:
        try:
            #reduce timer
            timer -= 1
            time.sleep(SLEEP_TIME)
            #receive incoming acknowledgments
            message = clientSocket.recv(1024)
            packetVariables = pickle.loads(message)
            if not message:
                pass
            elif (validate(packetVariables) and packetVariables.message == "ACK" and
                    packetVariables.seqNum == expSeqNum):
                    #received correct packet acknowledgment. Add to ACK list
                    ACKList.append(message)
                    return True
            elif(packetVariables.message == "NAK"):
                #checksum failed, so we received NAK
                NAKList.append(message)
                return False
        except:
            if(timer == 0):
                #acknowledgment never arrived
                lostPackets.append(lastPacket)
                return False
#-------------------------------------------------------------------------------
def stopWait(clientSocket):
    """
    Loops through the stop and wait protocol
        - keeps sending packets until 100 acknowledgments are returned
    """
    messageNum = 0
    while messageNum < NUM_ATTEMPTS:
        #generate a 1 or 0 seqNum
        seqNum = messageNum%2
        #create packet
        message = messages[messageNum]
        checksum = makeChecksum(message)
        packet = makePacket(seqNum, message, checksum)
        #send the packet to receiver
        sendPacket(packet,clientSocket)
        if(receivePacket(seqNum, packet,clientSocket)):
            #if we received the ackowledgments, send next packet
            messageNum += 1

#-------------------------------------------------------------------------------

def main():
    # Connect to socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(ADDR)
    clientSocket.setblocking(False)

    print("\n[STARTING]....\n")
    generateMessages()

    start = time.time()
    stopWait(clientSocket)
    end = time.time()

    print(f"[RESULTS].... Packet Loss Chance: {FAIL_PERCENT}%")
    print(f"After {NUM_ATTEMPTS} attempts, {len(ACKList)} messages were ACK'd "
          f"and {len(NAKList)} were NAK'd")

    #lost packets
    print("\nLost Packets:")
    print(f"-------------- {len(lostPackets)} lost packets\n"
          f"-------------- Total waiting time = {round(len(lostPackets)*(SLEEP_TIME*2),3)} seconds")

    #transmission time
    print("\nTransmission Rates:")
    print(f"-------------- Transmission time per packet = {packetSize*8} (bits) / 1,000,000 (bits/second) = "
          f"{(packetSize*8)/1000000} seconds\n"
          f"-------------- Total number of attempts to send packets from Sender/Receiver = {sentPacket*2}\n"
          f"-------------- Total Transmission time = {round(((packetSize*8)/1000000)*(sentPacket*2),3)} seconds\n"
          f"-------------- Total Bandwidth used = {round(((packetSize*8)*(sentPacket*2))/8000000,3)} MB")


    print(f"\nExecution time = {round(end-start,3)} seconds")
    print("\n[ENDING]....\n")
    quit()
#-------------------------------------------------------------------------------
#Comment out to run unit test
main()