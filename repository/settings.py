"""
This program gives access to all the global variables for the IonPhoton experiment.
It also sets up all the hardware in a default state.  This program can be run to change any of the base settings.
At the beginning of operations, run startup.py followed by settings.py.  After that, only use settings.py

M. Lichtman 2019-08-15
"""

import base_experiment

class settings(base_experiment.base_experiment):

    def build(self):

        self.load_globals_from_dataset()
        self.build_globals_arguments()
        self.build_common()
        print('settings.py build() done')

    def run(self):
        self.setup()
