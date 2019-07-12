#!/usr/bin/env python3

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph

from artiq.applets.simple import TitleApplet


class XYPlot(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self, args):
        pyqtgraph.GraphicsLayoutWidget.__init__(self)
        self.args = args
        self.num_channels = 0

    def data_changed(self, data, mods, title):

        try:
            y = data[self.args.y][1]
        except KeyError:
            return
        # expect a multi-dimensional array
        if not len(y.shape) == 2:
            print("data is not 2 dimensional")
            return
        # check that we have non-zero channels
        if y.shape[1] == 0:
            return

        # update the plot structure only for a new number of channels
        if self.num_channels != y.shape[1]:
            self.num_channels = y.shape[1]

            #self.setTitle(title)

            # create the plot widgets
            self.plots = []
            self.lines = []
            self.errbars = []
            for i in range(self.num_channels):
                self.plots += [self.addPlot()]
                if i > 0:
                    self.plots[i].setXLink(self.plots[0])
                # create the elements of each plot widget
                self.lines += [self.plots[i].plot(pen=i, symbol='o', symbolPen=('w'))]
                #self.errbars += [pyqtgraph.ErrorBarItem()]
                #self.plots[i].addItem(self.errbars[i])
                self.nextRow()

        points = data[self.args.points][1]

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

        # iterate over channels (2nd dimension)
        for i in range(self.num_channels):
            self.lines[i].setData(x, y[:, i])
            #if error is not None:
            #    # See https://github.com/pyqtgraph/pyqtgraph/issues/211
            #    if hasattr(error, "__len__") and not isinstance(error, np.ndarray):
            #        error = np.array(error)
            #    self.errbars[i].setData(x=np.array(x), y=np.array(y[:, i]), height=error[:, i])


def main():
    applet = TitleApplet(XYPlot)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("x", "X values", required=False)
    applet.add_dataset("error", "Error bars for each X value", required=False)
    applet.add_dataset("points", "Number of acquired points", required=False)
    applet.run()

if __name__ == "__main__":
    main()
