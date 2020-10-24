""" TTL Test

This script puts an output on the 12 new TTL outputs we installed
Will also attempt to read in an input using the 4 new edgecounters

George 2020-10-16
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


# Get the number of inputs & outputs from the settings file.


class TTL_Test(base_experiment.base_experiment):

    def build(self):

        super().build()

        """Add the Entangler driver."""
        self.setattr_device("core")

        # Add other inputs
        self.setattr_device("core_dma")
        self.setattr_argument('loops_to_run', NumberValue(100, step=100, min=1, max=1000000, ndecimals=0))

        # self.setattr_argument('calculate_runtime', BooleanValue(True))
        # self.setattr_argument('Alice493_TTL_vs_DDS', BooleanValue(False))
        # self.setattr_argument('run_singlephoton_loop', BooleanValue(True))
        # self.setattr_argument('pump_650sigma_1or2', NumberValue(1, step=1, min=1, max=2, ndecimals=0))
        # self.setattr_argument('pulse650_duration', NumberValue(10e-9, step=5e-10, unit='ns', min=0 * ns, ndecimals=0))



    def run(self):
        """
        Run certain functions on the computer instead of the core device.
        """
        try:
            t_now = time.time()     # Save the current time

            for i in range(self.loops_to_run):
                self.kernel_run()     # Run the rest of the program on the core device

            print("Actual time taken = {:.2f} seconds" .format(time.time() - t_now))        # Calculate how long the experiment took

            #
            # self.load_globals_from_dataset()    # This loads global settings from datasets
            # self.setup()        # This sends settings out to the ARTIQ hardware

        except TerminationRequested:
            self.load_globals_from_dataset()    # This loads global settings from datasets
            self.setup()        # This sends settings out to the ARTIQ hardware
            print('Terminated gracefully')

        finally:
            # These are necessary to restore the system to the state before the experiment.
            self.load_globals_from_dataset()    # This loads global settings from datasets
            self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run(self):

        self.core.reset()
        self.core.break_realtime()

        for i in range(self.loops_to_run):

            self.ttl_16.on()
            self.ttl_17.on()
            self.ttl_18.on()
            self.ttl_19.on()
            self.ttl_20.on()
            self.ttl_21.on()
            delay_mu(100000)
            self.ttl_16.off()
            self.ttl_17.off()
            self.ttl_18.off()
            self.ttl_19.off()
            self.ttl_20.off()
            self.ttl_21.off()

            delay_mu(100000)

            self.ttl_22.on()
            self.ttl_23.on()
            self.ttl_24.on()
            self.ttl_25.on()
            self.ttl_26.on()
            self.ttl_27.on()
            delay_mu(100000)
            self.ttl_22.off()
            self.ttl_23.off()
            self.ttl_24.off()
            self.ttl_25.off()
            self.ttl_26.off()
            self.ttl_27.off()

            delay_mu(100000)


            # Test Edge counter?

        # print("Kernel done")



