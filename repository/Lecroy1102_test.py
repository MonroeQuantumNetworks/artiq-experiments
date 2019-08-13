from artiq.experiment import *  # TODO: can we import rtio_log without import * ?
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment

import logging
import socket  # for TCP communication
import struct  # for TCP message formatting
import sys
import time
from ctypes import *


class Lecroy1102():
    """Class for programming a Lecroy 1102 AWG"""
    display_name = "Lecroy 1102 AWG"
    min_samples = 8  # minimum number of samples to program
    max_samples = 2000000  # maximum number of samples to program
    sample_chunk_size = 2  # number of samples must be a multiple of sample_chunk_size
    pad_value = 0  # the waveform will be padded with this number to make it a multiple of sample_chunk_size, or to make it the length of min_samples
    min_amplitude = 0  # minimum amplitude value (raw)
    max_amplitude = 1.5  # maximum amplitude value (raw)
    num_channels = 2  # number of channels
    calibration = lambda voltage: voltage  # function that returns raw amplitude number, given voltage
    calibrationInv = lambda raw: raw #function that returns voltage, given raw amplitude number

    def __enter__(self):
        print("__")
        return self.

    def __init__(self, IP_address, port, sample_rate, ext_clock_frequency):
        self.enabled = False
        self.IP_address = IP_address
        self.port = port
        self.sample_rate = sample_rate
        self.ext_clock_frequency = ext_clock_frequency

        self.waveforms = []
        for channel in range(self.deviceProperties['numChannels']):
            self.waveforms.append(None)

        self.sample_length = 1.0/self.sample_rate
        #new_mag('sample', sample)  # TODO: check whether the added samples = count / second in modules/quantity_units.txt
        #new_mag('samples', sample)  # replaces this

    def send(self, command_string):

       		# Send a well formatted message to the server.
            # The server must be running, and this instance must already have called connect().
            # Each message begins with MESG,
            # followed by 4 bytes (a 32 bit unsigned long integer) that give the length of the rest of the message,
            # followed by the rest of the message (command_string).

            # find the length of the command_string
            length = len(command_string)
            if length>=4294967296: #2**32
                logging.getLogger(__name__).error('Lecroy AWG TCP message is too long, size = '+str(length)+' bytes')

            # format the message
            message = b'MESG'+struct.pack("!L", length)+command_string

            # send the message
            self.sock.sendall(message)

    def open(self):
        logger = logging.getLogger(__name__)
        try:

            # set up TCP connection
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Open a connection to the TCP server.
            # The server should already be running at the given IP address.
            # The port numbers must agree between the client and server.
            self.sock.connect((self.IP_address, self.port))

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
            logger.info("Successfully opened {0}".format(self.display_name))
        except Exception as e:
            logger.error("Unable to open {0}: {1}".format(self.display_name, e))
            self.enabled = False
        return self.enabled

    def program(self, t0, t1, eq1, eq2):
        """
        :param t0: the start time in seconds (start does not delay, but this allows you to change window without modifying equations)
        :param t1: the end time in seconds
        :param eq1: a function handle for the first channel waveform.  Must accept a 1D numpy array of times in seconds as the only parameter.
        :param eq2: a function handle for the first channel waveform.  Must accept a 1D numpy array of times in seconds as the only parameter.
        :return:
        """

        logger = logging.getLogger(__name__)
        if self.enabled:
            channel_0_points = self.waveforms[0].evaluate()  # this is a 1D numpy array
            channel_1_points = self.waveforms[1].evaluate()  # this is a 1D numpy array
            logger.info("channel_0_points.dtype:"+str(channel_0_points.dtype))
            logger.info("channel_1_points.dtype:"+str(channel_1_points.dtype))
            logger.info( "writing {0} points to AWG channel 0".format(len(channel_0_points)) )
            logger.info( "writing {0} points to AWG channel 1".format(len(channel_1_points)) )

            # send waveforms over TCP to Lecroy C# server

            command_string = b'UPDA'
            command_string += struct.pack('!L', len(channel_0_points))
            command_string += channel_0_points.astype('<f8').tobytes()
            command_string += struct.pack('!L', len(channel_1_points))
            command_string += channel_1_points.astype('<f8').tobytes()

            self.send(command_string)

            time.sleep(1.5)  # wait 1.5 second for AWG programming to complete

        else:
            logger.warning("{0} unavailable. Unable to program.".format(self.display_name))

    def trigger(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            # SEND COMMAND TO TRIGGER AWG
            self.send('TRIG')
            logger.info("Triggered {0}".format(self.display_name))

    def close(self):
        logger = logging.getLogger(__name__)
        if self.enabled:
            # close the TCP connection to the AWG server
            self.sock.close()
            logger.info("Connection to {0} closed".format(self.display_name))

def eq1(t):
    return sin(2*np.pi*100*MHZ*t)

def eq2(t)
    return sin(2*np.pi*100*MHZ*t+np.pi)

class Lecroy1102_test(base_experiment.base_experiment):

    def run(self):
        IP_address = '192.168.1.100'  # server is running on JARVIS
        port = 11000
        sample_rate = 250 * MHz
        ext_clock_frequency = 10 * MHz
        with awg as Lecroy1102(IP_address, port, sample_rate, ext_clock_frequency):
        awg.open()
        t0 = 0
        t1 = 1*ms
        awg.program(t0, t1, eq1, eq2)


