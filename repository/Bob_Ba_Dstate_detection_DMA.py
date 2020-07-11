"""
Bob Barium D state pumping and detection, with scannable variables, partial DMA

In practice, we will only do either sigma_1 and pi pumping, or sigma_2 and pi pumping, so this
program only does one of the two to allow for easier optimization of that process

Turn on Ba_detection applet to plot

Update 2020-06-29
Tested and works reasonably well; delays not optimized

Allison Carter 2020-06-21
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


class Bob_Ba_Dstate_detection_DMA(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")

        self.setattr_argument('detections_per_point', NumberValue(2000, ndecimals=0, min=1, step=1))
        self.setattr_argument('pump_sigma_1_or_2', NumberValue(1, ndecimals=0, min=1, max=2, step=1))

        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'dummy']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('dummy__scan', Scannable(default=[NoScan(0), RangeScan(0, 10, 10)], global_min=0, global_step=0.1, ndecimals=1))

        # 1 <--> sigma_1, 2 <--> sigma_2, 3 <--> pi
        self.sum1 = 0
        self.sum2 = 0
        self.sum3 = 0
        self.sum13 = 0
        self.sum23 = 0

    def run(self):

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['D_{-3/2}', 'D_{-1/2}', 'D_{1/2}', 'D_{3/2}']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)

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

            # Counts number of points for scanning
            point_num = len([point for point in msm])

            # assume a 1D scan for plotting
            self.set_dataset('scan_x', [], broadcast=True, archive=True)
            self.set_dataset('sum1', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum2', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum3', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum13', np.zeros(point_num), broadcast=True, archive=True)
            self.set_dataset('sum23', np.zeros(point_num), broadcast=True, archive=True)
            point_num = 0
            self.prep_kernel_run()

            for point in msm:

                # print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # update the plot x-axis ticks
                self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                # Run the main portion of code here
                self.kernel_run()

                # For D state, ''ratios'' will contain calculated populations of different Zeeman states.
                # The derivation of these expressions is in Ksenia's thesis, and the results are in Allison's
                # OneNote notebook section.

                # Population of D_{-3/2} state
                d1 = (0.780311 + ((0.589575*self.sum23 - 0.00440285*self.sum13 - 0.361042*self.sum2 -
                                  0.22413*self.sum1)/(-0.551725*(self.sum13 + self.sum23) +
                                                      0.051725*(self.sum1 + self.sum2) + self.sum3)))

                # Population of D_{-1/2} state
                d2 = (-0.280311 - ((0.6522231*self.sum23 - 0.0670587*self.sum13 - 1.01768*self.sum2 +
                                    0.432504*self.sum1)/(-0.551725*(self.sum13 + self.sum23) +
                                                         0.051725*(self.sum1 + self.sum2) + self.sum3)))

                # Population of D_{1/2} state
                d3 = (-0.280311 + ((0.0670587*self.sum23 - 0.652231*self.sum13 - 0.432504*self.sum2 +
                                   1.01768*self.sum1)/(-0.551725*(self.sum13 + self.sum23) +
                                                       0.051725*(self.sum1 + self.sum2) + self.sum3)))

                # Population of D_{3/2} state
                d4 = (0.780311 - ((0.00440285*self.sum23 - 0.589575*self.sum13 + 0.22413*self.sum2 +
                                   0.361042*self.sum1)/(-0.551725*(self.sum13 + self.sum23) +
                                                        0.051725*(self.sum1 + self.sum2) + self.sum3)))

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
        self.prep_record()
        prep_handle = self.core_dma.get_handle("pulses_prep")
        self.core.break_realtime()
        self.core_dma.playback_handle(prep_handle)  # Turn on the 650 lasers

    @kernel
    def kernel_run(self):

        sum1 = 0
        sum2 = 0
        sum3 = 0
        sum13 = 0
        sum23 = 0

        self.core.reset()

        # Preparation for experiment
        self.record_ttl_pulse()
        if self.pump_sigma_1_or_2 == 1:
            self.record_pump_sigma1()
        else:
            self.record_pump_sigma2()
        self.record_detect1()
        self.record_detect2()
        self.record_detect3()
        self.record_detect13()
        self.record_detect23()

        pulses_handle_ttl = self.core_dma.get_handle("ttl_pulse")
        if self.pump_sigma_1_or_2 == 1:
            pulses_handle_pump = self.core_dma.get_handle("pulses_pump_1")
        else:
            pulses_handle_pump = self.core_dma.get_handle("pulses_pump_2")
        pulses_handle_detect1 = self.core_dma.get_handle("pulses_detect1")
        pulses_handle_detect2 = self.core_dma.get_handle("pulses_detect2")
        pulses_handle_detect3 = self.core_dma.get_handle("pulses_detect3")
        pulses_handle_detect13 = self.core_dma.get_handle("pulses_detect13")
        pulses_handle_detect23 = self.core_dma.get_handle("pulses_detect23")

        for i in range(self.detections_per_point):

            self.core.break_realtime()  # This is needed to create positive slack
            delay_mu(500000)        # Each pulse sequence needs about 70 us of slack to run

            # self.core_dma.playback_handle(pulses_handle_ttl)    # Trigger the Picoharp

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            with parallel:
                with sequential:
                    delay_mu(450)
                    gate_end_mu_1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect1)
            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            with parallel:
                with sequential:
                    delay_mu(450)
                    gate_end_mu_2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect2)
            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            with parallel:
                with sequential:
                    delay_mu(450)
                    gate_end_mu_3 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect3)
            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            with parallel:
                with sequential:
                    delay_mu(450)
                    gate_end_mu_13 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect13)
            delay_mu(200)

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool and pump
            with parallel:
                with sequential:
                    delay_mu(450)
                    gate_end_mu_23 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect23)
            delay_mu(200)

            sum1 += self.Bob_camera_side_APD.count(gate_end_mu_1)
            sum2 += self.Bob_camera_side_APD.count(gate_end_mu_2)
            sum3 += self.Bob_camera_side_APD.count(gate_end_mu_3)
            sum13 += self.Bob_camera_side_APD.count(gate_end_mu_13)
            sum23 += self.Bob_camera_side_APD.count(gate_end_mu_23)

        self.sum1 = sum1
        self.sum2 = sum2
        self.sum3 = sum3
        self.sum13 = sum13
        self.sum23 = sum23

    @kernel
    def prep_record(self):
        # This is used for detection
        with self.core_dma.record("pulses_prep"):
            self.DDS__493__Bob__sigma_1.sw.on()  # Bob 493 sigma 1
            self.DDS__493__Bob__sigma_2.sw.on()  # Bob 493 sigma 2
            self.ttl_Bob_650_pi.off()  # Bob 650 pi
            self.ttl_650_fast_cw.off()  # 650 fast AOM
            self.ttl_650_sigma_1.off()  # 650 sigma 1
            self.ttl_650_sigma_2.off()  # 650 sigma 2

    @kernel
    def record_ttl_pulse(self):
        with self.core_dma.record("ttl_pulse"):
            self.ttl0.pulse(20*ns)

    @kernel
    def record_pump_sigma1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 650 sigma 1
        """
        with self.core_dma.record("pulses_pump_1"):

            with parallel:
                self.ttl_Bob_650_pi.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()

            delay(self.cooling_time)

            self.ttl_650_sigma_2.off()

            delay(self.pumping_time)

            with parallel:
                self.ttl_Bob_650_pi.off()
                self.ttl_650_sigma_1.off()
                self.ttl_650_fast_cw.off()

            delay(500*ns)

    @kernel
    def record_pump_sigma2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 650 sigma 2
        """
        with self.core_dma.record("pulses_pump_2"):

            with parallel:
                self.ttl_Bob_650_pi.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()

            delay(self.cooling_time)

            self.ttl_650_sigma_1.off()

            delay(self.pumping_time)

            with parallel:
                self.ttl_Bob_650_pi.off()
                self.ttl_650_sigma_2.off()
                self.ttl_650_fast_cw.off()

            delay(500*ns)
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
            self.ttl_Bob_650_pi.on()
            delay(self.detection_time)
            self.ttl_Bob_650_pi.on()

    @kernel
    def record_detect13(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 1 and pi.
        """
        with self.core_dma.record("pulses_detect13"):
            self.ttl_Bob_650_pi.on()
            delay_mu(100)
            with parallel:
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()

            delay(self.detection_time)

            with parallel:
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_1.off()
                self.ttl_Bob_650_pi.off()

    @kernel
    def record_detect23(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 2 and pi.
        """
        with self.core_dma.record("pulses_detect23"):
            self.ttl_Bob_650_pi.on()
            delay_mu(100)
            with parallel:
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_2.on()

            delay(self.detection_time)
            with parallel:
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_2.off()
                self.ttl_Bob_650_pi.off()
