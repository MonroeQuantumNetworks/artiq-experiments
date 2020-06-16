""" Tested modified Legacy script, WORKING
Bob Barium detection, with scannable variables, partial DMA
Automatically does both pump12 and detect12
Turn on Ba_ratios and Ba_ratios_2 to plot the figures

Known issues:
    non-DMA detection, very slow
    Long delay between cool and pump >250 usec

George Toh 2020-06-15
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

class Ba_detection_Bob_2(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Bob_camera_side_APD

        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('detection_points', NumberValue(10000, ndecimals=0, min=1, step=1))

        # self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Bob__sigma_1__frequency', 'DDS__493__Bob__sigma_2__frequency', 'DDS__493__Bob__sigma_1__amplitude', 'DDS__493__Bob__sigma_2__amplitude']
        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        # self.setattr_argument('DDS__493__Bob__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_1__frequency), CenterScan(self.globals__DDS__493__Bob__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Bob__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_2__frequency), CenterScan(self.globals__DDS__493__Bob__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Bob__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        # self.setattr_argument('DDS__493__Bob__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Bob__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))

        # These are initialized as 1 to prevent divide by zero errors. Change 1 to 0 when fully working.
        self.sum11 = 1
        self.sum12 = 1
        self.sum21 = 1
        self.sum22 = 1

    @kernel
    def prep_record(self):
        # This is used for detection
        with self.core_dma.record("pulses"):
            self.DDS__493__Bob__sigma_1.sw.off() # Bob 493 sigma 1
            self.DDS__493__Bob__sigma_2.sw.off() # Bob 493 sigma 2
            self.ttl_650_pi.on() # Bob 650 pi
            self.ttl_650_fast_cw.on() # 650 fast AOM
            self.ttl_650_sigma_1.on() # 650 sigma 1
            self.ttl_650_sigma_2.on() # 650 sigma 2

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

        self.set_dataset('ratio_list11', [], broadcast=True, archive=True)
        self.set_dataset('ratio_list12', [], broadcast=True, archive=True)
        self.set_dataset('sum11', [], broadcast=True, archive=True)
        self.set_dataset('sum12', [], broadcast=True, archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect11', 'detect12']], broadcast=True, archive=True, persist=True)
        self.set_dataset('Ba_detection_names2', [bytes(i, 'utf-8') for i in ['detect21', 'detect22']], broadcast=True,
                         archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        self.set_dataset('ratio_list2', [], broadcast=True, archive=True)
        self.set_dataset('sum21', [], broadcast=True, archive=True)
        self.set_dataset('sum22', [], broadcast=True, archive=True)

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Detection_Counts",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "sum11 sum12 sum21 sum22"
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
        # Also, turn on Ba_ratios and Ba_ratios_2 to plot the figures

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
                # self.append_to_dataset('ratio_list11', ratio11)
                # self.append_to_dataset('ratio_list12', ratio12)
                self.append_to_dataset('ratio_list', ratios)

                # For pumping with sigma2
                ratio21 = self.sum21 / (self.sum21 + self.sum22)
                ratio22 = self.sum22 / (self.sum21 + self.sum22)
                ratios = np.array([ratio21, ratio22])

                self.append_to_dataset('sum21', self.sum21)
                self.append_to_dataset('sum22', self.sum22)
                # self.append_to_dataset('ratio_list21', ratio21)
                # self.append_to_dataset('ratio_list22', ratio22)
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
        # gate_end_mu_11 = self.record_pump_sigma1_detect_sigma1()    # This pre-records the DMA sequence
        # for i in range(self.detections_per_point):
        #     pulses_handle = self.core_dma.get_handle("pulses")      # I'm not sure this needs to be in the loop
        #     self.core.break_realtime()                              # Generate sufficient slack (125 us might be too much)
        #     self.core_dma.playback_handle(pulses_handle)            # Playback the cool/pump/detect sequence
        #     counts11 = self.detector.count(gate_end_mu_11)
        #     sum11 += counts11
        # self.sum11 = sum11

        for i in range(self.detections_per_point):
            delay(16000*ns)
            self.core_dma.playback_handle(pulses_handle)  # Turn on the 650 lasers
            counts11 = self.run_detection11()
            sum11 += counts11
        self.sum11 = sum11

        for i in range(self.detections_per_point):
            delay(16000 * ns)
            self.core_dma.playback_handle(pulses_handle)
            sum12 += self.run_detection12()
        self.sum12 = sum12

        for i in range(self.detections_per_point):
            delay(16000 * ns)
            self.core_dma.playback_handle(pulses_handle)
            sum21 += self.run_detection21()
        self.sum21 = sum21

        for i in range(self.detections_per_point):
            delay(16000 * ns)
            self.core_dma.playback_handle(pulses_handle)
            sum22 += self.run_detection22()
        self.sum22 = sum22

    # ARTIQ example
    # Using gateware counters, only a single input event each is
    # generated, greatly reducing the load on the input FIFOs:
    # with parallel:
    #     self.pmt_0_counter.gate_rising(10 * ms)
    #     self.pmt_1_counter.gate_rising(10 * ms)
    #
    # counts_0 = self.pmt_0_counter.fetch_count() # blocks
    # counts_1 = self.pmt_1_counter.fetch_count()

    @kernel
    def run_detection11(self):
        """Non-DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 1
        """

        self.core.break_realtime()
        # self.core.break_realtime()
        delay(150000 * ns)          # This extremely long delay is needed for rtio overflow

        # 650s are already switched ON
        self.DDS__493__Bob__sigma_1.sw.on()
        delay(self.pumping_time)
        self.DDS__493__Bob__sigma_1.sw.off()

        with parallel:
            # self.ttl_650_fast_cw.on()
            # self.ttl_650_sigma_1.on()
            # self.ttl_650_sigma_2.on()
            self.DDS__493__Bob__sigma_1.sw.on()
            # gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        delay(self.detection_time)

        with parallel:
            # self.ttl_650_fast_cw.off()
            # self.ttl_650_sigma_1.off()
            # self.ttl_650_sigma_2.off()
            self.DDS__493__Bob__sigma_1.sw.off()

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B1)

        return Bob_counts

    @kernel
    def run_detection12(self):
        """Non-DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 2
        """
        self.core.break_realtime()
        delay(250000 * ns)          # This extremely long delay is needed for rtio overflow

        self.DDS__493__Bob__sigma_1.sw.on()
        delay(self.pumping_time)
        self.DDS__493__Bob__sigma_1.sw.off()

        t1 = now_mu()
        with parallel:
            # gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_650_pi.pulse(self.detection_time)
            # self.ttl_650_fast_cw.pulse(self.detection_time)
            # self.ttl_650_sigma_1.pulse(self.detection_time)
            # self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)
            self.DDS__493__Bob__sigma_2.sw.pulse(self.detection_time)

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B2)

        return Bob_counts

    @kernel
    def run_detection21(self):
        """Non-DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 1
        """
        self.core.break_realtime()
        delay(250000 * ns)          # This extremely long delay is needed for rtio overflow

        self.DDS__493__Bob__sigma_2.sw.on()
        delay(self.pumping_time)
        self.DDS__493__Bob__sigma_2.sw.off()

        t1 = now_mu()
        with parallel:
            # gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_650_pi.pulse(self.detection_time)
            # self.ttl_650_fast_cw.pulse(self.detection_time)
            # self.ttl_650_sigma_1.pulse(self.detection_time)
            # self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_1.sw.pulse(self.detection_time)
            self.DDS__493__Bob__sigma_1.sw.pulse(self.detection_time)

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B1)

        return Bob_counts

    @kernel
    def run_detection22(self):
        """Non-DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 2
        """
        self.core.break_realtime()
        delay(250000 * ns)          # This extremely long delay is needed for rtio overflow

        self.DDS__493__Bob__sigma_2.sw.on()
        delay(self.pumping_time)
        self.DDS__493__Bob__sigma_2.sw.off()

        t1 = now_mu()
        with parallel:
            # gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_650_pi.pulse(self.detection_time)
            # self.ttl_650_fast_cw.pulse(self.detection_time)
            # self.ttl_650_sigma_1.pulse(self.detection_time)
            # self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)
            self.DDS__493__Bob__sigma_2.sw.pulse(self.detection_time)

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B2)

        return Bob_counts