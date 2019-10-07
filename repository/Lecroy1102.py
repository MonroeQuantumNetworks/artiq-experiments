import numpy as np
import base_experiment

import logging
import socket  # for TCP communication
import struct  # for TCP message formatting
import sys
import time
from ctypes import *

logger = logging.getLogger(__name__)

class Lecroy1102():
    """Class for programming a Lecroy 1102 AWG"""
    display_name = "Lecroy 1102 AWG"
    min_samples = 8  # minimum number of samples to program
    max_samples = 2000000  # maximum number of samples to program
    sample_chunk_size = 2  # number of samples must be a multiple of sample_chunk_size
    pad_value = 0  # the waveform will be padded with this number to make it a multiple of sample_chunk_size, or to make it the length of min_samples
    min_amplitude = -5  # minimum amplitude value (raw)
    max_amplitude = +5  # maximum amplitude value (raw)
    num_channels = 2  # number of channels
    calibration = lambda voltage: voltage  # function that returns raw amplitude number, given voltage
    calibrationInv = lambda raw: raw #function that returns voltage, given raw amplitude number

    def __init__(self, IP_address, port, sample_rate, ext_clock_frequency):
        print('__init__()')

        self.enabled = False
        self.IP_address = IP_address
        self.port = port
        self.sample_rate = sample_rate
        self.ext_clock_frequency = ext_clock_frequency
        self.sample_length = 1.0/self.sample_rate

    def send(self, command_string):
        print('send()')

        # Send a well formatted message to the server.
        # The server must be running, and this instance must already have called connect().
        # Each message begins with MESG,
        # followed by 4 bytes (a 32 bit unsigned long integer) that give the length of the rest of the message,
        # followed by the rest of the message (command_string).

        # find the length of the command_string
        length = len(command_string)
        if length>=4294967296: #2**32
            logger.error('Lecroy AWG TCP message is too long, size = '+str(length)+' bytes')

        # format the message
        message = b'MESG'+struct.pack("!L", length)+command_string

        # send the message
        self.sock.sendall(message)

    def open(self):
        print('open()')

        try:

            # set up TCP connection
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.sock.settimeout(1)

            print('trying connection')

            # Open a connection to the TCP server.
            # The server should already be running at the given IP address.
            # The port numbers must agree between the client and server.
            self.sock.connect((self.IP_address, self.port))

            print('connected')

            # message format:
            # MESG
            # 4 byte data length
            # CONF
            # command_string:
            #   4 byte command name
            #     4 byte command length
            #     command data
            #  repeat until done

            # start with a blank command string
            command_string = b'CONF'

            # sample rate: 4 byte command + 8 byte double
            command_string += b'rate'
            # convert double to byte encoding, and append to message
            command_string += struct.pack('!d', self.sample_rate)  # sample rate in Hz

            # external_clock_frequency: 4 byte command + 8 byte double
            command_string += b'eclk'
            # convert double to byte encoding, and append to message
            command_string += struct.pack('!d', self.ext_clock_frequency)

            self.send(command_string)

            self.enabled = True
            print("Successfully opened {0}".format(self.display_name))
        except Exception as e:
            logger.error("Unable to open {0}: {1}".format(self.display_name, e))
            self.enabled = False
        return self.enabled

    def program(self, waveform1, waveform2):
        print('program()')

        if self.enabled:

            for waveform in [waveform1, waveform2]:
                if len(waveform) < self.min_samples:
                    waveform = np.append(waveform, (self.min_samples - len(waveform)) * [self.pad_value])
                    logger.warning("Lecroy1102.program(): Sequence is too short.  Padding.")
                remainder = len(waveform) % self.sample_chunk_size
                if remainder != 0:
                    waveform = np.append(waveform, remainder * [self.pad_value])
                    logger.warning("Lecroy1102.program(): Sequence length is not a multiple of sample_chunk_size.  Padding.")
                if len(waveform) > self.max_samples:
                    logger.warning("Lecroy1102.program(): Sequence length exceeds max_samples. Truncating.")
                if np.amin(waveform) < self.min_amplitude:
                    waveform[waveform < self.min_amplitude] = self.min_amplitude
                if np.amax(waveform) > self.max_amplitude:
                    waveform[waveform > self.max_amplitude] = self.max_amplitude

            print("channel_0_points.dtype:"+str(waveform1.dtype))
            print("channel_1_points.dtype:"+str(waveform2.dtype))
            print("writing {0} points to AWG channel 0".format(len(waveform1)) )
            print("writing {0} points to AWG channel 1".format(len(waveform2)) )

            # send waveforms over TCP to Lecroy C# server

            command_string = b'UPDA'
            command_string += struct.pack('!L', len(waveform1))
            command_string += waveform1.astype('<f8').tobytes()
            command_string += struct.pack('!L', len(waveform2))
            command_string += waveform2.astype('<f8').tobytes()

            self.send(command_string)

            print('command sent')

            time.sleep(1.5)  # wait 1.5 second for AWG programming to complete

            print('sleep done')

        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.display_name))

    def trigger(self):
        print('trigger()')
        if self.enabled:
            # SEND COMMAND TO TRIGGER AWG
            self.send('TRIG')
            print("Triggered {0}".format(self.display_name))

    def close(self):
        print('close()')
        if self.enabled:
            # close the TCP connection to the AWG server
            self.sock.close()
            print("Connection to {0} closed".format(self.display_name))
