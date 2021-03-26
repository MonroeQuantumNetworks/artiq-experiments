"""
Curve fitting tool for D-state pumping data


George Toh 2020-3-24
"""
from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
import base_experiment
import os
import time

from AWGmessenger import sendmessage   # Other file in the repo, contains code for messaging Jarvis

class Curvefit_Tool_Dstate(base_experiment.base_experiment):

    kernel_invariants = {
        "detection_time",
        "cooling_time",
        "pumping_time",
        "delay_time",
        "raman_time",
    }

    def build(self):
        super().build()
        self.setattr_device("ccb")
        self.setattr_device("core_dma")

        self.setattr_argument('Instructions', EnumerationValue(["Choose which data set to fit to and set the fit parameters", "after fit is done, open applet Fit_results"]))
        self.setattr_argument('do_curvefit', BooleanValue(True))
        self.setattr_argument('Data_to_fit', EnumerationValue(["D-32", "D+32"], default="D-32"))

        self.setattr_argument('fit_points', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('fitparam_amp', NumberValue(1, ndecimals=0, min=1, step=0.1, max=4))
        # self.setattr_argument('fitparam_phase', NumberValue(0, ndecimals=0, min=-4, step=0.2, max=4))
        self.setattr_argument('fitparam_decaytime', NumberValue(5*us, ndecimals=0, min=1*us, step=5*us, max=1000*us, unit='us'))
        # self.setattr_argument('fitparam_decayt', NumberValue(100*us, ndecimals=0, min=1*us, step=10*us, max=1000*us, unit='us'))

    def run(self):

        # self.set_dataset('Ba_detection_names', [bytes(i, 'utf-8') for i in ['detect11', 'detect12', 'detect21', 'detect22']], broadcast=True, archive=True, persist=True)
        # self.set_dataset('ratio_list', [], broadcast=True, archive=True)
        #
        # self.set_dataset('runid', self.scheduler.rid, broadcast=True, archive=False)     # This is for display of RUNID on the figure

        # This creates a applet shortcut in the Artiq applet list
        ylabel = "Counts"
        xlabel = "Scanned variable"
        applet_stream_cmd = "$python -m applets.plot_multi_old" + " "   # White space is required
        self.ccb.issue(
            "create_applet",
            name="Fit_results",
            command=applet_stream_cmd
            + " --x " + "scan_x"        # Defined below in the msm handling, assumes 1-D scan
            + " --y-names " + "data"
            + " --x-fit " + "xfitdataset"
            + " --y-fits " + "yfitdataset"
            + " --rid " + "runid"            
            + " --y-label "
            + "'"
            + ylabel
            + "'"
            + " --x-label "
            + "'"
            + xlabel
            + "'"
        )

        # Also, turn on Ba_ratios 

        try:
            # Do curve fitting in this function
            if self.do_curvefit == True:
                self.fit_data()

        except TerminationRequested:
            print('Terminated gracefully')


        # These are necessary to restore the system to the state before the experiment.
        # Un-necessary since we do nothing in this script
        # self.load_globals_from_dataset()    # This loads global settings from datasets
        # self.setup()        # This sends settings out to the ARTIQ hardware


    def fit_data(self):
        """ Do curve fitting of data and display on graph here"""

        import numpy as np
        from scipy import optimize

        def exp_decay(x, amp, decayt):
            return amp * np.exp(-x / decayt)

        scanx = self.get_dataset('scan_x')

        # Change this to the dataset you want to fit
        data = self.get_dataset('ratio_list')
        data = np.array(data)
        if self.Data_to_fit == "D-32":
            datatofit = 1-data[:,0]
        else:
            datatofit = 1-data[:,3]


        datatofit = np.ascontiguousarray(datatofit)

        initialparams = [self.fitparam_amp, self.fitparam_decaytime]
        fitbounds = ([0,0],[10, 1000e-6])

        results1, covariances = optimize.curve_fit(exp_decay, scanx, datatofit, p0=initialparams, bounds = fitbounds)
        print('Fit results: ', results1)

        fittedx = np.linspace(0,max(scanx),self.fit_points)
        fitresult1 = exp_decay(fittedx, *results1)

        self.set_dataset('xfitdataset', fittedx, broadcast=True)
        self.set_dataset('yfitdataset', fitresult1, broadcast=True)

        self.set_dataset('data', datatofit, broadcast=True)

        # print("Amplitude: {:0.2f}".format(results1[0]), " ")
        print("Decay time (98%): {:0.2f}".format(results1[1]*4e6), " us")

