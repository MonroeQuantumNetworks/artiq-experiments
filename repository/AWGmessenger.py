"""
2020-09-25
@author: George
This contains the function to send a message to Glados to run the AWG.

Import this script to other Artiq scripts with "from AWGmessenger import sendmessage"
Call by writing "sendmessage(self, ....)
"""

def sendmessage(self, type = "quit", channel = 1, amplitude1 = 0.1, amplitude2 = 0.1, frequency1 = 83e6, frequency2 = 77e6, phase1=0, phase2=0, duration1 = 2000, duration2 = 0, pause1 =0, pause2 = 0):

    import sys
    from socket import socket, AF_INET, SOCK_DGRAM

    SERVER_IP   = '192.168.1.101'
    PORT_NUMBER = 10050
    SIZE = 1024
    print ("Test client sending packets to IP {0}, via port {1}".format(SERVER_IP, PORT_NUMBER))

    mySocket = socket( AF_INET, SOCK_DGRAM )

        # Message format: XXXX-Y-ZZZ-AAAAAAAA
        # Type = sine, sin2 or wave
        # channel = int(data2[1])     # 1 digit
        # amplitude = int(data2[2])   # (mV)
        # frequency = int(data2[3])   # (Hz)

    # Example messages
    # message-sine = "sine-1-100-20000000"
    # message-sin2 = "sin2-1-100-100-20000000-20000000-3.14"
    # message-wave = "wave-1-100-100-8e6-77e5-0-0-1000-0-0"
    # message-quit = "quit"

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
        + "-" + str(int(phase1*100000))     # We convert to int for transmission so *100000 gives 6 digits of resolution
        + "-" + str(int(phase2*100000))
        + "-" + str(int(duration1))
        + "-" + str(int(duration2))
        + "-" + str(int(pause1))
        + "-" + str(int(pause2))
        )
    elif type == "quit":
        message = "quit"
        
    elif type == "flush":
        message = "flush"

    print('Sending', message)
    i = 0
    while i < 1:
        mySocket.sendto(message.encode('utf-8'),(SERVER_IP,PORT_NUMBER))
        i = i + 1

    # sys.exit()

# Some examples to use sendmessage()

    # sendmessage(self)   # Writing nothing sends a quit

    # sendmessage(self,
    #             type = "wave",
    #             channel = self.channel,
    #             amplitude1 = self.amplitude1,
    #             amplitude2 = self.amplitude2,
    #             frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
    #             frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
    #             phase1 = self.phase,                                    # radians
    #             phase2 = self.phase_diff,  # radians
    #             duration1 = self.duration1,                             # ns
    #             duration2 = self.duration2,                             # ns
    #             pause1 = self.pause_before
    #             pause2 = self.pause_after
    #             )

    # sendmessage(self,
    #             type = "sine",
    #             channel = self.channel,
    #             amplitude1 = self.amplitude1,
    #             frequency1 = self.DDS__532__Alice__tone_1__frequency
    #             )

    # sendmessage(self,
    #             type = "sin2",
    #             channel = self.channel,
    #             amplitude1 = self.amplitude1,
    #             amplitude2 = self.amplitude2,
    #             frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
    #             frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
    #             )