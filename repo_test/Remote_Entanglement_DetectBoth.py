""" Remote Entanglement with 4-APD HOM measurement
Turn on Ba_ratios and Detection_Counts APPLETS to plot the figures
Run Remote entanglement on Alice and Bob only, using all 4 APDs

Collates the counts detected with sigma-1/2 for each pattern

Problems:
    Alice and Bob always detect using the same 493 sigma
    No detection for (A-1, B-2) or (A-2, B-1)

George Toh 2020-12-07

"""
import artiq.language.environment as artiq_env
import artiq.language.units as aq_units
import numpy as np
import math
import pkg_resources
from artiq.language.core import kernel, delay, delay_mu, parallel
from artiq.language.types import TInt32
from artiq.coredevice.rtio import rtio_output
from dynaconf import LazySettings
# George added these:
import base_experiment
from artiq.experiment import *
import time
from AWGmessenger import sendmessage   # Other file in the repo, contains code for messaging Jarvis

# Get the number of inputs & outputs from the settings file.
settings = LazySettings(
    ROOT_PATH_FOR_DYNACONF=pkg_resources.resource_filename("entangler", "")
)
num_inputs = settings.NUM_ENTANGLER_INPUT_SIGNALS
num_outputs = settings.NUM_OUTPUT_CHANNELS

# class Remote_Entanglement_Experiment_Sample(base_experiment.base_experiment):
# class EntanglerDemo(artiq_env.EnvExperiment):
class Remote_Entanglement_Test2(base_experiment.base_experiment):

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        "raman_time",
        "fastloop_run_ns",
    }

    def build(self):
        """Add the Entangler driver."""
        self.setattr_device("core")
        self.setattr_device("ccb")
        self.setattr_device("entangler")
        self.out0_0 = self.get_device("ttl0")

        # This hardcoding is necessary for writing to the gateware for the fast loop.
        self.entangle_inputs = [
            self.get_device("ttl{}".format(i)) for i in range(8, 12)
        ]
        self.generic_inputs = [self.get_device("ttl{}".format(i)) for i in range(12, 16)]

        # Add other inputs
        super().build()
        self.setattr_device("core_dma")

        self.setattr_argument('calculate_runtime', BooleanValue(True))
        self.setattr_argument('do_Raman_AWG', BooleanValue(True))
        self.setattr_argument('pump_650sigma_1or2', NumberValue(1, step=1, min=1, max=2, ndecimals=0))
        self.setattr_argument('fastloop_run_ns', NumberValue(500000, step=1000, min=1000, max=2e9, ndecimals=0))    # How long to run the entangler sequence for. Blocks, cannot terminate
        self.setattr_argument('entangle_cycles_per_loop', NumberValue(100, step=1, min=1, max=1000, ndecimals=0))     # How many cool+entangler cycles to run. Max 1 detection per cycle
        self.setattr_argument('loops_to_run', NumberValue(100, step=1, min=1, max=10000, ndecimals=0))
        self.setattr_argument('extra_pump', NumberValue(1000, step=100, min=-900, max=10000, ndecimals=0))

        self.scan_names = ['cooling_time', 'raman_time', 'detection_time', 'delay_time', 'DDS__532__Alice__tone_1__frequency', 'DDS__532__Alice__tone_2__frequency', 'DDS__532__Alice__tone_1__amplitude', 'DDS__532__Alice__tone_2__amplitude']
        # self.scan_names = ['cooling_time', 'pumping_time', 'detection_time', 'delay_time']
        self.setattr_argument('cooling_time__scan',   Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 20) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        # self.setattr_argument('pumping_time__scan',   Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 20) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))

        self.setattr_argument('Alice_raman_time', NumberValue(10, step=1, min=0.1, max=1000, unit='ns', ndecimals=3))
        self.setattr_argument('Bob_raman_pi_time', NumberValue(10, step=1, min=0.1, max=1000, unit='ns', ndecimals=3))
        self.setattr_argument('Bob_pause_between', NumberValue(10, step=1, min=0.1, max=1000, unit='ns', ndecimals=3))
        self.setattr_argument('Bob_raman_time', NumberValue(10, step=1, min=0.1, max=1000, unit='ns', ndecimals=3))

        # self.setattr_argument('raman_time__scan', Scannable(default=[NoScan(self.globals__timing__raman_time), RangeScan(1 * us, 3 * self.globals__timing__raman_time, 100)], global_min=0 * us, global_step=1 * us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 20) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('delay_time__scan', Scannable(default=[NoScan(450), RangeScan(300, 600, 20)], global_min=0, global_step=10, ndecimals=0))

        self.setattr_argument('DDS__532__Alice__tone_1__frequency__scan', Scannable(default=[NoScan(self.globals__DDS__532__Alice__tone_1__frequency), CenterScan(self.globals__DDS__532__Alice__tone_1__frequency / MHz, 1, 0.1)], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__532__Alice__tone_2__frequency__scan', Scannable(default=[NoScan(self.globals__DDS__532__Alice__tone_2__frequency), CenterScan(self.globals__DDS__532__Alice__tone_2__frequency / MHz, 1, 0.1)], unit='MHz', ndecimals=9))
        self.setattr_argument('DDS__532__Alice__tone_1__amplitude__scan', Scannable(default=[NoScan(self.globals__DDS__532__Alice__tone_1__amplitude), RangeScan(0, 1, 100)], global_min=0, global_step=0.1, ndecimals=3))
        self.setattr_argument('DDS__532__Alice__tone_2__amplitude__scan', Scannable(default=[NoScan(self.globals__DDS__532__Alice__tone_2__amplitude), RangeScan(0, 1, 100)], global_min=0, global_step=0.1, ndecimals=3))


    def run(self):

        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['ratiop1', 'ratiop2', 'ratiop3', 'ratiop4']], broadcast=True, archive=True, persist=True)
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        self.set_dataset('pattern_counts', [], broadcast=True, archive=True)

        self.set_dataset('sum_p1_A1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p1_A2', [], broadcast=True, archive=True)
        self.set_dataset('sum_p2_A1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p2_A2', [], broadcast=True, archive=True)
        self.set_dataset('sum_p3_A1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p3_A2', [], broadcast=True, archive=True)
        self.set_dataset('sum_p4_A1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p4_A2', [], broadcast=True, archive=True)

        self.set_dataset('sum_p1_B1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p1_B2', [], broadcast=True, archive=True)
        self.set_dataset('sum_p2_B1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p2_B2', [], broadcast=True, archive=True)
        self.set_dataset('sum_p3_B1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p3_B2', [], broadcast=True, archive=True)
        self.set_dataset('sum_p4_B1', [], broadcast=True, archive=True)
        self.set_dataset('sum_p4_B2', [], broadcast=True, archive=True)

        self.set_dataset('num_attempts', [], broadcast=True, archive=True)

        self.set_dataset('runid', self.scheduler.rid, broadcast=True, archive=False)     # This is for display of RUNID on the figure

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="IonPhoton_Counts",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "sum_p1_1 sum_p1_2"
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

        # For graphs, turn on Ba_ratios

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
            print("Number of points: ", point_num)

            # assume a 1D scan for plotting
            self.set_dataset('scan_x', [], broadcast=True, archive=True)

            t_now = time.time()  # Save the current time

            # Print estimated run-time
            if self.calculate_runtime:
                self.runtime_calculation()

            point_num = 0
            for point in msm:

                print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # update the plot x-axis ticks
                self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                # George hardcoded this in kernel_run to ensure all AOMs are updated
                # # update DDS if scanning DDS
                # for name in self.active_scan_names:
                #     if name.startswith('DDS'):
                #         if name.endswith('__frequency'):
                #             # print(name)
                #             channel_name = name.rstrip('__frequency')
                #             channel = getattr(self, channel_name)
                #             self.set_DDS_freq(channel, getattr(self, name))
                #         if name.endswith('__amplitude'):
                #             channel_name = name.rstrip('__amplitude')
                #             channel = getattr(self, channel_name)
                #             self.set_DDS_amp(channel, getattr(self, name))

                if self.do_Raman_AWG:
                    #  Program the Keysight AWG

                    # if self.flush_awg == True:
                    sendmessage(self, type="flush")
                    time.sleep(0.8)  # Need at least 0.7s of delay here for wave-trigger to work correctly

                    sendmessage(self,
                                type="wave",
                                channel=1,
                                amplitude1=self.DDS__532__Alice__tone_1__amplitude,
                                amplitude2=self.DDS__532__Alice__tone_1__amplitude,
                                frequency1=self.DDS__532__Alice__tone_1__frequency,  # Hz
                                frequency2=self.DDS__532__Alice__tone_2__frequency,  # Hz
                                phase1=0,  # radians
                                phase2=0,  # radians
                                duration1=self.Alice_raman_time/ns,  # ns
                                # duration2=self.Alice_raman_time/ns,  # ns
                                pause1=(self.Bob_raman_pi_time + self.Bob_pause_between)/ns,
                                # pause2=self.pause_between
                                )
                    time.sleep(0.1)

                    sendmessage(self,
                                type="wave",
                                channel=1,
                                amplitude1=self.DDS__532__Bob__tone_1__amplitude,
                                amplitude2=self.DDS__532__Bob__tone_1__amplitude,
                                frequency1=self.DDS__532__Bob__tone_1__frequency,  # Hz
                                frequency2=self.DDS__532__Bob__tone_2__frequency,  # Hz
                                phase1=0,  # radians
                                phase2=0,  # radians
                                duration1=self.Bob_raman_pi_time/ns,  # ns
                                duration2=self.Bob_raman_time/ns,  # ns
                                # pause1=self.pause_before,
                                pause2=self.Bob_pause_between/ns
                                )
                    time.sleep(0.1)

                # Run the main portion of code here
                detect_p1, detect_p2, detect_p3, detect_p4, sum_p1_A1, sum_p1_A2, sum_p2_A1, sum_p2_A2, sum_p3_A1, sum_p3_A2, sum_p4_A1, sum_p4_A2, sum_p1_B1, sum_p1_B2, sum_p2_B1, sum_p2_B2, sum_p3_B1, sum_p3_B2, sum_p4_B1, sum_p4_B2, attempts = self.kernel_run()

                ratioA_p1 = sum_p1_A1 / (sum_p1_A1 + sum_p1_A2)
                ratioA_p2 = sum_p2_A1 / (sum_p2_A1 + sum_p2_A2)
                ratioA_p3 = sum_p3_A1 / (sum_p3_A1 + sum_p3_A2)
                ratioA_p4 = sum_p4_A1 / (sum_p4_A1 + sum_p4_A2)
                ratiosA = [ratioA_p1, ratioA_p2, ratioA_p3, ratioA_p4]

                ratioB_p1 = sum_p1_B1 / (sum_p1_B1 + sum_p1_B2)
                ratioB_p2 = sum_p2_B1 / (sum_p2_B1 + sum_p2_B2)
                ratioB_p3 = sum_p3_B1 / (sum_p3_B1 + sum_p3_B2)
                ratioB_p4 = sum_p4_B1 / (sum_p4_B1 + sum_p4_B2)
                ratiosB = [ratioB_p1, ratioB_p2, ratioB_p3, ratioB_p4]

                pcounts = [detect_p1, detect_p2, detect_p3, detect_p4]
                ratios = [ratioA_p1, ratioA_p2, ratioA_p3, ratioA_p4, ratioB_p1, ratioB_p2, ratioB_p3, ratioB_p4]

                self.append_to_dataset('pattern_counts', pcounts)
                self.append_to_dataset('ratio_list', ratios)

                self.append_to_dataset('sum_p1_A1', sum_p1_A1)
                self.append_to_dataset('sum_p1_A2', sum_p1_A2)
                self.append_to_dataset('sum_p2_A1', sum_p2_A1)
                self.append_to_dataset('sum_p2_A2', sum_p2_A2)
                self.append_to_dataset('sum_p3_A1', sum_p3_A1)
                self.append_to_dataset('sum_p3_A2', sum_p3_A2)
                self.append_to_dataset('sum_p4_A1', sum_p4_A1)
                self.append_to_dataset('sum_p4_A2', sum_p4_A2)

                self.append_to_dataset('sum_p1_B1', sum_p1_B1)
                self.append_to_dataset('sum_p1_B2', sum_p1_B2)
                self.append_to_dataset('sum_p2_B1', sum_p2_B1)
                self.append_to_dataset('sum_p2_B2', sum_p2_B2)
                self.append_to_dataset('sum_p3_B1', sum_p3_B1)
                self.append_to_dataset('sum_p3_B2', sum_p3_B2)
                self.append_to_dataset('sum_p4_B1', sum_p4_B1)
                self.append_to_dataset('sum_p4_B2', sum_p4_B2)

                self.append_to_dataset('num_attempts', attempts)

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                point_num += 1

                # TODO Remove this later if you want to do scans
                break

        except TerminationRequested:
            # These are necessary to restore the system to the state before the experiment.
            self.load_globals_from_dataset()  # This loads global settings from datasets
            self.setup()  # This sends settings out to the ARTIQ hardware
            print('Terminated gracefully')

        print("Time taken = {:.2f} seconds".format(time.time() - t_now))  # Calculate how long the experiment took

        print("------------------------------------------------------------------DEBUG MESSAGES---------------------------------------------------------------------------")
        print("Code done running {:.0f} {:.0f} {:.0f} {:.0f}".format(detect_p1, detect_p2, detect_p3, detect_p4))
        print("ratio_p1, ratio_p2, ratio_p3, ratio_p4, {:.2f} {:.2f} {:.2f} {:.2f}".format(ratio_p1, ratio_p2, ratio_p3, ratio_p4))
        print("sum_p1_B1, sum_p2_B1, sum_p3_B1, sum_p4_B1,  {:.0f} {:.0f} {:.0f} {:.0f}".format(sum_p1_B1, sum_p2_B1, sum_p3_B1, sum_p4_B1))
        print("sum_p1_B2, sum_p2_B2, sum_p3_B2, sum_p4_B2,  {:.0f} {:.0f} {:.0f} {:.0f}".format(sum_p1_B2, sum_p2_B2, sum_p3_B2, sum_p4_B2))
        print("Total:  {:.0f} {:.0f}".format(detect_p1+ detect_p2+ detect_p3+ detect_p4, sum_p1_B1+ sum_p1_B2+ sum_p2_B1+ sum_p2_B2+ sum_p3_B1+ sum_p3_B2+ sum_p4_B1+ sum_p4_B2))
        print("Attempt%, Total_attempts: {:.2f} {:.0f}".format(100 * (detect_p1 + detect_p2 + detect_p3 + detect_p4) / attempts, attempts))

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()       # This loads global settings from datasets
        self.setup()        # This sends settings out to the ARTIQ hardware

    @kernel
    def kernel_run(self):
        """Init and run the Entangler on the kernel.

        Pretty much every line in here is important. Make sure you use ALL of them.
        Note that this can be used in loopback mode. If you connect an output to
        one of the end outputs and observe a different output on an oscilloscope,
        you can see the entanglement end early when it detects an "event".
        However, when the loopback cable is unplugged it will run for the full duration.
        """

        self.core.reset()
        self.core.break_realtime()

        self.init()

        # Turn off everything initially
        self.ttl_493_all.off()
        self.DDS__493__Alice__sigma_1.sw.on()
        self.DDS__493__Alice__sigma_2.sw.on()
        self.DDS__493__Bob__sigma_1.sw.on()
        self.DDS__493__Bob__sigma_2.sw.on()

        self.ttl_650_fast_cw.off()
        self.ttl_650_sigma_1.off()
        self.ttl_650_sigma_2.off()
        self.ttl_Alice_650_pi.off()
        delay_mu(100000)

        # Initialize counters to zero
        sum_p1_A1 = 0
        sum_p1_A2 = 0
        sum_p2_A1 = 0
        sum_p2_A2 = 0
        sum_p3_A1 = 0
        sum_p3_A2 = 0
        sum_p4_A1 = 0
        sum_p4_A2 = 0

        sum_p1_B1 = 0
        sum_p1_B2 = 0
        sum_p2_B1 = 0
        sum_p2_B2 = 0
        sum_p3_B1 = 0
        sum_p3_B2 = 0
        sum_p4_B1 = 0
        sum_p4_B2 = 0

        detect_p1 = 0
        detect_p2 = 0
        detect_p3 = 0
        detect_p4 = 0

        Alice_counts_detect1 = 0
        Alice_counts_detect1 = 0
        Alice_counts_detect2 = 0
        Alice_counts_detect2 = 0
        
        detect_flag = 1
        pattern = 0

        self.set_dataset('core_pattern1', [0], broadcast=True, archive=True)

        # Pre-load all the pulse sequences using DMA
        self.prerecord_cooling_loop()
        self.record_Alice_detect1()
        self.record_Alice_detect2()

        self.record_Bob_detect1()
        self.record_Bob_detect2()

        delay_mu(100000)

        # Assign handles to the pre-recorded sequences
        fast_loop_cooling_handle = self.core_dma.get_handle("cooling_loop_pulses")
        pulses_handle01 = self.core_dma.get_handle("pulses01")
        pulses_handle02 = self.core_dma.get_handle("pulses02")

        # Adding these delays to sync up gate rising with when the laser beams actually turn on
        delay1 = int(self.delay_time)   # For detect sigma1
        delay2 = delay1            # For detect sigma2

        loop = 0
        fail = 0
        total_cycles = 0

        for loop in range(self.loops_to_run):

            # Repeat running the entangler cycles_to_run times
            self.core.break_realtime()      # This appears to be necessary when running the dma
            end_timestamp = now_mu()

            for channel in range(self.entangle_cycles_per_loop):

                # self.core.break_realtime()
                total_cycles += self.entangler.get_ncycles()    # Add up the number of entangler attempts
                delay_mu(40000)

                # Cooling loop sequence using pre-recorded dma sequence
                self.core_dma.playback_handle(fast_loop_cooling_handle)
                # delay(self.cooling_time)

                extra_pump = self.extra_pump

                self.setup_entangler(   # This needs to be within the loop otherwise the FPGA freezes
                    cycle_len=1970+extra_pump,     # Current value 1970
                    # Pump on 650 sigma 1 or 650 sigma 2, generate photons with opposite
                    pump_650_sigma=self.pump_650sigma_1or2,
                    out_start=10,  # Pumping, turn on all except 650 sigma 1 or 2
                    out_stop=900+extra_pump,  # Done cooling and pumping, turn off all lasers
                    out_start2=1200+extra_pump,  # Turn on the opposite 650 sigma slow-AOM
                    out_stop2=1500+extra_pump,
                    out_start3=1350+extra_pump,  # Generate single photon by turning on the fast-pulse AOM Currently 1350
                    out_stop3=1360+extra_pump,  # Done generating
                    in_start=1900+extra_pump,  # Look for photons on APD0, this needs to be 470ns (measured) later than start3 due to AOM delays
                    in_stop=1950+extra_pump,
                    pattern_list=[0b0011, 0b1001, 0b0110, 0b1100],
                    # 0001 is ttl8, 0010 is ttl9, 0100 is ttl10, 1000 is ttl11
                    # Run_entangler Returns 1/2/4/8 depending on the pattern list left-right, independent of the binary patterns
                )
                end_timestamp, pattern = self.run_entangler(self.fastloop_run_ns)  # This runs the entangler sequence

                # self.check_entangler_status() # Do we need this?

                # # This causes the program to infinite loop on later loops
                # at_mu(end_timestamp)
                # delay_mu(100000)

                if pattern == 1 or pattern == 2:
                    # print("Entangler success", pattern)
                    # self.ttl_keysight_awg.on()
                    break
                elif pattern == 4 or pattern == 8:
                    # Rotate to match the other state
                    # self.ttl_keysight_awg.off()
                    self.ttl0.pulse(50*ns)  # This triggers the Keysight AWG on all channels                    
                    break
                else:   # Failed to entangle
                    pattern = 0
                    # Add a counter here to sum the number of failed attempts?

            at_mu(end_timestamp)
            delay_mu(30000)

            if pattern == 0:
                delay_mu(100)      # Do nothing

            elif detect_flag == 1:      # Detect flag determines which detection sequence to run
                # Detect on Alice
                delay_mu(100)
                with parallel:
                    with sequential:
                        delay_mu(delay1)   # For turn off/on time of the lasers
                        gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                        gate_end_mu_B1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)      # This consumes two more SED channels so we need to be very careful about outputs
                    self.core_dma.playback_handle(pulses_handle01)
                
                sumA1 = self.Alice_camera_side_APD.count(gate_end_mu_A1)    # This will usually be zero, ~0.05      
                sumB1 = self.Bob_camera_side_APD.count(gate_end_mu_B1)      # This will usually be zero, ~0.05

                # sumB2 = 0
                detect_flag = 2     # Set flag to 2 so we detect with 493 sigma2 next
                if pattern == 1:
                    detect_p1 += 1
                    sum_p1_A1 += sumA1
                    sum_p1_B1 += sumB1
                elif pattern == 2:
                    detect_p2 += 1
                    sum_p2_A1 += sumA1
                    sum_p2_B1 += sumB1
                elif pattern == 4:
                    detect_p3 += 1
                    sum_p3_A1 += sumA1
                    sum_p3_B1 += sumB1
                elif pattern == 8:
                    detect_p4 += 1
                    sum_p4_A1 += sumA1
                    sum_p4_B1 += sumB1

                self.core.break_realtime()
                delay_mu(self.fastloop_run_ns)      # This long delay is needed to make sure the code doesn't freeze, could be reduced by half on average

            elif detect_flag == 2:
                delay_mu(100)
                with parallel:
                    with sequential:
                        delay_mu(delay2)   # For turn off time of the lasers
                        gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                        gate_end_mu_B2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
                    self.core_dma.playback_handle(pulses_handle02)

                sumA2 = self.Alice_camera_side_APD.count(gate_end_mu_A2)
                sumB2 = self.Bob_camera_side_APD.count(gate_end_mu_B2)      # This will usually be zero, ~0.05

                # sumB1 = 0
                detect_flag = 1
                if pattern == 1:
                    detect_p1 += 1
                    sum_p1_A2 += sumA2
                    sum_p1_B2 += sumB2                    
                elif pattern == 2:
                    detect_p2 += 1
                    sum_p2_A2 += sumA2
                    sum_p2_B2 += sumB2                    
                elif pattern == 4:
                    detect_p3 += 1
                    sum_p3_A2 += sumA2
                    sum_p3_B2 += sumB2                    
                elif pattern == 8:
                    detect_p4 += 1
                    sum_p4_A2 += sumA2
                    sum_p4_B2 += sumB2                    

                self.core.break_realtime()
                delay_mu(self.fastloop_run_ns)  # This long delay is needed to make sure the code doesn't freeze

            else:
                fail += 1

            loop += 1


        print(loop, fail)
        # It costs 600 ms to return 1 to the host device
        return detect_p1, detect_p2, detect_p3, detect_p4, sum_p1_A1, sum_p1_A2, sum_p2_A1, sum_p2_A2, sum_p3_A1, sum_p3_A2, sum_p4_A1, sum_p4_A2, sum_p1_B1, sum_p1_B2, sum_p2_B1, sum_p2_B2, sum_p3_B1, sum_p3_B2, sum_p4_B1, sum_p4_B2, attempts


    @kernel
    def init(self):
        """One-time setup on device != entangler."""
        # self.out0_0.pulse(1.5 * aq_units.us)  # marker signal for observing timing
        for ttl_input in self.entangle_inputs:
            ttl_input.input()


    @kernel
    def setup_entangler(
        self, cycle_len, pump_650_sigma, out_start, out_stop, out_start2, out_stop2, out_start3, out_stop3, in_start, in_stop, pattern_list
    ):
        """Configure the entangler. Generating photons with 650sigma2

        These mostly shouldn't need to be changed between entangler runs, though
        you can with most of the set commands.

        Args:
            cycle_len (int): Length of each entanglement cycle.
            pump_650_sigma : Choose if 650 pump is sigma-1 or sigma-2
            out_start (int): Time in cycle when all pumping outputs should turn on.
            out_stop (int): Time in cycle when all pumping outputs should turn off.
            out_start2 (int): Time when opposite 650 sigma slow AOM should turn on
            out_stop2 (int): Time in cycle when opposite 650 sigma slow AOM should turn off (de-assert)
            out_start3 (int): Time in cycle when 650 sigma fast should turn on for single photon generation
            out_stop3 (int): End single photon generation
            in_start (int): Time in cycle when all inputs should start looking for input signals
            in_stop (int): Time in cycle when all inputs should STOP looking for input signals.
            pattern_list (list(int)): List of patterns that inputs are matched
                against. Matching ANY will stop the entangler.
        """
        #
        # TTL_output_list = [
        #     ('ttl0', 'ttl0', False),     Later this will be used for AWG 1/2 selection
        #     ('ttl_Bob_650_pi', 'ttl1', False),
        #     ('ttl_493_all', 'ttl2', False),
        #     ('ttl_650_fast_cw', 'ttl3', False),           This skips the pulse generator
        #     ('ttl_650_sigma_1', 'ttl4', False),
        #     ('ttl_650_sigma_2', 'ttl5', False),
        #     ('ttl_650_fast_pulse', 'ttl6', False),        This goes to pulse generator
        #     ('ttl_Alice_650_pi', 'ttl7', False)
        # ]
        self.entangler.init()

        # This writes an output-high time to all the channels
        for channel in range(num_outputs):
            self.entangler.set_timing_mu(channel, out_start, out_stop)
            # This deals with 650-slow, 493-all, 650-pi

        self.entangler.set_timing_mu(0, 10, 20)  # Hard coded this trigger pulse for testing. 0 = Picoharp trigger

        # Then we overwrite the channels where we have different timings
        if pump_650_sigma == 1:                                # If we pump with sigma1, generate photons with sigma2
            self.entangler.set_timing_mu(5, out_start2, out_stop2)   # Turn on 650sigma2 slow-aom
            self.entangler.set_timing_mu(6, out_start3, out_stop3)   # Turn on 650fast-pulse
        else:
            self.entangler.set_timing_mu(4, out_start2, out_stop2)   # Turn on 650sigma1 slow-aom
            self.entangler.set_timing_mu(6, out_start3, out_stop3)   # Turn on 650fast-pulse

        for channel in range(num_inputs):
            self.entangler.set_timing_mu(channel + num_outputs, in_start, in_stop)

        # NOTE: must set enable, defaults to disabled. If not standalone, tries to sync
        # w/ slave (which isn't there) & doesn't start
        self.entangler.set_config(enable=True, standalone=True)
        self.entangler.set_cycle_length_mu(cycle_len)
        self.entangler.set_patterns(pattern_list)

    @kernel
    def run_entangler(self, timeout_length: TInt32):
        """Run the entangler for a max time and wait for it to succeed/timeout."""
        with parallel:
            # This generates output events on the bus -> entangler
            # when rising edges are detected
            self.entangle_inputs[0].gate_rising_mu(np.int64(timeout_length))
            self.entangle_inputs[1].gate_rising_mu(np.int64(timeout_length))
            self.entangle_inputs[2].gate_rising_mu(np.int64(timeout_length))
            self.entangle_inputs[3].gate_rising_mu(np.int64(timeout_length))
            end_timestamp, reason = self.entangler.run_mu(timeout_length)
        # must wait after entangler ends to schedule new events.

        # Doesn't strictly NEED to break_realtime, but it's safe.
        # self.core.break_realtime()

        # Disable entangler control of outputs as soon as a pattern is detected
        at_mu(end_timestamp)
        delay_mu(15000)     # George found the minimum of 15 us delay here. Increase if necessary
        self.entangler.set_config(enable=False)

        # You might also want to disable gating for inputs, but out-of-scope

        return end_timestamp, reason

    @kernel
    def check_entangler_status(self):
        """Get Entangler end status and log to coreanalyzer.

        Not required in normal usage, recognized pattern is returned by run_entangler().
        """
        delay(100 * aq_units.us)
        status = self.entangler.get_status()
        if status & 0b010:
            rtio_log("entangler", "succeeded")
        else:
            rtio_log("entangler", "End status:", status)

        delay(100 * aq_units.us)
        num_cycles = self.entangler.get_ncycles()
        rtio_log("entangler", "#cycles:", num_cycles)
        delay(100 * aq_units.us)
        ntriggers = self.entangler.get_ntriggers()
        rtio_log("entangler", "#triggers (0 if no ref)", ntriggers)
        for channel in range(num_inputs):
            delay(150 * aq_units.us)
            channel_timestamp = self.entangler.get_timestamp_mu(channel)
            rtio_log("entangler", "Ch", channel, ": ts=", channel_timestamp)
        delay(150 * aq_units.us)

    @kernel
    def prerecord_cooling_loop(self):
        """Pre-record the cooling loop sequence. This is played in the slow loops, once every n number of fast loops
        """

        with self.core_dma.record("cooling_loop_pulses"):
            # Cool
            with parallel:
                self.ttl_Alice_650_pi.on()
                self.ttl_Bob_650_pi.on()
                self.ttl_493_all.on()
                delay_mu(8)
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()

                delay(self.cooling_time)

            with parallel:
                self.ttl_Alice_650_pi.off()
                self.ttl_Bob_650_pi.off()
                self.ttl_493_all.off()
                delay_mu(8)
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_1.off()
                self.ttl_650_sigma_2.off()

    @kernel
    def record_detect1(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 1
        We delay everything by 8ns because we are working with very few SED channels
        8ns is the minimum delay for reliability due to coarse timestamp or rtio clock
        """
        with self.core_dma.record("pulses01"):

            self.DDS__493__Alice__sigma_2.sw.off()  # Turn off the sigma2 laser
            delay_mu(8)
            self.DDS__493__Bob__sigma_2.sw.off()
            delay_mu(8)
            self.ttl_650_sigma_1.on() # 650 sigma 1
            delay_mu(8)
            self.ttl_650_sigma_2.on() # 650 sigma 2
            delay_mu(8)
            self.ttl_Alice_650_pi.on() # Alice 650 pi
            delay_mu(8)
            self.ttl_650_fast_cw.on() # 650 fast AOM
            delay_mu(8)
            self.ttl_493_all.on()                   # Turn all the 493 lasers (only sigma1)

            delay(self.detection_time)

            self.ttl_493_all.off()
            delay_mu(8)
            self.ttl_Alice_650_pi.off() # Alice 650 pi
            delay_mu(8)
            self.ttl_650_fast_cw.off() # 650 fast AOM
            delay_mu(8)
            self.ttl_650_sigma_1.off() # 650 sigma 1
            delay_mu(8)
            self.ttl_650_sigma_2.off() # 650 sigma 2
            delay_mu(8)
            self.DDS__493__Alice__sigma_2.sw.on()
            delay_mu(8)
            self.DDS__493__Bob__sigma_2.sw.on()
            # delay_mu(8)
    @kernel
    def record_detect2(self):
        """DMA detection loop sequence.
        This generates the pulse sequence needed for detection with 493 sigma 2
        We delay everything by 8ns because we are working with very few SED channels
        8ns is the minimum delay for reliability due to coarse timestamp or rtio clock
        """
        with self.core_dma.record("pulses02"):

            self.DDS__493__Alice__sigma_1.sw.off()
            delay_mu(8)
            self.DDS__493__Bob__sigma_1.sw.off()
            delay_mu(8)
            self.ttl_650_sigma_1.on() # 650 sigma 1
            delay_mu(8)
            self.ttl_650_sigma_2.on() # 650 sigma 2 
            delay_mu(8)
            self.ttl_Alice_650_pi.on() # Alice 650 pi
            delay_mu(8)            
            self.ttl_650_fast_cw.on() # 650 fast AOM
            delay_mu(8)
            self.ttl_493_all.on()

            delay(self.detection_time)

            self.ttl_493_all.off()
            delay_mu(8)
            self.ttl_Alice_650_pi.off() # Alice 650 pi
            delay_mu(8)
            self.ttl_650_fast_cw.off() # 650 fast AOM
            delay_mu(8)
            self.ttl_650_sigma_1.off() # 650 sigma 1
            delay_mu(8)
            self.ttl_650_sigma_2.off() # 650 sigma 2
            delay_mu(8)
            self.DDS__493__Alice__sigma_1.sw.on()
            delay_mu(8)
            self.DDS__493__Bob__sigma_1.sw.on()


    def runtime_calculation(self):
        """Non-kernel function to estimate how long the execution will take
        This function calculates the expected runtime with the given inputs
        """
        entangler_time = (self.cooling_time / ns + self.fastloop_run_ns)
        print("Entangler time", "{:.2f}".format(entangler_time * ns), "seconds")
        loop_time = (entangler_time + 40000) * self.entangle_cycles_per_loop
        print("Loop time", "{:.2f}".format(loop_time * ns), "seconds")
        total_time = (loop_time + 200000 + self.detection_time) * self.loops_to_run
        print("Maximum runtime", "{:.2f}".format(total_time * ns, 2), "seconds")
