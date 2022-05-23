"""
Bob Yb state detection calibration
Works. not able to pump to state 1

George Toh 2022-05-13
"""

from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
from repository import base_experiment
import os
import time

class Bob_Yb_State_det_calib(base_experiment.base_experiment):
    """ Bob Yb S-state detection calibration"""

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        "detections_per_point",
        # "raman_time",
        # "fastloop_run_ns",
    }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Bob_camera_side_APD

        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        # self.setattr_argument('photons_0_or_1', NumberValue(2, ndecimals=0, min=1, step=1))
        # self.setattr_argument('detection_points', NumberValue(1, ndecimals=0, min=1, step=1))

        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'delay_time']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('delay_time__scan', Scannable(default=[NoScan(500), RangeScan(0, 1000, 10)], global_min=0, global_step=10, ndecimals=0))

        # These are initialized as 1 to prevent divide by zero errors. Change 1 to 0 when fully working.
        self.sum11 = 0
        self.sum12 = 0
        self.sum21 = 0
        self.sum22 = 0


    def run(self):

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect11', 'detect12', 'detect21', 'detect22']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)

        self.set_dataset('runid', self.scheduler.rid, broadcast=True, archive=False)     # This is for display of RUNID on the figure

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "${artiq_applet}plot_hist" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Yb Histogram",
            command=applet_stream_cmd
            + "yb_hist_dataset2"
            + " --x " + "yb_hist_bins"        # BIN_BOUNDARIES_DATASET
            # + " --rid " + "runid"
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

            # This silly three lines counts the number of points we need to scan
            point_num = 0
            for point in msm: point_num += 1
            print(point_num)

            # assume a 1D scan for plotting
            # self.set_dataset('scan_x', [], broadcast=True, archive=True)
            self.set_dataset('yb_hist_dataset', [], broadcast=True, archive=True)
            # self.set_dataset('sum11', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum12', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum21', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum22', np.zeros(point_num), broadcast=True, archive=True)

            t_now = time.time()  # Save the current time

            point_num = 0
            for point in msm:

                print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # Run the main portion of code here
                self.kernel_run()

                # Extract data from dataset
                data = self.get_dataset('yb_hist_dataset')
                print(data)
                # Sort data for histogram
                noofbins = np.max(data) - np.min(data)
                sorteddata, edges = np.histogram(data,noofbins)
                # Set dataset for histogram
                print(sorteddata)
                # print(edges)
                self.set_dataset('yb_hist_dataset2', sorteddata, broadcast=True, archive=True)
                self.set_dataset('yb_hist_bins', edges-0.5, broadcast=True, archive=True)


                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                point_num += 1

        except TerminationRequested:
            print('Terminated gracefully')
            # These are necessary to restore the system to the state before the experiment.
            self.load_globals_from_dataset()  # This loads global settings from datasets
            self.setup()  # This sends settings out to the ARTIQ hardware

        print("Time taken = {:.2f} seconds".format(time.time() - t_now))  # Calculate how long the experiment took

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run(self):

        temp = 0

        self.core.reset()

        # Preparation for experiment
        # self.prep_record()
        # self.record_pump_0()
        
        # self.record_detect()

        # prep_handle = self.core_dma.get_handle("pulses_prep")
        # # pulses_handle1 = self.core_dma.get_handle("pulses1")
        # pulses_handle0 = self.core_dma.get_handle("pulses0")
        # pulses_detect = self.core_dma.get_handle("pulsesd")
        # self.core.break_realtime()
        # self.core_dma.playback_handle(prep_handle) 

        # Prepare laser beams (cooling configuration)
        self.ttl_370_2G_EOM.off()
        self.ttl_370_7G_EOM.on()
        self.ttl_370_AOM.on()
        self.ttl_935_EOM.on()

        delay1 = int(self.delay_time)
        
        gate_end_mu_B1 = 0
        for i in range(self.detections_per_point):
            self.core.break_realtime()  # This makes underflow errors less likely
            # delay_mu(100000)

            self.ttl_AWG_trigger.on()
            delay_mu(10)
            # self.core_dma.playback_handle(pulses_handle0)  # Cool then Pump 
            # Cooling beams
            self.ttl_370_2G_EOM.off()
            self.ttl_370_7G_EOM.on()
            self.ttl_370_AOM.on()
            self.ttl_935_EOM.on()

            delay(self.cooling_time)

            # Pumping beams
            self.ttl_370_2G_EOM.on()
            self.ttl_370_7G_EOM.off()
            # self.ttl_370_AOM.off()
            # self.ttl_935_EOM.off()

            delay(self.pumping_time)
            # delay_mu(10000)
            
            # Turn off all lasers before detection
            self.ttl_370_2G_EOM.off()
            self.ttl_370_7G_EOM.off()
            self.ttl_370_AOM.off()
            self.ttl_935_EOM.off()


            delay_mu(1000)   # To compensate for the differences in turn off time
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn on off time of the lasers
                    gate_end_mu_B1 = self.Bob_PMT.gate_rising(self.detection_time)
                # self.core_dma.playback_handle(pulses_detect)
                with sequential:
                    self.ttl_370_AOM.on()
                    # self.ttl_935_EOM.on()
                    # self.ttl_370_7G_EOM.on()
                    delay(self.detection_time)
                    # self.ttl_370_7G_EOM.off()
                    # self.ttl_935_EOM.off()
                    self.ttl_370_AOM.off()


            delay_mu(30000)

            temp = self.Bob_PMT.count(gate_end_mu_B1)

            self.core.break_realtime()
            self.append_to_dataset('yb_hist_dataset', temp)
            # print(i, temp)
            # self.ttl_AWG_trigger.off()
            self.core.break_realtime()

        return

    @kernel
    def prep_record(self):
        # Prepare the beams, get them in the cooling configuration
        with self.core_dma.record("pulses_prep"):
            self.ttl_370_2G_EOM.off()
            self.ttl_370_7G_EOM.on()
            self.ttl_370_AOM.on()
            self.ttl_935_EOM.on()

    @kernel
    def record_pump_0(self):
        """DMA pump and detection loop sequence.
        This generates the pulse sequence needed for pumping to state 0
        """
        with self.core_dma.record("pulses0"):
            
            self.ttl_370_2G_EOM.off()
            self.ttl_370_7G_EOM.on()
            self.ttl_370_AOM.on()
            self.ttl_935_EOM.on()

            delay(self.cooling_time)

            self.ttl_370_2G_EOM.on()
            self.ttl_370_7G_EOM.off()
            # self.ttl_370_AOM.off()
            # self.ttl_935_EOM.off()

            delay(self.pumping_time)
            

            self.ttl_370_2G_EOM.off()
            self.ttl_370_7G_EOM.off()
            self.ttl_370_AOM.off()
            self.ttl_935_EOM.off()

            delay_mu(1000)  # For timing detection timing purposes

            # self.ttl_370_AOM.on()
            # delay(self.detection_time)
            # self.ttl_370_AOM.off()

    @kernel
    def record_detect(self):
        """DMA pump and detection loop sequence.
        This generates the pulse sequence needed for detection
        """
        with self.core_dma.record("pulsesd"):
            self.ttl_370_AOM.on()
            delay(self.detection_time)
            self.ttl_370_AOM.off()

