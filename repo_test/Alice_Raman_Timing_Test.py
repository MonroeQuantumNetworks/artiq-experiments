""" Alice Timing Test Code

This generates a pulse for the Picoharp and sends 532 Raman light into the chamber
We use this to match the arrival time of 532 pulses at the ion


George 2020-10-02
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

class Alice_Raman_Timing_Test(base_experiment.base_experiment):

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

        self.setattr_argument('loops_to_run', NumberValue(1000000, step=1, min=1, max=10000000, ndecimals=0))
        self.setattr_argument('delay_one', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('delay_two', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('delay_three', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))

        # self.setattr_argument('test_mode', BooleanValue(True))
        self.setattr_argument('Alice493_TTL_vs_DDS', BooleanValue(False))
        self.setattr_argument('run_alice_beam', BooleanValue(False))
        # self.setattr_argument('pump_650sigma_1or2', NumberValue(1, step=1, min=1, max=2, ndecimals=0))
        # self.setattr_argument('pulse650_duration', NumberValue(10e-9, step=5e-10, unit='ns', min=0 * ns, ndecimals=0))

        self.setattr_argument('channel', NumberValue(1, ndecimals=0, min=1, step=1, max=4))

        self.setattr_argument('AWG__532__Alice__tone_1__amplitude__scan', Scannable(default=[NoScan(self.globals__AWG__532__Alice__tone_1__amplitude), RangeScan(0, 0.06, 20)], global_min=0,global_step=0.1, ndecimals=3))

    def run(self):
        """
        Run certain functions on the computer instead of the core device.
        """

        sendmessage(self,
                    type="wave",
                    channel=self.channel,
                    amplitude1=self.AWG__532__Alice__tone_1__amplitude,
                    amplitude2=0,
                    frequency1=80000000,  # Hz
                    frequency2=0,  # Hz
                    # phase1 = self.phase,                                    # radians
                    phase2=0,  # radians
                    duration1=self.raman_time / ns,  # Convert sec to ns
                    # duration2 = self.duration2,                             # ns
                    # pause1 = self.pause1
                    # pause2 = self.pause2
                    )
        time.sleep(0.5)

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

        # Initial setup of the beams needed
        if self.Alice493_TTL_vs_DDS:      # Are we toggling the 493 TTLs or 493 DDS?
            self.DDS__493__Alice__sigma_1.sw.off()
            self.DDS__493__Alice__sigma_2.sw.off()
        self.ttl_650_fast_cw.off()
        self.ttl_650_sigma_1.off()
        self.ttl_650_sigma_2.off()
        self.ttl_Alice_650_pi.off()

        # This checks if we run the single photon loop or the manually customized loop
        if self.run_alice_beam:
            # Pre-load all the pulse sequences using DMA
            self.prerecord_singlephoton_loop()
            delay_mu(100000)
            self.core.break_realtime()
            single_photon_handle = self.core_dma.get_handle("singlephoton_loop_pulses")
            self.core.break_realtime()
            delay_mu(1000000)

            for i in range(self.loops_to_run):
                delay_mu(5000)
                self.core_dma.playback_handle(single_photon_handle)  # Run full sequence for single photon generation


        else:
            # Pre-load all the pulse sequences using DMA
            self.prerecord_main_loop()
            delay_mu(100000)
            self.core.break_realtime()
            fast_loop_handle = self.core_dma.get_handle("main_loop_pulses")
            self.core.break_realtime()
            delay_mu(1000000)

            for i in range(self.loops_to_run):
                delay_mu(5000)
                self.core_dma.playback_handle(fast_loop_handle)     # Run custom sequence, modify below


        print("Kernel done")


    @kernel
    def prerecord_main_loop(self):
        """Pre-record the main loop sequence.
        This is a spare loop sequence you can switch to by unchecking "run_singlephoton_loop"
        Customize to run whatever sequence is required.
        """
        with self.core_dma.record("main_loop_pulses"):

            self.ttl0.pulse(20 * ns)  # This is the trigger pulse for the PicoHarp

            delay_mu(70)
            with parallel:
                # self.DDS__532__Alice__tone_1.sw.on()
                self.DDS__532__Bob__tone_2.sw.on()

            delay(self.delay_one)

            with parallel:
                # self.DDS__532__Alice__tone_1.sw.off()
                self.DDS__532__Bob__tone_2.sw.off()

    @kernel
    def prerecord_singlephoton_loop(self):
        """Pre-record the single photon generation loop sequence.
        This is faster than non pre-recorded
        """
        with self.core_dma.record("singlephoton_loop_pulses"):
            self.ttl0.pulse(20 * ns)  # This is the trigger pulse for the PicoHarp

            with parallel:
                self.DDS__532__Alice__tone_1.sw.on()

            delay(self.delay_one)

            with parallel:
                self.DDS__532__Alice__tone_1.sw.off()


