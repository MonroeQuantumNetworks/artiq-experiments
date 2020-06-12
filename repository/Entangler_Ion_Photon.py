""" Ion-Photon Entanglement with 4-APD HOM measurement
March 6 2020:
George created this file to run Ion-Photon entanglement measurements
A single ion emits only 1 photon so we detect 0001, 0010, 0100 and 1000.
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
from Lecroy1102 import Lecroy1102
import time

# Get the number of inputs & outputs from the settings file.
settings = LazySettings(
    ROOT_PATH_FOR_DYNACONF=pkg_resources.resource_filename("entangler", "")
)
num_inputs = settings.NUM_ENTANGLER_INPUT_SIGNALS
num_outputs = settings.NUM_OUTPUT_CHANNELS

# class Remote_Entanglement_Experiment_Sample(base_experiment.base_experiment):
# class EntanglerDemo(artiq_env.EnvExperiment):
class Entangler_Ion_Photon(base_experiment.base_experiment):
    """Experiment for Ion-Photon Entanglement generation - Bob.
    """

    def build(self):
        """Add the Entangler driver."""
        self.setattr_device("core")
        self.setattr_device("entangler")
        self.out0_0 = self.get_device("ttl0")

        # Pumping
        # 650pi = ttl1,
        # 493all = ttl2
        # 650fast-cw = ttl3
        # 650sigma1 = ttl4
        #
        # Single photon generation:
        # 650sigma2 = ttl5
        # 650fast-pulse = ttl6

        # This hardcoding is necessary for writing to the gateware for the fast loop.
        self.entangle_inputs = [
            self.get_device("ttl{}".format(i)) for i in range(8, 12)
        ]
        self.generic_inputs = [self.get_device("ttl{}".format(i)) for i in range(12, 16)]

        # Add other inputs
        super().build()
        self.setattr_device("core_dma")
        # self.setattr_argument('slack_time', NumberValue(40000, step=5000, min=15000, max=150000, ndecimals=0))
        self.setattr_argument('cooling_time', NumberValue(100000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('fastloop_run_ns', NumberValue(500000, step=1000, min=1000, max=2e9, ndecimals=0))
        self.setattr_argument('pump_650sigma_1or2', NumberValue(1, step=1, min=1, max=2, ndecimals=0))
        self.setattr_argument('entangle_cycles_per_loop', NumberValue(3, step=1, min=1, max=1000, ndecimals=0))
        self.setattr_argument('loops_to_run', NumberValue(3, step=1, min=1, max=1000, ndecimals=0))

        self.setattr_argument('detection_time', NumberValue(200e-6, unit='us', step=1e-6, min=0 * us, ndecimals=0))
        self.setattr_argument('raman_time', NumberValue(2e-6, unit='us', min=0 * us, ndecimals=0))

        self.setattr_argument('test_mode', BooleanValue(True))
        self.setattr_argument('calculate_runtime', BooleanValue(True))
        self.setattr_argument('prepare_awg_bool', BooleanValue(False))

        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(100), RangeScan(0 * us, 300, 100)], global_min=0 * us,
                                                              global_step=1 * us, unit='us', ndecimals=3))

    def run(self):
        """
        Run certain functions on the computer instead of the core device.

        :return:
        """

        self.set_dataset('data_list_sums', [], broadcast=True, archive=True)
        self.set_dataset('data_list_ratios', [], broadcast=True, archive=True)

        # Print estimated run-time
        if self.calculate_runtime:
            self.runtime_calculation()

        # Program the AWG in a non-kernel section of the code
        if self.prepare_awg_bool:
            self.prepare_awg()

        t_now = time.time()     # Save the current time

        detect_p1, sum_p1_B1, sum_p1_B2, sum_p2_B1, sum_p2_B2, sum_p3_B1, sum_p3_B2, sum_p4_B1, sum_p4_B2 = self.kernel_run()     # Run the rest of the program on the core device
        ratio_p1 = sum_p1_B1 / (sum_p1_B1 + sum_p1_B2)
        # ratio_p2 = sum_p2_B1 / (sum_p2_B1 + sum_p2_B2)
        # ratio_p3 = sum_p3_B1 / (sum_p3_B1 + sum_p3_B2)
        # ratio_p4 = sum_p4_B1 / (sum_p4_B1 + sum_p4_B2)
        # ratios = [ratio_p1, ratio_p2, ratio_p3, ratio_p4]
        ratios = [ratio_p1, ratio_p1, ratio_p1, ratio_p1]

        for i in range(len(ratios)):
            self.append_to_dataset('data_list_ratios', ratios[i])

        # self.append_to_dataset('data_list_ratios', ratios)

        print("Actual time taken = {:.2f} seconds" .format(time.time() - t_now))        # Calculate how long the experiment took

        # print("Entangler sequence is done", sum_p1_B1, sum_p1_B2, ratio_p1, "Test mode:", self.test_mode)
        print("Code is done running {:.0f} {:.0f} {:.0f} {:.2f}, Test mode: ".format(detect_p1, sum_p1_B1, sum_p1_B2, ratio_p1), self.test_mode)

        # These are necessary to restore the system to the state before the experiment.
        self.load_globals_from_dataset()    # This loads global settings from datasets
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
        self.core.break_realtime()  # Increases slack to at least 125 us
        self.init()

        # Turn these off for now
        # self.DDS__493__Bob__sigma_1.sw.off()
        # self.DDS__493__Bob__sigma_2.sw.off()
        # self.ttl_493_all.off()
        # self.ttl_650_fast_cw.off()


        # Turn off everything initially
        self.DDS__493__Bob__sigma_1.sw.off()
        self.DDS__493__Bob__sigma_2.sw.off()
        self.ttl_493_all.off()
        self.ttl_650_fast_cw.off()
        self.ttl_650_sigma_1.off()
        self.ttl_650_sigma_2.off()
        self.ttl_650_pi.off()
        delay_mu(100000)
        # They get restored to the initial values later

        # Initialize counters to zero
        sumA1 = 1
        sumB1 = 1
        sumA2 = 1
        sumB2 = 1

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

        ratio1 = float(0)

        Alice_counts_detect1 = 0
        Bob_counts_detect1 = 0
        Alice_counts_detect2 = 0
        Bob_counts_detect2 = 0
        detect_flag = 1
        pattern = 0
        slack = 0

        print('Check Pause test:', self.scheduler.check_pause())

        self.set_dataset('core_pattern1', [0], broadcast=True, archive=True)

        # Pre-load all the pulse sequences using DMA
        self.prerecord_cooling_loop()

        delay_mu(100000)

        # Assign handles to the pre-recorded sequences
        fast_loop_cooling_handle = self.core_dma.get_handle("cooling_loop_pulses")

        for loop in range(self.loops_to_run):

            # Repeat running the entangler cycles_to_run times
            self.core.break_realtime()      # This appears to be necessary when running the dma
            
            for channel in range(self.entangle_cycles_per_loop):

                # Cooling loop sequence using pre-recorded dma sequence
                # self.core_dma.playback_handle(fast_loop_cooling_handle)
                delay(self.cooling_time)

                self.setup_entangler(   # This needs to be within the loop otherwise the FPGA freezes
                    cycle_len=1970,
                    # Pump on 650 sigma 1 or 650 sigma 2, generate photons with opposite
                    pump_650_sigma=self.pump_650sigma_1or2,
                    out_start=10,  # Pumping, turn on all except 650 sigma 1 or 2
                    out_stop=500,  # Done cooling and pumping, turn off all lasers
                    out_start2=1400,  # Turn on the opposite 650 sigma slow-AOM
                    out_stop2=1600,
                    out_start3=1350,  # Generate single photon by turning on the fast-pulse AOM
                    out_stop3=1360,  # Done generating
                    in_start=700,  # Look for photons on APD0
                    in_stop=800,
                    pattern_list=[0b0010, 0b0001, 0b0100, 0b1000],
                    # 0001 is ttl8, 0010 is ttl9, 0100 is ttl10, 1000 is ttl11
                    # Run_entangler Returns 1/2/4/8 depending on the pattern list left-right
                )
                end_timestamp, pattern = self.run_entangler(self.fastloop_run_ns)  # This runs the entangler sequence

                # self.check_entangler_status() # Do we need this?

                if pattern == 1 or pattern == 2:
                    print("Entangler success", pattern)
                    break
                elif pattern == 4 or pattern == 8:
                    print("Entangler success", pattern)
                    # self.run_rotation() # Rotate to match the other state
                    break
                else:   # Failed to entangle
                    # delay_mu(100)
                    if self.test_mode:  # Generate some counts for test-mode
                        pattern = 1
                    else:
                        pattern = 0

            if pattern == 0:
                delay_mu(100)      # Do nothing
            elif detect_flag == 1:
                Bob_counts_detect1 = self.run_detection1()  # Run detection with 493 sigma-1
                sumB1 = Bob_counts_detect1
                sumB2 = 0
                detect_flag = 2
                if pattern == 1:
                    detect_p1 += 1
                    sum_p1_B1 += sumB1
                elif pattern == 2:
                    # detect_p2 += 1
                    sum_p2_B1 += sumB1
                elif pattern == 4:
                    # detect_p3 += 1
                    sum_p3_B1 += sumB1
                elif pattern == 8:
                    # detect_p4 += 1
                    sum_p4_B1 += sumB1
            elif detect_flag == 2:
                Bob_counts_detect2 = self.run_detection2()  # Run detection with 493 sigma-2
                sumB2 = Bob_counts_detect2
                sumB1 = 0
                detect_flag = 1
                if pattern == 1:
                    detect_p1 += 1
                    sum_p1_B2 += sumB2
                elif pattern == 2:
                    # detect_p2 += 1
                    sum_p2_B2 += sumB2
                elif pattern == 4:
                    # detect_p3 += 1
                    sum_p3_B2 += sumB2
                elif pattern == 8:
                    # detect_p4 += 1
                    sum_p4_B2 += sumB2

                # if pattern == 0:
                #     delay_mu(100)
                # elif pattern == 1:
                #     # detect_p1 += 1
                #     sum_p1_B1 += sumB1
                #     sum_p1_B2 += sumB2
                # elif pattern == 2:
                #     # detect_p2 += 1
                #     sum_p2_B1 += sumB1
                #     sum_p2_B2 += sumB2
                # elif pattern == 4:
                #     # detect_p3 += 1
                #     sum_p3_B1 += sumB1
                #     sum_p3_B2 += sumB2
                # elif pattern == 8:
                #     # detect_p4 += 1
                #     sum_p4_B1 += sumB1
                #     sum_p4_B2 += sumB2

                # ratio1 = sum_p1_B1 / (sum_p1_B1 + sum_p1_B2)        # This doesn't take too long
                # self.append_to_dataset('core_pattern1', ratio1)     # This doesn't take too long

        # print("Entangler sequence is done", sum_p1_B1, sumB2, ratio1, "Test mode:", self.test_mode)

        # It costs 600 ms to return 1 to the host device
        return detect_p1, sum_p1_B1, sum_p1_B2, sum_p2_B1, sum_p2_B2, sum_p3_B1, sum_p3_B2, sum_p4_B1, sum_p4_B2


    @kernel
    def init(self):
        """One-time setup on device != entangler."""
        self.out0_0.pulse(1.5 * aq_units.us)  # marker signal for observing timing
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
        #     ('ttl0', 'ttl0', False),
        #     ('ttl_650_pi', 'ttl1', False),
        #     ('ttl_493_all', 'ttl2', False),
        #     ('ttl_650_fast_cw', 'ttl3', False),
        #     ('ttl_650_sigma_1', 'ttl4', False),
        #     ('ttl_650_sigma_2', 'ttl5', False),
        #     ('ttl_650_fast_pulse', 'ttl6', False),
        #     ('ttl_test', 'ttl7', False)
        # ]
        self.entangler.init()
        # This writes an output-high time to all the channels
        for channel in range(num_outputs):
            self.entangler.set_timing_mu(channel, out_start, out_stop)
        self.entangler.set_timing_mu(0, 10, 20)  # Hard coded this trigger pulse for testing. 0 = Picoharp trigger
        # self.entangler.set_timing_mu(6, 1000, 1000)  # Turns off pulse generator if not used

        # Then we overwrite the channels where we have different timings
        if pump_650_sigma == 1:                                # If we pump with sigma1, generate photons with sigma2
            self.entangler.set_timing_mu(5, out_start2, out_stop2)   # Turn on 650sigma2 slow-aom
            self.entangler.set_timing_mu(6, out_start3, out_stop3)   # Turn on 650fast-pulse
        else:
            self.entangler.set_timing_mu(4, out_start2, out_stop2)   # Turn on 650sigma1 slow-aom
            self.entangler.set_timing_mu(6, out_start3, out_stop3)   # Turn on 650fast-pulse
        self.entangler.set_timing_mu(7, 2000, 2000)   # ttl7 unused, disable output
        # self.entangler.set_timing_mu(1, 2000, 2000)

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
        delay_mu(40000)     # George found the minimum of 15 us delay here. Increase if necessary

        # Disable entangler control of outputs
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
        """Pre-record the cooling loop sequence.

        Hopefully this is faster than non pre-recorded
        """

        with self.core_dma.record("cooling_loop_pulses"):
            # Cool
            with parallel:
                self.DDS__493__Bob__sigma_2.sw.on()     # Added for testing
                self.ttl_650_pi.on()
                with sequential:
                    delay_mu(750)
                    self.ttl_493_all.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()
                self.ttl_test.on()  # This channel for diagnostics

                # delay(1000 * us)
                delay(self.cooling_time)

            with parallel:
                self.DDS__493__Bob__sigma_2.sw.off()     # Added for testing
                self.ttl_650_pi.off()
                with sequential:
                    delay_mu(750)
                    self.ttl_493_all.off()
                self.ttl_650_fast_cw.off()
                self.ttl_650_sigma_1.off()
                self.ttl_650_sigma_2.off()
                self.ttl_test.off()

    @kernel
    def run_detection1(self):
        """Non-DMA detection loop sequence. With test pulses

        This generates the pulse sequence needed for detection with 493 sigma 1
        It currently generates a test pulse sequence on the 650_pi output for loopback testing
        """
        delay(100 * us)     # This is needed to buffer for pulse train generation
        t1 = now_mu()
        with parallel:
            # gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_650_pi.pulse(self.detection_time)
            self.ttl_650_fast_cw.pulse(self.detection_time)
            self.ttl_650_sigma_1.pulse(self.detection_time)
            self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_1.sw.pulse(self.detection_time)
            # self.DDS__493__Bob__sigma_1.sw.pulse(self.detection_time)
            with sequential:    # Generate fake pulse sequence for triggering the counter
                for i in range(31):
                    self.ttl_650_pi.pulse(1 * us)
                    delay(1 * us)
            with sequential:     # This would have to run on SED channel 9 which does not exist
                for i in range(31):
                    self.ttl_test.pulse(1 * us)
                    delay(1 * us)

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B1)

        return Bob_counts

    @kernel
    def run_detection2(self):
        """Non-DMA detection loop sequence. With test pulses

        This generates the pulse sequence needed for detection with 493 sigma 2
        It currently generates a test pulse sequence on the 650_pi output for loopback testing
        """
        delay(100 * us)     # This is needed to buffer for pulse train generation
        t1 = now_mu()
        with parallel:
            # gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
            gate_end_mu_B2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)

        at_mu(t1)
        with parallel:
            # self.ttl_650_pi.pulse(self.detection_time)
            self.ttl_650_fast_cw.pulse(self.detection_time)
            self.ttl_650_sigma_1.pulse(self.detection_time)
            self.ttl_650_sigma_2.pulse(self.detection_time)
            # self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)
            # self.DDS__493__Bob__sigma_2.sw.pulse(self.detection_time)
            with sequential:    # Generate fake pulse sequence for triggering the counter
                for i in range(13):
                    self.ttl_650_pi.pulse(1 * us)
                    delay(1 * us)

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B2)

        return Bob_counts

    def prepare_awg(self):
        """ Non-kernel code section for preparing the Lecroy 1102 AWG

        This does not work on the kernel (executed on the core device / FPGA)
        """
        IP_address = '192.168.1.100'  # server is running on JARVIS
        port = 11000
        sample_rate = 250 * MHz
        ext_clock_frequency = 10 * MHz

        try:
            awg = Lecroy1102(IP_address, port, sample_rate, ext_clock_frequency)
            awg.open()
            if not awg.enabled:
                return
            print('awg.sample_length', awg.sample_length)
            t = np.arange(0, 5 * us, awg.sample_length)
            print('length t:', len(t))
            waveform1 = np.sin(2 * np.pi * 106.9 * MHz * t) + np.sin(2 * np.pi * 113.3 * MHz * t)
            waveform2 = np.sin(2 * np.pi * 85 * MHz * t)
            awg.program(waveform1, waveform2)
            self.set_dataset('waveforms', np.array([q for q in zip(waveform1, waveform2)]), broadcast=True,
                             persist=True, archive=True)
            self.set_dataset('waveform1', waveform1, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform2', waveform2, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_names', [bytes(i, 'utf-8') for i in ['channel 1', 'channel 2']], broadcast=True,
                             persist=True, archive=True)
            self.set_dataset('waveform_t', t, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_x_names', [bytes(i, 'utf-8') for i in ['time']], broadcast=True, persist=True,
                             archive=True)
        finally:
            awg.close()

        self.kernel_run()

        print('end')

    def runtime_calculation(self):
        """Non-kernel function to estimate how long the execution will take
        This function calculates the expected runtime with the given inputs
        """
        entangler_time = (self.cooling_time / ns + self.fastloop_run_ns)
        print("Entangler time", "{:.2f}".format(entangler_time * ns), "seconds")
        loop_time = (entangler_time + 40000) * self.entangle_cycles_per_loop
        print("Loop time", "{:.2f}".format(loop_time * ns), "seconds")
        total_time = (loop_time + 200000 + self.detection_time) * self.loops_to_run
        print("Estimated runtime", "{:.2f}".format(total_time * ns, 2), "seconds")

    # @rpc(flags={"async"})
    # def rpc_check_pause(self):
    #     self.scheduler.check_pause()  # enclosing it in an RPC might not be necessary