""" Modified to do Raman using the Keysight AWG
Bob Barium detection, with scannable variables, DMA detection
Turn on Ba_ratios and Detection_Counts APPLETS to plot the figures
Fixed AOM amplitude scanning and update
Also does curve fitting at the very end (Fit to Raman time scan)

Uses Keysight AWG to drive Raman lasers

Known issues:


George Toh 2020-12-18
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

class Curvefit_Tool(base_experiment.base_experiment):

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
        self.setattr_argument('Data_to_fit', EnumerationValue(["detect11", "detect12", "detect21", "detect22"], default="detect12"))

        self.setattr_argument('fit_points', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('fitparam_amp', NumberValue(1, ndecimals=0, min=1, step=0.1, max=4))
        self.setattr_argument('fitparam_phase', NumberValue(0, ndecimals=0, min=-4, step=0.2, max=4))
        self.setattr_argument('fitparam_pitime', NumberValue(5*us, ndecimals=0, min=1*us, step=5*us, max=1000*us, unit='us'))
        self.setattr_argument('fitparam_decayt', NumberValue(100*us, ndecimals=0, min=1*us, step=10*us, max=1000*us, unit='us'))

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
            + " --y-fits " + "yfitdataset21"
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

            # self.set_dataset('scan_x', [], broadcast=True, archive=True)
            # self.set_dataset('sum11', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum12', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum21', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('sum22', np.zeros(point_num), broadcast=True, archive=True)
            #
            # self.set_dataset('ratio21', np.zeros(point_num), broadcast=True, archive=True)
            # self.set_dataset('ratio22', np.zeros(point_num), broadcast=True, archive=True)

            self.set_dataset('data', [], broadcast=True, archive=True)
            self.set_dataset('xfitdataset', [], broadcast=True, archive=True)
            self.set_dataset('yfitdataset21', [], broadcast=True, archive=True)
            self.set_dataset('yfitdataset22', [], broadcast=True, archive=True)

        except TerminationRequested:
            print('Terminated gracefully')

        # Do curve fitting in this function
        if self.do_curvefit == True:
            self.fit_data()


        # These are necessary to restore the system to the state before the experiment.
        # self.load_globals_from_dataset()    # This loads global settings from datasets
        # self.setup()        # This sends settings out to the ARTIQ hardware


    def fit_data(self):
        """ Do curve fitting of data and display on graph here"""

        import numpy as np
        from scipy import optimize
                
        def cos_func(x, amp, phase, pitime):
            return amp * 0.5 * (np.cos(x * np.pi / pitime + phase)) + 0.5

        def cos_decay(x, amp, phase, pitime, decayt):
            return amp * 0.5 * (np.cos(x * np.pi / pitime + phase))*np.exp(-x/decayt) + 0.5

        # detect21 = self.get_dataset('ratio21')
        # detect22 = self.get_dataset('ratio22')
        # detect11 = self.get_dataset('ratio11')
        # detect12 = self.get_dataset('ratio12')
        scanx = self.get_dataset('scan_x')

        # Change this to the dataset you want to fit
        if self.Data_to_fit == "detect11":
            datatofit = self.get_dataset('ratio11')
        elif self.Data_to_fit == "detect12":
            datatofit = self.get_dataset('ratio12')
        elif self.Data_to_fit == "detect22":
            datatofit = self.get_dataset('ratio22')
        else:  # Data_to_fit == "detect21"
            datatofit = self.get_dataset('ratio21')


        # initialparams = [1,0,5e-6]      # amp, phase, pitime
        initialparams = [self.fitparam_amp, self.fitparam_phase, self.fitparam_pitime]
        fitbounds = ([0.2,-6.3,0],[1,6.3,20e-6])

        results1, covariances = optimize.curve_fit(cos_func, scanx[1:20], datatofit[1:20], p0=initialparams, bounds = fitbounds)
        print('Fit results: ', results1)

        fitbounds = ([0.2,-6.3,0,0],[1,100,20e-6,0.001])        # amp, phase, pitime, decayt

        results2, covariances = optimize.curve_fit(cos_decay, scanx[1:70], datatofit[1:70], p0=[*results1, self.fitparam_decayt], bounds = fitbounds)
        print('Fit results: ', results2)

        fittedx = np.linspace(0,max(scanx),self.fit_points)
        # fitresult1 = cos_func(fittedx, *results2)
        fitresult2 = cos_decay(fittedx, *results2)

        # print(fittedx)
        # print(fitresult2)

        self.set_dataset('xfitdataset', fittedx, broadcast=True)
        self.set_dataset('yfitdataset21', fitresult2, broadcast=True)

        self.set_dataset('data', datatofit, broadcast=True)

        # self.set_dataset('xfitdataset', [1,2,3,4,5,6,7,8,9,10], broadcast=True)
        # self.set_dataset('yfitdataset21', [0,1,0,1,0,1,0,1,0,1], broadcast=True)
        # self.set_dataset('yfitdataset22', np.zeros(20), broadcast=True)

        print("Amplitude: {:0.2f}".format(results2[0]), " ")
        print("Phase: {:0.2f}".format(results2[1]), " ")
        print("Pi Time: {:0.2f}".format(results2[2]*1e6), " us")
        print("Lifetime: {:0.0f}".format(results2[3]*1e6), " us")