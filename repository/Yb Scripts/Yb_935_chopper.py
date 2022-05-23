""" Tested, works
This script chops the 935 laser on and off to help with alignment of optics
Added an additional line at the end of kernel_run to wait

George Toh 2022-05-20, Isabella Goetting 2022-05-23
"""

from artiq.experiment import *
# from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
import numpy as np
from repository import base_experiment
import os
import time

class Yb_935_chopper(base_experiment.base_experiment):
    """ Yb 935 chopper"""

    # kernel_invariants = {
    #     "Repetitions",
    #     "On_time",
    #     "Off_time",
    # }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")

        self.setattr_argument('Repetitions', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('On_time', NumberValue(1000*ms, ndecimals=0, min=0*ms, step=100*ms, unit='ms'))
        self.setattr_argument('Off_time', NumberValue(1000*ms, ndecimals=0, min=0*ms, step=100*ms, unit='ms'))

    def run(self):

        try:

            t_now = time.time()  # Save the current time

            # Run the main portion of code here
            self.kernel_run2()

                # allow other experiments to preempt
            self.core.comm.close()
            self.scheduler.pause()

                # point_num += 1

        except TerminationRequested:
            print('Terminated gracefully')
            # These are necessary to restore the system to the state before the experiment.
            self.load_globals_from_dataset()  # This loads global settings from datasets
            self.setup()  # This sends settings out to the ARTIQ hardware

        print("Time taken = {:.2f} seconds".format(time.time() - t_now))  # Calculate how long the experiment took

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run2(self):

        self.core.reset()
        self.core.break_realtime()

        for i in range(self.Repetitions):
            delay(self.On_time)
            self.ttl_935_shutter.off()
            delay(self.Off_time)
            self.ttl_935_shutter.on()
            
        self.core.wait_until_mu(now_mu())