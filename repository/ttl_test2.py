from artiq.language.core import kernel, delay, now_mu
from artiq.experiment import TerminationRequested
from artiq.language.units import s, ms, us, ns, MHz
import base_experiment


class ttl_test2(base_experiment.base_experiment):

    @kernel
    def run(self):
        self.core.reset()
        try:  # catch TerminationRequested
            while True:
                self.ttl9.pulse(500 * us)
                delay(500*us)
        except TerminationRequested:
            print('Terminated gracefully')
