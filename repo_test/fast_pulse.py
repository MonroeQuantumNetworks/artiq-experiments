
import traceback

from artiq.experiment import *
#from artiq.language.core import kernel, delay
#from artiq.language.environment import EnvExperiment
#from artiq.language.units import s, ms, us, ns, MHz
import base_experiment


class fast_pulse(base_experiment.base_experiment):
    kernel_invariants = {"t"}

    def run(self):
        self.t = 1*ms
        self.kernel_run()

    @kernel
    def kernel_run(self):
        self.core.reset()
        rtio_log("ttl8", "place 1")
        self.ttl8.pulse(self.t)
        rtio_log("ttl8", "place 2")
        delay(self.t)
        rtio_log("ttl8", "place 3")
        self.ttl8.pulse(self.t)
        rtio_log("ttl8", "place 4")
