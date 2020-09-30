""" Legacy script
Alice Barium Raman frequency+time scan script using DMA and AWG

    Simple script to do a Raman time scan on Alice (Frequency fixed)

    Does Cool/Pump1/Detect1&2 - No Pump2
    Hardcoded urukul channels, but names are listed in this script
    Does not have functions experiment_specific_run(self) and experiment_specific_preamble(self)

    Line 186: Dataset Ba_detection_names seemingly unused. For applet labels?
    Waveforms are hardcoded: (Line 198)
            waveform1 = 0.115*(np.sin(2 * np.pi * 106.9 * MHz * t) + np.sin(2 * np.pi * 113.2 * MHz * t))
            waveform2 = np.sin(2 * np.pi * 85 * MHz * t)

George Toh 2020-04-20
"""

import time
from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment
from Lecroy1102 import Lecroy1102


class Alice_Ba_Raman_AWG_DMA(base_experiment.base_experiment):
    kernel_invariants = {"raman_time", "cooling_time", "pumping_time", "detection_time"}

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))

        self.setattr_device("core_dma")
        self.detector = self.Alice_camera_side_APD

        self.scan_names = ['dummy', 'cooling_time', 'pumping_time', 'detection_time', 'raman_time']
        self.setattr_argument('dummy__scan', Scannable(default=[NoScan(0), RangeScan(1, 10000, 10000)], global_min=0, global_step=1, ndecimals=0))
        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('raman_time__scan', Scannable(default=[NoScan(self.globals__timing__raman_time), RangeScan(0*us, 3*self.globals__timing__raman_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))

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
            # cooling
            with parallel:
                #self.urukul2_ch2.sw.on()
                #self.urukul2_ch3.sw.off()
                self.ttl14.off()
                self.ttl12.off()
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
            with parallel:
                self.ttl14.pulse(20*us)
                self.ttl12.pulse(self.raman_time)

            delay(20*us)
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
                self.ttl12.off()
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
            with parallel:
                self.ttl14.pulse(20*us)
                self.ttl12.pulse(self.raman_time)

            delay(20*us)

            #detection, sigma 2
            t12 = now_mu()
            gate_end_mu_12 = self.detector.gate_rising(self.detection_time)
            at_mu(t12-1100)

            self.urukul3_ch0.sw.on()
            delay(self.detection_time)
            self.urukul3_ch0.sw.off()

        return gate_end_mu_12


    def run(self):

        # Define AWG information
        IP_address = '192.168.1.100'  # server is running on JARVIS
        port = 11000
        sample_rate = 250 * MHz
        ext_clock_frequency = 10 * MHz

        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        self.set_dataset('sum11', [], broadcast=True, archive=True)
        self.set_dataset('sum12', [], broadcast=True, archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['sum11', 'sum12', 'detect11', 'detect12']], broadcast=True, archive=True, persist=True)

        # Program AWG
        try:
            awg = Lecroy1102(IP_address, port, sample_rate, ext_clock_frequency)
            awg.open()
            if not awg.enabled:
                return
            print('awg.sample_length', awg.sample_length)
            t = np.arange(0, 20*us, awg.sample_length)
            print('length t:', len(t))
            waveform1 = 0.115*(np.sin(2 * np.pi * 106.9 * MHz * t) + np.sin(2 * np.pi * 113.2 * MHz * t))
            waveform2 = np.sin(2 * np.pi * 85 * MHz * t)
            awg.program(waveform1, waveform2)
            self.set_dataset('waveforms', np.array([q for q in zip(waveform1, waveform2)]), broadcast=True,
                             persist=True, archive=True)
            self.set_dataset('waveform1', waveform1, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform2', waveform2, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_names', [bytes(i, 'utf-8') for i in ['channel 1', 'channel 2']], broadcast=True,
                             persist=True, archive=True)
            self.set_dataset('waveform_t', t, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_x_names', [bytes(i, 'utf-8') for i in ['time']], broadcast=True, persist=True,
                             archive=True)
        finally:
            awg.close()
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

                kernel_run_start_time = time.time()
                self.kernel_run()
                print("Kernel run time: {}".format(time.time()-kernel_run_start_time))

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




