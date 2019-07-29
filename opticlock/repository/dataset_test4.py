#from artiq.language.core import kernel, delay
from artiq.language.environment import EnvExperiment  # HasEnvironment
#from artiq.experiment import NumberValue, BooleanValue, TerminationRequested
#from artiq.language.units import s, ms, us, MHz
#import numpy as np

class dataset_test4(EnvExperiment):

    def build(self):
        self.setattr_device("core")

    def run(self):

        self.set_dataset("test/test1", 5, broadcast=True, archive=True)
