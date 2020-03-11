"""
This program gives access to all the global variables for the IonPhoton experiment.
It also sets up all the hardware in a default state.  This program can be run to change any of the base settings.
At the beginning of operations, run startup.py followed by settings.py.  After that, only use settings.py

M. Lichtman 2019-08-15
"""

import base_experiment


class settings(base_experiment.base_experiment):

    def build(self):
        print("settings build Hello1")
        self.load_globals_from_dataset()  # This now does nothing
        print("settings build Hello2")
        self.build_globals_arguments()      # Generates the values to be listed in the GUI
        print("settings build Hello3")
        self.build_common()                 # Builds lists from default settings hardcoded in base_experiment
        print('settings build Hello2.5')


        print('{}.build() done'.format(self.__class__))

    def run(self):
        # Here we override run(), not run_worker() as usual, to avoid calling write_globals_to_datasets() twice.
        self.setup()            # Error is in here
        print("Hello4")
        self.write_globals_to_datasets(archive=True)
        print("Hello5")