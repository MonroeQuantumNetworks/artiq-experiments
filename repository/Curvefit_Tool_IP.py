"""
Curve fitting tool for IonPhoton Data


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

class Curvefit_Tool_IonPhoton(base_experiment.base_experiment):

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
        self.setattr_argument('Data_to_fit', EnumerationValue(["sump1", "sump2", "sump3", "sump4"], default="sump1"))

        self.setattr_argument('fit_points', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('fitparam_amp', NumberValue(1, ndecimals=0, min=1, step=0.1, max=4))
        self.setattr_argument('fitparam_phase', NumberValue(0, ndecimals=0, min=-4, step=0.2, max=4))
        self.setattr_argument('fitparam_pitime', NumberValue(5, ndecimals=0, min=1*us, step=5, max=1000))
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

        def cos_func2(x, amp, phase, pitime, offset):
            return amp * 0.5 * (np.cos(x * np.pi / pitime + phase)) + offset

        def cos_decay(x, amp, phase, pitime, decayt):
            return amp * 0.5 * (np.cos(x * np.pi / pitime + phase))*np.exp(-x/decayt) + 0.5

        # detect21 = self.get_dataset('ratio21')
        # detect22 = self.get_dataset('ratio22')
        # detect11 = self.get_dataset('ratio11')
        # detect12 = self.get_dataset('ratio12')
        scanx = self.get_dataset('scan_x')

        # Change this to the dataset you want to fit
        data = self.get_dataset('ratio_list')
        data = np.array(data)

        if self.Data_to_fit == "sump1":
            datatofit = data[:,0]
            counts1 = np.array(self.get_dataset('sum_p1_1'))
            counts2 = np.array(self.get_dataset('sum_p1_2'))
        elif self.Data_to_fit == "sump2":
            datatofit = data[:,1]
            counts1 = np.array(self.get_dataset('sum_p2_1'))
            counts2 = np.array(self.get_dataset('sum_p2_2'))
        elif self.Data_to_fit == "sump3":
            datatofit = data[:,2]
            counts1 = np.array(self.get_dataset('sum_p3_1'))
            counts2 = np.array(self.get_dataset('sum_p3_2'))
        else:  # self.Data_to_fit == "sump4"
            # datatofit = np.array(data)
            datatofit = data[:,3]
            counts1 = np.array(self.get_dataset('sum_p4_1'))
            counts2 = np.array(self.get_dataset('sum_p4_2'))


        datatofit = np.ascontiguousarray(datatofit)

        # Calculate the uncertainties here
        error = np.sqrt(counts1)

        initialparams = [self.fitparam_amp, self.fitparam_phase, self.fitparam_pitime, 0.5]
        fitbounds = ([0.2,-6.3,0,0],[1,6.3,100,1])

        results1, covariances = optimize.curve_fit(cos_func2, scanx[1:20], datatofit[1:20], p0=initialparams, bounds = fitbounds)
        print('Fit results: ', results1)

        fittedx = np.linspace(0,max(scanx),self.fit_points)
        fitresult1 = cos_func2(fittedx, *results1)

        self.set_dataset('xfitdataset', fittedx, broadcast=True)
        self.set_dataset('yfitdataset', fitresult1, broadcast=True)

        self.set_dataset('data', datatofit, broadcast=True)

        # self.set_dataset('xfitdataset', [1,2,3,4,5,6,7,8,9,10], broadcast=True)
        # self.set_dataset('yfitdataset21', [0,1,0,1,0,1,0,1,0,1], broadcast=True)
        # self.set_dataset('yfitdataset22', np.zeros(20), broadcast=True)

        print("Amplitude: {:0.2f}".format(results1[0]), " ")
        print("Phase: {:0.2f}".format(results1[1]), " ")
        print("Fitted Pi: {:0.2f}".format(results1[2]), " ")
        print("Offset: {:0.2f}".format(results1[3]))

        bestangle = -results1[1]/3.14 * results1[2]

        if bestangle > 45:
            bestangle = bestangle - 45
        elif bestangle < 0:
            bestangle = bestangle + 45

        if bestangle < 0:
            bestangle = bestangle + 45

        print("Best Angle: {:0.2f}".format(bestangle))