# DeformableMirror.py created 2017-10-23 18:01:02.220436

import numpy as np
from math import isnan

# for creating graphs of the optimizer progress
# import matplotlib as mpl
# mpl.use('PDF')
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_pdf import PdfPages

import time

setScan('Deformable_Mirror_Scan')
setEvaluation('Dm_detection')
setAnalysis('blank')


class Optimization():
    # yi is the current cost
    xlist = []  # a history of the settings (shape=(iterations,axes))
    ylist = []  # a history of the costs (shape=(iterations))
    best_xi = None
    best_yi = np.inf

    def __init__(self, method, use_zernikes=True, pause=False, delay=1, relax_every_update=False):
        methods = {'genetic': self.genetic, 'gradient_descent': self.gradient_descent, 'simplex': self.simplex,
                   'weighted_simplex': self.weighted_simplex, 'breadth_first': self.breadth_first,
                   'depth_first': self.depth_first}
        self.optimization_method = methods[method]
        self.num = 0  # iteration number
        self.pause = pause  # if True, the scan will be paused during settings updates.
        self.delay = delay  # the delay, in seconds, between when the pulse program is unpaused and when the data is acquired in self.measure()
        self.relax_every_update = relax_every_update  # if True, the mirror will go through the relaxation process after every update

        # Below, define variables used in optimization. For each variable, there should be a minimum allowed value, a maximum allowed value, and a unit (or for no unit, '').
        # Variables can be added to the current arrays, as long as all other information is added as well.
        if use_zernikes:  # Optimize using Zerinkes, except use tiptilt1-tiptilt3 instead of amp and angle
            self.optimization_variables = ['dm_z{}'.format(actuator) for actuator in range(4, 16)] + ['dm_tiptilt1',
                                                                                                      'dm_tiptilt2',
                                                                                                      'dm_tiptilt3']
            self.variable_min = np.full(len(self.optimization_variables), -1.0)
            self.variable_min[12:15]
            self.variable_max = np.full(len(self.optimization_variables), 1.0)
            self.variable_max[12:15] = 200
            self.variable_units = 12 * [''] + 3 * ['V']
        else:  # use actuators
            self.optimization_variables = ['dm_a' + str(n + 1) for n in range(40)] + ['dm_tiptilt1', 'dm_tiptilt2',
                                                                                      'dm_tiptilt3']
            self.variable_min = np.zeros(len(self.optimization_variables))
            self.variable_max = np.full(len(self.optimization_variables), 200.0)
            self.variable_units = len(self.optimization_variables) * ['V']

        # scale the step size to the range for each variable
        self.initial_step = (self.variable_max - self.variable_min) / 100.0
        # create an array to store the separate initial steps for each variable
        self.n_axes = len(self.optimization_variables)
        self.axes = range(self.n_axes)  # the number of axes
        # set the end tolerances relative to the initial step
        self.end_tolerances = self.initial_step / 100.0

        self.is_done = False
        self.firstrun = True  # so we can record the initial cost

        # get the current settings to use as the starting point
        self.xi = np.empty(self.n_axes)
        for i, z in enumerate(self.optimization_variables):
            self.xi[i] = getGlobal(z).magnitude
        print(self.xi)

        # measure the cost at the initial settings
        # startScan(wait = False)
        if self.pause:
            pauseScan()  # scan will be paused most of the time
        self.yi = self.measure()

    def update(self, step_size=None):
        if isnan(self.yi):
            self.yi = np.inf

        self.xlist.append(self.xi)
        self.ylist.append(self.yi)

        if self.yi < self.best_yi:
            self.best_xi = self.xi
            self.best_yi = self.yi
            if step_size is not None:
                self.initial_step = (self.initial_step + .1 * np.abs(step_size)) / 1.1

            # print the best result
            print('iteration = {}, cost = {}'.format(self.num, -self.yi))

        self.num += 1

    def set_variables(self, x):
        # set all the variables
        for i in self.axes:
            self.set_variable(i, x[i])

    def set_variable(self, i, xi):
        # set just one variable
        # enforce the variable min and max range
        if xi > self.variable_max[i]:
            xi = self.variable_max[i]
        elif xi < self.variable_min[i]:
            xi = self.variable_min[i]
        # update the global variables to actuate the changes
        setGlobal(self.optimization_variables[i], xi, self.variable_units[i])

    def measure(self):
        if self.relax_every_update:
            self.relax()
        # unpause
        if self.pause:
            pauseScan()
        # delay to make sure the deformable mirror has updated.  time.sleep takes in seconds, self.delay is specified in milliseconds
        time.sleep(self.delay / 1000)
        # wait for a new point and read the data
        ion_counts = 0
        ion_counts_threshold = getGlobal('ion_counts_threshold').magnitude
        while (ion_counts < ion_counts_threshold):
            # time.sleep takes in delay as seconds.  self.delay is specified in milliseconds
            result = getData()
            ion_counts = result['ion_counts'][1]
        # re-pause
        if self.pause:
            pauseScan()
        return -result['dm_eval'][1]

    def relax(self):
        # relax the mirrors.  Math modulo 2 prevents the dummy variables from getting really big
        setGlobal('RelaxMirror', (getGlobal('RelaxMirror').magnitude + 1) % 2, '')
        setGlobal('RelaxTilt', (getGlobal('RelaxTilt').magnitude + 1) % 2, '')
        # setGlobal('RelaxMirror1',(getGlobal('RelaxMirror1').magnitude+1)%2,'')
        # setGlobal('RelaxTilt1', (getGlobal('RelaxTilt1').magnitude+1)%2,'')

    def genetic(self):

        x0 = self.xi

        while not self.is_done:
            # re-evaluate the previously best spot every time, to account for drift
            self.set_variables(x0)
            y0 = self.measure()

            # take random step on each axis, gaussian distribution with mean = 0, and deviation = step size
            step_size = np.random.normal(0, self.initial_step, self.xi.shape)
            self.xi = x0 + step_size
            self.set_variables(self.xi)
            self.yi = self.measure()

            if self.yi < y0:
                x0 = self.xi
                y0 = self.yi
                # self.update()  # if you want adapative step sizes use: step_size)

            # reset the global variables to the best value when the script is stopped, and end the scan gracefully
            if scriptIsStopped():
                self.set_variables(self.xi)
                # stopScan()
                self.is_done = True

    def breadth_first(self):
        # cycle through each variable, adjusting it a little bit, then move on to the next one
        x0 = self.xi
        while not self.is_done:

            for i in self.axes:
                # re-evaluate the previously best spot every time, to account for drift
                self.set_variables(x0)
                y0 = self.measure()

                # start from the known best position
                self.xi = x0.copy()

                # pick a direction
                if np.random.randint(2):
                    self.xi[i] += self.initial_step[i]
                    print("axis {} step +{}".format(i, self.initial_step[i]))
                else:
                    self.xi[i] -= self.initial_step[i]
                    print("axis {} step -{}".format(i, self.initial_step[i]))
                # set just this one axis and then measure
                self.set_variables(self.xi)
                self.yi = self.measure()

                if self.yi < y0:
                    # this setting is better, keep it.  Otherwise the next pass will reset to x0 again
                    print("axis {} keeping setting {}, dy {}".format(i, self.xi[i], self.yi - y0))
                    x0 = self.xi
                    y0 = self.yi

            # reset the global variables to the best value when the script is stopped, and end the scan gracefully
            if scriptIsStopped():
                self.set_variables(self.x0)
                # stopScan()
                self.is_done = True

    def depth_first(self):
        # cycle through each variable, adjusting it a little bit, then move on to the next one
        # if the results are better continue in that direction, but never undo a bad move
        y0 = self.yi

        while not self.is_done:

            for i in self.axes:

                # pick a direction
                if np.random.randint(2):
                    dx = self.initial_step[i]
                else:
                    dx = -self.initial_step[i]

                n = 0
                y0 = self.yi
                # change one variable
                self.xi[i] += dx
                print("axis {} trial {} step {}".format(i, n, dx))
                # set just this one axis and then measure
                self.set_variable(i, self.xi[i])
                self.yi = self.measure()

                if self.yi > y0:
                    # we went the wrong way.  invert dx
                    dx = -dx

                # continue driving as long as it continues to improve
                while (n == 0) or (self.yi < y0):
                    n += 1
                    # save the previous cost
                    y0 = self.yi
                    # change one variable
                    self.xi[i] += dx
                    print("axis {} trial {} step {}".format(i, n, dx))
                    # set just this one axis and then measure
                    self.set_variable(i, self.xi[i])
                    self.yi = self.measure()

            # reset the global variables to the best value when the script is stopped, and end the scan gracefully
            if scriptIsStopped():
                self.is_done = True

    def gradient_descent(self):
        """An optimization algorithm that finds the local gradient, then moves in the direction of fastest descent.
        A line search is done along that direction, then the process repeats."""

        # start the iteration at the current settings
        x0 = self.xi

        while not self.is_done:
            # re-measure y0
            self.set_variables(x0)
            y0 = self.measure()

            # find gradient at the current point by making a small move on each axis
            dx = self.initial_step
            dy = np.zeros(self.n_axes)
            y_last = y0
            x_test = x0.copy()
            for i in self.axes:
                print('testing gradient on axis' + str(i))
                # use a smaller step for gradient evaluation
                # dx[i] = self.initial_step[i]

                # x_test = x0.copy()

                x_test[i] += dx[i]
                # if x_test[i] > self.variable_max[i]:
                #    x_test[i] = self.variable_max[i]

                # if the range limits are hit, try going the other way
                # upper_margin = self.variable_max[i] - x_test[i]
                # lower_margin = x_test[i] - self.variable_min[i]
                # if upper_margin < dx[i]:
                #    if lower_margin < dx[i]:
                #        if upper_margin > lower_margin:
                #            x_test[i] = self.variable_max[i]
                #        else:
                #            x_test[i] = self.variable_min[i]
                #    else:
                #        x_test[i] -= dx[i]
                # else:
                #    x_test[i] += dx[i]

                # keep track of how big the actual dx was after the range was enforced
                # dx[i] = x_test[i]-x0[i]

                # update just the single axis
                print("global: {}, {}".format(i, x_test[i]))
                # setGlobal(self.optimization_variables[i], x_test[i], self.variable_units[i])
                # self.set_variables(x_test)
                self.set_variable(i, x_test[i])

                self.yi = self.measure()
                dy[i] = self.yi - y_last
                y_last = self.yi

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
            if scriptIsStopped():
                self.is_done = True
                break

    def simplex(self):
        """Perform the simplex algorithm.  x is 2D array of settings.  y is a 1D array of costs at each of those settings.
        When comparisons are made, lower is better."""

        # x0 is assigned when this generator is created, but nothing else is done until the first time next() is called

        n = self.n_axes + 1
        x = np.zeros((n, self.n_axes))
        y = np.zeros(n)
        x0 = self.xi
        x[0] = x0
        y[0] = self.yi

        # for the first several measurements, we just explore the cardinal axes to create the simplex
        for i in self.axes:
            print('simplex: exploring axis' + str(i))
            # for the new settings, start with the initial settings and then modify them by unit vectors
            xi = x0.copy()
            # add the initial step size as the first offset
            xi[i] += self.initial_step[i]
            x_test = xi
            self.set_variable(i, x_test[i])
            self.yi = self.measure()
            self.set_variable(i, x0[i])
            self.update()
            x[i + 1] = xi
            y[i + 1] = self.yi

        print('Finished simplex exploration.')

        # loop until the simplex is smaller than the end tolerances on each axis
        while np.any((np.amax(x, axis=0) - np.amin(x, axis=0)) > self.end_tolerances):

            print('Starting new round of simplex algorithm.')

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
            self.yi = self.measure()
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
                self.set_variables(xe)
                self.yi = self.measure()
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
                self.set_variables(xc)
                self.yi = self.measure()
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
                        self.set_variables(x[i])
                        self.yi = self.measure()
                        y[i] = self.yi
            if scriptIsStopped():
                break

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


detect_time = getGlobal('detect_DM_time_global').magnitude
dm_optimization = Optimization(method='simplex', use_zernikes=True, pause=False, delay=detect_time,
                               relax_every_update=True)
dm_optimization.optimization_method()
