""" Legacy script
Alice Barium Single Photon Excitation script

    Appears to be a simple script to run the single photon excitation scheme infinite times
    Writes a mega long DMA sequence (repeated 2000 times)
    Does Cool/Pump/Excite - No detect?
    Hardcoded urukul channels, but names are listed in this script
    Has some timing adjustments in the code to make sure the laser pulses overlap

George Toh 2020-04-19
"""

from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment
import os
import time


class Ba_Excitation_Alice(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("core_dma")

        self.setattr_argument('cooling_time', NumberValue(5e-6, unit='us', min=0*us, ndecimals=3))
        self.setattr_argument('pumping_time', NumberValue(3e-6, unit='us', min=0*us, ndecimals=3))
        self.excitation_number = 10000

    @kernel
    def prep(self):
        self.urukul0_ch0.sw.off() # Alice 493 sigma 1
        self.urukul3_ch0.sw.off() # Alice 493 sigma 2
        self.urukul1_ch2.sw.off() # Alice 650 pi
        self.urukul1_ch0.sw.off() # 650 sigma 1
        self.urukul1_ch1.sw.off() # 650 sigma 2
        self.urukul2_ch1.sw.off() # Alice 493 cooling
        self.ttl11.off() # This turns on/off the CW mode of 650 sigma
        delay(10*ns)
        self.ttl8.off() # This TTL controls the pulsing of the 650 sigma

    @kernel
    def experiment_record(self):
        with self.core_dma.record("pulses"):
            for j in range(2000):
                self.ttl14.pulse(50*ns)
                delay(10*ns)

                # Cooling--all beams on
                self.ttl11.on() #650 CW switch on (no DDS to sigma AOMs yet)
                delay(100*ns)

                # 650 sigma 2 needs to be turned on 726 ns before other beams
                t0 = now_mu()
                self.urukul1_ch1.sw.on() # Alice 650 sigma 2
                at_mu(t0+726)

                with parallel:
                    self.urukul1_ch2.sw.on()  # Alice 650 pi
                    self.urukul1_ch0.sw.on() # 650 sigma 1
                    self.urukul3_ch0.sw.on() # Alice 493 sigma 2

                # 493 sigma 1 needs to be turned on 267 ns after other beams
                at_mu(t0 + 267 + 726)
                self.urukul0_ch0.sw.on()  # Alice 493 sigma 1


                # Pumping--all 493 beams on, 650 sigma 2 and pi on--fast AOM should be on
                self.urukul1_ch0.sw.off()
                delay(3*us) # pumping time

                # Prepare for excitation--all beams off, but sigma 2 AOM on (beam will be off because fast AOM will be off)
                t1 = now_mu()
                self.urukul1_ch1.sw.off()
                at_mu(t1 + 726)

                with parallel:
                    self.ttl11.off() # 650 fast AOM, CW
                    self.urukul1_ch2.sw.off()
                    self.urukul3_ch0.sw.on()

                at_mu(t1+726+267)
                self.urukul0_ch0.sw.off()


                delay(1000*ns)

                self.urukul1_ch0.sw.on() # 650 sigma 1

                delay(600*ns)

                # Excite
                self.ttl8.pulse(100*ns)

                self.urukul1_ch0.sw.off()

                delay(700*ns)


    @kernel
    def kernel_experiment_run(self, pulses_handle):
        num = 0
        while True:
            delay(10*us)
            self.core_dma.playback_handle(pulses_handle)
            #num += 1
            #print(num)



    def run(self):
        try:
            # Set up experiment
            self.prep()
            print('Prepared')
            self.core.break_realtime()
            num = 0
            self.experiment_record()
            pulses_handle = self.core_dma.get_handle("pulses")
            self.kernel_experiment_run(pulses_handle)
        except TerminationRequested:
            print("Terminated gracefully")
