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


class TTL_Test_2(base_experiment.base_experiment):

    def build(self):

        super().build()

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

            # for i in range(1):
            print("Before Kernel_run")
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

        self.record_cool()

        cool_handle = self.core_dma.get_handle("cool")

        # Using gateware counters, only a single input event each is
        # generated, greatly reducing the load on the input FIFOs:

        self.core.break_realtime()

        # self.ttl28.gate_rising(10 * us)
        # self.Counter1.gate_rising(10 * us)
        # self.Counter2.gate_rising(10 * ms)
        # self.Counter3.gate_rising(10 * ms)
        # self.Counter4.gate_rising(10 * ms)

        counts_1 = 0

        at_mu(self.core.get_rtio_counter_mu())

        rtio_log("beforedelay", 0)

        delay_mu(200000)

        rtio_log("after100000delay", 0)

        t_start = now_mu()
        # self.ttl28.set_config(count_rising=True, count_falling= False,
        #            send_count_event = False, reset_to_zero= True)

        with parallel:
            gate_end = self.Alice_PMT.gate_rising(100 * us)
            gate2_end = self.Counter_2.gate_rising(100 * us)
            for i in range(self.loops_to_run):

                with sequential:

                    self.ttl_20.on()    # 20 goes to Edgecounter1
                    delay(1*ns)
                    self.ttl_21.on()    # 21 goes to Alice_PMT
                    delay(1 * us)

                    self.ttl_20.off()
                    delay(1 * ns)
                    self.ttl_21.off()
                    delay(1 * us)

        # self.ttl29.gate_rising(100 * us)
        # delay_mu(1000000)

        # counts_1 = 13
        counts_1 = self.Alice_PMT.count(gate_end)

        # counts_2 = self.ttl29.fetch_count()
        # delay_mu(1000000000)
        at_mu(t_start+100000)

        with sequential:
            timeout, counts_2 = self.Counter_2.fetch_timestamped_count(timeout_mu=t_start + 1000)
            # counts_2 = self.Counter_2.fetch_count()
            print(t_start, now_mu() - t_start, gate2_end - t_start)
        # counts_2 = self.Counter1.fetch_count()
        # counts_2 = self.Counter2.fetch_count()
        # counts_3 = self.Counter3.fetch_count()
        # counts_4 = self.Counter4.fetch_count()

        print(counts_1, counts_2, timeout)   #, counts_3, counts_4)

        # rtio_log("slack", now_mu()-self.core.get_rtio_counter_mu())
        for i in range(100):
            rtio_log("slack", "george")
            delay_mu(100)
        print(self.core.mu_to_seconds(now_mu()-self.core.get_rtio_counter_mu()))  # Display Slack remaining

            # Test Edge counter?

        # print("Kernel done")

    @kernel
    def record_cool(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 493 sigma 1
        """
        with self.core_dma.record("cool"):
            # with parallel:

            self.ttl_21.on()

            delay(1 * us)

            self.ttl_21.off()
            delay(1 * us)
            self.ttl_21.on()

            delay(1 * us)

            self.ttl_21.off()
            delay(1 * us)
            self.ttl_21.on()

            delay(1 * us)

            self.ttl_21.off()
            delay(1 * us)

            # with parallel:

