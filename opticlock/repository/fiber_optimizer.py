from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

import numpy as np
import time

# for motors
import CONEX_TRB

# for optimizer
import optimizer

class fiber_optimizer(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")

    @kernel
    def prep_kernel(self):
        self.core.reset()
        self.ttl0.input()

    def run(self):
        self.prep_kernel()

        # setup motors

        self.motor_helper = CONEX_TRB.motor_helper()
        self.motors = self.motor_helper.open_motors()

      #  variable_names = ['lens_Y', 'lens_tilt_Y', 'lens_X', 'lens_tilt_X', 'lens_focus', 'fiber_H', 'fiber_tilt_H', 'fiber_V', 'fiber_tilt_V']
        variable_names = ['fiber_H', 'fiber_tilt_H', 'fiber_V', 'fiber_tilt_V', 'fiber_focus']
        initial_values = np.array([self.motors[name].get_position() for name in variable_names])
        variable_min =   np.maximum(np.array([self.motors[name].get_minimum()  for name in variable_names]), initial_values-0.1)
        variable_max =   np.minimum(np.array([self.motors[name].get_maximum()  for name in variable_names]), initial_values+0.1)
        variable_min[4] = initial_values[4] - .5
        variable_max[4] = initial_values[4] + .5
        self.optimizer = optimizer.Optimization(self.cost, self.set_position, variable_names, initial_values, variable_min, variable_max)
        self.optimizer.scipy_optimize()

        self.motor_helper.close()

    def cost(self):
        # wait for motors to stop moving
        # TODO: make this check motor status
        return -self.count()

    @kernel
    def count(self):

        self.core.break_realtime()

        # get detector counts
        error = True
        num_rising_edges = -1
        while error:
            try:
                gate_end_mu = self.ttl0.gate_rising(1*s)
                num_rising_edges = self.ttl0.count(gate_end_mu)
            except RTIOOverflow:
                print("RTIO input overflow, attenuate signal!")
                # drain counters
                num_rising_edges = 1
                while num_rising_edges != 0:
                    try:
                        num_rising_edges = self.ttl0.count(now_mu())
                    except RTIOOverflow:
                        pass
                        print("RTIO input overflow, attenuate signal!")
            else:
                error = False
                print('counts:', num_rising_edges)
        return num_rising_edges

    @rpc(flags={"async"})
    def set_position(self, name, value):
        self.motors[name].set_position(value)