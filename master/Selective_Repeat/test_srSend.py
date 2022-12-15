import unittest
import srSend
import srPacket
import socket

class TestSend(unittest.TestCase):
    def run_fake_server(self):
        SERVER_NAME = 'localhost'
        SERVER_PORT = 1235
        ADDR = (SERVER_NAME, SERVER_PORT)

        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(ADDR)
        serverSocket.listen(0)
        serverSocket.accept()
        serverSocket.close()

    def test_generateMessage(self):
        srSend.generateMessages()
        #Correct number of messages generated
        self.assertEqual(len(srSend.messages), srSend.NUM_MESSAGES)

    def test_makePacket(self):
        #make sure packet is being generated correctly
        packet = srSend.makePacket(0,"hey",0)
        self.assertEqual(packet.srcPort, 1234)
        self.assertEqual(packet.dstPort,1234)
        self.assertEqual(packet.message, "hey")
        self.assertEqual(packet.seqNum, 0)
        self.assertEqual(packet.checksum, 0)
        self.assertEqual(packet.length, len("hey"))

    def test_makeChecksum(self):
        result = srSend.makeChecksum("0")
        checksum = (' '.join(format(ord(x), 'b') for x in "0"))
        self.assertEqual(result, ~(int(checksum,2)))

    def test_validate(self):
        checksum = (' '.join(format(ord(x), 'b') for x in "0"))
        checksum = ~(int(checksum,2))
        packet = srPacket.Packet(0,0,0,checksum,"0",0)
        result = srSend.validate(packet)
        self.assertEqual(result, True)

if __name__ == '__main__':
    unittest.main()