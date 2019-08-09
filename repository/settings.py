# TODO: settings only updates, while another startup class initializes (to prevent DDS glitching on trap RF)
"""
This program gives access to all the global variables for the IonPhoton experiment.
It also sets up all the hardware in a default state.  This program can be run to change any of the base settings.
This should be run once at the beginning of operations to set up the appropriate DDS frequencies and TTL states.
It should be used as the startup kernel (untested).
Other experiments should subclass base_experiment, not this file.

M. Lichtman 2019-08-02
"""

import traceback

from artiq.language.core import kernel, delay, delay_mu
from artiq.language.units import s, ms, us, ns, MHz
import base_experiment


class settings(base_experiment.base_experiment):

    def build(self):

        self.load_globals_from_dataset()
        self.build_globals_arguments()
        self.build_common()
        print('settings.py build() done')

    @kernel
    def DDS_setup(self, i):
        """
        Sets up one DDS channel based on passed in info
        :param i:  The index for the matching lists of DDS info created during build().
        :return:
        """

        # name = self.DDS_name_list[i]
        channel = self.DDS_device_list[i]
        freq = self.DDS_freq_list[i]
        amp = self.DDS_amp_list[i]
        att = self.DDS_att_list[i]
        sw = self.DDS_sw_list[i]

        # setup the channel
        #channel.init()

        if not sw:
            channel.sw.off()

        delay(10*us)
        channel.set_att(att)
        delay(10*us)
        channel.set(freq, amplitude=amp)
        delay(10*us)

        if sw:
            channel.sw.on()

    def run(self):
        """This run method is used as the startup kernel.  It should be run whenever settings are changed. Otherwise,
        all other experiments overwrite it without calling super(). and so these commands are not repeated every
        experiment."""

        # self.set_dataset('counter_channels', self.counter_channel_names, persist=True, broadcast=True)

        # To make it easy to run through all the DDS and turn them on, create a list of the default parameters

        self.DDS_freq_list = [getattr(self, 'globals__DDS__' + name + '__frequency') for name in self.DDS_name_list]
        self.DDS_amp_list = [getattr(self, 'globals__DDS__' + name + '__amplitude') for name in self.DDS_name_list]
        self.DDS_att_list = [getattr(self, 'globals__DDS__' + name + '__attenuation') for name in self.DDS_name_list]
        self.DDS_sw_list = [getattr(self, 'globals__DDS__' + name + '__switch') for name in self.DDS_name_list]

        self.kernel_run()


    @kernel
    def kernel_run(self):

        self.core.reset()

        # DDS channels #

        #self.urukul0_cpld.init()
        #self.urukul1_cpld.init()
        #self.urukul2_cpld.init()

        for i in range(len(self.DDS_device_list)):
            self.DDS_setup(i)
