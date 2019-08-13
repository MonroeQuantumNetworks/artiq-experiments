"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment


class Ba_detection_timescan_multiscan(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))

        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'Raman_time']
        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('Raman_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))


        print('Raman_rotation.py build() done')

    @kernel
    def cool(self):

        delay_mu(100000)
        self.DDS__493__Bob__sigma_1.sw.on()
        self.DDS__493__Bob__sigma_2.sw.on()
        #self.DDS__493__Bob__pi.sw.on()

        delay(self.globals__timing__cooling_time)

        self.DDS__493__Bob__sigma_1.sw.off()
        self.DDS__493__Bob__sigma_2.sw.off()
        #self.DDS__493__Bob__pi.sw.off()

    @kernel
    def pump1(self):
        self.DDS__493__Bob__sigma_1.sw.pulse(self.globals__timing__pumping_time)

    @kernel
    def pump2(self):
        self.DDS__493__Bob__sigma_2.sw.pulse(self.globals__timing__pumping_time)

    @kernel
    def detect1(self):
        t = now_mu()
        gate_end_mu = self.Bob_camera_side_APD.gate_rising(self.detection_time)
        at_mu(t)
        self.DDS__493__Bob__sigma_1.sw.on()
        delay(self.detection_time)
        self.DDS__493__Bob__sigma_1.sw.off()

        delay_mu(100000)

        return self.Bob_camera_side_APD.count(gate_end_mu)

    @kernel
    def detect2(self):
        t = now_mu()
        gate_end_mu = self.Bob_camera_side_APD.gate_rising(self.detection_time)
        at_mu(t)
        self.DDS__493__Bob__sigma_2.sw.on()
        delay(self.detection_time)
        self.DDS__493__Bob__sigma_2.sw.off()

        delay_mu(100000)

        return self.Bob_camera_side_APD.count(gate_end_mu)

    def Raman_rotation(self):
        self.DDS__532__AOM1.sw.pulse(self.globals__timing__Raman_time)

    @kernel
    def setup(self):

        delay_mu(10000)
        self.DDS__493__Bob__sigma_1.sw.off()
        self.DDS__493__Bob__sigma_2.sw.off()
        self.DDS__650__sigma_1.sw.on()
        self.DDS__650__sigma_2.sw.on()
        self.DDS__650__Bob__pi.sw.on()
        self.DDS__650__fast_AOM.sw.on()
        self.DDS__493__Bob__pi.sw.off()

    @kernel
    def unsetup(self):

        delay_mu(10000)
        self.DDS__493__Bob__sigma_1.sw.on()
        self.DDS__493__Bob__sigma_2.sw.on()
        self.DDS__650__sigma_1.sw.on()
        self.DDS__650__sigma_2.sw.on()
        self.DDS__650__Bob__pi.sw.on()
        self.DDS__650__fast_AOM.sw.on()
        self.DDS__493__Bob__pi.sw.on()

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

        self.core.reset()

        self.sum11 = 0
        self.sum12 = 0
        self.sum21 = 0
        self.sum22 = 0

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

        self.core.break_realtime()
        delay_mu(25000)
        rtio_log('msg', 'after reset')

        self.setup()

        trials = 0

        while (trials <= self.max_trials_per_point) and ((self.sum11 + self.sum12 +self.sum21 + self.sum22) < self.detections_per_point):

            delay_mu(25000)
            rtio_log('msg', 'starting trial ', trials, 'sum11 ', self.sum11, 'sum12 ', self.sum12, 'sum21', self.sum21, 'sum22', self.sum22)

            self.cool()
            self.pump1()
            self.Raman_rotation()
            self.sum11 += self.detect1()

            self.cool()
            self.pump1()
            self.Raman_rotation()
            self.sum12 += self.detect2()

            self.cool()
            self.pump2()
            self.Raman_rotation()
            self.sum21 += self.detect1()

            self.cool()
            self.pump2()
            self.Raman_rotation()
            self.sum22 += self.detect2()

            trials += 1

        self.unsetup()


