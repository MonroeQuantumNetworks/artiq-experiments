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

class Ba_detection_Bob_DMA(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))
        self.setattr_device("core_dma")
        self.detector = self.Bob_camera_side_APD
        self.detection_points = 10
        self.cooling_time = 1*us
        self.pumping_time = 1*us
        self.detection_time = 1*us
        self.setattr_device("ttl9")
        self.setattr_device("ttl8")


    @kernel
    def prep_record(self):
        delay_mu(18000)
        rtio_log('msg', 'p')

        with self.core_dma.record("pulses"):
            self.urukul0_ch2.sw.off() # Bob 493 sigma 1
            self.urukul0_ch3.sw.off() # Bob 493 sigma 2
            self.urukul1_ch3.sw.on() # Bob 650 pi
            self.urukul2_ch0.sw.on() # 650 fast AOM
            self.urukul1_ch0.sw.on() # 650 sigma 1
            self.urukul1_ch1.sw.on() # 650 sigma 2

    @kernel
    def record(self):
        gate_end_mu = 0
        with self.core_dma.record("pulses"):
            for i in range(self.detection_points):

                # cooling
                self.urukul0_ch2.sw.on()  # Bob 493 sigma 1
                self.urukul0_ch3.sw.on()  # Bob 493 sigma 2

                delay(self.cooling_time)

                self.urukul0_ch2.sw.off()
                self.urukul0_ch3.sw.off()

                delay(10*ns)

                # pumping, sigma 1
                self.urukul0_ch3.sw.on()
                delay(self.pumping_time)
                self.urukul0_ch3.sw.off()

                delay(10*ns)

                # detection, sigma 1
                t = now_mu()
                gate_end_mu = self.detector.gate_rising(self.detection_time)
                at_mu(t)

                self.urukul0_ch3.sw.on()
                delay(self.detection_time)
                self.urukul0_ch3.sw.off()

        return gate_end_mu


    def run(self):
        self.core.break_realtime()
        self.coreanalyzer_purge()
        try:
            self.kernel_run()
        except TerminationRequested:
            print('Terminated gracefully')
        finally:
            self.coreanalyzer_write()


    @kernel
    def kernel_run(self):
        counts = 0
        self.core.reset()
        self.prep_record()
        pulses_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()
        self.core_dma.playback_handle(pulses_handle)
        sum = 0
        gate_end_mu = self.record()
        pulses_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()

        self.core_dma.playback_handle(pulses_handle)

        counts = self.detector.count(gate_end_mu)
        sum += counts
        self.core.break_realtime()
        print(sum)