# multi-dimension optimizer code
# M. Lichtman 2019-03-22
# based on prior code by M. Lichtman

import numpy as np
from math import isnan
import time
import scipy.optimize
import h5py
import datetime
import os

# for creating graphs of the optimizer progress
# import matplotlib as mpl
# mpl.use('PDF')
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_pdf import PdfPages


class Optimization():

    def __init__(self, cost_function, set_function, variable_names, initial_values, variable_min, variable_max):
        # cost_function is a handle to a method that returns the numerical value to be minimized
        # set_function is a handle to a method set_function(name, value) for setting one variable where name is a string from variable_names
        # set_all_function is a handle to a function set_all_function(valuelist) for setting all variables, where valuelist is of the same length as variable_names
        # setting_function is a function handle that takes a list of values to be set for all variables
        # variable_names, initial_values, variable_min, variable_max must be lists or arrays of the same size
        # variable_names must be a list of strings
        # initial_values, variable_min, variable_max must be numerical arrays or lists

        self.measure = cost_function
        self.set_function = set_function
        self.optimization_variables = variable_names
        self.variable_min = np.array(variable_min, dtype=np.float64)
        self.variable_max = np.array(variable_max, dtype=np.float64)
        self.num = 0  # iteration number

        # scale the step size to the range for each variable
        self.initial_step = (self.variable_max - self.variable_min) / 200.0
        # create an array to store the separate initial steps for each variable
        self.n_axes = len(self.optimization_variables)
        self.axes = range(self.n_axes)  # a generator for the axes numbers
        # set the end tolerances relative to the initial step
        self.end_tolerances = self.initial_step / 1000.0

        self.is_done = False
        self.firstrun = True  # so we can record the initial cost

        # yi is the current cost
        self.tested_xi_list = []  # a history of all tested settings, shape=(iterations,axes)
        self.tested_yi_list = []  # a history of costs for all tested settings, shape=(iterations)
        self.best_xi_list   = []  # a history of the best points, shape=(?, axes)
        self.best_yi_list   = []  # a history of the best costs, shape=(?)
        self.best_xi = None
        self.best_yi = np.inf


        # get the current settings to use as the starting point
        self.xi = np.array(initial_values, dtype=np.float64)
        print(self.xi)
        self.current_x = self.xi

        # measure the cost at the initial settings
        self.yi = self.measure()
        self.update(self.xi, self.yi, force_best=True)

    def write_hdf5(self):

        # write an hdf5 file for recording optimizer track
        directory = '/home/monroe/Documents/fiber_optimization_data'
        filename = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_optimizer_data.hdf5')
        path = os.path.join(directory, filename)
        h5file = h5py.File(filename, 'w')

        h5file.create_dataset('variable_names', data=self.optimzation_variables)
        h5file.create_dataset('variable_min', data=self.variable_min)
        h5file.create_dataset('variable_max', data=self.variable_max)
        h5file.create_dataset('end_tolerances', data=self.end_tolerances)
        h5file.create_dataset('iterations', data=self.num)
        h5file.create_dataset('tested_x_list', data=self.tested_xi_list)
        h5file.create_dataset('tested_y_list', data=self.tested_yi_list)
        h5file.create_dataset('best_x_list', data=self.best_xi_list)
        h5file.create_dataset('best_y_list', data=self.best_y_list)
        h5file.close()

    def update(self, x, y, step_size=None, force_best=False):

        # if the cost function did not return a number, then assume the cost is infinite
        if isnan(y):
            y = np.inf

        self.tested_xi_list.append(x)
        self.tested_yi_list.append(y)

        # if this point is the best
        if ((y < self.best_yi) or force_best):
            dy = self.best_yi - y
            self.best_xi = x
            self.best_yi = y
            self.best_xi_list.append(x)
            self.best_yi_list.append(y)

            # for adaptive step sizes, go 10% of the way from the current step size
            if step_size is not None:
                self.initial_step = (self.initial_step + .1 * np.abs(step_size)) / 1.1

            # print the best result
            print('trial={} dy={} cost={} keeping setting: {}'.format(self.num, dy, y, x))
        else:
            print('trial={}'.format(self.num))

        self.num += 1

    def set_variables(self, x, force=False):
        # set the position twice, once -100um on each axis, and again at the correct position

        for i in self.axes:
            if ((self.current_x[i] != x[i]) or force):
                self.set_variable(i, x[i]-0.100)

        # wait until motors have hopefully finished moving
        # TODO: replace this with a status check
        time.sleep(1)

        for i in self.axes:
            if ((self.current_x[i] != x[i]) or force):
                self.set_variable(i, x[i])

        # wait until motors have hopefully finished moving
        # TODO: replace this with a status check
        time.sleep(1)

        self.current_x = x

    def set_variable(self, i, x):
        # enforce the variable range
        if self.variable_max[i] < x:
            print("Bounds enforced: {} attempted to set above maximum.".format(self.optimization_variables[i]))
            x = self.variable_max[i]
        elif self.variable_min[i] > x:
            print("Bounds enforced: {} attempted to set below minimum.".format(self.optimization_variables[i]))
            x = self.variable_min[i]

        # set just one variable
        self.set_function(self.optimization_variables[i], x)


    def scipy_fun(self, x):
        # objective function for scipy_optimize
        # this sets the position and then tests

        self.set_variables(x)
        try:
            y = self.measure()
        except:
            print("Exception in self.measure() for x: ", x)
            y = np.inf
        if isnan(y):
            y = np.inf

        self.update(x, cost)

        self.measure()
        return cost

    def scipy_optimize(self):
        x0 = self.xi.copy()
        bounds = [(self.variable_min[i], self.variable_max[i]) for i in self.axes]
        options = {'disp':True}
        res = scipy.optimize.minimize(scipy_fun, x0, method='Nelder-Mead', bounds=bounds, options=options)

        print("Result solution:\n", res.x)
        print("Result success:", res.success)
        print("Result message:", res.message)

        print("Setting position to optimizer solution.")
        cost = scipy_fun(res.x)
        print("Final measured cost:", cost)

        self.write_hdf5()

    def genetic(self):
        # Make random moves.  Keep them if they are better, otherwise discard them.
        # Possible extensions include "evolutionary" algorithm that keeps several branches in competition.
        print("starting genetic optimizer")

        while not self.is_done:
            # re-evaluate the previously best spot every time, to account for drift
            self.xi = self.best_xi

            self.set_variables(self.xi)
            self.yi = self.measure()
            self.update(self.xi, self.yi, force_best=True)

            # take random step on each axis, gaussian distribution with mean = 0, and deviation = step size
            print('self.xi:', self.xi)
            print('self.initial_step', self.initial_step)
            print('self.xi.shape', len(self.xi))
            self.xi = np.random.normal(self.best_xi, self.initial_step, len(self.xi))

            # enforce the variable range
            self.xi = np.maximum(np.minimum(self.variable_max, self.xi), self.variable_min)

            self.set_variables(self.xi)
            self.yi = self.measure()
            self.update(self.xi, self.yi)

        # reset the variables to the best value when the optimizer is stopped
        self.set_variables(x0)

    def breadth_first(self):
        # cycle through each variable, adjusting it a little bit, then move on to the next one

        while not self.is_done:

            for i in self.axes:
                # re-evaluate the previously best spot every time, to account for drift
                self.xi = self.best_yi

                self.set_variables(self.xi)
                self.yi = self.measure()
                self.update(force_best=True)

                # pick a direction
                if np.random.randint(2):
                    self.xi[i] += self.initial_step[i]
                    print("axis {} step +{}".format(i, self.initial_step[i]))
                else:
                    self.xi[i] -= self.initial_step[i]
                    print("axis {} step -{}".format(i, self.initial_step[i]))

                # set just this one axis and then measure
                self.set_variable(i, self.xi[i]-0.100)
                time.sleep(1)
                self.set_variable(i, self.xi[i])
                time.sleep(1)
                self.yi = self.measure()
                self.update()

        # reset the variables to the best value when the optimizer is stopped
        self.set_variables(self.best_xi)

    def depth_first(self):
        # cycle through each variable, adjusting it a little bit, then move on to the next one
        # if the results are better continue in that direction, but never undo a bad move

        while not self.is_done:

            for i in self.axes:

                # pick a direction
                if np.random.randint(2):
                    dx = self.initial_step[i]
                else:
                    dx = -self.initial_step[i]

                n = 0
                y0 = self.yi
                x0 = self.xi[i]
                # change one variable
                self.xi[i] += dx
                print("axis {} trial {} step {}".format(i, n, dx))
                # set just this one axis and then measure

                self.set_variable(i, self.xi[i]-0.100)
                time.sleep(1)
                self.set_variable(i, self.xi[i])
                time.sleep(1)
                self.yi = self.measure()
                self.update()

                if self.yi > y0:
                    # we went the wrong way.  invert dx
                    dx = -dx

                # continue driving as long as it continues to improve
                while (n == 0) or (self.yi < y0):
                    n += 1
                    # save the previous cost
                    y0 = self.yi
                    # change one variable
                    self.xi[i] = x0 + n*dx
                    print("axis {} trial {} step {}".format(i, n, dx))
                    # set just this one axis and then measure
                    self.set_variable(i, self.xi[i]-0.100)
                    time.sleep(1)
                    self.set_variable(i, self.xi[i])
                    time.sleep(1)
                    self.yi = self.measure()
                    self.update()

        # reset the variables to the best value when the optimizer is stopped
        self.set_variables(self.best_xi)

    def gradient_descent(self):
        """An optimization algorithm that finds the local gradient, then moves in the direction of fastest descent.
        A line search is done along that direction, then the process repeats."""

        while not self.is_done:

            # re-measure the best point
            self.set_variables(self.best_xi)
            self.yi = self.measure()
            self.update(force_best=True)

            # find gradient at the current point by making a small move on each axis
            dx = self.initial_step
            dy = np.zeros(self.n_axes)
            x0 = self.best_xi
            y0 = self.yi

            for i in self.axes:
                print('testing gradient on axis {}'.format(i))
                self.xi = x0.copy()
                self.xi[i] += dx[i]

                # test the change along this axis
                self.set_variables(self.xi)
                self.yi = self.measure()
                self.update()

                # record the change
                dy[i] = self.yi - y0

            gradient = dy / dx
            gradient[
                ~np.isfinite(gradient)] = 0  # if the step size was zero, then set the gradient to zero along that axis
            gradient = gradient / np.sqrt(np.sum(gradient ** 2))  # normalize gradient

            print("gradient: ", gradient)

            # re-measure y0
            self.set_variables(x0)
            y0 = self.measure()

            # try a point in the direction of decreasing cost, opposite the gradient
            step_size = self.initial_step
            x_test = x0 - step_size * gradient
            self.set_variables(x_test)
            self.yi = self.measure()
            self.xi = x_test
            self.update()

            # compare the new point to the old one
            x_best = x0
            y_best = y0
            if self.yi < y_best:
                n_double = 0
                # the new point is better, but there may be more room for improvement,
                # do a line search by doubling the step size as many times as we can,
                # until there is no more improvement
                # the loop will enter at least once
                while self.yi < y_best:
                    print("extending line search: ", n_double)
                    x_best = self.xi
                    y_best = self.yi
                    step_size *= 2  # double the step size
                    x_test = x0 - step_size * gradient
                    self.set_variables(x_test)
                    self.yi = self.measure()
                    self.xi = x_test
                    self.update()
                    n_double += 1
                    if scriptIsStopped():
                        break
                # the line search loop has exited because no more improvement is being found
                # keep the second to last point and use that as a starting point
                x0 = x_best
                y0 = y_best
            else:
                # the new point was no improvement, so halve the step size until we find something better
                n_half = 0
                while self.yi >= y_best:
                    print("halving line search: ", n_half)
                    # or end the optimization if the step size gets sufficiently small
                    if n_half > 10:
                        # self.is_done = True
                        print("Reached minimum step size while halving line search.")
                        break
                    step_size *= 0.5
                    x_test = x0 - step_size * gradient
                    self.set_variables(x_test)
                    self.yi = self.measure()
                    self.xi = x_test
                    self.update()
                    n_half += 1
                    if scriptIsStopped():
                        self.is_done = True
                        break
                else:
                    # the line search loop has exited because we found a better point
                    # keep the last point and use that as a starting point
                    x0 = self.xi
                    y0 = self.yi

    def simplex(self):
        """Perform the simplex algorithm.  x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better."""
        print("starting simplex optimizer")

        # x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        n = self.n_axes + 1
        x = np.zeros((n, self.n_axes))
        y = np.zeros(n)
        x0 = self.xi  # label the initial state
        x[0] = x0
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in self.axes:
            print('simplex: exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            # add the initial step size as the first offset
            xi[i] += self.initial_step[i]
            self.set_variables(xi)  # deviate one axis
            yi = self.measure()
            self.update(xi, yi)
            self.set_variables(x0)  # return that axis to where it started
            x[i + 1] = xi
            y[i + 1] = yi

        print('Finished simplex exploration.')

        simplex_iteration = 0

        # loop until the simplex is smaller than the end tolerances on every axis
        while np.any((np.amax(x, axis=0) - np.amin(x, axis=0)) > self.end_tolerances):

            simplex_iteration += 1
            print('\nsimplex iteration = ', simplex_iteration)

            # order the values
            order = np.argsort(y)
            x[:] = x[order]
            y[:] = y[order]

            # find the mean of all except the worst point
            x0 = np.mean(x[:-1], axis=0)

            # reflection
            print('simplex: reflecting')
            # reflect the worst point in the mean of the other points, to try and find a better point on the other side
            a = 1
            xr = x0 + a * (x0 - x[-1])
            # yield so we can take a datapoint
            self.set_variables(xr)
            yr = self.measure()
            self.update(xr, yr)

            if y[0] <= yr < y[-2]:
                # if the new point is no longer the worst, but not the best, use it to replace the worst point
                print('simplex: keeping reflection')
                x[-1] = xr
                y[-1] = yr

            # expansion
            elif yr < y[0]:
                print('simplex: expanding')
                # if the new point is the best, keep going in that direction
                b = 2
                xe = x0 + b * (x0 - x[-1])
                # yield so we can take a datapoint
                self.set_variables(xe)
                ye = self.measure()
                self.update(xe, ye)
                if ye < yr:
                    # if this expanded point is even better than the initial reflection, keep it
                    print('simplex: keeping expansion')
                    x[-1] = xe
                    y[-1] = ye
                else:
                    # if the expanded point is not any better than the reflection, use the reflection
                    print('simplex: keeping reflection (after expansion)')
                    x[-1] = xr
                    y[-1] = yr

            # contraction
            else:
                print('simplex: contracting')
                # The reflected point is still worse than all other points, so try not crossing over the mean,
                # but instead go halfway between the original worst point and the mean.
                c = -0.5
                xc = x0 + c * (x0 - x[-1])
                # yield so we can take a datapoint
                self.set_variables(xc)
                yc = self.measure()
                self.update(xc, yc)
                if yc < y[-1]:
                    # if the contracted point is better than the original worst point, keep it
                    print('simplex: keeping contraction')
                    x[-1] = xc
                    y[-1] = yc

                # reduction
                else:
                    # the contracted point is the worst of all points considered.  So reduce the size of the whole
                    # simplex, bringing each point in halfway towards the best point
                    print('simplex: reducing')
                    d = 0.9
                    # we don't technically need to re-evaluate x[0] here, as it does not change
                    # however, due to noise in the system it is preferable to re-evaluate x[0] occasionally,
                    # and now is a good time to do it
                    for i in self.axes:
                        x[i] = x[0] + d * (x[i] - x[0])
                        # yield so we can take a datapoint
                        self.set_variables(x[i])
                        y[i] = self.measure()
                        self.update(x[i], y[i])

    def weighted_simplex(self, x0):
        """Perform the simplex algorithm.
        This is the same as simplex(), except that a weighted mean is used to find the centroid of n points
        during reflection, instead of an unweighted mean.
        x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better."""

        # x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        n = self.axes + 1
        x = np.zeros((n, self.axes))
        y = np.zeros(n)
        x[0] = x0
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in self.axes:
            print('simplex: exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            # add the initial step size as the first offset
            xi[i] += self.initial_step[i]
            if x[i] > self.variable_max[i]:
                x[i] = self.variable_max[i]
            elif x[i] < self.variable_min[i]:
                x[i] = self.variable_min[i]
            setGlobal(self.optimization_variables[i], x[i], self.variable_units[i])
            startScan(wait=True)
            count = getAnalysis()['dm_analysis']['value']
            self.yi = -1 * count
            x[i + 1] = xi
            y[i + 1] = self.yi

        logger.debug('Finished simplex exploration.')

        # loop until the simplex is smaller than the end tolerances on each axis
        while np.any((np.amax(x, axis=0) - np.amin(x, axis=0)) > self.end_tolerances):

            logger.debug('Starting new round of simplex algorithm.')

            # order the values
            order = np.argsort(y)
            x[:] = x[order]
            y[:] = y[order]

            # find the mean of all except the worst point, taking into account the weight of how good each point is
            # negative weight is used because cost is a minimizer
            x0 = np.average(x[:-1], axis=0, weights=-y[:-1])

            # reflection
            print('simplex: reflecting')
            # reflect the worst point in the mean of the other points, to try and find a better point on the other side
            a = 1
            xr = x0 + a * (x0 - x[-1])
            # yield so we can take a datapoint
            for i in range(xr.shape[0]):
                if xr[i] > self.variable_max[i]:
                    xr[i] = self.variable_max[i]
                elif xr[i] < self.variable_min[i]:
                    xr[i] = self.variable_min[i]
            for i, channel in enumerate(self.optimization_variables):
                setGlobal(channel, xr[i], self.variable_units[i])
            startScan(wait=True)
            count = getAnalysis()['dm_analysis']['value']
            self.yi = -1 * count
            yr = self.yi

            if y[0] <= yr < y[-2]:
                # if the new point is no longer the worst, but not the best, use it to replace the worst point
                print('simplex: keeping reflection')
                x[-1] = xr
                y[-1] = yr

            # expansion
            elif yr < y[0]:
                print('simplex: expanding')
                # if the new point is the best, keep going in that direction
                b = 2
                xe = x0 + b * (x0 - x[-1])
                # yield so we can take a datapoint
                for i in range(xe.shape[0]):
                    if xe[i] > self.variable_max[i]:
                        xe[i] = self.variable_max[i]
                    elif xe[i] < self.variable_min[i]:
                        xe[i] = self.variable_min[i]
                for i, channel in enumerate(self.optimization_variables):
                    setGlobal(channel, xe[i], self.variable_units[i])
                startScan(wait=True)
                count = getAnalysis()['dm_analysis']['value']
                self.yi = -1 * count
                ye = self.yi
                if ye < yr:
                    # if this expanded point is even better than the initial reflection, keep it
                    print('simplex: keeping expansion')
                    x[-1] = xe
                    y[-1] = ye
                else:
                    # if the expanded point is not any better than the reflection, use the reflection
                    print('simplex: keeping reflection (after expansion)')
                    x[-1] = xr
                    y[-1] = yr

            # contraction
            else:
                print('simplex: contracting')
                # The reflected point is still worse than all other points, so try not crossing over the mean,
                # but instead go halfway between the original worst point and the mean.
                c = -0.5
                xc = x0 + c * (x0 - x[-1])
                # yield so we can take a datapoint
                for i in range(xc.shape[0]):
                    if xe[i] > self.variable_max[i]:
                        xe[i] = self.variable_max[i]
                    elif xe[i] < self.variable_min[i]:
                        xe[i] = self.variable_min[i]
                for i, channel in enumerate(self.optimization_variables):
                    setGlobal(channel, xe[i], self.variable_units[i])
                startScan(wait=True)
                count = getAnalysis()['dm_analysis']['value']
                self.yi = -1 * count
                yc = self.yi
                if yc < y[-1]:
                    # if the contracted point is better than the original worst point, keep it
                    print('simplex: keeping contraction')
                    x[-1] = xc
                    y[-1] = yc

                # reduction
                else:
                    # the contracted point is the worst of all points considered.  So reduce the size of the whole
                    # simplex, bringing each point in halfway towards the best point
                    print('simplex: reducing')
                    d = 0.9
                    # we don't technically need to re-evaluate x[0] here, as it does not change
                    # however, due to noise in the system it is preferable to re-evaluate x[0] occasionally,
                    # and now is a good time to do it
                    for i in self.axes:
                        x[i] = x[0] + d * (x[i] - x[0])
                        # yield so we can take a datapoint
                        if x[i] > self.variable_max[i]:
                            x[i] = self.variable_max[i]
                        elif x[i] < self.variable_min[i]:
                            x[i] = self.variable_min[i]
                        setGlobal(self.optimization_variables[i], x[i], self.variable_units[i])
                        startScan(wait=True)
                        count = getAnalysis()['dm_analysis']['value']
                        self.yi = -1 * count
                        y[i] = self.yi
            if scriptIsStopped():
                break

