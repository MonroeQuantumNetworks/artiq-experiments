"""
Bob Barium 650 excitation calibration
Scan 650 excitation AOM amplitude while counting the number of photons obtained
Keep the 650 re-pump off, detect with both 493 beams

George 2021-04
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
from scipy import optimize

class Bob_Ba_650_excitation_calibrate(base_experiment.base_experiment):

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        "DDS_650exc_amplitude",
        "DDS_650exc_frequency",
        "DDS_650exc_attenuation",
    }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")
        # self.detector = self.Bob_camera_side_APD

        self.setattr_argument('detections_per_point', NumberValue(200, ndecimals=0, min=1, step=1))
        self.setattr_argument('pump_sigma_1_or_2', NumberValue(1, ndecimals=0, min=1, max=2, step=1))

        # self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'DDS__493__Bob__sigma_1__frequency', 'DDS__493__Bob__sigma_2__frequency', 'DDS__493__Bob__sigma_1__amplitude', 'DDS__493__Bob__sigma_2__amplitude']
        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'delay_time', 'DDS_650exc_frequency', 'DDS_650exc_amplitude', 'DDS_650exc_attenuation']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 10) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('delay_time__scan', Scannable(default=[NoScan(500), RangeScan(0, 1000, 10)], global_min=0, global_step=10, ndecimals=0))

        self.setattr_argument('DDS_650exc_frequency__scan', Scannable(default=[NoScan(82.5e6), RangeScan(82.9e6, 83.1e6, 20)], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS_650exc_amplitude__scan', Scannable(default=[NoScan(0.5), RangeScan(0, 0.5, 20)], global_min=0, global_step=0.1, ndecimals=1))
        self.setattr_argument('DDS_650exc_attenuation__scan', Scannable(default=[NoScan(11), RangeScan(0, 0.5, 20)], unit='dB', scale=1.0, ndecimals=9, global_min=0.0, global_max=31.5, global_step=0.5))

        # 1 <--> sigma_1, 2 <--> sigma_2, 3 <--> pi
        self.sum1 = 0

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
            # self.set_dataset('sum2', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum3', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum13', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum23', np.zeros(point_num), broadcast=True, archive=True)
            point_num = 0

            # self.prep_kernel_run()  #

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

                self.mutate_dataset('sum1', point_num, self.sum1)

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

        self.core.reset()   # This is necessary to make it run fast
        # self.core.break_realtime()    # Extremely slow
        # delay_mu(100000)
        # self.DDS__urukul3_ch1.set_att(self.DDS_650exc_attenuation)
        delay_mu(100000)
        self.DDS__urukul3_ch1.set(self.DDS_650exc_frequency, amplitude=self.DDS_650exc_amplitude)

        # Preparation for experiment
        # if self.pump_sigma_1_or_2 == 1:
        #     self.record_pump_sigma1()
        # else:
        self.record_pump_sigma2()
        self.record_detect1()

        # Prep beams
        self.prep_record()
        pulses_handle_prep = self.core_dma.get_handle("pulses_prep")
        self.core.break_realtime()
        self.core_dma.playback_handle(pulses_handle_prep)
        delay_mu(1000)

        # cool_handle = self.core_dma.get_handle("pulses_cool")
        # if self.pump_sigma_1_or_2 == 1:
        #     pulses_handle_pump = self.core_dma.get_handle("pulses_pump_1")
        # else:
        pulses_handle_pump = self.core_dma.get_handle("pulses_pump_2")
        pulses_handle_detect1 = self.core_dma.get_handle("pulses_detect1")  #Move this up the stack, Have a segment to run all get_handle together??

        delay1 = int(self.delay_time)   # For turn-on time of the laser

        for i in range(self.detections_per_point):

            self.core.break_realtime()  # This is necessary to create slack
            delay_mu(-100000) #Is this required?

            self.core_dma.playback_handle(pulses_handle_pump)  # Cool then Pump
            delay_mu(1000)
            with parallel:
                with sequential:
                    delay_mu(delay1)   # For turn off time of the lasers
                    gate_end_mu_1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                self.core_dma.playback_handle(pulses_handle_detect1)

            delay_mu(1000)

            sum1 += self.Bob_camera_side_APD.count(gate_end_mu_1)

        self.sum1 = sum1


    @kernel
    def prep_record(self):
        # Turn off everything
        with self.core_dma.record("pulses_prep"):

            self.DDS__493__Bob__sigma_1.sw.off() # Bob 493 sigma 1
            self.DDS__493__Bob__sigma_2.sw.off() # Bob 493 sigma 2
            self.DDS__493__Bob__strong_sigma_1.sw.off()  # Bob 493 sigma 1 strong
            self.DDS__493__Bob__strong_sigma_2.sw.off()  # Bob 493 sigma 2 strong
            self.ttl_493_all.off()
            delay_mu(10)
            self.ttl_Bob_650_pi.off() # Bob 650 pi
            self.ttl_650_sigma_1.off() # 650 sigma 1
            self.ttl_650_sigma_2.off() # 650 sigma 2
            delay_mu(10)
            self.ttl_650_fast_cw.on()  # 650 fast AOM
            self.DDS__650__weak_sigma_1.sw.off()
            self.DDS__650__weak_sigma_2.sw.off()
            self.DDS__650__Bob__weak_pi.sw.off()
            delay_mu(10)
            self.DDS__urukul3_ch1.sw.on()
            self.DDS__urukul3_ch2.sw.on()


    @kernel
    def record_pump_sigma2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for pumping with 650 sigma 2
        """
        with self.core_dma.record("pulses_pump_2"):

            # Trigger the picoharp
            self.ttl0.pulse(50 * ns)

            delay_mu(100)

            # Turn on cooling lasers
            self.DDS__650__weak_sigma_1.sw.on()
            self.DDS__650__weak_sigma_2.sw.on()
            self.ttl_650_fast_cw.on()
            self.DDS__650__Bob__weak_pi.sw.on()
            self.DDS__493__Bob__sigma_1.sw.on()
            self.DDS__493__Bob__sigma_2.sw.on()

            # Wait while lasers cool
            delay(self.cooling_time)

            # Turn off cooling lasers
            self.DDS__650__weak_sigma_1.sw.off()
            self.DDS__650__weak_sigma_2.sw.off()
            self.ttl_650_fast_cw.off()
            self.DDS__650__Bob__weak_pi.sw.off()
            self.DDS__493__Bob__sigma_1.sw.off()
            self.DDS__493__Bob__sigma_2.sw.off()

            delay_mu(1000)

            with parallel:
                self.ttl_650_fast_cw.on()
                self.ttl_Bob_650_pi.on()
                self.ttl_493_all.on()
                self.DDS__493__Bob__strong_sigma_1.sw.on()
                self.DDS__493__Bob__strong_sigma_2.sw.on()
                self.ttl_650_sigma_2.on()

            delay(self.pumping_time)  # This delay cannot be zero or ARTIQ will spit out errors

            # Now turn off all the beams
            self.ttl_650_fast_cw.off()
            self.ttl_Bob_650_pi.off()
            self.ttl_650_sigma_2.off()
            delay_mu(200)
            self.ttl_493_all.off()
            self.DDS__493__Bob__strong_sigma_1.sw.off()
            self.DDS__493__Bob__strong_sigma_2.sw.off()

            delay_mu(1000)

            # Turn on the slow AOM first, no 650 light because 650 fast is off
            self.ttl_650_sigma_1.on()
            delay_mu(200)  # Wait 200 ns so that the slow AOMs are fully turned on

            # self.ttl_650_fast_cw.pulse(self.pulse650_duration)          # Use this if using an rf switch
            self.ttl_650_fast_pulse.pulse(40 * ns)  # Use this if using the pulse generator
            delay_mu(100)
            self.ttl_650_sigma_1.off()
            delay_mu(500)


    @kernel
    def record_detect1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 650 sigma 1
        """
        with self.core_dma.record("pulses_detect1"):

            self.DDS__493__Bob__sigma_1.sw.on()
            self.DDS__493__Bob__sigma_2.sw.on()
            delay(self.detection_time)
            self.DDS__493__Bob__sigma_1.sw.off()
            self.DDS__493__Bob__sigma_2.sw.off()
