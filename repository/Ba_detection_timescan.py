"""This idle program reads out 8 counters while blinking "I D L E" in morse code on LED0."""

from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment


class Ba_detection_timescan(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('max_trials_per_point', NumberValue(10000, ndecimals=0, min=1, step=1))
        self.setattr_argument('detection_time_scan', Scannable( default=RangeScan(1*us,100*us,100), global_min=0*us, global_step=1*us, unit='us', ndecimals=3 ) )
        #self.detection_time = self.globals__timing__detection_time
        #self.detection_time = float(self.detection_time)
        print('Ba_detection_timescan.py build() done')

    @kernel
    def cool(self):

        delay_mu(100000)
        self.DDS__493__Bob__sigma_1.sw.on()
        self.DDS__493__Bob__sigma_2.sw.on()
        self.DDS__493__Bob__pi.sw.on()

        delay(self.globals__timing__cooling_time)

        self.DDS__493__Bob__sigma_1.sw.off()
        self.DDS__493__Bob__sigma_2.sw.off()
        self.DDS__493__Bob__pi.sw.off()

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

    def run(self):

        self.set_dataset('ratio_list',[], archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['pump1', 'pump2', 'detect1', 'detect2']], broadcast=True, archive=True, persist=True)

        try:  # catch TerminationRequested
            #while True:
            for self.detection_time in self.detection_time_scan:
                print('detection_time:', self.detection_time)

                self.core.reset()

                self.sum11 = 0
                self.sum12 = 0
                self.sum21 = 0
                self.sum22 = 0

                self.kernel_run()
                # export ratio of detections
                ratios = np.array([self.sum11 / (self.sum11 + self.sum12), self.sum21 / (self.sum21 + self.sum22), self.sum11 / (self.sum11 + self.sum21), self.sum12 / (self.sum12 + self.sum22)])

                #print('sum 11:', self.sum11, 'sum12:', self.sum12, 'sum21:', self.sum21, 'sum22', self.sum22)
                #print("['pump1', 'pump2', 'detect1', 'detect2']", ratios)

                self.set_dataset('Ba_detection_ratios', ratios, broadcast=True, archive=True)
                self.append_to_dataset('ratio_list', ratios)

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

        except TerminationRequested:
            print('Terminated gracefully')

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
            self.sum11 += self.detect1()

            self.cool()
            self.pump1()
            self.sum12 += self.detect2()

            self.cool()
            self.pump2()
            self.sum21 += self.detect1()

            self.cool()
            self.pump2()
            self.sum22 += self.detect2()

            trials += 1
