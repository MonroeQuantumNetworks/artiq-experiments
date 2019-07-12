#!/usr/bin/env python3

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph

from artiq.applets.simple import TitleApplet


class XYPlot(pyqtgraph.PlotWidget):
    def __init__(self, args):
        pyqtgraph.PlotWidget.__init__(self)
        self.args = args

    def data_changed(self, data, mods, title):

        points = data[self.args.points][1]

        try:
            y = data[self.args.y][1]
        except KeyError:
            return
        # expect a multi-dimensional array
        if not len(y.shape) == 2:
            print("data is not 2 dimensional")
            return
        # truncate the data to only that taken so far
        y = y[:points]

        x = data.get(self.args.x, (False, None))[1]
        if x is None:
            x = np.arange(len(y))
        else:
            x = x[:points]
        # check that the first y index is non-zero length and matches the size of x
        if not len(y) or len(y) != len(x):
            return

        error = data.get(self.args.error, (False, None))[1]
        # check error array
        if error is not None and hasattr(error, "__len__"):
            if not len(error):
                error = None
            else:
                error = error[:points]
                if error.shape != y.shape:
                    print("plot_multi_xy: error array does not have the same shape as y array")
                    return

        fit = data.get(self.args.fit, (False, None))[1]
        # check fit array
        if fit is not None:
            if not len(fit):
                fit = None
            else:
                fit = fit[:points]
                if fit.shape != y. shape:
                    print("plot_multi_xy: fit array does not have the same shape as y array")
                    return

        self.clear()
        self.setTitle(title)
        # iterate over channels (2nd dimension)
        for i in range(y.shape[1]):
            self.plot(x, y[:, i], pen=i, symbol='o')
            if error is not None:
                # See https://github.com/pyqtgraph/pyqtgraph/issues/211
                if hasattr(error, "__len__") and not isinstance(error, np.ndarray):
                    error = np.array(error)
                errbars = pyqtgraph.ErrorBarItem(
                    x=np.array(x), y=np.array(y[:, i]), height=error[:, i])
                self.addItem(errbars)
            if fit is not None:
                xi = np.argsort(x)
                self.plot(x, fit[:, i], pen=i)


def main():
    applet = TitleApplet(XYPlot)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("x", "X values", required=False)
    applet.add_dataset("error", "Error bars for each X value", required=False)
    applet.add_dataset("fit", "Fit values for each X value", required=False)
    applet.add_dataset("points", "Number of acquired points", required=False)
    applet.run()

if __name__ == "__main__":
    main()
