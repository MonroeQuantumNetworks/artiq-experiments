""" This is a scan example program.
    Use the code segments in here to create a real program with scannable objects
"""

from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment


class scantest(base_experiment.base_experiment):

    def build(self):
        super().build()
        self.setattr_argument('cooling_time_scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time_scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time_scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        print('scantest.py build() done')

    def run(self):

        try:  # catch TerminationRequested

            # setup the scans to only scan the active variables
            self.scans = [  # name the different scan types
                ("cooling_time", self.cooling_time_scan),
                ("pumping_time", self.pumping_time_scan),
                ("detection_time", self.detection_time_scan)
            ]
            self.active_scans = []
            self.active_scan_names = []
            for name, scan in self.scans:
                if isinstance(scan, NoScan):
                    # just set the single value
                    setattr(self, name, scan.value)
                    print('No Scan Needed for', name)
                else:
                    print('Something to scan on', name)
                    self.active_scans.append((name, scan))
                    self.active_scan_names.append(name)
            # Create datasets for each scan?
            self.set_dataset('active_scan_names', [bytes(i, 'utf-8') for i in self.active_scan_names], broadcast=True, archive=True, persist=True)
            self.set_dataset('dummy_data_x', [], broadcast=True, archive=True)
            self.set_dataset('dummy_data_y', [], broadcast=True, archive=True)

            # Combine the scan variables into a multiscan
            print('Multi-scan run:')
            counter = 1     # Added this to count the number of scans
            msm = MultiScanManager(*self.active_scans)
            for point in msm:
                print(counter, ["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])
                self.append_to_dataset('dummy_data_x', getattr(point, name))   # Create dummy dataset for practice
                self.append_to_dataset('dummy_data_y', bytes(name, 'utf-8'))  # Create dummy dataset for practice

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                # print(self.active_scan_names)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))
                    # print('This is getattr', name, getattr(self, name))

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

                counter = counter+1

                # Insert code to run experiment with scanned variables here

        except TerminationRequested:
            print('Terminated gracefully')
