"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.experiment import *  # TODO: can we import rtio_log without import * ?
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment
import os
import time


class Ba_detection_Bob(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))

        self.scan_names = ['dummy', 'cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Bob__sigma_1__frequency', 'DDS__493__Bob__sigma_2__frequency', 'DDS__493__Bob__sigma_1__amplitude', 'DDS__493__Bob__sigma_2__amplitude']
        self.setattr_argument('dummy__scan', Scannable(default=[NoScan(0), RangeScan(1, 10000, 10000)], global_min=0, global_step=1, ndecimals=0))
        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('DDS__493__Bob__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_1__frequency), CenterScan(self.globals__DDS__493__Bob__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__493__Bob__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_2__frequency), CenterScan(self.globals__DDS__493__Bob__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__493__Bob__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        self.setattr_argument('DDS__493__Bob__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))

        self.detector = self.Bob_camera_side_APD

        #print('{}.build() done'.format(self.__class__))

    @kernel
    def cool(self):

        delay_mu(100000)
        self.DDS__493__Bob__sigma_1.sw.on()
        self.DDS__493__Bob__sigma_2.sw.on()
        #self.DDS__493__Bob__pi.sw.on()

        delay(self.cooling_time)

        self.DDS__493__Bob__sigma_1.sw.off()
        self.DDS__493__Bob__sigma_2.sw.off()
        #self.DDS__493__Bob__pi.sw.off()

    @kernel
    def pump1(self):
        self.DDS__493__Bob__sigma_1.sw.pulse(self.pumping_time)

    @kernel
    def pump2(self):
        self.DDS__493__Bob__sigma_2.sw.pulse(self.pumping_time)

    @kernel
    def detect1(self):
        t = now_mu()
        gate_end_mu = self.detector.gate_rising(self.detection_time)
        at_mu(t)
        self.DDS__493__Bob__sigma_1.sw.on()
        delay(self.detection_time)
        self.DDS__493__Bob__sigma_1.sw.off()

        delay_mu(100000)

        return self.detector.count(gate_end_mu)

    @kernel
    def detect2(self):
        t = now_mu()
        gate_end_mu = self.detector.gate_rising(self.detection_time)
        at_mu(t)
        self.DDS__493__Bob__sigma_2.sw.on()
        delay(self.detection_time)
        self.DDS__493__Bob__sigma_2.sw.off()

        delay_mu(100000)

        return self.detector.count(gate_end_mu)

    @kernel
    def setup(self):

        delay_mu(10000)
        self.DDS__493__Bob__sigma_1.sw.off()
        self.DDS__493__Bob__sigma_2.sw.off()
        self.DDS__650__sigma_1.sw.on()
        self.DDS__650__sigma_2.sw.on()
        self.DDS__650__Bob__pi.sw.on()
        self.DDS__650__fast_AOM.sw.on()
        #self.DDS__493__Bob__pi.sw.off()

    @kernel
    def unsetup(self):

        delay_mu(10000)
        self.DDS__493__Bob__sigma_1.sw.on()
        self.DDS__493__Bob__sigma_2.sw.on()
        self.DDS__650__sigma_1.sw.on()
        self.DDS__650__sigma_2.sw.on()
        self.DDS__650__Bob__pi.sw.on()
        self.DDS__650__fast_AOM.sw.on()
        #self.DDS__493__Bob__pi.sw.on()

    def run(self):

        self.experiment_specific_preamble()

        try:  # catch TerminationRequested

            # setup the scans to only scan the active variables
            self.scans = [(name, getattr(self, name+'__scan')) for name in self.scan_names]
            self.active_scans = []
            self.active_scan_names = []
            for name, scan in self.scans:
                if isinstance(scan, NoScan):
                    # just set the single value
                    setattr(self, name, scan.value)
                else:
                    self.active_scans.append((name, scan))
                    self.active_scan_names.append(name)
            self.set_dataset('active_scan_names', [bytes(i, 'utf-8') for i in self.active_scan_names], broadcast=True, archive=True, persist=True)
            msm = MultiScanManager(*self.active_scans)

            # assume a 1D scan for plotting
            self.set_dataset('scan_x', [], broadcast=True, archive=True)

            self.point_num = 0

            for point in msm:

                #print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # update the plot x-axis ticks
                self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                self.experiment_specific_run()

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                self.point_num += 1

        except TerminationRequested:
            print('Terminated gracefully')

    def experiment_specific_preamble(self):
        self.set_dataset('ratio_list',[], broadcast=True, archive=True)
        self.set_dataset('sum11', [], archive=True)
        self.set_dataset('sum12', [], archive=True)
        self.set_dataset('sum21', [], archive=True)
        self.set_dataset('sum22', [], archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['pump1', 'pump2', 'detect1', 'detect2']], broadcast=True, archive=True, persist=True)

    def experiment_specific_run(self):

        self.sum11 = 0
        self.sum12 = 0
        self.sum21 = 0
        self.sum22 = 0

        if self.point_num == 0:
            self.coreanalyzer_purge()
            try:
                self.kernel_run()
            finally:
                self.coreanalyzer_write()
        else:
            self.kernel_run()

        # export ratio of detections
        pump1 = self.sum11 / (self.sum11 + self.sum12)
        pump2 = self.sum21 / (self.sum21 + self.sum22)
        detect1 = self.sum11 / (self.sum11 + self.sum21)
        detect2 = self.sum12 / (self.sum12 + self.sum22)

        ratios = np.array([pump1, pump2, detect1, detect2])

        self.append_to_dataset('sum11', self.sum11)
        self.append_to_dataset('sum12', self.sum12)
        self.append_to_dataset('sum21', self.sum21)
        self.append_to_dataset('sum22', self.sum22)
        self.append_to_dataset('ratio_list', ratios)

    @kernel
    def kernel_run(self):

        self.core.reset()

        delay_mu(18000)
        rtio_log('msg', '1')
        delay_mu(18000)
        rtio_log('msg', '2')
        delay_mu(18000)
        rtio_log('msg', '3')
        delay_mu(18000)
        rtio_log('msg', '4')


        # update DDS frequency and amplitude at each step
        delay_mu(100000)
        self.DDS__493__Bob__sigma_1.set(self.DDS__493__Bob__sigma_1__frequency, amplitude=self.DDS__493__Bob__sigma_1__amplitude)

        delay_mu(18000)
        rtio_log('msg', '2')

        delay_mu(100000)
        self.DDS__493__Bob__sigma_2.set(self.DDS__493__Bob__sigma_2__frequency, amplitude=self.DDS__493__Bob__sigma_2__amplitude)

        delay_mu(18000)
        rtio_log('msg', '3')

        delay_mu(100000)

        self.setup()

        delay_mu(18000)
        rtio_log('msg', '4')


        trials = 0

        while (trials <= self.max_trials_per_point) and ((self.sum11 + self.sum12 +self.sum21 + self.sum22) < self.detections_per_point):

            delay_mu(22000)
            rtio_log('msg', 'starting trial ', trials, 'sum11 ', self.sum11, 'sum12 ', self.sum12, 'sum21', self.sum21, 'sum22', self.sum22)

            delay_mu(18000)
            rtio_log('msg', '5')

            self.cool()
            self.pump1()
            self.sum11 += self.detect1()

            delay_mu(18000)
            rtio_log('msg', '6')

            self.cool()
            self.pump1()
            self.sum12 += self.detect2()

            delay_mu(18000)
            rtio_log('msg', '7')

            self.cool()
            self.pump2()
            self.sum21 += self.detect1()

            delay_mu(18000)
            rtio_log('msg', '8')

            self.cool()
            self.pump2()
            self.sum22 += self.detect2()

            delay_mu(18000)
            rtio_log('msg', '9')

            trials += 1

        delay_mu(18000)
        rtio_log('msg', '10')

        self.unsetup()

        delay_mu(18000)
        rtio_log('msg', '11')

