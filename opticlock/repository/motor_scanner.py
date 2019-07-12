from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

# for motors
import CONEX_TRB

import numpy as np

# for plotting
from PyQt5 import QtGui
import pyqtgraph as pg

import h5py
import time
class motor_scanner(EnvExperiment):

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

        axis='fiber_V'
        center = 7.435
        n = 15
        distance1 = .01
        position = np.linspace(center-distance1, center+distance1, n)
#        counts = np.full(n, np.nan)

        axis2 = 'fiber_H'
        center2 = 1.25
        n2 = 15
        distance2 = .01
        position2 = np.linspace(center2-distance2, center2+distance2, n2)

        axis3 = 'fiber_focus'
        center3 = 6.8
        n3 = 10
        distance3 = .025
        position3 = np.linspace(center3 - distance3, center3 + distance3, n3)

        counts = np.full((n, n2, n3), np.nan)

#        for i in range(len(position)):
#           self.set_position(axis, position[i])
#            counts[i] = self.count()

        for i in range(len(position)):
            if i ==0:
                self.set_position(axis,position[0]-.1)
                time.sleep(1)
            self.set_position(axis, position[i])
            for j in range(len(position2)):
                if j == 0:
                    self.set_position(axis2, position2[0]-.1)
                    time.sleep(1)
                self.set_position(axis2, position2[j])
                time.sleep(1)
                for k in range(len(position3)):
                    if k == 0:
                        self.set_position(axis3, position3[0]-.1)
                        time.sleep(1)
                    self.set_position(axis3, position3[k])
                    time.sleep(1)
                    counts[i, j, k] = self.count()

        self.set_position(axis3, center3-.1)
        self.set_position(axis2, center2-.1)
        self.set_position(axis, center-.1)
        time.sleep(1)
        self.set_position(axis3, center3)
        self.set_position(axis2, center2)
        self.set_position(axis, center)

#        counts2 = np.transpose(counts)
#        [position_array1, position_array2] = np.meshgrid(position, position2)
#        data_array = np.stack((position_array1, position_array2, counts2), axis=0)

        directory = '/home/monroe/Documents/FiberMotorScans/'
        filename = (directory + axis + '_distance' + str(distance1) + '_center' + str(center) + '_' + str(n) + 'points_'
                    + axis2 + '_distance' + str(distance2) + '_center' + str(center2) + '_' + str(n2) + 'points_'
                    + axis3 + '_distance' + str(distance3) + '_center' + str(center3) + '_' + str(n3) + 'points_' +
                    '_scan_data.hdf5')
        h5file = h5py.File(filename, 'w')
        h5file.create_dataset('counts_1', data=counts)
        h5file.close()

        # set to the maximum
        best_counts = np.max(counts)
#        best_position = position[np.argmax(counts)]
        best_position = np.argwhere(counts == best_counts)
#        print('best result: {} counts at position {}'.format(best_counts, best_position))
#        self.set_position(axis, best_position)
        position_final1 = position[best_position[0, 0]]
        position_final2 = position2[best_position[0, 1]]
        print(position_final1, position_final2)
        #self.set_position(axis, position_final1)
        #self.set_position(axis2, position_final2)

        self.motor_helper.close()

#        plt = pg.plot()
#        plt.addLegend()
#        for i in range(len(position)):
#            plt.plot(position2, counts[i, :], pen=(i, len(position)), name=position[i])
#        pg.QtGui.QApplication.exec_()


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



