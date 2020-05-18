"""Generate fake data on the applet and fit

This script runs on the Host device only (No kernel)
Generate sine data and plot point by point
It should plot data live as it updates as a line
    then fit the data and plot fit (line) and data (dots)

George Toh 2020-04-23
"""
from artiq.experiment import *
import base_experiment
from artiq.language.core import delay
import artiq.language.units as aq_units

import time
import numpy as np
# import matplotlib.pyplot as plt
from scipy import optimize
import logging      # How to use this?

class plotfit_applet_test(base_experiment.base_experiment):
    '''Plot and Fit applet test'''
    def build(self):
        super().build()
        self.setattr_device("ccb")
        # Fake data to be generated
        self.setattr_argument('points_to_plot', NumberValue(200, ndecimals=0, min=1, step=10))
        self.setattr_argument('sine_amp', NumberValue(1, ndecimals=1, min=0.1, step=0.1))
        self.setattr_argument('sine_lambda', NumberValue(10, ndecimals=0, min=10, step=10))
        self.setattr_argument('sine_phase', NumberValue(0, ndecimals=1, min=0, step=0.1))

        # Initial parameters for fit
        self.setattr_argument('fit_amp', NumberValue(1, ndecimals=1, min=0.1, step=0.1))
        self.setattr_argument('fit_lambda', NumberValue(10, ndecimals=0, min=10, step=10))
        self.setattr_argument('fit_phase', NumberValue(0, ndecimals=1, min=0, step=0.1))


        self.scan_names = ['cooling_time', 'pumping_time', 'detection_time']
        self.setattr_argument('cooling_time__scan', Scannable(default=[NoScan(self.globals__timing__cooling_time), RangeScan(0*us, 3*self.globals__timing__cooling_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('pumping_time__scan', Scannable(default=[NoScan(self.globals__timing__pumping_time), RangeScan(0*us, 3*self.globals__timing__pumping_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))
        self.setattr_argument('detection_time__scan', Scannable( default=[NoScan(self.globals__timing__detection_time), RangeScan(0*us, 3*self.globals__timing__detection_time, 100) ], global_min=0*us, global_step=1*us, unit='us', ndecimals=3))

    def run(self):

        self.experiment_specific_preamble()

        try:  # catch TerminationRequested

            # setup the scans to only scan the active variables
            self.scans = [(name, getattr(self, name+'__scan')) for name in self.scan_names]
            self.active_scans = []
            self.active_scan_names = []
            for name, scan in self.scans:
                if isinstance(scan, NoScan):
                    # just set the single value
                    setattr(self, name, scan.value)
                else:
                    self.active_scans.append((name, scan))
                    self.active_scan_names.append(name)
            self.set_dataset('active_scan_names', [bytes(i, 'utf-8') for i in self.active_scan_names], broadcast=True, archive=True, persist=True)
            msm = MultiScanManager(*self.active_scans)

            # assume a 1D scan for plotting
            self.set_dataset('scan_x', [], broadcast=True, archive=True)

            for point in msm:

                #print(["{} {}".format(name, getattr(point, name)) for name in self.active_scan_names])

                # update the instance variables (e.g. self.cooling_time=point.cooling_time)
                for name in self.active_scan_names:
                    setattr(self, name, getattr(point, name))

                # update the plot x-axis ticks
                # self.append_to_dataset('scan_x', getattr(point, self.active_scan_names[0]))

                self.experiment_specific_run()

                # allow other experiments to preempt
                self.core.comm.close()
                self.scheduler.pause()

        except TerminationRequested:
            print('Terminated gracefully')


    def experiment_specific_preamble(self):

        # Create datasets to hold data for plotting
        self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        self.set_dataset('xdataset', np.arange(self.points_to_plot), broadcast=True, archive=True)
        self.set_dataset('ydataset2', np.zeros(self.points_to_plot), broadcast=True, archive=True)

        self.set_dataset('xfitdataset', np.arange(self.points_to_plot), broadcast=True, archive=True)
        self.set_dataset('yfitdataset', np.zeros(self.points_to_plot), broadcast=True, archive=True)
        self.set_dataset('yfitdataset2', np.zeros(self.points_to_plot), broadcast=True, archive=True)
        # self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['xdata', 'ydata', 'detect1', 'detect2']], broadcast=True, archive=True, persist=True)


        # self.set_variables(
        # data_folder=self.data_folder,
        # applet_name=self.applet_name,
        # applet_group=self.applet_group,
        # ylabel=self.ylabel,
        # xlabel=self.xlabel,
        # )    

        # These are from Euriqa basic_environment.py

        # def set_variables(
        #     self,
        #     data_folder: str = _DATA_FOLDER,
        #     applet_name: str = _APPLET_NAME,
        #     applet_group: str = _APPLET_GROUP_NAME,
        #     fit_type=_FIT_TYPE,
        #     units=_UNITS,
        #     xlabel: str = _XLABEL,
        #     ylabel: str = _YLABEL,
        # ):
        #     """Set data output destinations.
        #     Should be called from prepare() of the child class.
        #     """
        #     self._DATA_FOLDER = data_folder
        #     self._APPLET_NAME = applet_name
        #     self._APPLET_GROUP_NAME = applet_group
        #     self._FIT_TYPE = fit_type
        #     self._UNITS = units
        #     self._XLABEL = xlabel
        #     self._YLABEL = ylabel
        
        # def set_experiment_data(self, dataset_name: str, value: typing.Any, **kwargs ) -> None:
        #     """Simplify saving datasets to this experiment."""
        #     self.set_dataset(self._exp_dataset_path(dataset_name), value, **kwargs)

        # def _exp_dataset_path(self, dataset_name: str) -> str:
        #     """Return the string-path where an experiment dataset is stored."""
        #     return self._experiment_dataset_name_format.format(exp_name=self._DATA_FOLDER, dataset_name=dataset_name)

        # self.set_experiment_data(
        # "avg_parity", np.full((1, self.num_steps), np.nan), broadcast=True
        # )
        # self.set_experiment_data(
        #     "parity_error_bars", np.full((1, self.num_steps), np.nan), broadcast=True
        # )

        # self.set_experiment_data(
        #     "dummy_active_pmts", np.asarray([1]), persist=False, broadcast=True
        # )

        ylabel = "Signal"
        xlabel = "Datapoints"

        applet_stream_cmd = "$python -m applets.plot_multi" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Plot_Fit_Test",
            command=applet_stream_cmd
            + " --x " + "xdataset"
            + " --y-names " + "ydataset ydataset2"  # The code requires >1 datasets to be submitted here
            + " --x-fit " + "xfitdataset"
            + " --y-fits " + "yfitdataset yfitdataset2"
            + " --y-label "
            + "'"
            + ylabel
            + "'"
            + " --x-label "
            + "'"
            + xlabel
            + "'"
            # + " --active-pmts "
            # + self._exp_dataset_path("dummy_active_pmts")
            # + " --error-bars-bottom "
            # + self._exp_dataset_path("parity_error_bars")
            # + " --error-bars-top "
            # + self._exp_dataset_path("parity_error_bars"),
            # group=self.applet_group,
        )


    def experiment_specific_run(self):

        # Generate fake data
        for t in range(self.points_to_plot):
            ydata = self.sine_amp * np.sin( 2 * np.pi / self.sine_lambda * t)
            xdata = t

            # self.mutate_dataset(key, index, value)
            # updates the dataset value at given index to value
            self.mutate_dataset('xdataset', t, xdata)
            self.mutate_dataset('ydataset', t, ydata)
            self.mutate_dataset('ydataset2', t, ydata*0.7)


            ratios = np.array([xdata, ydata, 0, 0])
            self.append_to_dataset('ratio_list', ratios)

            time.sleep(0.1)

        def sinecurve(t, amp, lambda1, phase):
            return amp * np.sin(2 * np.pi / lambda1 * t + phase)

        # Once done generating fake data, time to fit

        params = (self.fit_amp, self.fit_lambda, self.fit_phase)    # Initial parameters
        results, cov = optimize.curve_fit(sinecurve, self.get_dataset('xdataset'), self.get_dataset('ydataset'), p0=params)   # Do the fit
        print('Init params: ', params)
        print('Fit results: ', results)

        xfit = np.arange(1,self.points_to_plot,1)
        yfit = sinecurve(xfit, *results)   # The * passes multiple arguments to the function

        params = (self.fit_amp, self.fit_lambda, self.fit_phase)    # Initial parameters
        results, cov = optimize.curve_fit(sinecurve, self.get_dataset('xdataset'), self.get_dataset('ydataset2'), p0=params)   # Do the fit
        yfit2 = sinecurve(xfit, *results)   # The * passes multiple arguments to the function

        self.mutate_dataset('xfitdataset', xfit, xfit)  # This loads the whole fit at once instead of term by term
        self.mutate_dataset('yfitdataset', xfit, yfit)  
        self.mutate_dataset('yfitdataset2', xfit, yfit2)  
   
