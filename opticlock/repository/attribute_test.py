"""
Used to understand how setattr_arguments and get_arguments work.

M. Lichtman 2019-07-15
"""

from artiq.experiment import *  # EnvExperiment, NumberValue, BooleanValue, kernel

class attribute_test(EnvExperiment):

    def build(self):

        # base functionality #

        self.setattr_device('core')

        # timing variables #

        self.dummy = self.get_argument('dummy', NumberValue(10*us, unit='us', ndecimals=1, min=0.0, step=1.0))


    def run(self):
        print(self.dummy)
