
import traceback

from artiq.language.core import kernel, delay
from artiq.language.environment import EnvExperiment
from artiq.language.units import s, ms, us, ns, MHz
import base_experiment


class fast_pulse(base_experiment.base_experiment):
    kernel_invariants = {"t"}

    def run(self):
        self.t = 1*ms
        self.kernel_run()

    @kernel
    def kernel_run(self):
        self.core.reset()
        self.ttl8.pulse(self.t)
        delay(self.t)
        self.ttl8.pulse(self.t)
