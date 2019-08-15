"""
This program updates the default values stored in the datasets, but does not set the settings.  It is used
to change settings while the idle_counters are running, since the idle counters will call the base_experiment.setup()
method again anyway.

M. Lichtman 2019-08-15
"""

import base_experiment


class idle_settings(base_experiment.base_experiment):

    def build(self):

        self.load_globals_from_dataset()
        self.build_globals_arguments()
        self.build_common()
        print('settings.py build() done')

