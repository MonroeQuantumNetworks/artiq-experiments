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


class Ba_Excitation_Bob(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("core_dma")

        self.setattr_argument('cooling_time', NumberValue(5e-6, unit='us', min=0*us, ndecimals=3))
        self.setattr_argument('pumping_time', NumberValue(3e-6, unit='us', min=0*us, ndecimals=3))
        self.excitation_number = 10000

    @kernel
    def prep(self):
        self.urukul0_ch2.sw.off() # Bob 493 sigma 1
        self.urukul0_ch3.sw.off() # Bob 493 sigma 2
        self.urukul1_ch3.sw.off() # Bob 650 pi
        self.urukul1_ch0.sw.off() # 650 sigma 1
        self.urukul1_ch1.sw.off() # 650 sigma 2
        self.urukul2_ch1.sw.off() # Bob 493 cooling
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

                # 493 sigma 2 needs to be turned on 330 ns before other beams
                t0 = now_mu()
                self.urukul0_ch3.sw.on()
                at_mu(t0+260)
                self.urukul0_ch2.sw.on()

                with parallel:
                    self.urukul1_ch3.sw.on()  # Bob 650 pi
                    self.urukul1_ch0.sw.on() # 650 sigma 1
                    self.urukul1_ch1.sw.on() # 650 sigma 2
                    self.urukul0_ch3.sw.on() # Bob 493 sigma 2
                    #self.urukul0_ch2.sw.on()  # Bob 493 sigma 1

                delay(1*us)

                # t1 = now_mu()
                # self.urukul0_ch3.sw.off()
                # at_mu(t1+260)
                # self.urukul0_ch2.sw.off()
                # at_mu(t1+330)
                #
                # with parallel:
                #     self.urukul1_ch3.sw.off()
                #     self.urukul1_ch0.sw.off()
                #     self.urukul1_ch1.sw.off()
                #     # self.urukul0_ch3.sw.off()
                #     self.urukul0_ch2.sw.off()
                #
                # delay(1*us)
                #
                # # Pumping--all 493 beams on, 650 sigma 2 and pi on--fast AOM should be on
                # t2 = now_mu()
                # self.urukul0_ch3.sw.on()
                # at_mu(t2+260)
                # self.urukul0_ch2.sw.on()
                # at_mu(t2+330)
                #
                # with parallel:
                #     self.urukul1_ch3.sw.on()
                #     self.urukul1_ch1.sw.on()
                #     self.urukul0_ch3.sw.on()
                #     # self.urukul0_ch2.sw.on()

                self.urukul1_ch0.sw.off()
                delay(3*us)

                # Prepare for excitation--all beams off, but sigma 2 AOM on (beam will be off because fast AOM will be off)
                with parallel:
                    self.ttl11.off() # 650 fast AOM, CW
                    self.urukul1_ch3.sw.off()
                    self.urukul0_ch3.sw.off()
                    self.urukul0_ch2.sw.off()
                    self.urukul1_ch1.sw.off()
                    self.urukul1_ch0.sw.on() # 650 sigma 1

                delay(1500*ns)

                # Excite
                self.ttl8.pulse(100*ns)
                delay(100*ns)
                self.urukul1_ch0.sw.off()

                delay(1000*ns)


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
