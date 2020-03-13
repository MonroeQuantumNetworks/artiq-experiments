"""
This program starts up the hardware using the values saved in the datasets.
It initializes hardware and then calls the run method of it's parent class: settings.py.
It does not present GUI arguments.
This should be run once at the beginning of operations to set up the appropriate DDS frequencies and TTL states.
After that, do not use this because it takes longer and causes the DDSs to glitch, just run settings.py directly.
Settings.py will not glitch the DDS.
This file should be used as the startup kernel (untested).
Other experiments should subclass base_experiment, not this file.

M. Lichtman 2019-08-02

Because of how I changed load_globals_from_dataset, may need to revisit the ordering of calls in startup.build()
George Toh 2020-03-11
"""

from artiq.language.core import kernel
import settings


class startup(settings.settings):

    def build(self):
        # This appears the same as base_experiment.build(), but we write it again to override settings.build()
        self.load_globals_from_dataset()
        self.build_common()
        print('startup.py build() done')

    def run(self):
        # Overrides settings.run(), not base_experiment.run()
        self.startup_kernel()
        super().run()
        print("STARTUP super run done")

    @kernel
    def startup_kernel(self):

        self.core.reset()

        # DDS #

        for i in range(len(self.urukul_cplds)):
            self.urukul_cplds[i].init()
        for channel in self.DDS_device_list:
            channel.init()

        # DAC #

        self.zotino0.init()

