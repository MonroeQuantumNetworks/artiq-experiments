"""
Created on Sun Apr 12 15:09:22 2020

@author: George
"""
from IPython import get_ipython

# get_ipython().magic('reset -sf')

import matplotlib.pyplot as plt
import h5py
import numpy as np
import easygui
from scipy import optimize
# import lmfit.models as fit
# from lmfit import Model

filename = easygui.fileopenbox

file = h5py.File('../results/2020-10-19/12/000015757-Alice_Ba_Raman_twobeams.h5', 'r')      # 2-6 MHz
# file = h5py.File('../results/2020-10-19/13/000015758-Alice_Ba_Raman_twobeams.h5', 'r')      # 6-10 MHz
# file = h5py.File('../results/2020-10-19/14/000015759-Alice_Ba_Raman_twobeams.h5', 'r')      # 10-14 MHz
# file = h5py.File('../results/2020-10-19/15/000015760-Alice_Ba_Raman_twobeams.h5', 'r')      # 14-16 MHz
# file = h5py.File('../results/2020-10-19/15/000015761-Alice_Ba_Raman_twobeams.h5', 'r')      # 3-7 MHz
# file = h5py.File('../results/2020-10-19/16/000015762-Alice_Ba_Raman_twobeams.h5', 'r')      # 10.5-14 MHz
# file = h5py.File('../results/2020-10-19/17/000015763-Alice_Ba_Raman_twobeams.h5', 'r')      # 14-16 MHz

# print(list(file.keys()))

rid = file['rid'][...]
runtime = file['run_time']
runtime_value = runtime[...]
starttime = file['start_time']
version = file['artiq_version'][...]

scannames = file['datasets/active_scan_names']

# print(rid[...])
# print(scannames)
# print(scannames[...])

xdata1 = file['datasets/scan_x'][...]  # This gets the dataset
ydata1 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

sum11 = file['datasets/sum11'][...]
sum12 = file['datasets/sum12'][...]
sum21 = file['datasets/sum21'][...]
sum22 = file['datasets/sum22'][...]

# print(xdata[:])
# print(xdata[...])
# print(ydata)

file = h5py.File('../results/2020-10-19/13/000015758-Alice_Ba_Raman_twobeams.h5', 'r')      # 6-10 MHz
xdata2 = file['datasets/scan_x'][...]
ydata2 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

file = h5py.File('../results/2020-10-19/14/000015759-Alice_Ba_Raman_twobeams.h5', 'r')      # 6-10 MHz
xdata3 = file['datasets/scan_x'][...]
ydata3 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

file = h5py.File('../results/2020-10-19/15/000015760-Alice_Ba_Raman_twobeams.h5', 'r')      # 6-10 MHz
xdata4 = file['datasets/scan_x'][...]
ydata4 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

file = h5py.File('../results/2020-10-19/15/000015761-Alice_Ba_Raman_twobeams.h5', 'r')      # 3-7 MHz
xdata5 = file['datasets/scan_x'][...]
ydata5 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

file = h5py.File('../results/2020-10-19/16/000015762-Alice_Ba_Raman_twobeams.h5', 'r')      # 10.5-14 MHz
xdata6 = file['datasets/scan_x'][...]
ydata6 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

file = h5py.File('../results/2020-10-19/17/000015763-Alice_Ba_Raman_twobeams.h5', 'r')      # 14-16 MHz
xdata7 = file['datasets/scan_x'][...]
ydata7 = file['datasets/ratio_list'][...]  # Adding the ellipsis makes an array of the values

# Concatenate all the arrays

print(type(xdata1))
print(type(xdata2))

xdata = np.concatenate([xdata1, xdata2, xdata3, xdata4])
ydata12 = np.concatenate([ydata1[:,1], ydata2[:,1], ydata3[:,1], ydata4[:,1]])
ydata21 = np.concatenate([ydata1[:,2], ydata2[:,2], ydata3[:,2], ydata4[:,2]])


# print(xdata[0:4])
# print(ydata[0:4])
# print(len(xdata))
# print(len(ydata))

# =============================================================================
# Plot the data
# =============================================================================


plt.figure(0, figsize=(30,12))

plt.plot(xdata, ydata21, 'b-o', label='First scan 21')
# plt.plot(xdata, ydata12, 'r-o', label='detect12')
plt.plot(xdata5, ydata5[:,0], 'g-o', label='Second scan 11')
plt.plot(xdata6, ydata6[:,0], 'g-o') #, label='detect11')
plt.plot(xdata7, ydata7[:,0], 'g-o') #, label='detect11')

plt.legend(loc='best')
x1,x2,y1,y2 = plt.axis()
# plt.axis((3e6,75e5, y1, y2))
# plt.axis((105e5,160e5, y1, y2))
# plt.show()

plt.figure(1, figsize=(30,12))

plt.plot(xdata, ydata21, 'b-o', label='First scan 21')
# plt.plot(xdata, ydata12, 'r-o', label='detect12')
plt.plot(xdata5, ydata5[:,0], 'g-o', label='Second scan 11')
# plt.plot(xdata6, ydata6[:,0], 'g-o', label='detect11')
# plt.plot(xdata7, ydata7[:,0], 'g-o', label='detect11')

plt.legend(loc='best')
x1,x2,y1,y2 = plt.axis()
plt.axis((3e6,75e5, y1, y2))


plt.figure(2, figsize=(30,12))

plt.plot(xdata, ydata21, 'b-o', label='First scan 21')
# plt.plot(xdata, ydata12, 'r-o', label='detect12')
# plt.plot(xdata5, ydata5[:,0], 'g-o', label='detect11')
plt.plot(xdata6, ydata6[:,0], 'g-o', label='Second scan 11')
plt.plot(xdata7, ydata7[:,0], 'g-o') #, label='detect11')

plt.legend(loc='best')
x1,x2,y1,y2 = plt.axis()

plt.axis((105e5,160e5, y1, y2))
plt.show()


# plt.figure(1, figsize=(30,8))
# plt.plot(xdata, sum11, 'r-o', label='sum11')
# plt.plot(xdata, sum22, 'b-o', label='sum22')
#
# plt.legend(loc='best')
# plt.show()


# --------------------- Curve fitting -------------------------

# # =============================================================================
# # Try harder with lmfit
# # =============================================================================
# from lmfit.models import GaussianModel
# from lmfit import Model
#
#
# def gaussian(x, amp, cen, sig):
#     '''
#     Parameters
#     ----------
#     x : TYPE
#         Independent variable
#     amp : TYPE
#         Amplitude of Gaussian
#     cen : TYPE
#         Center of Gaussian
#     sig : TYPE
#         Sigma
#
#     Returns
#     -------
#     TYPE
#         amp / sig / np.sqrt(2*np.pi) * np.exp(-(x-cen)**2 / (2*sig**2))
#     '''
#     return amp / sig / np.sqrt(2 * np.pi) * np.exp(-(x - cen) ** 2 / (2 * sig ** 2))
#
#
# x = np.linspace(-10, 10, 101)
# y = gaussian(x, 1, 2, 1.5) + np.random.normal(0, 0.05, x.size)
#
# gmodel = Model(gaussian)
# print('parameter names: {}'.format(gmodel.param_names))
# print('independent variables: {}'.format(gmodel.independent_vars))
#
# # Now check the parameters and variables for Gaussian Model
# print('parameter names: {}'.format(GaussianModel().param_names))
# print('independent variables: {}'.format(GaussianModel().independent_vars))
# # parameter names: ['amplitude', 'center', 'sigma']
# # independent variables: ['x']
#
# # Now generate some dummy gaussian data
# # f(x; A, \mu, \sigma) = \frac{A}{\sigma\sqrt{2\pi}} e^{[{-{(x-\mu)^2}/{{2\sigma}^2}}]}
# # gaussian(x, amplitude, center, sigma) =
# #     (amplitude/(s2pi*sigma)) * exp(-(1.0*x-center)**2 / (2*sigma**2))
# params = GaussianModel().make_params(amplitude=1, center=0, sigma=0.5)
#
# # Parameters([('amplitude', <Parameter 'amplitude', value=1, bounds=[-inf:inf]>),
# #             ('center', <Parameter 'center', value=2, bounds=[-inf:inf]>),
# #             ('sigma', <Parameter 'sigma', value=0.5, bounds=[0:inf]>),
# #             ('fwhm', <Parameter 'fwhm', value=1.17741, bounds=[-inf:inf], expr='2.3548200*sigma'>),
# #             ('height', <Parameter 'height', value=0.7978846, bounds=[-inf:inf], expr='0.3989423*amplitude/max(2.220446049250313e-16, sigma)'>)])
#
# # Generate a curve from the model:
# # x_eval = np.linspace(0, 10, 201)
# # y_eval = GaussianModel().eval(params, x=x_eval)
#
# result = GaussianModel().fit(y, params, x=x)
# print(result.fit_report())
#
# # print number of function efvals
# print(result.nfev)
# # print number of data points
# print(result.ndata)
# # print number of variables
# print(result.nvarys)
# # chi-sqr
# print(result.chisqr)
# # reduce chi-sqr
# print(result.redchi)
# # Akaike info crit
# print(result.aic)
# # Bayesian info crit
# print(result.bic)
#
# # This makes a dictionary of the fitted parameters
# fitvalues = result.params.valuesdict()
# print('Amplitude: ', fitvalues['amplitude'], 'FWHM: ', fitvalues['fwhm'], 'Height: ', fitvalues['height'])
#
# # This returns an array with the values of the three dictionary keys requested
# from operator import itemgetter
#
# itemgetter('amplitude', 'fwhm', 'height')(fitvalues)
#
# # =============================================================================
# # Now try the same Gaussian fit with scipy.optimize.curve_fit
# # =============================================================================
# params, params_covariance = optimize.curve_fit(gaussian, x, y, p0=[1, 0, 0.5])
# print('Parameters:', params)
# print('Covariance:', params_covariance)
#
# np.sqrt(params_covariance[0, 0])
# np.sqrt(params_covariance[1, 1])
# np.sqrt(params_covariance[2, 2])
#
# errors = np.sqrt(np.diag(params_covariance))
# print('Errors:', errors)
#
# plt.plot(x, y)
# # plt.plot(x_eval, y_eval)
# plt.plot(x, result.best_fit, 'r-', label='best fit')