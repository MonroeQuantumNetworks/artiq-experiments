"""
2020-09-23
@author: George
This contains the function to send a message to Jarvis to run the AWG.

"""

def sendmessage(self, type = "quit", channel = 1, amplitude1 = 0.1, amplitude2 = 0.1, frequency1 = 83e6, frequency2 = 77e6, phase1=0, phase2=0, duration1 = 2000, duration2 = 0, pause = 0):

    import sys
    from socket import socket, AF_INET, SOCK_DGRAM

    # class awg_client():       # Don't worry about classes until later

    SERVER_IP   = '192.168.1.101'
    PORT_NUMBER = 10050
    SIZE = 1024
    print ("Test client sending packets to IP {0}, via port {1}".format(SERVER_IP, PORT_NUMBER))

    mySocket = socket( AF_INET, SOCK_DGRAM )

        # Message format: XXXX-Y-ZZZ-AAAAAAAA
        # Type = sine or wave
        # channel = int(data2[1])     # 1 digit
        # amplitude = int(data2[2])   # (mV)
        # frequency = int(data2[3])   # (Hz)

    # Example messages
    message1 = "sine-1-100-20000000"
    message2 = "wave-1-100-5e6-2e6-1000-0-0"
    messageq = "quit"

    if type == "sine":          # Continuous sine output with 1 frequency
        message = ("sine-" + str(channel)
        + "-" + str(int(amplitude1*1000))
        + "-" + str(int(frequency1))
        )
    elif type == "sin2":        # Continuous sine output with 2 frequencies
        message = ("sin2-" + str(channel)
        + "-" + str(int(amplitude1*1000))
        + "-" + str(int(amplitude2*1000))
        + "-" + str(int(frequency1))
        + "-" + str(int(frequency2))
        + "-" + str(int(phase1))
        )
    elif type == "wave":        # Pulsed sine output with 2 frequencies, can have a second pulse after pause
        message = ("wave-" + str(channel)
        + "-" + str(int(amplitude1*1000))
        + "-" + str(int(amplitude2*1000))
        + "-" + str(int(frequency1))
        + "-" + str(int(frequency2))
        + "-" + str(int(phase1*100000))
        + "-" + str(int(phase2 * 100000))
        + "-" + str(int(duration1))
        + "-" + str(int(duration2))
        + "-" + str(int(pause))
        )
    elif type == "quit":
        message = "quit"

    print('Sending', message)
    i = 0
    while i < 1:
        mySocket.sendto(message.encode('utf-8'),(SERVER_IP,PORT_NUMBER))
        i = i + 1

    # sys.exit()
