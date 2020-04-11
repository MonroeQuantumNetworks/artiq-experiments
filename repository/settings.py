"""
 Run this program to change/update any of the base settings.
This program gives access to all the global variables for the IonPhoton experiment.
It also sets up all the hardware in a default state. 
At the beginning of operations, run startup.py followed by settings.py.  After that, only use settings.py

M. Lichtman 2019-08-15

Updated.

George Toh 2020-04-11
"""

import base_experiment


class settings(base_experiment.base_experiment):
    """Settings 

    Run this to change or update default globals values 
    """

    def build(self):
        self.load_globals_from_dataset()    # This is hardcoded to obtain values from the globals
        self.build_globals_arguments()      # Generates the entries to be listed in the GUI
        self.build_common()                 # Builds lists from default settings hardcoded in base_experiment

        print('{}.build() done'.format(self.__class__))

    def run(self):
        # Here we override run(), not run_worker() as usual, to avoid calling write_globals_to_datasets() twice.
        self.setup()            
        self.write_globals_to_datasets(archive=True)