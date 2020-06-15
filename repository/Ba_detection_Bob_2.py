""" Untested modified Legacy script
Bob Barium detection using DMA, with scannable variables
Automatically does both pump12 and detect12

    Hard-coded urukul channels have been modified into readable names
    650 remains ON for all cool/pump/detect stages
    Repeats pump1/detect1 many times, then does pump1/detect2 many times
    
Changed ttl11 (650 fast) to ttl_650_fast_cw

George Toh 2020-06-12
"""
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

class Ba_detection_Bob_DMA(base_experiment.base_experiment):
    # """Experiment for Time Scans - Bob.
    # """

    def build(self):
        super().build()
        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('detection_points', NumberValue(10000, ndecimals=0, min=1, step=1))

        self.setattr_device("core_dma")
        self.detector = self.Bob_camera_side_APD

        # self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Bob__sigma_1__frequency', 'DDS__493__Bob__sigma_2__frequency', 'DDS__493__Bob__sigma_1__amplitude', 'DDS__493__Bob__sigma_2__amplitude']
        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        # self.setattr_argument('DDS__493__Bob__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_1__frequency), CenterScan(self.globals__DDS__493__Bob__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Bob__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_2__frequency), CenterScan(self.globals__DDS__493__Bob__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Bob__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        # self.setattr_argument('DDS__493__Bob__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))

        self.sum11 = 0
        self.sum12 = 0
        self.sum21 = 0
        self.sum22 = 0

    @kernel
    def prep_record(self):
        # This is used for detection
        with self.core_dma.record("pulses"):
            self.DDS__493__Bob__sigma_1.sw.off() # Bob 493 sigma 1
            self.DDS__493__Bob__sigma_2.sw.off() # Bob 493 sigma 2
            self.ttl_650__Bob__pi.on() # Bob 650 pi
            self.ttl_650__fast_AOM.on() # 650 fast AOM
            self.ttl_650__sigma_1.on() # 650 sigma 1
            self.ttl_650__sigma_2.on() # 650 sigma 2

    @kernel
    def record_pump_sigma1_detect_sigma1(self):
        gate_end_mu_11 = 0

        with self.core_dma.record("pulses"):
            # cooling
            self.DDS__493__Bob__sigma_1.sw.on()  # Bob 493 sigma 1
            self.DDS__493__Bob__sigma_2.sw.on()  # Bob 493 sigma 2

            delay(self.cooling_time)

            self.DDS__493__Bob__sigma_1.sw.off()
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

            # pumping, sigma 1
            self.DDS__493__Bob__sigma_1.sw.on()
            delay(self.pumping_time)
            self.DDS__493__Bob__sigma_1.sw.off()

            delay(10*ns)

            # detection, sigma 1
            t11 = now_mu()
            gate_end_mu_11 = self.detector.gate_rising(self.detection_time)
            at_mu(t11)

            self.DDS__493__Bob__sigma_1.sw.on()
            delay(self.detection_time)
            self.DDS__493__Bob__sigma_1.sw.off()

            delay(10*ns)

        return gate_end_mu_11

    @kernel
    def record_pump_sigma1_detect_sigma2(self):
        gate_end_mu_12 = 0

        with self.core_dma.record("pulses"):
            # cooling
            self.DDS__493__Bob__sigma_1.sw.on()  # Bob 493 sigma 1
            self.DDS__493__Bob__sigma_2.sw.on()  # Bob 493 sigma 2

            delay(self.cooling_time)

            self.DDS__493__Bob__sigma_1.sw.off()
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

            # pumping, sigma 1
            self.DDS__493__Bob__sigma_1.sw.on()
            delay(self.pumping_time)
            self.DDS__493__Bob__sigma_1.sw.off()

            delay(10*ns)

            # detection, sigma 1
            t12 = now_mu()
            gate_end_mu_12 = self.detector.gate_rising(self.detection_time)
            at_mu(t12)

            self.DDS__493__Bob__sigma_2.sw.on()
            delay(self.detection_time)
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

        return gate_end_mu_12

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

    def run(self):

        self.set_dataset('ratio_list1', [], broadcast=True, archive=True)
        self.set_dataset('sum11', [], archive=True)
        self.set_dataset('sum12', [], archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect1', 'detect2']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list2', [], broadcast=True, archive=True)
        self.set_dataset('sum21', [], archive=True)
        self.set_dataset('sum22', [], archive=True)

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Time"
        xlabel = "Ratios"
        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Plot_Fit_Test",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "ratio_list1, ratiolist2" 
            # + " --x-fit " + "xfitdataset"
            # + " --y-fits " + "yfitdataset"
            + " --y-label "
            + "'"
            + ylabel
            + "'"
            + " --x-label "
            + "'"
            + xlabel
            + "'"
        )

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

                # Run the main portion of code here
                self.kernel_run()

                # For pumping with sigma1
                ratio11 = self.sum11 / (self.sum11 + self.sum12)
                ratio12 = self.sum12 / (self.sum11 + self.sum12)
                ratios = np.array([ratio11, ratio12])

                self.append_to_dataset('sum11', self.sum11)
                self.append_to_dataset('sum12', self.sum12)
                self.append_to_dataset('ratio_list1', ratios)

                # For pumping with sigma2
                ratio11 = self.sum21 / (self.sum21 + self.sum22)
                ratio12 = self.sum22 / (self.sum21 + self.sum22)
                ratios = np.array([ratio21, ratio22])

                self.append_to_dataset('sum21', self.sum11)
                self.append_to_dataset('sum22', self.sum12)
                self.append_to_dataset('ratio_list2', ratios)

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                self.point_num += 1

        except TerminationRequested:
            print('Terminated gracefully')
        # finally:
        #     print(self.sum11, self.sum12)

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run(self):
        counts11 = 0
        counts12 = 0
        counts21 = 0
        counts22 = 0

        sum11 = 0
        sum12 = 0
        sum21 = 0
        sum22 = 0
        self.core.reset()

        # Preparation for experiment
        self.prep_record()
        pulses_handle = self.core_dma.get_handle("pulses")
        self.core.break_realtime()
        self.core_dma.playback_handle(pulses_handle)
        self.core.break_realtime()

        # Pump sigma 1, detect sigma 1
        gate_end_mu_11 = self.record_pump_sigma1_detect_sigma1()    # This pre-records the DMA sequence
        for i in range(self.detections_per_point):
            pulses_handle = self.core_dma.get_handle("pulses")      # I'm not sure this needs to be in the loop
            self.core.break_realtime()                              # Generate sufficient slack (125 us might be too much)
            self.core_dma.playback_handle(pulses_handle)            # Playback the cool/pump/detect sequence
            counts11 = self.detector.count(gate_end_mu_11)
            sum11 += counts11
        self.sum11 = sum11

        # Pump sigma 1, detect sigma 2
        self.core.break_realtime()
        gate_end_mu_12 = self.record_pump_sigma1_detect_sigma2()
        for i in range(self.detections_per_point):
            pulses_handle = self.core_dma.get_handle("pulses")
            self.core.break_realtime()
            self.core_dma.playback_handle(pulses_handle)
            counts12 = self.detector.count(gate_end_mu_12)
            sum12 += counts12
        self.sum12 = sum12

        # Pump sigma 2, detect sigma 1
        self.core.break_realtime()
        gate_end_mu_21 = self.record_pump_sigma2_detect_sigma1()
        for i in range(self.detections_per_point):
            pulses_handle = self.core_dma.get_handle("pulses")
            self.core.break_realtime()
            self.core_dma.playback_handle(pulses_handle)
            counts21 = self.detector.count(gate_end_mu_12)
            sum21 += counts21
        self.sum21 = sum21

        # Pump sigma 2, detect sigma 2
        self.core.break_realtime()
        gate_end_mu_22 = self.record_pump_sigma2_detect_sigma2()
        for i in range(self.detections_per_point):
            pulses_handle = self.core_dma.get_handle("pulses")
            self.core.break_realtime()
            self.core_dma.playback_handle(pulses_handle)
            counts12 = self.detector.count(gate_end_mu_12)
            sum22 += counts22
        self.sum22 = sum22        


    @kernel
    def record_pump_sigma2_detect_sigma1(self):
        gate_end_mu_11 = 0

        with self.core_dma.record("pulses"):
            # cooling
            self.DDS__493__Bob__sigma_1.sw.on()
            self.DDS__493__Bob__sigma_2.sw.on()

            delay(self.cooling_time)

            self.DDS__493__Bob__sigma_1.sw.off()
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

            # pumping, sigma 2
            self.DDS__493__Bob__sigma_2.sw.on()
            delay(self.pumping_time)
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

            # detection, sigma 1
            t11 = now_mu()
            gate_end_mu_11 = self.detector.gate_rising(self.detection_time)
            at_mu(t11)

            self.DDS__493__Bob__sigma_1.sw.on()
            delay(self.detection_time)
            self.DDS__493__Bob__sigma_1.sw.off()

            delay(10*ns)

        return gate_end_mu_21

    @kernel
    def record_pump_sigma2_detect_sigma2(self):
        gate_end_mu_11 = 0

        with self.core_dma.record("pulses"):
            # cooling
            self.DDS__493__Bob__sigma_1.sw.on()
            self.DDS__493__Bob__sigma_2.sw.on()

            delay(self.cooling_time)

            self.DDS__493__Bob__sigma_1.sw.off()
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

            # pumping, sigma 2
            self.DDS__493__Bob__sigma_2.sw.on()
            delay(self.pumping_time)
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

            # detection, sigma 2
            t11 = now_mu()
            gate_end_mu_11 = self.detector.gate_rising(self.detection_time)
            at_mu(t11)

            self.DDS__493__Bob__sigma_2.sw.on()
            delay(self.detection_time)
            self.DDS__493__Bob__sigma_2.sw.off()

            delay(10*ns)

        return gate_end_mu_22