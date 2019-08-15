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

    @kernel
    def startup_kernel(self):

        self.core.reset()

        # DDS channels #

        self.urukul0_cpld.init()
        self.urukul1_cpld.init()
        self.urukul2_cpld.init()
