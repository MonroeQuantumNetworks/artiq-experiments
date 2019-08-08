"""An ARTIQ applet that makes a scrolling plot of any number of channels, with linked x-axes.
M. Lichtman 2019-07-11"""

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph
import datetime
import time
import dateaxisitem

from artiq.applets.simple import TitleApplet


class plot_separate_scrolling_xy(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self, args):
        pyqtgraph.GraphicsLayoutWidget.__init__(self)
        self.args = args
        self.num_channels = 0  # start with 0 channels so any increase triggers re-initialization
        self.channel_names = []  # start with no channels
        self.n = 1000  # number of points to keep

    def data_changed(self, data, mods, title):

        # load the channel names
        try:
            channel_names = [str(i, 'utf-8') for i in data[self.args.counter_channel_names][1]]
        except KeyError:
            print("KeyError in plot_separate_scrolling_xy")
            return

        # update the plot structure if there is any change to the channel list
        if self.channel_names != channel_names:
            self.channel_names = channel_names
            self.num_channels = len(channel_names)

            # re-initialize the data arrays
            self.clear()
            self.y = np.full((self.n, self.num_channels), np.nan, dtype=np.float64)
            self.x = np.full(self.n, time.time(), dtype=np.float64)

            # create the plot widgets
            self.plots = []
            self.lines = []
            self.name_labels = []
            self.now_labels = []
            self.avg_labels = []
            for i in range(self.num_channels):
                self.plots += [self.addPlot(rowspan=3, axisItems={'bottom': dateaxisitem.DateAxisItem(orientation='bottom')})]
                # link x-axes of all plots to the top one
                if i > 0:
                    self.plots[i].setXLink(self.plots[0])
                # create the elements of each plot widget
                self.lines += [self.plots[i].plot(pen=i, symbol='o', symbolPen=('w'))]
                # add text readout
                self.name_labels += [self.addLabel(self.channel_names[i], color='w', size='20pt')]
                self.nextRow()
                self.now_labels += [self.addLabel('', color='w', size='50pt')]
                self.nextRow()
                self.avg_labels += [self.addLabel('', color='w', size='20pt')]
                self.nextRow()

        # load new data
        try:
            y = data[self.args.y][1]
            # expect a 1D array
            if not ((len(y.shape) == 1) and (len(y) == self.num_channels)):
                print("data is not 1D array of length=num_channels")
                return

            # roll the arrays back and replace the latest value
            self.x = np.roll(self.x, -1)
            self.y = np.roll(self.y, -1, axis=0)
            self.x[-1] = time.time()  # new x-value is a timestamp
            self.y[-1] = y  # latest values from the 'detectors' dataset

            # iterate over channels and set the plot data
            for i in range(self.num_channels):
                self.lines[i].setData(self.x, self.y[:, i])
                self.now_labels[i].setText('{:d}'.format(int(self.y[-1, i])))
                self.avg_labels[i].setText('avg {:.1f}'.format(np.nanmean(self.y[:, i])))

        except KeyError:
            return


def main():
    applet = TitleApplet(plot_separate_scrolling_xy)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("counter_channel_names", "names of channels")
    applet.run()

if __name__ == "__main__":
    main()
