from artiq.experiment import *
import time
import numpy as np

class dataset_test1(EnvExperiment):
    def build(self):

        self.setattr_device("core")

    @kernel
    def run(self):
        count=10
        self.set_dataset("parabola", np.full(count, np.nan), broadcast=True)
        for i in range(count):
            self.mutate_dataset("parabola", i, i*i)
            time.sleep(0.1)
