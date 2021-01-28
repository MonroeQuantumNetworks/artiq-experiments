""" Alice Timing Test Code

This generates pulsed pumping and single photon generation sequences in Alice for test purposes
It does not use the FPGA/entangler to run any of the beams



George 2020-06-17
updated 2020-01-22
"""

import artiq.language.environment as artiq_env
import artiq.language.units as aq_units
import numpy as np
import math
import pkg_resources
from artiq.language.core import kernel, delay, delay_mu, parallel
from artiq.language.types import TInt32
from artiq.coredevice.rtio import rtio_output
from dynaconf import LazySettings
# George added these:
import base_experiment
from artiq.experiment import *
import time
# import settings as settings3

# Get the number of inputs & outputs from the settings file.
settings = LazySettings(
    ROOT_PATH_FOR_DYNACONF=pkg_resources.resource_filename("entangler", "")
)
num_inputs = settings.NUM_ENTANGLER_INPUT_SIGNALS
num_outputs = settings.NUM_OUTPUT_CHANNELS

# class Remote_Entanglement_Experiment_Sample(base_experiment.base_experiment):
# class EntanglerDemo(artiq_env.EnvExperiment):

class Alice_Timing_Test(base_experiment.base_experiment):

    kernel_invariants = {
        "cool_time",
        "delay_one",
        "delay_two",
        "delay_three",
        "loops_to_run",
    }

    def build(self):

        super().build()

        """Add the Entangler driver."""
        self.setattr_device("core")
        self.setattr_device("entangler")
        self.out0_0 = self.get_device("ttl0")

        # This hardcoding is necessary for writing to the gateware for the fast loop.
        self.entangle_inputs = [
            self.get_device("ttl{}".format(i)) for i in range(8, 12)
        ]
        self.generic_inputs = [self.get_device("ttl{}".format(i)) for i in range(12, 16)]

        # Add other inputs
        self.setattr_device("core_dma")
        self.setattr_argument('cool_time', NumberValue(500e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('run_cooling_sequence', BooleanValue(True))
        self.setattr_argument('delay_one', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('delay_two', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('delay_three', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('loops_to_run', NumberValue(1000000, step=1, min=1, max=10000000, ndecimals=0))


        # self.setattr_argument('detection_time', NumberValue(200e-6, unit='us', step=1e-6, min=0 * us, ndecimals=0))
        # self.setattr_argument('raman_time', NumberValue(2e-6, unit='us', min=0 * us, ndecimals=0))

        # self.setattr_argument('test_mode', BooleanValue(True))
        self.setattr_argument('calculate_runtime', BooleanValue(True))
        self.setattr_argument('Alice493_TTL_vs_DDS', BooleanValue(False))
        self.setattr_argument('run_singlephoton_loop', BooleanValue(True))
        self.setattr_argument('pump_650sigma_1or2', NumberValue(1, step=1, min=1, max=2, ndecimals=0))
        self.setattr_argument('pulse650_duration', NumberValue(10e-9, step=5e-10, unit='ns', min=0 * ns, ndecimals=0))

        # self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(100), RangeScan(0 * us, 300, 100)], global_min=0 * us,
        #                                                       global_step=1 * us, unit='us', ndecimals=3))


    def run(self):
        """
        Run certain functions on the computer instead of the core device.
        """

        t_now = time.time()     # Save the current time

        self.kernel_run()     # Run the rest of the program on the core device

        print("Actual time taken = {:.2f} seconds" .format(time.time() - t_now))        # Calculate how long the experiment took

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run(self):

        self.core.reset()
        self.core.break_realtime()  # Increases slack to at least 125 us
        # self.init()

        # Pre-load all the pulse sequences using DMA
        # self.prerecord_singlephoton_loop()
        # delay_mu(100000)
        # self.core.break_realtime()
        # single_photon_handle = self.core_dma.get_handle("singlephoton_loop_pulses")

        # self.prerecord_cooling_loop()
        # delay_mu(100000)
        # self.core.break_realtime()
        # fast_loop_cooling_handle = self.core_dma.get_handle("cooling_loop_pulses")

        self.core.break_realtime()
        delay_mu(1000000)

        # Initial setup of the beams needed
        if self.Alice493_TTL_vs_DDS:      # Are we toggling the 493 TTLs or 493 DDS?
            self.DDS__493__Alice__sigma_1.sw.off()
            self.DDS__493__Alice__sigma_2.sw.off()
        self.ttl_650_fast_cw.off()
        self.ttl_650_sigma_1.off()
        self.ttl_650_sigma_2.off()
        self.ttl_Alice_650_pi.off()

        # This checks if we run the single photon loop or the manually customized loop
        if self.run_singlephoton_loop:
            # Pre-load all the pulse sequences using DMA
            self.prerecord_singlephoton_loop()
            delay_mu(100000)
            self.core.break_realtime()
            single_photon_handle = self.core_dma.get_handle("singlephoton_loop_pulses")
            self.core.break_realtime()
            delay_mu(1000000)

            for i in range(self.loops_to_run):
                self.core_dma.playback_handle(single_photon_handle)  # Run full sequence for single photon generation
                delay_mu(6000)

        else:
            # Pre-load all the pulse sequences using DMA
            self.prerecord_main_loop()
            delay_mu(100000)
            self.core.break_realtime()
            fast_loop_handle = self.core_dma.get_handle("main_loop_pulses")
            self.core.break_realtime()
            delay_mu(1000000)

            for i in range(self.loops_to_run):
                self.core_dma.playback_handle(fast_loop_handle)     # Run custom sequence, modify below
                delay_mu(6000)

        print("Kernel done")

    @kernel
    def run_cooling_loop(self):

        # Turn on cooling lasers
        self.ttl_650_sigma_1.on()
        self.ttl_650_sigma_2.on()
        self.ttl_650_fast_cw.on()
        self.ttl_Alice_650_pi.on()
        self.DDS__493__Alice__sigma_1.sw.on()
        self.DDS__493__Alice__sigma_2.sw.on()

        # Wait while lasers cool
        delay(self.cool_time)

        # Turn off cooling lasers
        self.ttl_650_sigma_1.off()
        self.ttl_650_sigma_2.off()
        self.ttl_650_fast_cw.off()
        self.ttl_Alice_650_pi.off()
        self.DDS__493__Alice__sigma_1.sw.off()
        self.DDS__493__Alice__sigma_2.sw.off()

    @kernel
    def prerecord_main_loop(self):
        """Pre-record the main loop sequence.
        This is a spare loop sequence you can switch to by unchecking "run_singlephoton_loop"
        Customize to run whatever sequence is required.
        """
        with self.core_dma.record("main_loop_pulses"):

            self.ttl0.pulse(20 * ns)  # This is the trigger pulse for the PicoHarp

            self.ttl_650_fast_cw.on()
            delay_mu(1000)
            self.DDS__493__Alice__sigma_1.sw.on()
            delay_mu(1000)
            self.DDS__493__Alice__sigma_2.sw.on()
            delay_mu(1000)
            self.ttl_Alice_650_pi.on()
            delay_mu(1000)
            self.ttl_650_sigma_1.on()
            delay_mu(1000)
            self.ttl_650_sigma_2.on()
            delay_mu(1000)
            self.ttl_Alice_650_pi.off()
            delay_mu(1000)
            self.ttl_Alice_650_pi.on()
            delay_mu(1000)
            self.ttl_650_fast_cw.off()
            delay_mu(1000)
            self.ttl_650_fast_cw.on()


            # delay(self.delay_one)       # In case some additional delay is needed
            #
            # delay(self.delay_two)
            # with parallel:
            #     self.ttl_650_sigma_1.on()
            #     self.ttl_650_sigma_2.on()
            #
            # delay(self.delay_three)

            delay_mu(10000)

            with parallel:
                self.ttl_Alice_650_pi.off()
                self.ttl_650_sigma_1.off()
                self.ttl_650_sigma_2.off()
                self.ttl_650_fast_cw.off()
                self.DDS__493__Alice__sigma_1.sw.off()
                self.DDS__493__Alice__sigma_2.sw.off()

    @kernel
    def prerecord_singlephoton_loop(self):
        """Pre-record the single photon generation loop sequence.
        This is faster than non pre-recorded
        """
        with self.core_dma.record("singlephoton_loop_pulses"):
            self.ttl0.pulse(20 * ns)  # This is the trigger pulse for the PicoHarp
            delay_mu(50)
            if self.run_cooling_sequence:
                # Turn on cooling lasers
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()
                self.ttl_650_fast_cw.on()
                self.ttl_Alice_650_pi.on()
                self.DDS__493__Alice__sigma_1.sw.on()
                self.DDS__493__Alice__sigma_2.sw.on()

                # Wait while lasers cool
                delay(self.cool_time)

                # Turn off cooling lasers
                self.ttl_650_sigma_1.off()
                self.ttl_650_sigma_2.off()
                self.ttl_650_fast_cw.off()
                self.ttl_Alice_650_pi.off()
                self.DDS__493__Alice__sigma_1.sw.off()
                self.DDS__493__Alice__sigma_2.sw.off()

                # delay(300*ns)
                delay(self.delay_one)

            # Pump sequence:
            with parallel:
                self.ttl_650_fast_cw.on()

                self.DDS__493__Alice__sigma_1.sw.on()
                self.DDS__493__Alice__sigma_2.sw.on()

                if self.pump_650sigma_1or2 == 1:
                    self.ttl_650_sigma_1.on()
                else:
                    self.ttl_650_sigma_2.on()

            # delay_mu(1500)

            self.ttl_Alice_650_pi.on()

            delay(self.delay_two)       # This delay cannot be zero or ARTIQ will spit out errors

            # Now turn off all the beams

            self.ttl_650_fast_cw.off()
            self.ttl_Alice_650_pi.off()
            delay_mu(200)
            if self.pump_650sigma_1or2 == 1:
                self.ttl_650_sigma_1.off()
            else:
                self.ttl_650_sigma_2.off()
            delay_mu(200)
            self.DDS__493__Alice__sigma_1.sw.off()
            self.DDS__493__Alice__sigma_2.sw.off()

            delay(self.delay_three)

             # Turn on the slow AOM first, no 650 light because 650 fast is off
            if self.pump_650sigma_1or2 == 1:
               self.ttl_650_sigma_2.on()
            else:
                self.ttl_650_sigma_1.on()

            delay_mu(200)       # Wait 100 ns so that the slow AOMs are fully turned on

            # self.ttl_650_fast_cw.pulse(self.pulse650_duration)          # Use this if using an rf switch
            self.ttl_650_fast_pulse.pulse(20*ns)     # Use this if using the pulse generator

            # Wait a little while before turning off the slow AOMS to maximize signal
            delay_mu(1000)        # This is needed if using the pulse generator due to the ~100ns delay introduced

            self.ttl_650_sigma_1.off()
            self.ttl_650_sigma_2.off()

    # Detection sequences are unused here
    @kernel
    def run_detection1(self):
        """Non-DMA detection loop sequence. With test pulses

        This generates the pulse sequence needed for detection with 493 sigma 1
        """

        t1 = now_mu()
        with parallel:
            # gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_Alice_650_pi.pulse(self.detection_time)
            self.ttl_650_fast_cw.pulse(self.detection_time)
            self.ttl_650_sigma_1.pulse(self.detection_time)
            self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_1.sw.pulse(self.detection_time)
            self.DDS__493__Alice__sigma_1.sw.pulse(self.detection_time)

        Alice_counts = self.Alice_camera_side_APD.count(gate_end_mu_B1)

        return Alice_counts

    @kernel
    def run_detection2(self):
        """Non-DMA detection loop sequence. With test pulses

        This generates the pulse sequence needed for detection with 493 sigma 2
        """

        t1 = now_mu()
        with parallel:
            # gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_Alice_650_pi.pulse(self.detection_time)
            self.ttl_650_fast_cw.pulse(self.detection_time)
            self.ttl_650_sigma_1.pulse(self.detection_time)
            self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)
            self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)

        Alice_counts = self.Alice_camera_side_APD.count(gate_end_mu_B2)

        return Alice_counts

