"""An ARTIQ applet that makes a scrolling plot of any number of channels, with linked x-axes.
M. Lichtman 2019-07-11"""

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph
import datetime
import time
import dateaxisitem

from artiq.applets.simple import TitleApplet


class scan_plot_1D(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self, args):
        pyqtgraph.GraphicsLayoutWidget.__init__(self)
        self.args = args
        self.num_channels = 0  # start with 0 channels so any increase triggers re-initialization
        self.channel_names = []  # start with no channels
        self.n = 10  # number of points to keep

    def data_changed(self, data, mods, title):

        # load the channel names
        try:
            channel_names = [str(i, 'utf-8') for i in data[self.args.counter_channel_names][1]]
        except KeyError:
            print("KeyError in scan_plot")
            return

        # update the plot structure if there is any change to the channel list
        if self.channel_names != channel_names:
            self.channel_names = channel_names
            self.num_channels = len(channel_names)

            # re-initialize the data arrays
            self.clear()

            self.y = np.full((self.n, self.num_channels), np.nan, dtype=np.float64)
            self.x = np.full(self.n, np.nan, dtype=np.float64)

            # create the plot widgets
            self.plots = []
            self.lines = []
            self.name_labels = []
            self.now_labels = []
            self.avg_labels = []
            for i in range(self.num_channels):
                self.plots += [self.addPlot(rowspan=3)]  #, axisItems={'bottom': dateaxisitem.DateAxisItem(orientation='bottom')})]
                # create the elements of each plot widget
                self.lines += [self.plots[i].plot(pen='w', symbol=None, symbolPen=('w'))]
                # add text readout
                self.name_labels += [self.addLabel(self.channel_names[i], color='w', size='20pt')]
                self.nextRow()
                self.now_labels += [self.addLabel('', color='w', size='50pt')]
                self.nextRow()
                self.avg_labels += [self.addLabel('', color='w', size='20pt')]
                self.nextRow()
                # link x-axes of all plots to the top one
                if i != 0:
                    self.plots[i].setXLink(self.plots[0])


        # load new data
        try:

            self.y = np.array(data[self.args.y][1])
            # account for 1D shape when we only have the first point
            if len(self.y.shape) == 1:
                self.y = np.reshape(self.y, (1, len(self.y)))

            # expect that x is a 1D array of the same length as y
            self.x = np.array(data.get(self.args.x, (False, None))[1])
            #self.xlabel = [', '.join(i) for i in data.get(self.args.xlabel, (False, None))[1]]

            # check to see that we have both x and y updated
            if len(self.x) != len(self.y):
                return

            # iterate over channels and set the plot data
            for i in range(self.num_channels):
                self.lines[i].setData(self.x, self.y[:, i])
                self.now_labels[i].setText('{:.2f}'.format(float(self.y[-1, i])))
                self.avg_labels[i].setText('avg {:.1f}'.format(np.nanmean(self.y[:, i])))

        except Exception:
            return


def main():
    applet = TitleApplet(scan_plot_1D)
    applet.add_dataset("y", "Y values")
    applet.add_dataset("counter_channel_names", "names of channels")
    applet.add_dataset("x", "scan values")
    applet.add_dataset("xlabel", "x axis label")
    applet.run()

if __name__ == "__main__":
    main()
