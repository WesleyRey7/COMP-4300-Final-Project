"""
Author: Wesley Reynolds
Student #: 7842362
Course: COMP 4300
Prof: Dr. Rouhani

Description:
    Selective_Repeat Protocol:
    Sends packets until we receive 100 acknowledgments from the server
    Steps:
        Create a thread that waits for incoming messages
        Make and send packets until the window is full
            each packet has their own timer thread
            if the timer finishes, it will resend the packet
        if we receive an acknowledgment for a packet
            if its the base, remove it and find the next sequence number in the window that hasnt been acknowledged
            if its not the base, note that it has been acknowledged
"""

import string, random, socket, time, pickle, threading
import sys

from srPacket import Packet
#-----------------------------------------------------------------------------------------------------------------------
# Socket global constants
PORT = 1234
SERVER_NAME = 'localhost'
ADDR = (SERVER_NAME, PORT)

WAIT_TIME = 0.2
NUM_MESSAGES = 500
NUM_ATTEMPTS = 100
messages = []

#list of packets/seqNums
ACKList = []
NAKList = []
lostPackets = []
retransmitList = []
window = []

#window variables 
base = 0
nextSeqNum = 0
expSeqNum = 0

#Complexity Variables
#CHANGE THESE TO TEST DIFFERENT COMPLEXITIES                  <---------------------
LOSE_PERCENT = 10
WINDOW_SIZE = 5

#used for data collection
packetSize = -1
sentPackets = 0

#socket variables
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket.setblocking(False)

#Locks for threads
retransmitListLock = threading.Lock()
windowLock = threading.Lock()
ACKLock = threading.Lock()
lostPacketLock = threading.Lock()
socketLock = threading.Lock()


#-----------------------------------------------------------------------------------------------------------------------
def generateMessages():
    '''
    Randomly generates NUM_MESSAGES and adds them to the messages array
        each message is of size 10 and has random number and letters
    '''
    # Generates a random lowercase string of size 10
    for i in range(NUM_MESSAGES):
        message = string.ascii_lowercase
        message = (''.join(random.choice(message) for j in range(3)))
        messages.append(message)

def plusOne(self, value):
    return value+1
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
    checksumInt = 0
    checksumReverse = 0
    splitChecksum = ""

    checksum = (' '.join(format(ord(x), 'b') for x in packet.message))
    splitChecksum = checksum.split(" ")
    for y in splitChecksum:
        checksumInt += int(y, 2)
    checksumReverse = (~checksumInt)

    if (checksumReverse == packet.checksum):
        return True
    return False
#-----------------------------------------------------------------------------------------------------------------------
def sendPacket(packet):
    '''
    Sends our packets over the TCP socket to the receiver
    '''
    global packetSize
    global sentPackets

    lost = random.randint(1,101)
    sentPackets += 1

    #send packet if we don't lose it
    if(lost > LOSE_PERCENT):
        packetString = pickle.dumps(packet)
        #get the size of a packet (in bytes)
        if packetSize == -1:
            packetSize = sys.getsizeof((packetString))

        #send over TCP conenction
        clientSocket.send(packetString)

    #send it anyway to meet out exact percent for data collection
    with lostPacketLock:
        if(len(lostPackets) >= LOSE_PERCENT):
            packetString = pickle.dumps(packet)
            clientSocket.send(packetString)


#-----------------------------------------------------------------------------------------------------------------------
def receivePacket():
    global base
    global nextSeqNum
    while True:
        try:
            message = clientSocket.recv(1024)
            packetVariables = pickle.loads(message)
            if not message:
                pass
            elif (validate(packetVariables) and packetVariables.message == "ACK"):
                with ACKLock:
                    if packetVariables.seqNum not in ACKList:
                        ACKList.append(packetVariables.seqNum)
                #increase the base to the next
                if(int(packetVariables.seqNum) == int(base)):
                    #change base and check if new base has already been ACK'd
                    sent = True
                    while sent:
                        with windowLock:
                            window.pop(0)
                            #increment the window
                            if(len(window) > 0):
                                base = window[0]
                            else:
                                base += 1
                        #check if our new base has already been ACK'd
                        if int(base) not in ACKList:
                            sent = False
            elif (packetVariables.message == "NAK"):
                NAKList.append(message)
        except:
            pass
#-----------------------------------------------------------------------------------------------------------------------
def startTimer(packet):
    """
    Each packet needs their own timer
    """

    #Packet was never acknowledged. Resend and restart the timer
    ACKLock.acquire()
    if packet.seqNum not in ACKList:
        ACKLock.release()
        with lostPacketLock:
            lostPackets.append(packet.seqNum)
        sendPacket(packet)

        # start a timer that will resend lost packets
        timerThread = threading.Timer(WAIT_TIME, startTimer, [packet])
        timerThread.daemon = True
        timerThread.start()
    else:
        ACKLock.release()

#-----------------------------------------------------------------------------------------------------------------------
def SR():
    attemptNum = 0
    global nextSeqNum
    global base
    global expSeqNum
    timerThread = None

    while nextSeqNum < NUM_ATTEMPTS:
        message = messages[nextSeqNum]
        #send a new packet
        windowLock.acquire()
        if (nextSeqNum < base + WINDOW_SIZE):
            windowLock.release()
            checksum = makeChecksum(message)
            packet = makePacket(nextSeqNum, message, checksum)
            with windowLock:
                window.append(nextSeqNum)
            sendPacket(packet)

            # start a timer that will resend lost packets
            timerThread = threading.Timer(WAIT_TIME, startTimer, [packet])
            timerThread.daemon = True
            timerThread.start()

            nextSeqNum += 1
        #refuse to send because window is full
        else:
            windowLock.release()

#-----------------------------------------------------------------------------------------------------------------------
def main():
    # Connect to socket
    try:
        clientSocket.connect(ADDR)
    except Exception as e:
        print(f"Failed to conenct to TCP socket. Exception: {e}")

    #generate NUM_MESSAGE random messages
    generateMessages()

    # start another thread to receive messages from the server
    receiveThread = threading.Thread(name="receiver",target=receivePacket)
    receiveThread.daemon = True
    receiveThread.start()

    print("\n[STARTING]....")
    start = time.time()
    SR()
    end = time.time()

    time.sleep(1)
    # Print results
    print(f"\n[RESULTS]: Window Size = {WINDOW_SIZE}, Lose Percentage = {LOSE_PERCENT}")
    print(f"After {NUM_ATTEMPTS} expected ACK/NAK, {len(ACKList)} messages were ACK'd "
          f"and {len(NAKList)} were NAK'd.")

    # lost packets
    print(f"There were {len(lostPackets)} lost packets that were re-transmitted")

    # transmission time
    print("\nTransmission Rates:")
    print(f"-------------- Transmission time per packet = {packetSize * 8} (bits) / 1,000,000 (bits/second) = "
          f"{(packetSize * 8) / 1000000} seconds\n"
          f"-------------- Total number of attempts to send packets from Sender/Receiver = {sentPackets * 2}\n"
          f"-------------- Total Transmission time = {round(((packetSize * 8) / 1000000) * (sentPackets * 2), 3)} seconds\n"
          f"-------------- Total Bandwidth used = {round(((packetSize * 8) * (sentPackets * 2)) / 8000000, 3)} MB")

    # execution time
    print(f"\nExecution time = {round(end - start, 3)} seconds")
    print("\n[ENDING]....\n")

    clientSocket.close()
    quit()
#-----------------------------------------------------------------------------------------------------------------------
#Comment out to run unit test
main()