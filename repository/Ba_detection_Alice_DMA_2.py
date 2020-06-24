""" Tested modified Legacy script, WORKING
Alice Barium detection, with scannable variables, partial DMA
Automatically does both pump12 and detect12
Turn on Ba_ratios and Detection_Counts APPLETS to plot the figures

Known issues:
    Have no control over Alice 650 pi, always ON
    non-DMA detection, slow
    Long delay between cool and pump >250 usec

George Toh 2020-06-16
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

class Ba_detection_Alice_DMA_2(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Alice_camera_side_APD

        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('detection_points', NumberValue(10000, ndecimals=0, min=1, step=1))

        # self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Alice__sigma_1__frequency', 'DDS__493__Alice__sigma_2__frequency', 'DDS__493__Alice__sigma_1__amplitude', 'DDS__493__Alice__sigma_2__amplitude']
        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        # self.setattr_argument('DDS__493__Alice__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Alice__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Alice__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        # self.setattr_argument('DDS__493__Alice__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))

        # These are initialized as 1 to prevent divide by zero errors. Change 1 to 0 when fully working.
        self.sum11 = 0
        self.sum12 = 0
        self.sum21 = 0
        self.sum22 = 0

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

        # self.set_dataset('ratio_list11', [], broadcast=True, archive=True)
        # self.set_dataset('ratio_list12', [], broadcast=True, archive=True)

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect11', 'detect12', 'detect21', 'detect22']], broadcast=True, archive=True, persist=True)
        # self.set_dataset('Ba_detection_names2', [bytes(i, 'utf-8') for i in ['detect21', 'detect22']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        # self.set_dataset('ratio_list2', [], broadcast=True, archive=True)
        # self.set_dataset('sum21', [], broadcast=True, archive=True)
        # self.set_dataset('sum22', [], broadcast=True, archive=True)

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

            # This silly three lines counts the number of points we need to scan
            point_num = 0
            for point in msm: point_num += 1
            print(point_num)

            # assume a 1D scan for plotting
            self.set_dataset('scan_x', [], broadcast=True, archive=True)
            self.set_dataset('sum11', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum12', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum21', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum22', np.zeros(point_num), broadcast=True, archive=True)

            point_num = 0
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
                # ratios = np.array([ratio11, ratio12])

                self.mutate_dataset('sum11', point_num, self.sum11)
                self.mutate_dataset('sum12', point_num, self.sum12)

                # # For pumping with sigma2
                ratio21 = self.sum21 / (self.sum21 + self.sum22)
                ratio22 = self.sum22 / (self.sum21 + self.sum22)
                ratios = np.array([ratio11, ratio12, ratio21, ratio22])

                self.mutate_dataset('sum21', point_num, self.sum21)
                self.mutate_dataset('sum22', point_num, self.sum22)
                self.append_to_dataset('ratio_list', ratios)


                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                point_num += 1

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
        self.core.reset()             # Program is slow with this line un-commented, 10x slower when commented out
        # self.core.break_realtime()    # This is extremely slow, at least 10x slower than core.reset

        # Preparation for experiment
        self.prep_record()
        self.record_pump_sigma1()
        self.record_pump_sigma2()
        self.record_detect1()
        self.record_detect2()
        # self.record_cool()
        prep_handle = self.core_dma.get_handle("pulses_prep")
        # cool_handle = self.core_dma.get_handle("pulses_cool")
        pulses_handle10 = self.core_dma.get_handle("pulses10")
        pulses_handle01 = self.core_dma.get_handle("pulses01")
        pulses_handle20 = self.core_dma.get_handle("pulses20")
        pulses_handle02 = self.core_dma.get_handle("pulses02")
        self.core.break_realtime()
        self.core_dma.playback_handle(prep_handle) # Turn on the 650 lasers

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

            delay_mu(300000)        # Each pulse sequence needs about 70 us of slack to run

            self.core_dma.playback_handle(pulses_handle10)  # Cool then Pump
            with parallel:
                gate_end_mu_B1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle01)

            self.core_dma.playback_handle(pulses_handle10)  # Cool then Pump
            with parallel:
                gate_end_mu_B2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle02)

            self.core_dma.playback_handle(pulses_handle20)  # Cool then Pump
            # delay_mu(300)
            with parallel:
                gate_end_mu_B3 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle01)

            self.core_dma.playback_handle(pulses_handle20)  # Cool then Pump
            # delay_mu(500)
            with parallel:
                gate_end_mu_B4 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle02)

            # delay_mu(500)

            sum11 += self.Alice_camera_side_APD.count(gate_end_mu_B1)
            sum12 += self.Alice_camera_side_APD.count(gate_end_mu_B2)
            sum21 += self.Alice_camera_side_APD.count(gate_end_mu_B3)
            sum22 += self.Alice_camera_side_APD.count(gate_end_mu_B4)

        self.sum11 = sum11
        self.sum12 = sum12
        self.sum21 = sum21
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
    def prep_record(self):
        # This is used for detection
        with self.core_dma.record("pulses_prep"):
            self.DDS__493__Alice__sigma_1.sw.off() # Alice 493 sigma 1
            self.DDS__493__Alice__sigma_2.sw.off() # Alice 493 sigma 2
            # self.ttl_Alice_650_pi.on() # Bob 650 pi
            self.ttl_650_fast_cw.on() # 650 fast AOM
            self.ttl_650_sigma_1.on() # 650 sigma 1
            self.ttl_650_sigma_2.on() # 650 sigma 2

    @kernel
    def record_pump_sigma1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 493 sigma 1
        """
        with self.core_dma.record("pulses10"):
            self.DDS__493__Alice__sigma_1.sw.on()
            self.DDS__493__Alice__sigma_2.sw.on()
            delay(self.cooling_time)
            self.DDS__493__Alice__sigma_1.sw.off()
            self.DDS__493__Alice__sigma_2.sw.off()

            self.DDS__493__Alice__sigma_1.sw.on()
            delay(self.pumping_time)
            self.DDS__493__Alice__sigma_1.sw.off()

    @kernel
    def record_pump_sigma2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 493 sigma 1
        """
        with self.core_dma.record("pulses20"):
            self.DDS__493__Alice__sigma_1.sw.on()
            self.DDS__493__Alice__sigma_2.sw.on()
            delay(self.cooling_time)
            self.DDS__493__Alice__sigma_1.sw.off()
            self.DDS__493__Alice__sigma_2.sw.off()

            self.DDS__493__Alice__sigma_2.sw.on()
            delay(self.pumping_time)
            self.DDS__493__Alice__sigma_2.sw.off()

    @kernel
    def record_detect1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 1
        """
        with self.core_dma.record("pulses01"):

            self.DDS__493__Alice__sigma_1.sw.on()
            delay(self.detection_time)
            self.DDS__493__Alice__sigma_1.sw.off()

    @kernel
    def record_detect2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 1
        """
        with self.core_dma.record("pulses02"):

            self.DDS__493__Alice__sigma_2.sw.on()
            delay(self.detection_time)
            self.DDS__493__Alice__sigma_2.sw.off()

    # @kernel
    # def record_cool(self):
    #     """DMA detection loop sequence.
    #     This generates the pulse sequence needed for pumping with 493 sigma 1
    #     """
    #     with self.core_dma.record("pulses_cool"):
    #         self.DDS__493__Alice__sigma_1.sw.on()
    #         self.DDS__493__Alice__sigma_2.sw.on()
    #         delay(self.cooling_time)
    #         self.DDS__493__Alice__sigma_1.sw.off()
    #         self.DDS__493__Alice__sigma_2.sw.off()