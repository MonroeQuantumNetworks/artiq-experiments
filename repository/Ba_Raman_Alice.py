""" Legacy script
Alice Barium Raman frequency+time scan script

    Simple script to do a Raman time and frequency scan on Alice

    Does Cool/Pump1/Detect1&2 - No Pump2
    Hardcoded urukul channels, but names are listed in this script
    Uses functions experiment_specific_run(self) and experiment_specific_preamble(self) to insert the code to be run
    Line 220: Runs coreanalyzer purge??

George Toh 2020-04-20
"""

import time

from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment


class Ba_Raman_Alice(base_experiment.base_experiment):
    kernel_invariants = {"raman_time", "detection_time"}
    def build(self):
        start_time = time.time()
        super().build()
        print("build_time: {}".format(time.time() - start_time))
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))
        self.setattr_argument('cooling_time', NumberValue(5e-6, unit='us', min=0*us, ndecimals=3))
        self.setattr_argument('pumping_time', NumberValue(5e-6, unit='us', min=0*us, ndecimals=3))
        self.setattr_argument('detection_time', NumberValue(1e-6, unit='us', min=0*us, ndecimals=3))
        self.scan_names = ['raman_time', 'DDS__532__tone_2__frequency']

        self.setattr_argument('raman_time__scan', Scannable(default=[NoScan(self.globals__timing__raman_time), RangeScan(0*us, 3*self.globals__timing__raman_time, 100)], global_min=0*us, global_step=1, unit='us', ndecimals=3))
        self.setattr_argument('DDS__532__tone_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__532__tone_2__frequency), CenterScan(self.globals__DDS__532__tone_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))

        self.detector = self.Alice_camera_side_APD
    @kernel
    def setup(self):

        self.ttl11.off()
        delay_mu(8)
        self.urukul0_ch0.sw.off()
        delay_mu(8)
        self.urukul3_ch0.sw.off()
        delay_mu(8)
        self.urukul1_ch2.sw.off()
        delay_mu(8)
        self.urukul2_ch2.sw.off()
        delay_mu(8)
        self.urukul2_ch3.sw.off()
        delay(10*ns)
        with parallel:
            self.urukul1_ch0.sw.on()
            self.urukul1_ch1.sw.on()

    @kernel
    def cool(self):
        with parallel:
            self.ttl11.on()
            self.urukul0_ch0.sw.on()
            self.urukul3_ch0.sw.on()
            self.urukul1_ch2.sw.on()

        delay(self.cooling_time)

        with parallel:
            self.ttl11.off()
            self.urukul0_ch0.sw.off()
            self.urukul3_ch0.sw.off()
            self.urukul1_ch2.sw.off()
        delay(1*us)

    @kernel
    def pump1(self):
        with parallel:
            self.ttl11.on()
            self.urukul0_ch0.sw.on()
            self.urukul1_ch2.sw.on()

        delay(self.pumping_time)

        with parallel:
            self.ttl11.off()
            self.urukul0_ch0.sw.off()
            self.urukul1_ch2.sw.off()


    @kernel
    def pump2(self):
        with parallel:
            self.ttl11.on()
            self.urukul3_ch0.sw.on()
            self.urukul1_ch2.sw.on()

        delay(self.pumping_time)

        with parallel:
            self.ttl11.off()
            self.urukul3_ch0.sw.off()
            self.urukul1_ch2.sw.off()

    @kernel
    def detect1(self):
        delay_mu(75000)
        t = now_mu()
        gate_end_mu = self.detector.gate_rising(self.detection_time)
        at_mu(t)
        with parallel:
            self.ttl11.on()
            self.urukul0_ch0.sw.on()
            self.urukul1_ch2.sw.on()

        delay(self.detection_time)
        with parallel:
            self.ttl11.off()
            self.urukul0_ch0.sw.off()
            self.urukul1_ch2.sw.off()
        return self.detector.count(gate_end_mu)

    @kernel
    def detect2(self):
        delay_mu(75000)
        t = now_mu()
        gate_end_mu = self.detector.gate_rising(self.detection_time)
        at_mu(t)
        with parallel:
            self.ttl11.on()
            self.urukul0_ch0.sw.on()
            self.urukul1_ch2.sw.on()

        delay(self.detection_time)
        with parallel:
            self.ttl11.off()
            self.urukul0_ch0.sw.off()
            self.urukul1_ch2.sw.off()


        return self.detector.count(gate_end_mu)

    @kernel
    def raman(self):
        with parallel:
            self.urukul2_ch2.sw.on()
            self.urukul2_ch3.sw.on()
        delay(self.raman_time)
        with parallel:
            self.urukul2_ch2.sw.off()
            self.urukul2_ch3.sw.off()
        delay(6*us)

    @kernel
    def unsetup(self):

        delay_mu(50000)
        self.ttl11.on()
        self.urukul0_ch0.sw.on()
        self.urukul3_ch0.sw.on()
        self.urukul1_ch2.sw.on()

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
            #     for name in self.active_scan_names:
            #         setattr(self, name, getattr(point, name))
                self.raman_time = getattr(point, 'raman_time')
                # update the plot x-axis ticks
                self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                self.experiment_specific_run()

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()
                self.point_num += 1
        except TerminationRequested:
            print('Terminated gracefully')
            self.unsetup()


    def experiment_specific_preamble(self):
        self.set_dataset('ratio_list',[], broadcast=True, archive=True)
        self.set_dataset('sum11', [], archive=True)
        self.set_dataset('sum12', [], archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect1', 'detect2']], broadcast=True, archive=True, persist=True)

    def experiment_specific_run(self):
        exp_start_time = time.time()
        self.sum11 = 0
        self.sum12 = 0
        if self.point_num == 0:

            self.coreanalyzer_purge()
            core_purge_time = time.time()
            print("Coreanalyzer purge time: {}".format(core_purge_time-exp_start_time))
            try:
                self.kernel_run()
            finally:
                kernel_run_time = time.time()
                print("run time: {}".format(kernel_run_time - core_purge_time))
                self.coreanalyzer_write()
                print("coreanalyzer write time: {}".format(time.time() - kernel_run_time))
        else:
            try:
                self.kernel_run()
            finally:
                print("kernel run time: {}".format(time.time() - exp_start_time))

        # export ratio of detections
        detect1 = self.sum11 / (self.sum11 + self.sum12)
        detect2 = self.sum12 / (self.sum11 + self.sum12)

        ratios = np.array([detect1, detect2])

        self.append_to_dataset('sum11', self.sum11)
        self.append_to_dataset('sum12', self.sum12)
        self.append_to_dataset('ratio_list', ratios)

    @kernel
    def kernel_run(self):
        self.setup()

        self.core.reset()

        # update DDS frequency and amplitude at each step
        # self.DDS__532__tone_2.set(self.DDS__532__tone_2__frequency)
        # delay(200*us)

        trials = 0
        while (trials <= self.max_trials_per_point) and ((self.sum11 + self.sum12) < self.detections_per_point):
            delay(170*us)
            self.cool()
            self.pump1()
            #self.raman()
            self.sum11 += self.detect1()

            delay(170*us)
            self.cool()
            self.pump1()
            #self.raman()
            self.sum12 += self.detect2()
            trials += 1
