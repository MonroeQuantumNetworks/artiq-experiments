"""
Alice Barium D state pumping and detection, with scannable variables, using 4 HOM APDs for detection

Turn on Ba_detection and Detection_Counts applets to plot the figures

George Toh 2021-01-22
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

class Alice_Ba_Dstate_detection_HOM(base_experiment.base_experiment):

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        # "raman_time",
        # "fastloop_run_ns",
    }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Alice_camera_side_APD

        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('pump_sigma_1_or_2', NumberValue(1, ndecimals=0, min=1, max=2, step=1))

        # self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Alice__sigma_1__frequency', 'DDS__493__Alice__sigma_2__frequency', 'DDS__493__Alice__sigma_1__amplitude', 'DDS__493__Alice__sigma_2__amplitude']
        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'delay_time']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('delay_time__scan', Scannable(default=[NoScan(500), RangeScan(0, 1000, 10)], global_min=0, global_step=10, ndecimals=0))
        # self.setattr_argument('DDS__493__Alice__sigma_1__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_1__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Alice__sigma_2__frequency__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__frequency), CenterScan(self.globals__DDS__493__Alice__sigma_2__frequency/MHz, 1, 0.1) ], unit='MHz', ndecimals=9))
        # self.setattr_argument('DDS__493__Alice__sigma_1__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_1__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))
        # self.setattr_argument('DDS__493__Alice__sigma_2__amplitude__scan', Scannable( default=[NoScan(self.globals__DDS__493__Alice__sigma_2__amplitude), RangeScan(0, 1, 100) ], global_min=0, global_step=0.1, ndecimals=3))

        # 1 <--> sigma_1, 2 <--> sigma_2, 3 <--> pi
        self.sum1 = 0
        self.sum2 = 0
        self.sum3 = 0
        self.sum13 = 0
        self.sum23 = 0

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

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['D_{-3/2}', 'D_{-1/2}', 'D_{1/2}', 'D_{3/2}']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)

        self.set_dataset('runid', self.scheduler.rid, broadcast=True, archive=False)         # This is for display of RUNID on the figure

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Detection_Counts",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "sum1 sum2 sum3 sum13 sum23"
            # + " --x-fit " + "xfitdataset"
            # + " --y-fits " + "yfitdataset"
            + " --rid " + "runid"            
            + " --y-label "
            + "'"
            + ylabel
            + "'"
            + " --x-label "
            + "'"
            + xlabel
            + "'"
        )

        # Also, turn on Ba_ratios 

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
            self.set_dataset('sum1', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum2', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum3', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum13', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum23', np.zeros(point_num), broadcast=True, archive=True)
            point_num = 0

            self.prep_kernel_run()  # Break real time and turn on 493 lasers

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

                # print("STARTING KERNEL RUN")
                # Run the main portion of code here
                self.kernel_run()

                # For D state, ''ratios'' will contain calculated populations of different Zeeman states.
                # The derivation of these expressions is in Ksenia's thesis, and the results are in Allison's
                # OneNote notebook section.


                mean1 = self.sum1     #/self.detections_per_point
                mean2 = self.sum2     #/self.detections_per_point
                mean3 = self.sum3     #/self.detections_per_point
                mean13 = self.sum13   #/self.detections_per_point
                mean23 = self.sum13   #/self.detections_per_point

                # Population of D_{-3/2} state

                d1 = (0.780311 + ((0.589575*mean23 - 0.00440285*mean13 - 0.361042*mean2 -
                                  0.22413*mean1)/(-0.551725*(mean13 + mean23) + 0.051725*(mean1 + mean2) + mean3)))

                # Population of D_{-1/2} state
                d2 = (-0.280311 - ((0.6522231*mean23 - 0.0670587*mean13 - 1.01768*mean2 +
                                    0.432504*mean1)/(-0.551725*(mean13 + mean23) + 0.051725*(mean1 + mean2) + mean3)))

                # Population of D_{1/2} state
                d3 = (-0.280311 + ((0.0670587*mean23 - 0.652231*mean13 - 0.432504*mean2 +
                                   1.01768*mean1)/(-0.551725*(mean13 + mean23) + 0.051725*(mean1 + mean2) + mean3)))

                # Population of D_{3/2} state
                d4 = (0.780311 - ((0.00440285*mean23 - 0.589575*mean13 + 0.22413*mean2 +
                                   0.361042*mean1)/(-0.551725*(mean13 + mean23) + 0.051725*(mean1 + mean2) + mean3)))


                ratios = np.array([d1, d2, d3, d4])
                self.mutate_dataset('sum1', point_num, self.sum1)
                self.mutate_dataset('sum2', point_num, self.sum2)
                self.mutate_dataset('sum3', point_num, self.sum3)
                self.mutate_dataset('sum13', point_num, self.sum13)
                self.mutate_dataset('sum23', point_num, self.sum23)
                self.append_to_dataset('ratio_list', ratios)

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                point_num += 1

        except TerminationRequested:
            print('Terminated gracefully')

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def prep_kernel_run(self):
        self.core.reset()
        self.core.break_realtime()
        delay_mu(5000)
        self.prep_record()
        prep_handle = self.core_dma.get_handle("pulses_prep")   # This sequence turns on the 493 lasers

        self.core.break_realtime()
        delay_mu(100000)

        self.core_dma.playback_handle(prep_handle)  # Turn on the 493 lasers



    @kernel
    def kernel_run(self):

        sum1 = 0
        sum2 = 0
        sum3 = 0
        sum13 = 0
        sum23 = 0

        self.core.reset()   # This is necessary to make it run fast
        # self.core.break_realtime()    # Extremely slow


        # Preparation for experiment
        if self.pump_sigma_1_or_2 == 1:
            self.record_pump_sigma1()
        else:
            self.record_pump_sigma2()
        self.record_detect1()
        self.record_detect2()
        self.record_detect3()
        self.record_detect13()
        self.record_detect23()

        # cool_handle = self.core_dma.get_handle("pulses_cool")
        if self.pump_sigma_1_or_2 == 1:
            pulses_handle_pump = self.core_dma.get_handle("pulses_pump_1")
        else:
            pulses_handle_pump = self.core_dma.get_handle("pulses_pump_2")
        pulses_handle_detect1 = self.core_dma.get_handle("pulses_detect1")
        pulses_handle_detect2 = self.core_dma.get_handle("pulses_detect2")
        pulses_handle_detect3 = self.core_dma.get_handle("pulses_detect3")
        pulses_handle_detect13 = self.core_dma.get_handle("pulses_detect13")
        pulses_handle_detect23 = self.core_dma.get_handle("pulses_detect23")

        delay1 = int(self.delay_time)   # For turn-on time of the laser

        for i in range(self.detections_per_point):

            self.core.break_realtime()  # This is necessary to create slack
            delay_mu(20000)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            delay_mu(1000)
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn off time of the lasers
                    with parallel:
                        gate_end_mu_B1 = self.HOM0.gate_rising(self.detection_time)
                        gate_end_mu_B1 = self.HOM1.gate_rising(self.detection_time)
                        gate_end_mu_B1 = self.HOM2.gate_rising(self.detection_time)
                        gate_end_mu_B1 = self.HOM3.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect1)

            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            delay_mu(1000)
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn off time of the lasers
                    with parallel:
                        gate_end_mu_B2 = self.HOM0.gate_rising(self.detection_time)
                        gate_end_mu_B2 = self.HOM1.gate_rising(self.detection_time)
                        gate_end_mu_B2 = self.HOM2.gate_rising(self.detection_time)
                        gate_end_mu_B2 = self.HOM3.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect2)

            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            delay_mu(1000)
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn off time of the lasers
                    with parallel:
                        gate_end_mu_B3 = self.HOM0.gate_rising(self.detection_time)
                        gate_end_mu_B3 = self.HOM1.gate_rising(self.detection_time)
                        gate_end_mu_B3 = self.HOM2.gate_rising(self.detection_time)
                        gate_end_mu_B3 = self.HOM3.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect3)

            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            delay_mu(1000)
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn off time of the lasers
                    with parallel:
                        gate_end_mu_B13 = self.HOM0.gate_rising(self.detection_time)
                        gate_end_mu_B13 = self.HOM1.gate_rising(self.detection_time)
                        gate_end_mu_B13 = self.HOM2.gate_rising(self.detection_time)
                        gate_end_mu_B13 = self.HOM3.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect13)

            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump) # Cool and pump
            delay_mu(1000)
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn off time of the lasers
                    with parallel:
                        gate_end_mu_B23 = self.HOM0.gate_rising(self.detection_time)
                        gate_end_mu_B23 = self.HOM1.gate_rising(self.detection_time)
                        gate_end_mu_B23 = self.HOM2.gate_rising(self.detection_time)
                        gate_end_mu_B23 = self.HOM3.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect23)

            sum1 += self.HOM0.count(gate_end_mu_B1) + self.HOM1.count(gate_end_mu_B1) + self.HOM2.count(gate_end_mu_B1) + self.HOM3.count(gate_end_mu_B1)
            sum2 += self.HOM0.count(gate_end_mu_B2) + self.HOM1.count(gate_end_mu_B2) + self.HOM2.count(gate_end_mu_B2) + self.HOM3.count(gate_end_mu_B2)
            sum3 += self.HOM0.count(gate_end_mu_B3) + self.HOM1.count(gate_end_mu_B3) + self.HOM2.count(gate_end_mu_B3) + self.HOM3.count(gate_end_mu_B3)
            sum13 += self.HOM0.count(gate_end_mu_B13) + self.HOM1.count(gate_end_mu_B13) + self.HOM2.count(gate_end_mu_B13) + self.HOM3.count(gate_end_mu_B13)
            sum23 += self.HOM0.count(gate_end_mu_B23) + self.HOM1.count(gate_end_mu_B23) + self.HOM2.count(gate_end_mu_B23) + self.HOM3.count(gate_end_mu_B23)

        self.sum1 = sum1
        self.sum2 = sum2
        self.sum3 = sum3
        self.sum13 = sum13
        self.sum23 = sum23

    @kernel
    def prep_record(self):
        # This is used for detection
        with self.core_dma.record("pulses_prep"):
            self.DDS__493__Alice__sigma_1.sw.on()  # Alice 493 sigma 1
            self.DDS__493__Alice__sigma_2.sw.on()  # Alice 493 sigma 2
            self.ttl_Alice_650_pi.off()  # Alice 650 pi
            delay_mu(10)
            self.ttl_650_fast_cw.off()  # 650 fast AOM
            self.ttl_650_sigma_1.off()  # 650 sigma 1
            self.ttl_650_sigma_2.off()  # 650 sigma 2

    @kernel
    def record_pump_sigma1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 650 sigma 1
        """
        with self.core_dma.record("pulses_pump_1"):
            with parallel:
                self.ttl_Alice_650_pi.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()

            delay(self.cooling_time)

            self.ttl_650_sigma_2.off()

            delay(self.pumping_time)

            with parallel:
                self.ttl_Alice_650_pi.off()
                self.ttl_650_sigma_1.off()
                self.ttl_650_fast_cw.off()

    @kernel
    def record_pump_sigma2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 650 sigma 2
        """
        with self.core_dma.record("pulses_pump_2"):
            with parallel:
                self.ttl_Alice_650_pi.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()

            delay(self.cooling_time)

            self.ttl_650_sigma_1.off()

            delay(self.pumping_time)

            with parallel:
                self.ttl_Alice_650_pi.off()
                self.ttl_650_sigma_2.off()
                self.ttl_650_fast_cw.off()

    @kernel
    def record_detect1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 1
        """
        with self.core_dma.record("pulses_detect1"):
            with parallel:
                self.ttl_650_sigma_1.on()
                self.ttl_650_fast_cw.on()
            delay(self.detection_time)
            with parallel:
                self.ttl_650_sigma_1.off()
                self.ttl_650_fast_cw.off()

    @kernel
    def record_detect2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 2
        """
        with self.core_dma.record("pulses_detect2"):
            with parallel:
                self.ttl_650_sigma_2.on()
                self.ttl_650_fast_cw.on()
            delay(self.detection_time)
            with parallel:
                self.ttl_650_sigma_2.off()
                self.ttl_650_fast_cw.off()

    @kernel
    def record_detect3(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 pi.
        """
        with self.core_dma.record("pulses_detect3"):
            with parallel:
                self.ttl_Alice_650_pi.on()
            delay(self.detection_time)
            with parallel:
                self.ttl_Alice_650_pi.on()

    @kernel
    def record_detect13(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 1 and pi.
        """
        with self.core_dma.record("pulses_detect13"):
            with parallel:
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_Alice_650_pi.on()

            delay(self.detection_time)
            with parallel:
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_1.off()
                self.ttl_Alice_650_pi.off()

    @kernel
    def record_detect23(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 2 and pi.
        """
        with self.core_dma.record("pulses_detect23"):
            with parallel:
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_2.on()
                self.ttl_Alice_650_pi.on()

            delay(self.detection_time)
            with parallel:
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_2.off()
                self.ttl_Alice_650_pi.off()
