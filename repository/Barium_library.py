""" Barium Library for commonly used functions
April 6 2020:
George created this file to compile and store functions commonly used for Barium 

"""
import artiq.language.environment as artiq_env
import artiq.language.units as aq_units
import numpy as np
import math
import pkg_resources
from artiq.language.core import kernel, delay, delay_mu, parallel
from artiq.language.types import TInt32
from artiq.coredevice.rtio import rtio_output
# George added these:
import base_experiment
from artiq.experiment import *
import time

class Barium_library(base_experiment.base_experiment):
    """Barium library of functions
    """

    def build(self):
        self.setattr_argument('cooling_time', NumberValue(100000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('detection_time', NumberValue(200e-6, unit='us', step=1e-6, min=0 * us, ndecimals=0))

    def run(self):
        """
        Run certain functions on the computer (non-Kernel) instead of the core device.

        :return:
        """

        # Since this is a library, do nothing
        pass

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run(self):
        # do nothing
        pass

    @kernel
    def prerecord_cooling_loop(self):
        """Pre-record the cooling loop sequence.

        Hopefully this is faster than non pre-recorded
        """

        with self.core_dma.record("cooling_loop_pulses"):
            # Cool
            with parallel:
                self.ttl_650_pi.on()
                self.ttl_493_all.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()
                self.ttl_test.on()  # This channel for diagnostics

                delay(self.cooling_time)

            with parallel:
                self.ttl_650_pi.off()
                self.ttl_493_all.off()
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_1.off()
                self.ttl_650_sigma_2.off()
                self.ttl_test.off()

    @kernel
    def run_detection1(self):
        """Non-DMA detection loop sequence. With test pulses

        This generates the pulse sequence needed for detection with 493 sigma 1
        """
        t1 = now_mu()
        with parallel:
            gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            self.ttl_650_fast_cw.pulse(self.detection_time)
            self.ttl_650_sigma_1.pulse(self.detection_time)
            self.ttl_650_sigma_2.pulse(self.detection_time)
            self.DDS__493__Alice__sigma_1.sw.pulse(self.detection_time)
            self.DDS__493__Bob__sigma_1.sw.pulse(self.detection_time)

        Alice_counts = self.Alice_camera_side_APD.count(gate_end_mu_A1)
        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B1)

        return Alice_counts, Bob_counts

    @kernel
    def run_detection2(self):
        """Non-DMA detection loop sequence. With test pulses

        This generates the pulse sequence needed for detection with 493 sigma 2
        """
        t1 = now_mu()
        with parallel:
            gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            self.ttl_650_fast_cw.pulse(self.detection_time)
            self.ttl_650_sigma_1.pulse(self.detection_time)
            self.ttl_650_sigma_2.pulse(self.detection_time)
            self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)
            self.DDS__493__Bob__sigma_2.sw.pulse(self.detection_time)

        Alice_counts = self.Alice_camera_side_APD.count(gate_end_mu_A2)
        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B2)

        return Alice_counts, Bob_counts

