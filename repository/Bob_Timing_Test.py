""" Bob Timing Test Code

This generates pulsed pumping and single photon generation sequences in Bob for test purposes
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
# import settings as settings3

# Get the number of inputs & outputs from the settings file.
settings = LazySettings(
    ROOT_PATH_FOR_DYNACONF=pkg_resources.resource_filename("entangler", "")
)
num_inputs = settings.NUM_ENTANGLER_INPUT_SIGNALS
num_outputs = settings.NUM_OUTPUT_CHANNELS

# class Remote_Entanglement_Experiment_Sample(base_experiment.base_experiment):
# class EntanglerDemo(artiq_env.EnvExperiment):

class Bob_Timing_Test(base_experiment.base_experiment):
# class Bob_Timing_Test(settings3.settings):
    """Experiment for Testing AOM Timings - Bob.
    """

    def build(self):

        super().build()

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
        self.setattr_device("core_dma")
        # self.setattr_argument('slack_time', NumberValue(40000, step=5000, min=15000, max=150000, ndecimals=0))
        self.setattr_argument('cooling_time', NumberValue(1000e-9, unit='ns', min=0 * ns, ndecimals=0))
        self.setattr_argument('fastloop_run_ns', NumberValue(500000, step=1000, min=1000, max=2e9, ndecimals=0))
        self.setattr_argument('pump_650sigma_1or2', NumberValue(1, step=1, min=1, max=2, ndecimals=0))
        # self.setattr_argument('entangle_cycles_per_loop', NumberValue(3, step=1, min=1, max=1000, ndecimals=0))
        self.setattr_argument('loops_to_run', NumberValue(3, step=1, min=1, max=1000, ndecimals=0))

        self.setattr_argument('detection_time', NumberValue(200e-6, unit='us', step=1e-6, min=0 * us, ndecimals=0))
        self.setattr_argument('raman_time', NumberValue(2e-6, unit='us', min=0 * us, ndecimals=0))

        self.setattr_argument('test_mode', BooleanValue(True))
        self.setattr_argument('calculate_runtime', BooleanValue(True))
        self.setattr_argument('prepare_awg_bool', BooleanValue(False))

        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(100), RangeScan(0 * us, 300, 100)], global_min=0 * us,
                                                              global_step=1 * us, unit='us', ndecimals=3))

        # for i in range(len(self.DDS_device_list)):
        #     self.DDS_setup(i)
        #
        # @kernel
        # def DDS_setup(self, i):
        #     """
        #     Sets up one DDS channel based on passed in info
        #     :param i:  The index for the matching lists of DDS info created during build().
        #     :return:
        #     """

        # i = 1
        # delay_mu(10000)
        # # name = self.DDS_name_list[i]
        # channel = self.DDS_device_list[i]
        # freq = self.DDS_freq_list[i]
        # amp = self.DDS_amp_list[i]
        # att = self.DDS_att_list[i]
        # sw = self.DDS_sw_list[i]
        #
        # print(channel, freq, amp, att, sw)

            # if not sw:
            #     channel.sw.off()
            #
            # delay_mu(41000)
            # channel.set_att(att)
            # delay_mu(4000)
            #
            # delay_mu(95000)
            # channel.set(freq, amplitude=amp)
            # delay_mu(6000)
            #
            # delay_mu(10000)
            #
            # if sw:
            #     channel.sw.on()

    def run(self):
        """
        Run certain functions on the computer instead of the core device.
        """

        t_now = time.time()     # Save the current time

        self.kernel_run()     # Run the rest of the program on the core device

        print("Actual time taken = {:.2f} seconds" .format(time.time() - t_now))        # Calculate how long the experiment took

    @kernel
    def kernel_run(self):

        self.core.reset()
        self.core.break_realtime()  # Increases slack to at least 125 us
        self.init()

        # Pre-load all the pulse sequences using DMA
        self.prerecord_cooling_loop()

        delay_mu(100000)
        self.core.break_realtime()

        fast_loop_cooling_handle = self.core_dma.get_handle("cooling_loop_pulses")

        self.core.break_realtime()
        delay_mu(1000000)

        for i in range(self.loops_to_run):
            # self.ttl0.on()      # This is the trigger pulse for the PicoHarp
            # delay_mu(100)
            # self.ttl0.off()
            delay_mu(100000)

            self.core_dma.playback_handle(fast_loop_cooling_handle)
            self.core.break_realtime()

        i = 1
        delay_mu(10000)
        # name = self.DDS_name_list[i]
        channel = self.DDS_device_list[i]
        # freq = self.globals__DDS__532__tone_1__switch

        freq = self.globals__DDS__493__Alice__sigma_1__frequency
        amp = self.globals__DDS__493__Alice__sigma_1__amplitude
        att = self.globals__DDS__493__Alice__sigma_1__attenuation
        sw = self.globals__DDS__493__Alice__sigma_1__switch

        print(channel, freq, amp, att, sw)

    @kernel
    def init(self):
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
        self.entangler.init()
        # This writes an output-high time to all the channels
        for channel in range(num_outputs):
            self.entangler.set_timing_mu(channel, out_start, out_stop)

        # Then we overwrite the channels where we have different timings
        if pump_650_sigma == 1:                                # If we pump with sigma1, generate photons with sigma2
            self.entangler.set_timing_mu(5, out_start2, out_stop2)   # Turn on 650sigma2 slow-aom
            self.entangler.set_timing_mu(6, out_start3, out_stop3)   # Turn on 650fast-pulse
        else:
            self.entangler.set_timing_mu(4, out_start2, out_stop2)   # Turn on 650sigma1 slow-aom
            self.entangler.set_timing_mu(6, out_start3, out_stop3)   # Turn on 650fast-pulse
        # self.entangler.set_timing_mu(7, 10000, 10000)   # ttl7 unused, disable output

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

        This is faster than non pre-recorded
        """
        with self.core_dma.record("cooling_loop_pulses"):
            # Cool
            self.ttl0.pulse(100 * ns)      # This is the trigger pulse for the PicoHarp
            self.ttl_test.pulse(100 * ns)
            delay_mu(5000)

            with parallel:
                self.ttl_650_pi.on()
                self.ttl_493_all.on()
                self.DDS__493__Bob__sigma_1.sw.on()
                self.DDS__493__Bob__sigma_2.sw.on()
                self.ttl_650_fast_cw.on()
                self.ttl_650_sigma_1.on()
                self.ttl_650_sigma_2.on()
                self.ttl_test.on()  # This channel for diagnostics

                # delay(1000 * us)
                delay(self.cooling_time)

            with parallel:
                self.ttl_650_pi.off()
                self.ttl_493_all.off()
                self.DDS__493__Bob__sigma_1.sw.off()
                self.DDS__493__Bob__sigma_2.sw.off()
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
            self.DDS__493__Bob__sigma_1.sw.pulse(self.detection_time)
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
            self.DDS__493__Bob__sigma_2.sw.pulse(self.detection_time)
            with sequential:    # Generate fake pulse sequence for triggering the counter
                for i in range(13):
                    self.ttl_650_pi.pulse(1 * us)
                    delay(1 * us)

        Bob_counts = self.Bob_camera_side_APD.count(gate_end_mu_B2)

        return Bob_counts

