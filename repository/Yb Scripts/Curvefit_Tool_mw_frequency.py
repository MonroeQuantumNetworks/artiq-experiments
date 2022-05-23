""" Modified to do Raman using the Keysight AWG
Bob Barium detection, with scannable variables, DMA detection
Turn on Ba_ratios and Detection_Counts APPLETS to plot the figures
Fixed AOM amplitude scanning and update
Also does curve fitting at the very end (Fit to Raman time scan)

Uses Keysight AWG to drive Raman lasers

Known issues:


Sagnik Saha 2022-05-18
"""
from artiq.experiment import *
#from artiq.language.core import kernel, delay, delay_mu, now_mu, at_mu
#from artiq.language.units import s, ms, us, ns, MHz
#from artiq.coredevice.exceptions import RTIOOverflow
#from artiq.experiment import NumberValue
#from artiq.language.scan import Scannable
import numpy as np
from repository import base_experiment
import os
import time

# from AWGmessenger import sendmessage   # Other file in the repo, contains code for messaging Jarvis

class Curvefit_Tool_mw_frequency(base_experiment.base_experiment):

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
        self.setattr_argument('Data_to_fit', EnumerationValue(["detect11", "detect12", "detect21", "detect22"], default="detect11"))

        self.setattr_argument('fit_points', NumberValue(100, ndecimals=0, min=1, step=1))
        self.setattr_argument('fitparam_center', NumberValue(1, ndecimals=3, min=1e6, step=1, max=40e7, unit='MHz'))
        self.setattr_argument('fitparam_sigma', NumberValue(1, ndecimals=4, min=1e2, step=1, max=4e7, unit='MHz'))
        self.setattr_argument('fitparam_amp', NumberValue(1, ndecimals=2, min=0, step=1, max=1000000))
        self.setattr_argument('fitparam_offset', NumberValue(0.1, ndecimals=2, min=0, step=0.1, max=10))

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
        #Introduce lorentzian for Raman frequency scan fit
        def lorentz(x,gamma,center,amp):
            return amp/np.pi*((gamma/2)/((x-center)**2+(gamma/2)**2))

        def gaussian(x,sigma,center,amp, offset):
            return amp*np.exp(-(x-center)**2/(2*sigma)**2) + offset
        #
        # def sinc(x,freq, disp, amp):
        #     return amp*(np.sin(2*np.pi*freq))
        # detect21 = self.get_dataset('ratio21')
        # detect22 = self.get_dataset('ratio22')
        # detect11 = self.get_dataset('ratio11')
        # detect12 = self.get_dataset('ratio12')
        scanx = self.get_dataset('scan_x')

        data1 = self.get_dataset('sum12')
        data2 = self.get_dataset('sum11')
        datatofit = data1/(data1+data2)

        # Change this to the dataset you want to fit
        # if self.Data_to_fit == "detect11":
        #     datatofit = self.get_dataset('sum11')
        # else: # self.Data_to_fit == "detect12":
        #     datatofit = self.get_dataset('sum12')
        # elif self.Data_to_fit == "detect22":
        #     datatofit = self.get_dataset('ratio22')
        # else:  # Data_to_fit == "detect21"
        #     datatofit = self.get_dataset('ratio21')


        # initialparams = [1,0,5e-6]      # amp, phase, pitime
        initialparams = [self.fitparam_sigma, self.fitparam_center,self.fitparam_amp, self.fitparam_offset]
        fitbounds = ([0,0,0, 0],[0.05*MHz,400*MHz,1, 1])

        results1, covariances = optimize.curve_fit(gaussian, scanx, datatofit, p0=initialparams, bounds=fitbounds,maxfev=100000)
        print('Fit results: ', results1)

        # fitbounds = ([0.2,-6.3,0,0],[1,100,50e-6,0.01])        # amp, phase, pitime, decayt

        # results2, covariances = optimize.curve_fit(cos_decay, scanx[1:100], datatofit[1:100], p0=[*results1, self.fitparam_decayt], bounds = fitbounds)
        # print('Fit results: ', results2)

        fittedx = np.linspace(min(scanx),max(scanx),self.fit_points)
        # fitresult1 = cos_func(fittedx, *results2)
        fitresult2 = gaussian(fittedx, *results1)

        # print(fittedx)
        # print(fitresult2)

        self.set_dataset('xfitdataset', fittedx, broadcast=True)
        self.set_dataset('yfitdataset21', fitresult2, broadcast=True)

        self.set_dataset('data', datatofit, broadcast=True)

        # self.set_dataset('xfitdataset', [1,2,3,4,5,6,7,8,9,10], broadcast=True)
        # self.set_dataset('yfitdataset21', [0,1,0,1,0,1,0,1,0,1], broadcast=True)
        # self.set_dataset('yfitdataset22', np.zeros(20), broadcast=True)

        print("Center: {:0.6f}".format(results1[1]/MHz), "MHz")
        print("Sigma: {:0.6f}".format(results1[0]/MHz), "MHz")
        print("Offset: {:0.6f}".format(results1[3]/MHz))
        # print(covariances)