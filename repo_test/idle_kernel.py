from artiq.experiment import *


class idle_kernel(EnvExperiment):

    def build(self):
        self.setattr_device('core')
        self.setattr_device('led0')

    @kernel
    def run(self):

        self.core.reset()

        dot = 125*ms
        dash = 3*dot
        space = 7*dot
        while True:

            # I
            self.led0.pulse(dot)
            delay(dot)
            self.led0.pulse(dot)
            delay(dash)
            
            # D
            self.led0.pulse(dash)
            delay(dot)
            self.led0.pulse(dot)
            delay(dot)
            self.led0.pulse(dot)
            delay(dash)
            
            # L
            self.led0.pulse(dot)
            delay(dot)
            self.led0.pulse(dash)
            delay(dot)
            self.led0.pulse(dot)
            delay(dot)
            self.led0.pulse(dot)
            delay(dash)
            
            # E
            self.led0.pulse(dot)
            
            delay(space)
            
