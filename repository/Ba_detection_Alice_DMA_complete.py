from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment
import os
import time

class Ba_detection_Alice_DMA_complete(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))

        self.setattr_device("core_dma")
        self.detector = self.Alice_camera_side_APD

        self.scan_names = ['dummy', 'cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Alice__sigma_1__frequency', 'DDS__493__Alice__sigma_2__frequency', 'DDS__493__Alice__sigma_1__amplitude', 'DDS__493__Alice__sigma_2__amplitude']
        self.setattr_argument('dummy__scan', Scannable(default=[NoScan(0), RangeScan(1, 10000, 10000)], global_min=0, global_step=1, ndecimals=0))
        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('DDS__493__Alice__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__493__Alice__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__493__Alice__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        self.setattr_argument('DDS__493__Alice__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))

        self.sum11 = 1
        self.sum12 = 1

    @kernel
    def set_DDS_freq(self, channel, freq):
        self.core.reset()
        delay_mu(95000)
        channel.set_frequency(freq)
        delay_mu(6000)

    @kernel
    def set_DDS_amp(self, channel, amp):
        self.core.reset()
        delay_mu(95000)
        channel.set_amplitude(amp)
        delay_mu(6000)

    @kernel
    def prep_record(self):

        with self.core_dma.record("pulses"):
            self.urukul0_ch0.sw.off() # Alice 493 sigma 1
            self.urukul3_ch0.sw.off() # Alice 493 sigma 2
            self.urukul1_ch2.sw.on() # Alice 650 pi
            self.urukul2_ch0.sw.on() # 650 fast AOM
            self.urukul1_ch0.sw.on() # 650 sigma 1
            self.urukul1_ch1.sw.on() # 650 sigma 2
            self.urukul2_ch1.sw.off() # Alice 493 cooling


    @kernel
    def record_pump_sigma1_detect_sigma1(self):
        gate_end_mu_11 = 0
        gate_end_mu_12 = 0
        with self.core_dma.record("sigma_1_pulses"):
            # cooling
            self.urukul0_ch0.sw.on()  # Alice 493 sigma 1
            self.urukul3_ch0.sw.on()  # Alice 493 sigma 2
            self.urukul2_ch1.sw.on() # Alice 493 cooling

            delay(self.cooling_time)

            self.urukul0_ch0.sw.off()
            self.urukul3_ch0.sw.off()
            self.urukul2_ch1.sw.off()

            delay(100*ns)

            # pumping, sigma 1
            self.urukul0_ch0.sw.on()
            delay(self.pumping_time)
            self.urukul0_ch0.sw.off()

            delay(500*ns)

            # detection, sigma 1
            t11 = now_mu()
            gate_end_mu_11 = self.detector.gate_rising(self.detection_time)
            at_mu(t11)

            self.urukul3_ch0.sw.on()
            delay(self.detection_time)
            self.urukul3_ch0.sw.off()
            delay(50*ns)

        return gate_end_mu_11

    @kernel
    def record_pump_sigma1_detect_sigma2(self):
        with self.core_dma.record("sigma_2_pulses"):
            # cooling
            self.urukul0_ch0.sw.on()
            self.urukul3_ch0.sw.on()
            self.urukul2_ch1.sw.on()

            delay(self.cooling_time)

            self.urukul0_ch0.sw.off()
            self.urukul3_ch0.sw.off()
            self.urukul2_ch1.sw.off()

            # pumping, sigma 1
            self.urukul0_ch0.sw.on()
            delay(self.pumping_time)
            self.urukul0_ch0.sw.off()

            delay(500*ns)

            #detection, sigma 2
            t12 = now_mu()
            gate_end_mu_12 = self.detector.gate_rising(self.detection_time)
            at_mu(t12)

            self.urukul0_ch0.sw.on()
            delay(self.detection_time)
            self.urukul0_ch0.sw.off()

            delay(50*ns)

        return gate_end_mu_12

    def run(self):

        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        self.set_dataset('sum11', [], archive=True)
        self.set_dataset('sum12', [], archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect11', 'detect12']], broadcast=True, archive=True, persist=True)
        try:

            # setup the scans to only scan the active variables
            self.scans = [(name, getattr(self, name + '__scan')) for name in self.scan_names]
            self.active_scans = []
            self.active_scan_names = []
            for name, scan in self.scans:
                if isinstance(scan, NoScan):
                    # just set the single value
                    setattr(self, name, scan.value)
                else:
                    self.active_scans.append((name, scan))
                    self.active_scan_names.append(name)
            self.set_dataset('active_scan_names', [bytes(i, 'utf-8') for i in self.active_scan_names], broadcast=True,
                             archive=True, persist=True)
            msm = MultiScanManager(*self.active_scans)

            # assume a 1D scan for plotting
            self.set_dataset('scan_x', [], broadcast=True, archive=True)

            self.point_num = 0
            # Preparation for experiment
            self.kernel_prep_run()

            for point in msm:

                print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # update the plot x-axis ticks
                self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                # update DDS if scanning DDS
                for name in self.active_scan_names:
                    if name.startswith('DDS'):
                        if name.endswith('__frequency'):
                            channel_name = name.rstrip('__frequency')
                            channel = getattr(self, channel_name)
                            self.set_DDS_freq(channel, getattr(self, name))
                        if name.endswith('__amplitude'):
                            channel_name = name.rstrip('__amplitude')
                            channel = getattr(self, channel_name)
                            self.set_DDS_amp(channel, getattr(self, name))


                self.kernel_run()

                ratio11 = self.sum11 / (self.sum11 + self.sum12)
                ratio12 = self.sum12 / (self.sum11 + self.sum12)
                ratios = np.array([ratio11, ratio12])

                self.append_to_dataset('sum11', self.sum11)
                self.append_to_dataset('sum12', self.sum12)
                self.append_to_dataset('ratio_list', ratios)

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                self.point_num += 1

        except TerminationRequested:
            print('Terminated gracefully')

    @kernel
    def kernel_prep_run(self):
        # Preparation for experiment
        self.prep_record()
        pulses_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()
        self.core_dma.playback_handle(pulses_handle)
        self.core.break_realtime()
        #gate_end_mu_11, gate_end_mu_12 = self.record_init()
        #return gate_end_mu_11, gate_end_mu_12

    @kernel
    def kernel_run(self):
        counts11 = 0
        counts12 = 0
        sum11 = 1
        sum12 = 1
        self.core.reset()

        # Pump sigma 1, detect sigma 1

        gate_end_mu_11= self.record_pump_sigma1_detect_sigma1()
        self.core.reset()
        gate_end_mu_12 = self.record_pump_sigma1_detect_sigma2()
        pulses_handle_sigma_1 = self.core_dma.get_handle("sigma_1_pulses")
        pulses_handle_sigma_2 = self.core_dma.get_handle("sigma_2_pulses")
        self.core.reset()
        for i in range(self.detections_per_point):
            delay_mu(5000)
            self.core_dma.playback_handle(pulses_handle_sigma_1)

            counts11 = self.detector.count(gate_end_mu_11)
            sum11 += counts11

            delay_mu(5000)
            at_mu(t)
            self.core_dma.playback_handle(pulses_handle_sigma_2)

            counts12 = self.detector.count(gate_end_mu_12)
            sum12 += counts12

        self.sum11 = sum11
        self.sum12 = sum12



