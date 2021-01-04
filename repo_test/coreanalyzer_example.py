"""This file shows how to use the coreanalyzer seamlessly from within an experiment.
M. Lichtman 2019-08-15"""

from artiq.experiment import *
import base_experiment
import os

class coreanalyzer_example(base_experiment.base_experiment):

    def run(self):

        self.coreanalyzer_purge()

        try:
            # do some prep here
            self.kernel_run()
        finally:
            self.coreanalyzer_write()

    @kernel
    def kernel_run(self):
        # do some RTIO events
        self.core.reset()
        delay_mu(18000)
        rtio_log('msg', 'event 1')
        delay_mu(18000)
        rtio_log('msg', 'event 2')
        delay_mu(18000)
        rtio_log('msg', 'event 3')
