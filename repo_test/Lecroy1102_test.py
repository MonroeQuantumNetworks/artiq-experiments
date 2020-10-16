from artiq.experiment import *  # TODO: can we import rtio_log without import * ?

import numpy as np
import base_experiment
from Lecroy1102 import Lecroy1102

class Lecroy1102_test(base_experiment.base_experiment):

    def run(self):

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
            t = np.arange(0, 5*us, awg.sample_length)
            print('length t:', len(t))
            waveform1 = np.sin(2*np.pi*106.9*MHz*t) + np.sin(2*np.pi*113.3*MHz*t)
            waveform2 = np.sin(2*np.pi*85*MHz*t)
            awg.program(waveform1, waveform2)
            self.set_dataset('waveforms', np.array([q for q in zip(waveform1, waveform2)]), broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform1', waveform1, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform2', waveform2, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_names', [bytes(i, 'utf-8') for i in ['channel 1', 'channel 2']], broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_t', t, broadcast=True, persist=True, archive=True)
            self.set_dataset('waveform_x_names', [bytes(i, 'utf-8') for i in ['time']], broadcast=True, persist=True, archive=True)
        finally:
            awg.close()

        self.kernel_run()

        print('end')

    @kernel
    def kernel_run(self):
        self.core.reset()
        for i in range(1000000):
            delay(1 * ms)
            with parallel:
                self.ttl14.pulse(1*ms)  # AWG trigger
                self.ttl9.pulse(1*ms)  # scope trigger
            delay(1*ms)

