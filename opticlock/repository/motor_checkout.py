from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

# for motors
import CONEX_TRB

import numpy as np

class motor_checkout(EnvExperiment):

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


        self.motor_helper.list_motor_limits()
        self.motor_helper.get_positions()


        self.motor_helper.close()

    @kernel
    def count(self):

        self.core.break_realtime()

        # get detector counts
        error = True
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
                print('counts', num_rising_edges)
                return num_rising_edges

    @rpc(flags={"async"})
    def set_position(self, name, value):
        self.motors.set_position(name, value)

