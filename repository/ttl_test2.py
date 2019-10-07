from artiq.language.core import kernel, delay, now_mu
from artiq.experiment import TerminationRequested
from artiq.language.units import s, ms, us, ns, MHz
import base_experiment


class ttl_test2(base_experiment.base_experiment):

    def build(self):
        super().build()

    @kernel
    def run(self):

        self.core.break_realtime()
        try:  # catch TerminationRequested
            num = 0
            while True:
                self.ttl14.pulse(200*ns)
                #self.ttl8.pulse(200*ns)
                delay(1*us)
                num +=1
                print(num)
                self.core.break_realtime()
        except TerminationRequested:
            print('Terminated gracefully')
