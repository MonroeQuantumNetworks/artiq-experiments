from artiq.experiment import *
import time
import numpy as np

class dataset_test2(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.x_pixels = 10
        self.y_pixels = 20
        self.set_dataset("image_dataset", np.zeros((self.x_pixels, self.y_pixels)), broadcast=True)

    @kernel
    def run(self):
        for i in range(self.x_pixels):
            for j in range(self.y_pixels):
                self.mutate_dataset("image_dataset", ((i, i+1, None), (j, j+1, None)), 1/(1+((i-5)*(i-5)+(j-5)*(j-5))))
                time.sleep(0.01)
