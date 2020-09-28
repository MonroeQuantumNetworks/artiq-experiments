""" 
Test code for running the AWG through the Artiq interface

George Toh 2020-09-23
"""

from artiq.experiment import *
import numpy as np
import base_experiment
import os
import time

from AWGmessenger import sendmessage   # Other file in the repo, contains code for messaging Jarvis

class AWG_test(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")

        self.setattr_argument('channel', NumberValue(1, ndecimals=0, min=1, step=1, max=4))
        self.setattr_argument('AWG_quit', BooleanValue(False))
        self.setattr_argument('flush_awg', BooleanValue(False))
        self.setattr_argument('Wave', BooleanValue(False))
        self.setattr_argument('Two_tones', BooleanValue(False))
        self.setattr_argument('amplitude1', NumberValue(0.1, ndecimals=3, min=0, step=0.1))
        self.setattr_argument('amplitude2', NumberValue(0.1, ndecimals=3, min=0, step=0.1))
        self.setattr_argument('DDS__532__Alice__tone_1__frequency', NumberValue(20000000, ndecimals=0, min=1, step=1000000))
        self.setattr_argument('DDS__532__Alice__tone_2__frequency', NumberValue(20000000, ndecimals=0, min=1, step=1000000))
        self.setattr_argument('duration1', NumberValue(1000, ndecimals=0, min=0, step=1, max=1000000))
        self.setattr_argument('pause', NumberValue(1000, ndecimals=0, min=0, step=1, max=1000000))
        self.setattr_argument('duration2', NumberValue(1000, ndecimals=0, min=0, step=1, max=1000000))
        self.setattr_argument('phase', NumberValue(0, ndecimals=5, min=0, max = 300000))
        self.setattr_argument('phase_diff', NumberValue(0, ndecimals=5, min=0, max=300000))

    def run(self):

        try:

            t_now = time.time()  # Save the current time

            # Update the AWG with tone 1 and tone 2
            # self.DDS__532__Alice__tone_1__frequency     self.DDS__532__Alice__tone_1__amplitude
            # self.DDS__532__Alice__tone_2__frequency     self.DDS__532__Alice__tone_2__amplitude

            # Syntax 1: wave, channel=1-4, amplitude(mV), freq1(Hz), freq2(Hz), duration1(ns), duration2(ns), delay(ns)
            # Syntax 2: sine, channel=1-4, amplitude(mV), freq(Hz)
            # message1 = "wave-1-100-"+str(int(self.DDS__532__Alice__tone_1__frequency))+"-"+str(int(self.DDS__532__Alice__tone_2__frequency))+"-"+str(int(self.raman_time/ns))+"-100-500"
            # message2 = "sine-1-100-"+str(int(self.DDS__532__Alice__tone_1__frequency))
            # messageq = "quit"

            if self.flush_awg == True:
                sendmessage(self, type="flush")

            if self.AWG_quit == True:
                sendmessage(self)   # Writing nothing sends a quit
            elif self.Wave == True:
                sendmessage(self,
                            type = "wave",
                            channel = self.channel,
                            amplitude1 = self.amplitude1,
                            amplitude2 = self.amplitude2,
                            frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
                            frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
                            phase1 = self.phase,                                    # radians
                            phase2 = self.phase_diff,  # radians
                            duration1 = self.duration1,                             # ns
                            duration2 = self.duration2,                             # ns
                            pause = self.pause
                            )
            elif self.Two_tones == False:
                sendmessage(self,
                            type = "sine",
                            channel = self.channel,
                            amplitude1 = self.amplitude1,
                            frequency1 = self.DDS__532__Alice__tone_1__frequency
                            )
            else:
                sendmessage(self,
                            type = "sin2",
                            channel = self.channel,
                            amplitude1 = self.amplitude1,
                            amplitude2 = self.amplitude2,
                            frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
                            frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
                            )



            # TODO May need to insert a delay here

            # allow other experiments to preempt
            self.core.comm.close()
            self.scheduler.pause()



        except TerminationRequested:
            sys.exit()
            print('Terminated gracefully')


        print("Time taken = {:.2f} seconds".format(time.time() - t_now))  # Calculate how long the experiment took

        # sys.exit()


''' Draft code for remote entanglement experiment

    # Clear waveforms from the AWG
    sendmessage(self, type="flush")
    
    # This loads the AWG with the waveform needed, trigger with ttl_AWG_trigger
    sendmessage(self,
        type = "wave",
        channel = 1,
        amplitude1 = self.DDS__532__Alice__tone_1__amplitude,
        amplitude2 = self.DDS__532__Alice__tone_2__amplitude,
        frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
        frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
        # phase1 = self.phase,                                    # radians
        phase2 = 3.14,                               # radians
        duration1 = self.raman_time/ns,                         # Convert sec to ns
        # duration2 = self.duration2,                             # ns
        # pause = self.pause
        )

    sendmessage(self,
        type = "wave",
        channel = 2,
        amplitude1 = self.DDS__532__Alice__tone_1__amplitude,
        amplitude2 = self.DDS__532__Alice__tone_2__amplitude,
        frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
        frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
        # phase1 = self.phase,                                    # radians
        phase2 = 3.14,                               # radians
        duration1 = self.raman_time/ns,                         # Convert sec to ns
        # duration2 = self.duration2,                             # ns
        # pause = self.pause
        )

    sendmessage(self,
        type = "wave",
        channel = 3,
        amplitude1 = self.DDS__532__Alice__tone_1__amplitude,
        amplitude2 = self.DDS__532__Alice__tone_2__amplitude,
        frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
        frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
        # phase1 = self.phase,                                    # radians
        phase2 = 3.14,                               # radians
        duration1 = self.raman_time/ns,                         # Convert sec to ns
        # duration2 = self.duration2,                             # ns
        # pause = self.pause
        )

    sendmessage(self,
        type = "wave",
        channel = 4,
        amplitude1 = self.DDS__532__Alice__tone_1__amplitude,
        amplitude2 = self.DDS__532__Alice__tone_2__amplitude,
        frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
        frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
        # phase1 = self.phase,                                  # radians
        phase2 = 3.14,                                          # radians
        duration1 = self.raman_time/ns,                         # Convert sec to ns
        # duration2 = self.duration2,                           # ns
        # pause = self.pause
        )

    # Do remote entanglement
    # Depending on what we get from the HOM APDs:
        # if 0101, 1010: set ttl16 off
        # if 0011, 1100: set ttl16 on
    # Trigger the AWG to run all 4 outputs

'''