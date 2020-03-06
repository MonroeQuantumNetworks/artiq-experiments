from artiq.experiment import *
import numpy as np
import base_experiment
from Lecroy1102 import Lecroy1102

class Remote_Entanglement_Experiment_Sample(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_device("core_dma")
        self.setattr_argument('trials_per_point', NumberValue(500, min=0, ndecimals=1))
        self.setattr_argument('trials_per_point', NumberValue(10000, min=0, ndecimals=0))
        self.setattr_argument('cooling_time', NumberValue(5e-6, unit='us', min=0 * us, ndecimals=3))
        self.setattr_argument('pumping_time', NumberValue(3e-6, unit='us', min=0 * us, ndecimals=3))
        self.setattr_argument('raman_time', NumberValue(2e-6, unit='us', min=0*us, ndecimals=3))
        self.setattr_argument('single_photon_time', NumberValue(3e-8, unit='ns', min=0*ns, ndecimals = 0))
        self.setattr_argument('detection_time', NumberValue(1e-6, unit='us', min=0*us, ndecimals=3))

    @kernel
    def fast_loop(self):
        with self.core_dma.record("fast_loop_pulses"):
            # Cool
            with parallel:
                self.DDS__650__sigma_1.sw.on()
                self.DDS__650__sigma_2.sw.on()
            delay_mu(8)
            with parallel:
                self.DDS__493__Alice__sigma_1.sw.on()
                self.DDS__493__Alice__sigma_2.sw.on()
                self.DDS__493__Bob__sigma_1.sw.on()
                self.DDS__493__Bob__sigma_2.sw.on()
                self.DDS__650__Alice__pi.sw.on()
                self.DDS__650__Bob__pi.sw.on()
                self.ttl11.on()
            delay(self.cooling_time)


            # Pump to D manifold edge state
            self.DDS__650__sigma_2.sw.off()
            delay(self.pumping_time)

            with parallel:
                self.DDS__493__Alice__sigma_1.sw.off()
                self.DDS__493__Alice__sigma_2.sw.off()
                self.DDS__493__Bob__sigma_1.sw.off()
                self.DDS__493__Bob__sigma_2.sw.off()
                self.DDS__650__Alice__pi.sw.off()
                self.DDS__650__Bob__pi.sw.off()
                self.DDS__650__sigma_1.sw.off()
                self.ttl11.off()

            # Wait for AOMs to turn off all the way
            delay_mu(200)


            # Fast 650 nm excitation
            self.DDS__650__sigma_2.sw.on()      # Prepare by turning on slow AOM
            delay_mu(100)
            self.ttl8.pulse(100*ns)

            # Look for single photons
            t0 = now_mu()
            with parallel:
                gate_end_mu_detector0 = self.HOM0.gate_rising(self.single_photon_time)
                gate_end_mu_detector1 = self.HOM1.gate_rising(self.single_photon_time)
                gate_end_mu_detector2 = self.HOM2.gate_rising(self.single_photon_time)
                gate_end_mu_detector3 = self.HOM3.gate_rising(self.single_photon_time)

        return gate_end_mu_detector0, gate_end_mu_detector1, gate_end_mu_detector2, gate_end_mu_detector3

    @kernel
    def slow_loop_detect_sigma_1(self):
        with self.core_dma.record("slow_loop_detect_sigma_1_pulses"):
            # Raman
            self.ttl14.pulse(5*us) # Trigger AWG to put out Raman for both traps

            # Detection
            t1 = now_mu()
            with parallel:
                gate_end_mu_A1 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                gate_end_mu_B1 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
            at_mu(t1)

            with parallel:
                self.DDS__493__Alice__sigma_1.sw.pulse(self.detection_time)
                self.DDS__493__Bob__sigma_1.sw.pulse(self.detection_time)
                self.DDS__650__Alice__pi.sw.pulse(self.detection_time)
                self.DDS__650__Bob__pi.sw.pulse(self.detection_time)
                self.ttl11.pulse(self.detection_time)
                self.DDS__650__sigma_1.sw.pulse(self.detection_time)
                self_DDS__650__sigma_2.sw.pulse(self.detection_time)

            return gate_end_mu_A1, gate_end_mu_B1

    @kernel
    def slow_loop_detect_sigma_2(self):
        with self.core_dma.record("slow_loop_detect_sigma_2_pulses"):
            # Raman
            self.ttl14.pulse(5 * us)  # Trigger AWG to put out Raman for both traps

            # Detection
            t1 = now_mu()
            with parallel:
                gate_end_mu_A2 = self.Alice_camera_side_APD.gate_rising(self.detection_time)
                gate_end_mu_B2 = self.Bob_camera_side_APD.gate_rising(self.detection_time)
            at_mu(t1)

            with parallel:
                self.DDS__493__Alice__sigma_2.sw.pulse(self.detection_time)
                self.DDS__493__Bob__sigma_2.sw.pulse(self.detection_time)
                self.DDS__650__Alice__pi.sw.pulse(self.detection_time)
                self.DDS__650__Bob__pi.sw.pulse(self.detection_time)
                self.ttl11.pulse(self.detection_time)
                self.DDS__650__sigma_1.sw.pulse(self.detection_time)
                self_DDS__650__sigma_2.sw.pulse(self.detection_time)

            return gate_end_mu_A2, gate_end_mu_B2

    def run(self):
        # Define AWG information
        IP_address = '192.168.1.100'  # server is running on JARVIS
        port = 11000
        sample_rate = 250 * MHz
        ext_clock_frequency = 10 * MHz

        self.set_dataset('Alice_sum_1', [], broadcast=True, archive=True)
        self.set_dataset('Bob_sum_1', [], broadcast=True, archive=True)
        self.set_dataset('Alice_sum_2', [], broadcast=True, archive=True)
        self.set_dataset('Bob_sum_2', [], broadcast=True, archive=True)
        self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['Alice_sum_1', 'Bob_sum_1', 'Alice_sum_2', 'Bob_sum_2']],
                         broadcast=True, archive=True, persist=True)

        # Program AWG
        try:
            awg = Lecroy1102(IP_address, port, sample_rate, ext_clock_frequency)
            awg.open()
            if not awg.enabled:
                return
            t = np.arange(0, 20 * us, awg.sample_length)
            waveform1 = 0.115 * (np.sin(2 * np.pi * 106.9 * MHz * t) + np.sin(2 * np.pi * 113.2 * MHz * t))
            waveform2 = np.sin(2 * np.pi * 85 * MHz * t)
            awg.program(waveform1, waveform2)
        finally:
            awg.close()

        try:
            self.kernel_run()
        except TerminationRequested:
            print('Terminated gracefully')

    @kernel
    def kernel_run(self):
        self.core.reset()

        gate_end_mu_detector0, gate_end_mu_detector1, gate_end_mu_detector2, gate_end_mu_detector3 = self.fast_loop()
        self.core.reset()
        gate_end_mu_A1, gate_end_mu_B1 = self.slow_loop_detect_sigma_1()
        self.core.reset()
        gate_end_mu_A2, gate_end_mu_B2 = self.slow_loop_detect_sigma_2()

        fast_loop_pulses_handle = self.core_dma.get_handle("fast_loop_pulses")
        slow_loop_sigma_1_pulses_handle = self.core_dma.get_handle("slow_loop_sigma_1_pulses")
        slow_loop_sigma_2_pulses_handle = self.core_dma.get_handle("slow_loop_sigma_2_pulses")
        self.core.reset()

        while points <= self.points:
            sumA1 = 0
            sumA2 = 0
            sumB1 = 0
            sumB2 = 0
            trials = 0
            while trials <= self.trials_per_point:
                delay_mu(2000)
                self.core_dma.playback(fast_loop_pulses_handle)
                with parallel:
                    counts0 = self.HOM0.count(gate_end_mu_detector0)
                    counts1 = self.HOM1.count(gate_end_mu_detector1)
                    counts2 = self.HOM2.count(gate_end_mu_detector2)
                    counts3 = self.HOM3.count(gate_end_mu_detector3)
                if (counts0> 0 and counts1 > 0) or (counts0 > 0 and counts2 > 0) or (counts1 > 0 and counts3 > 0) or (counts2 > 0 and counts3 > 0):
                    self.core.reset()
                    delay_mu(2000)
                    self.core_dma.playback(slow_loop_sigma_1_pulses_handle)
                    Alice_counts_detect1 = self.Alice_camera_side_APD.count(gate_end_mu_A1)
                    Bob_counts_detect1 = self.Bob_camera_side_APD.count(gate_end_mu_B1)
                    sumA1 += Alice_counts_detect1
                    sumB1 += Bob_counts_detect1


                trials += 1

                delay_mu(2000)
                self.core_dma.playback(fast_loop_pulses_handle)
                with parallel:
                    counts0 = self.HOM0.count(gate_end_mu_detector0)
                    counts1 = self.HOM1.count(gate_end_mu_detector1)
                    counts2 = self.HOM2.count(gate_end_mu_detector2)
                    counts3 = self.HOM3.count(gate_end_mu_detector3)
                if (counts0 > 0 and counts1 > 0) or (counts0 > 0 and counts2 > 0) or (counts1 > 0 and counts3 > 0) or (counts2 > 0 and counts3 > 0):
                    self.core.reset()
                    delay_mu(2000)
                    self.core_dma.playback(slow_loop_sigma_2_pulses_handle)
                    Alice_counts_detect2 = self.Alice_camera_side_APD.count(gate_end_mu_A2)
                    Bob_counts_detect2 = self.Bob_camera_side_APD.count(gate_end_mu_B2)
                    sumA1 += Alice_counts_detect2
                    sumB1 += Bob_counts_detect2
                trials += 1

            self.append_to_dataset('Alice_sum_1', sumA1)
            self.append_to_dataset('Bob_sum_1', sumB1)
            self.append_to_dataset('Alice_sum_2', sumA2)
            self.append_to_dataset('Bob_sum_2', sumB2)
            points += 1



