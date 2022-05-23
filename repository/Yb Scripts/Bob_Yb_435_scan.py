""" Tested, ought to be working
Alice Yb 435 scan


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

class Bob_Yb_435_scan(base_experiment.base_experiment):
    """ Bob Yb 435 Scan"""

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        "photons_0_or_1",
        # "raman_time",
        # "fastloop_run_ns",
    }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Bob_camera_side_APD

        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('photons_0_or_1', NumberValue(2.5, ndecimals=1, min=0.5, step=1))
        # self.setattr_argument('detection_points', NumberValue(1, ndecimals=0, min=1, step=1))

        # Anything with a scannable needs to be listed here
        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'delay_time', 'shelving_time', 'AOM435_frequency', 'AOM435_amplitude']

        # Inputs for 370 laser
        self.setattr_argument('cooling_time__scan', group = '370', processor = Scannable(default=[NoScan(self.globals__timing__cooling_time), 
                                RangeScan(0*us, 3*self.globals__timing__cooling_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        
        self.setattr_argument('pumping_time__scan', group = '370', processor = Scannable(default=[NoScan(self.globals__timing__pumping_time), 
                                RangeScan(0*us, 3*self.globals__timing__pumping_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        
        self.setattr_argument('detection_time__scan', group = '370', processor = Scannable(default=[NoScan(self.globals__timing__detection_time), 
                                RangeScan(0*us, 3*self.globals__timing__detection_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        
        self.setattr_argument('delay_time__scan', group = '370', processor = Scannable(default=[NoScan(500), 
                                RangeScan(0, 1000, 10)], global_min=0, global_step=10, ndecimals=0))

        # Inputs for 435 laser
        self.setattr_argument('shelving_time__scan', group = '435', processor = Scannable(default=[NoScan(1*us), RangeScan(0, 50*us, 10)], 
                                global_min=0*us, global_step=1*us, unit='us', ndecimals=3))

        self.setattr_argument('AOM435_frequency__scan', group = '435', processor =  Scannable(default=[NoScan(80e6), RangeScan(78e6, 82e6, 10)], 
                                unit='MHz', ndecimals=9))

        self.setattr_argument('AOM435_amplitude__scan', group = '435', processor =  Scannable(default=[NoScan(0.5), RangeScan(0.1, 0.5, 20)], 
                                global_min=0, global_step=0.1, ndecimals=3))
        
        self.sum11 = 0
        self.sum12 = 0

    def run(self):

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect12', 'detect11']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)

        self.set_dataset('runid', self.scheduler.rid, broadcast=True, archive=False)     # This is for display of RUNID on the figure

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Detection_Counts",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "sum12 sum11"
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


        # Also, turn on Ba_ratios to plot the figures

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

                # For Yb, these are all that are needed:
                ratio11 = self.sum11 / (self.sum11 + self.sum12)
                ratio12 = self.sum12 / (self.sum11 + self.sum12)
                
                self.mutate_dataset('sum11', point_num, self.sum11)
                self.mutate_dataset('sum12', point_num, self.sum12)

                ratios = np.array([ratio12, ratio11]) 

                self.append_to_dataset('ratio_list', ratios)


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
        self.DDS__AOM435.set(self.AOM435_frequency, amplitude=self.AOM435_amplitude)
        # delay_mu(95000)
        # self.DDS__AOM435.set(self.AOM435_frequency, amplitude=self.AOM435_amplitude)

        sum0 = 0
        sum1 = 0
        self.core.reset()

        # Preparation for experiment
        self.prep_record()
        self.record_pump_0()
        self.record_detect()

        prep_handle = self.core_dma.get_handle("pulses_prep")
        pulses_handle0 = self.core_dma.get_handle("pulses0")
        pulses_detect = self.core_dma.get_handle("pulsesd")
        self.core.break_realtime()
        self.core_dma.playback_handle(prep_handle) 

        delay1 = int(self.delay_time)
        
        gate_end_mu_B1 = 0
        for i in range(self.detections_per_point):
            self.core.break_realtime()  # This makes underflow errors less likely
            
            delay_mu(30000)
            # for i in range(10):

            self.core_dma.playback_handle(pulses_handle0)  # Cool then Pump then apply 435
            # delay_mu(500)   # To compensate for AOM turn off time

            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn on off time of the lasers
                    gate_end_mu_B1 = self.Bob_PMT.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_detect)
            
            # for i in range(10):
            delay_mu(100000)

            temp = self.Bob_PMT.count(gate_end_mu_B1)
            if temp > self.photons_0_or_1:
                sum1 += 1
            else:
                sum0 += 1

            # sum0 = self.Bob_PMT.count(gate_end_mu_B1)

        self.sum11 = sum0
        self.sum12 = sum1

        # Cool ion during return to host
        self.ttl_370_2G_EOM.off()
        self.ttl_370_7G_EOM.on()
        self.ttl_370_AOM.on()
        self.ttl_935_EOM.on()



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

            delay_mu(1000)
            # delay_mu(7000000)

            # self.ttl_935_EOM.on()
            # delay_mu(100000)
            self.DDS__AOM435.sw.on()

            delay(self.shelving_time)

            # self.ttl_935_EOM.off()
            self.DDS__AOM435.sw.off()

            delay_mu(1000)  # For timing detection timing purposes

            # delay_mu(5000000)
            # self.ttl_370_AOM.on()
            # delay(self.detection_time)
            # self.ttl_370_AOM.off()

            # self.ttl_935_EOM.on()
            # delay_mu(1500000)      # Try to de-shelve the ion
            # self.ttl_935_EOM.off() 

    @kernel
    def record_detect(self):
        """DMA pump and detection loop sequence.
        This generates the pulse sequence needed for detection
        """
        with self.core_dma.record("pulsesd"):
            self.ttl_370_AOM.on()
            self.ttl_935_EOM.on()
            # self.ttl_370_7G_EOM.on()
            # self.DDS__AOM435.sw.on()
            # self.ttl_370_2G_EOM.on()

            delay(self.detection_time)

            # self.DDS__AOM435.sw.off()
            # self.ttl_370_7G_EOM.off()  
            self.ttl_935_EOM.off()          
            self.ttl_370_AOM.off()
            # self.ttl_370_2G_EOM.off()
