""" Not Tested, ought to work
Bob RF scan for compensating micromotion


George Toh 2022-05-20
"""

from artiq.experiment import *
import numpy as np
from repository import base_experiment
import os
import time

class Bob_TrapRF_scan(base_experiment.base_experiment):
    """ Bob TrapRF for Micromotion"""

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        "photons_0_or_1",
        # "raman_time",
        # "fastloop_run_ns",
        "RF_freq",
        "RF_amp",
    }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Bob_camera_side_APD

        # self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        # self.setattr_argument('photons_0_or_1', NumberValue(2.5, ndecimals=1, min=0.5, step=1))
        # self.setattr_argument('detection_points', NumberValue(1, ndecimals=0, min=1, step=1))

        # Anything with a scannable needs to be listed here
        self.scan_names = ['detection_time', 'RF_freq', 'RF_amp']

        # Inputs for 370 laser
        self.setattr_argument('detection_time__scan', group = '370', processor = Scannable(default=[NoScan(100 * ms), 
                                RangeScan(100*us, 1000*ms, 10) ], global_min=0*ms, global_step=100*ms, unit='ms', ndecimals=3))
        

        # RF
        self.setattr_argument('RF_freq__scan', group = 'RF', processor =  Scannable(default=[NoScan(20e6), RangeScan(10e6, 20e6, 10)], 
                                unit='MHz', ndecimals=9))

        self.setattr_argument('RF_amp__scan', group = 'RF', processor =  Scannable(default=[NoScan(0.5), RangeScan(0.1, 0.5, 20)], 
                                global_min=0, global_step=0.1, ndecimals=3))
        
        self.sum11 = 0
        self.sum12 = 0

    def run(self):

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect12', 'detect11']], broadcast=True, archive=True, persist=True)
        # self.set_dataset('ratio_list', [], broadcast=True, archive=True)

        self.set_dataset('runid', self.scheduler.rid, broadcast=True, archive=False)     # This is for display of RUNID on the figure

        # assume a 1D scan for plotting
        self.set_dataset('scan_x', [], broadcast=True, archive=True)
        self.set_dataset('sum11', np.zeros(point_num), broadcast=True, archive=True)
        # self.set_dataset('sum12', np.zeros(point_num), broadcast=True, archive=True)

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Detection_Counts",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "sum11"
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

        # $python -m applets.plot_multi  --x scan_x --y-names sum11 sum12 --rid runid --y-label 'Counts' --x-label 'Scanned variable'

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


            t_now = time.time()  # Save the current time

            point_num = 0
            for point in msm:

                print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # update the plot x-axis ticks
                self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                # Run the main portion of code here
                self.kernel_run()

                self.mutate_dataset('sum11', point_num, self.sum11)

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

        self.core.reset()
        self.core.break_realtime()

        # Hard-coded to set the AOM frequency and amplitude
        delay_mu(95000)
        self.DDS__urukul3_ch2.set(self.RF_freq, amplitude=self.RF_amp)

        # Turn on the DDS
        self.DDS__urukul3_ch2.sw.on()

        # Make sure the lasers are turned on
        self.ttl_370_2G_EOM.off()
        self.ttl_370_7G_EOM.on()
        self.ttl_370_AOM.on()
        self.ttl_935_EOM.on()
        
        gate_end_mu_B1 = self.Bob_PMT.gate_rising(self.detection_time)

        temp = self.Bob_PMT.count(gate_end_mu_B1)
        self.sum11 = temp


        # Cool ion during return to host
        self.ttl_370_2G_EOM.off()
        self.ttl_370_7G_EOM.on()
        self.ttl_370_AOM.on()
        self.ttl_935_EOM.on()
