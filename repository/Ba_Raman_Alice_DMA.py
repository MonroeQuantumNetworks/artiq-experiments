""" Legacy script
Alice Barium Raman frequency+time scan script using DMA

    Simple script to do a Raman time and frequency scan on Alice

    Does Cool/Pump1/Detect1&2 - No Pump2
    Hardcoded urukul channels, but names are listed in this script
    Does not have functions experiment_specific_run(self) and experiment_specific_preamble(self)

    Line 188: Dataset Ba_detection_names seemingly unused. For applet labels?

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


class Ba_Raman_Alice_DMA(base_experiment.base_experiment):
    kernel_invariants = {"raman_time", "DDS__493__Alice__sigma_1__frequency", "DDS__493__Alice__sigma_2__frequency", "DDS__532__tone_1__frequency", "DDS__532__tone_2__frequency"}

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))

        self.setattr_device("core_dma")
        self.detector = self.Alice_camera_side_APD

        self.scan_names = ['dummy', 'cooling_time', 'pumping_time', 'detection_time', 'raman_time', 'DDS__493__Alice__sigma_1__frequency', 'DDS__493__Alice__sigma_2__frequency', 'DDS__493__Alice__sigma_1__amplitude', 'DDS__493__Alice__sigma_2__amplitude','DDS__532__tone_1__frequency', 'DDS__532__tone_2__frequency']
        self.setattr_argument('dummy__scan', Scannable(default=[NoScan(0), RangeScan(1, 10000, 10000)], global_min=0, global_step=1, ndecimals=0))
        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('raman_time__scan', Scannable(default=[NoScan(self.globals__timing__raman_time), RangeScan(0*us, 3*self.globals__timing__raman_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('DDS__493__Alice__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__493__Alice__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__493__Alice__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        self.setattr_argument('DDS__493__Alice__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        self.setattr_argument('DDS__532__tone_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__532__tone_1__frequency), CenterScan(self.globals__DDS__532__tone_1__frequency/MHz, 1, 0.1)], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__532__tone_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__532__tone_2__frequency), CenterScan(self.globals__DDS__532__tone_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))


        self.sum11 = 1
        self.sum12 = 1

    @kernel
    def set_DDS_freq(self, channel, freq):
        self.core.reset()
        delay_mu(95000)
        channel.set_frequency(freq)

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
            self.urukul1_ch0.sw.on() # 650 sigma 1
            self.urukul1_ch1.sw.on() # 650 sigma 2
            self.urukul2_ch1.sw.off() # Alice 493 cooling
            delay(8*ns)
            self.urukul2_ch2.sw.on()
            self.urukul2_ch3.sw.on()
            self.ttl14.off()


    @kernel
    def record_pump_sigma1_detect_sigma1(self):
        gate_end_mu_11 = 0
        gate_end_mu_12 = 0
        with self.core_dma.record("pulses"):
            self.ttl12.pulse(100*ns)
            # cooling
            with parallel:
                #self.urukul2_ch2.sw.on()
                #self.urukul2_ch3.sw.off()
                self.ttl14.off()
            delay(8*ns)
            with parallel:
                self.urukul0_ch0.sw.on()  # Alice 493 sigma 1
                self.urukul3_ch0.sw.on()  # Alice 493 sigma 2

            delay(self.cooling_time)

            with parallel:
                self.urukul0_ch0.sw.off()
                self.urukul3_ch0.sw.off()

            delay(1000*ns)

            # pumping, sigma 1
            self.urukul0_ch0.sw.on()
            delay(self.pumping_time)
            self.urukul0_ch0.sw.off()

            delay(1000*ns)

            # Raman
            self.ttl14.pulse(self.raman_time)
            # with parallel:
            #     self.urukul2_ch2.sw.pulse(self.raman_time)
            #     self.urukul2_ch3.sw.pulse(self.raman_time)
            # #self.urukul2_ch3.sw.pulse(self.raman_time)

            delay(1000*ns)
            # detection, sigma 1
            t11 = now_mu()
            gate_end_mu_11 = self.detector.gate_rising(self.detection_time)
            at_mu(t11-1100)

            self.urukul0_ch0.sw.on()
            delay(self.detection_time)
            self.urukul0_ch0.sw.off()

            delay(50*ns)
        return gate_end_mu_11

    @kernel
    def record_pump_sigma1_detect_sigma2(self):
        with self.core_dma.record("pulses"):
            # cooling
            with parallel:
                #self.urukul2_ch2.sw.on()
                #self.urukul2_ch3.sw.on()
                self.ttl14.off()
            delay(8*ns)
            with parallel:
                self.urukul0_ch0.sw.on()
                self.urukul3_ch0.sw.on()

            delay(self.cooling_time)

            with parallel:
                self.urukul0_ch0.sw.off()
                self.urukul3_ch0.sw.off()

            delay(1000*ns)

            # pumping, sigma 1
            self.urukul0_ch0.sw.on()
            delay(self.pumping_time)
            self.urukul0_ch0.sw.off()

            delay(1000*ns)

            # Raman
            self.ttl14.pulse(self.raman_time)
            # with parallel:
            #     self.urukul2_ch2.sw.pulse(self.raman_time)
            #     self.urukul2_ch3.sw.pulse(self.raman_time)

            #self.urukul2_ch3.sw.pulse(self.raman_time)

            delay(1000*ns)

            #detection, sigma 2
            t12 = now_mu()
            gate_end_mu_12 = self.detector.gate_rising(self.detection_time)
            at_mu(t12-1100)

            self.urukul3_ch0.sw.on()
            delay(self.detection_time)
            self.urukul3_ch0.sw.off()

        return gate_end_mu_12


    def run(self):

        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        self.set_dataset('sum11', [], broadcast=True, archive=True)
        self.set_dataset('sum12', [], broadcast=True, archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['sum11', 'sum12', 'detect11', 'detect12']], broadcast=True, archive=True, persist=True)
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

            for point in msm:

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
                            #self.set_DDS_freq(channel, getattr(self, name))
                        if name.endswith('__amplitude'):
                            channel_name = name.rstrip('__amplitude')
                            channel = getattr(self, channel_name)
                            #self.set_DDS_amp(channel, getattr(self, name))
                kernel_run_start_time = time.time()
                self.kernel_run()

                ratio11 = self.sum11 / (self.sum11 + self.sum12)
                ratio12 = self.sum12 / (self.sum11 + self.sum12)
                ratios = np.array([self.sum11, self.sum12, ratio11, ratio12])

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
        self.core.reset()
        counts11 = 0
        counts12 = 0
        sum11 = 1
        sum12 = 1

          # update DDS frequency and amplitude at each step
        delay(600*us)
        self.urukul0_ch0.set_frequency(self.DDS__493__Alice__sigma_1__frequency)
        self.core.break_realtime()
        print(self.DDS__493__Alice__sigma_1__frequency)
        self.core.break_realtime()
        delay(600*us)
        self.urukul3_ch0.set_frequency(self.DDS__493__Alice__sigma_2__frequency)
        self.core.break_realtime()
        delay(600 * us)
        self.urukul2_ch2.set(self.DDS__532__tone_1__frequency, phase=0.0)
        self.core.break_realtime()
        delay(600*us)
        self.urukul2_ch3.set(self.DDS__532__tone_2__frequency, phase=0.1)
        self.core.break_realtime()
        delay(600 * us)
        self.core.reset()


        gate_end_mu_11 = self.record_pump_sigma1_detect_sigma1()
        pulses_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()
        for i in range(self.detections_per_point):
            delay_mu(5000)
            self.core_dma.playback_handle(pulses_handle)

            counts11 = self.detector.count(gate_end_mu_11)
            sum11 += counts11

        gate_end_mu_12 = self.record_pump_sigma1_detect_sigma2()
        pulses_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()

        for i in range(self.detections_per_point):
            delay_mu(5000)
            self.core_dma.playback_handle(pulses_handle)

            counts12 = self.detector.count(gate_end_mu_12)
            sum12 += counts12

        self.sum11 = sum11
        self.sum12 = sum12




