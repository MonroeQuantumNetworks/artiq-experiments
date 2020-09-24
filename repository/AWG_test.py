""" 
Test code for running the AWG

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

        self.setattr_argument('AWG_quit', BooleanValue(False))
        self.setattr_argument('Two_tones', BooleanValue(False))
        self.setattr_argument('amplitude1', NumberValue(0.1, ndecimals=2, min=0, step=0.1))
        self.setattr_argument('amplitude2', NumberValue(0.1, ndecimals=2, min=0, step=0.1))
        self.setattr_argument('DDS__532__Alice__tone_1__frequency', NumberValue(20000000, ndecimals=0, min=1, step=1))
        self.setattr_argument('DDS__532__Alice__tone_2__frequency', NumberValue(20000000, ndecimals=0, min=1, step=1))

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

            if self.AWG_quit == True:
                sendmessage(self)   # Writing nothing sends a quit
            elif self.Two_tones == False:
                sendmessage(self,
                            type = "sine",
                            channel = 1,
                            amplitude1 = 0.1,
                            frequency1 = self.DDS__532__Alice__tone_1__frequency
                            )
            else:
                sendmessage(self,
                    type = "sin2",
                    channel = 1,
                    amplitude1 = 0.1,
                    amplitude2 = 0.1,
                    frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
                    frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
                    )

            # sendmessage(
            #     type = "wave",
            #     channel = 1,
            #     amplitude1 = 0.1,
            #     amplitude2 = 0.1,
            #     frequency1 = self.DDS__532__Alice__tone_1__frequency,   # Hz
            #     frequency2 = self.DDS__532__Alice__tone_2__frequency,   # Hz
            #     phase = 0                                               # radians
            #     duration1 = self.raman_time/ns,                         # ns
            #     duration2 = 0,                                          # ns
            #     pause = 0)

            # TODO May need to insert a delay here

            # allow other experiments to preempt
            self.core.comm.close()
            self.scheduler.pause()



        except TerminationRequested:
            sys.exit()
            print('Terminated gracefully')


        print("Time taken = {:.2f} seconds".format(time.time() - t_now))  # Calculate how long the experiment took

        # sys.exit()

