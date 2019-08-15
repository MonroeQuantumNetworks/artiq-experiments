"""This file shows how to use the coreanalyzer seamlessly from within an experiment.
M. Lichtman 2019-08-15"""

from artiq.experiment import *
import base_experiment
import os
from artiq.coredevice.comm_analyzer import (get_analyzer_dump,
                                            decode_dump, decoded_dump_to_vcd)

class coreanalyzer_example(base_experiment.base_experiment):

    def run(self):

        core_addr = '192.168.1.98'
        with open('/usr/monroe/Documents/github/artiq-experiments/purge.vcd', "w") as f:
            decoded_dump_to_vcd(f, self.get_device_db(), decode_dump(get_analyzer_dump(core_addr)))
        #os.system(r'cd ~/Documents/github/artiq-experiments/; artiq_coreanalyzer -w rtio.vcd')

        try:
            # do some prep here
            self.kernel_run()
        finally:
            with open('rtio.vcd', "w") as f:
                decoded_dump_to_vcd(f, self.get_device_db(), decode_dump(get_analyzer_dump(core_addr)))
            #os.system(r'cd ~/Documents/github/artiq-experiments/; artiq_coreanalyzer -w rtio.vcd')

    @kernel
    def kernel_run(self):
        # do some RTIO events
        self.core.reset()
        delay_mu(1800)
        rtio_log('msg', 'event 1')
        delay_mu(1800)
        rtio_log('msg', 'event 2')
        delay_mu(1800)
        rtio_log('msg', 'event 3')
