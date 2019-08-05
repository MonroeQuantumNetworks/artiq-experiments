
import traceback

from artiq.language.core import kernel, delay
from artiq.language.environment import EnvExperiment
from artiq.language.units import s, ms, us, ns, MHz
#import base_experiment


class fast_pulse(EnvExperiment):
    kernel_invariants = {"t"}

    def build(self):
        self.setattr_device('core')
        self.setattr_device('ttl8')

    def run(self):
        self.t = 1*s

    @kernel
    def kernel_run(self):
        self.core.break_realtime()
        self.ttl8.pulse(self.t)
        delay(self.t)
        self.ttl8.pulse(self.t)