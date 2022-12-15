"""
Author: Wesley Reynolds
Student #: 7842362
Course: COMP 4300
Prof: Dr. Rouhani

Description:
    Implements the GBN protocol for reliable data transfer.
    Generate 500 random messages sends packets to gbnRecv server until it receives 100 acknowledgments
        - Packet are gbnPacket objects
    Steps:
        Create a thread that waits for received messages from the server
        Loop through:
            Make and send a packet until window is full
            The base packet has a timer
                if the timer finishes, resend the entire window
        When we receive a packet:
            Validate it to make sure it's not corrupt
            If it's the base packet, remove it from the window and stop the timer
                Otherwise, ignore it
            Wait for the next packet
"""

import string, random, socket, time, pickle, threading, sys
from gbnPacket import Packet

#-----------------------------------------------------------------------------------------------------------------------
#Socket global constants
PORT = 1234
SERVER_NAME = 'localhost'
ADDR = (SERVER_NAME, PORT)

#constants
WAIT_TIME = 0.02 #Time to wait for ACK/NAK
NUM_MESSAGES = 500 #total number of generated messages
NUM_ATTEMPTS = 100 #number of expected ACK/NAK we want
messages = [] #list of randomly generated messages

#Arrays of packets
ACKList = [] #list of all ACK'd packages
NAKList = [] #list of all NAK'd packages
lostPackets = [] #List of all lost packets (their seqNum)
window = [] #list of packets currently in the window
retransmitted = [] #list of all packets that were retransmitted

#changes in complexity
#CHANGE THESE TO TEST DIFFERENT COMPLEXITIES                  <---------------------
WINDOW_SIZE = 5 #fixed window size
LOSE_PERCENT = 10 #% chance for sender to lose packet

#window variables
base = 0 #current base packet seqNum in window
nextSeqNum = 0 #seqNum of next packet to be sent
expSeqNum = 0 #the expected seqNum we should receive

#used for final data
sentPacket = 0 #total number of packets sent by Sender (2x for sender/receiver system)
discardedPacket = 0 #total number of discarded packets (out of order)
packetSize = -1 #total size of the first packet we send (in bytes)

#Thread locks
ACKLock = threading.Lock() #lock for ACKlist
windowLock = threading.Lock() #lock for window
seqNumLock = threading.Lock() #lock for nextSeqNum
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
    Generates a checksum for a given message
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

    if(checksumReverse == packet.checksum):
        return True
    print(f"{packet.seqNum} Failed validation")
    return False
#-----------------------------------------------------------------------------------------------------------------------

def sendPacket(packet, clientSocket):
    '''
    Sends our packets over the TCP socket to the receiver
        there is a LOSE_PERCENT chance the packet is lost
    '''
    global window
    global packetSize

    percent = random.randint(1,101)
    packetString = pickle.dumps(packet)
    #calculates the size of a packet in bytes
    if(packetSize == -1):
        packetSize = sys.getsizeof(packetString)

    #Send the packet as long as it didn't get lost
    if(percent > LOSE_PERCENT):
        clientSocket.send(packetString)
    #send the packet if we already have enough lost packets
    elif(len(lostPackets) == LOSE_PERCENT):
        clientSocket.send(packetString)
#-----------------------------------------------------------------------------------------------------------------------
def receivePacket(clientSocket):
    """
    A thread that is waiting for received packets from Receiver
        Remove base from window if we receive expected packet
        Increments discardedPacket if we receive unexpected packet
    """
    global base
    global nextSeqNum
    global window
    global discardedPacket

    while True:
        try:
            #receive packet
            message = clientSocket.recv(1024)
            packetVariables = pickle.loads(message)
            if not message:
                pass
            #check the checksum and message type
            elif validate(packetVariables) and packetVariables.message == "ACK":
                windowLock.acquire()
                #if the packet is our base, increment window, add packet to ACK list
                if (int(packetVariables.seqNum) == int(window[0].seqNum)):
                    window.pop(0)
                    windowLock.release()
                    ACKList.append(packetVariables.seqNum)
                    base += 1
                #Discard out of order packets
                else:
                    discardedPacket += 1
                    windowLock.release()
            #Add packet to NAK list
            elif(packetVariables.message == "NAK"):
                NAKList.append(message)

        except:
            pass
#-----------------------------------------------------------------------------------------------------------------------
def startTimer(packet):
    """
    Waits WAIT_TIME before checking if the base is still the same
        If the base is the same, reset nextSeqNum to base to resend the entire window
    """
    global nextSeqNum
    global window
    with windowLock:
        if(len(window)>0):
            if int(window[0].seqNum) == int(packet.seqNum):
                with seqNumLock:
                    nextSeqNum = packet.seqNum
                lostPackets.append(packet.seqNum)
#-----------------------------------------------------------------------------------------------------------------------
def GBN(clientSocket):

    """
    Sends messages until there are NUM_ATTEMPTS ACK'd or NAK'd packets
    """
    #globals
    global nextSeqNum
    global base
    global expSeqNum
    global window
    global sentPacket
    global ACKList
    global NAKList
    global WINDOW_SIZE
    global lostPackets

    #reset for new run
    resend = False
    sentPacket = 0
    window = []
    expSeqNum = 0
    base = 0
    nextSeqNum = 0
    ACKList = []
    NAKList = []
    lostPackets = []
    timerThread = None

    while nextSeqNum < NUM_ATTEMPTS or (len(ACKList)+len(NAKList)) < 100:
        resend = False
        seqNumLock.acquire()
        message = messages[nextSeqNum]
        #if the window is not full, send a packet to Receiver
        if(nextSeqNum < base+WINDOW_SIZE):
            #make a packet
            checksum = makeChecksum(message)
            packet = makePacket(nextSeqNum, message, checksum)
            seqNumLock.release()

            #Add the packet to the window if we are not retransmitting it
            with windowLock:
                for x in window:
                    if x.seqNum == packet.seqNum:
                        resend = True
                if not resend:
                    window.append(packet )
                elif resend:
                    retransmitted.append(packet)

            #send the packet
            sendPacket(packet, clientSocket)
            sentPacket += 1

            #start a timer if it's our base
            seqNumLock.acquire()
            if base == nextSeqNum:
                seqNumLock.release()
                # start a timer that will resend lost packets
                timerThread = threading.Timer(WAIT_TIME, startTimer, [packet])
                timerThread.daemon = True
                timerThread.start()

            if seqNumLock.locked():
                seqNumLock.release()

            with seqNumLock:
                nextSeqNum += 1

        #window is full, refuse sending data
        else:
            seqNumLock.release()
    timerThread.join()
#-----------------------------------------------------------------------------------------------------------------------
def main():
    # Connect to socket
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.connect(ADDR)
    clientSocket.setblocking(False)

    #generates 500 random messages
    generateMessages()

    # start another thread to receive messages from the server
    receiveThread = threading.Thread(target=receivePacket, args=[clientSocket])
    receiveThread.daemon = True
    receiveThread.start()

    print("\n[STARTING]....\n")
    #start timer and run GBN protocol
    start = time.time()
    GBN(clientSocket)
    end = time.time()

    #Print results
    print(f"\n\n[RESULTS]: Window Size = {WINDOW_SIZE}, Lose Percentage = {LOSE_PERCENT}")
    print(f"After {NUM_ATTEMPTS} expected ACK/NAK, {len(ACKList)} messages were ACK'd "
          f"and {len(NAKList)} were NAK'd.")

    #lost packets
    print(f"\nThere were {len(lostPackets)} lost packets:\n"
          f"-------------- Number of retransmitted packet from Sender = {len(retransmitted)}")

    #transmission time
    print("\nTransmission Rates:")
    print(f"-------------- Transmission time per packet = {packetSize*8} (bits) / 1,000,000 (bits/second) = "
          f"{(packetSize*8)/1000000} seconds\n"
          f"-------------- Total number of attempts to send packets from Sender/Receiver = {sentPacket*2}\n"
          f"-------------- Total Transmission time = {round(((packetSize*8)/1000000)*(sentPacket*2),3)} seconds\n"
          f"-------------- Total Bandwidth used = {round(((packetSize*8)*(sentPacket*2))/8000000,3)} MB")

    #wasted time
    print("\nWasted Packets:")
    print(f"-------------- There were {discardedPacket} packets ACK'd out of order\n"
          f"-------------- That wasted {round(((packetSize*8/1000000)*(discardedPacket*2)),3)} seconds")

    #execution time
    print(f"\nExecution time = {round(end-start,3)} seconds")
    print("\n[ENDING]....\n")
    time.sleep(2)
    quit()
#-----------------------------------------------------------------------------------------------------------------------
#Comment out to run unit test
main()