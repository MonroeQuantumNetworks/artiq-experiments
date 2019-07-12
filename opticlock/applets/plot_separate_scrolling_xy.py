"""An ARTIQ applet that makes a scrolling plot of any number of channels, with linked x-axes.
M. Lichtman 2019-07-11"""

import numpy as np
import PyQt5  # make sure pyqtgraph imports Qt5
import pyqtgraph
import datetime, time

from artiq.applets.simple import TitleApplet


# plotting utilities from https://gist.github.com/iverasp/9349dffa42aeffb32e48a0868edfa32d

def timestamp():
    return int(time.mktime(datetime.datetime.now().timetuple()))

class TimeAxisItem(pyqtgraph.AxisItem):

    # override tickStrings
    def tickStrings(self, values, scale, spacing):
        return [datetime.datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]

# plotting utility from https://gist.github.com/cpascual/cdcead6c166e63de2981bc23f5840a98

class DateAxisItem(pyqtgraph.AxisItem):
    """
    A tool that provides a date-time aware axis. It is implemented as an
    AxisItem that interprets positions as unix timestamps (i.e. seconds
    since 1970).
    The labels and the tick positions are dynamically adjusted depending
    on the range.
    It provides a  :meth:`attachToPlotItem` method to add it to a given
    PlotItem
    """

    # Max width in pixels reserved for each label in axis
    _pxLabelWidth = 80

    def __init__(self, *args, **kwargs):
        pyqtgraph.AxisItem.__init__(self, *args, **kwargs)
        self._oldAxis = None

    def tickValues(self, minVal, maxVal, size):
        """
        Reimplemented from PlotItem to adjust to the range and to force
        the ticks at "round" positions in the context of time units instead of
        rounding in a decimal base
        """

        maxMajSteps = int(size / self._pxLabelWidth)

        dt1 = datetime.datetime.fromtimestamp(minVal)
        dt2 = datetime.datetime.fromtimestamp(maxVal)

        dx = maxVal - minVal
        majticks = []

        if dx > 63072001:  # 3600s*24*(365+366) = 2 years (count leap year)
            d = datetime.timedelta(days=366)
            for y in range(dt1.year + 1, dt2.year):
                dt = datetime.datetime(year=y, month=1, day=1)
                majticks.append(time.mktime(dt.timetuple()))

        elif dx > 5270400:  # 3600s*24*61 = 61 days
            d = datetime.timedelta(days=31)
            dt = dt1.replace(day=1, hour=0, minute=0,
                             second=0, microsecond=0) + d
            while dt < dt2:
                # make sure that we are on day 1 (even if always sum 31 days)
                dt = dt.replace(day=1)
                majticks.append(time.mktime(dt.timetuple()))
                dt += d

        elif dx > 172800:  # 3600s24*2 = 2 days
            d = datetime.timedelta(days=1)
            dt = dt1.replace(hour=0, minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(time.mktime(dt.timetuple()))
                dt += d

        elif dx > 7200:  # 3600s*2 = 2hours
            d = datetime.timedelta(hours=1)
            dt = dt1.replace(minute=0, second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(time.mktime(dt.timetuple()))
                dt += d

        elif dx > 1200:  # 60s*20 = 20 minutes
            d = datetime.timedelta(minutes=10)
            dt = dt1.replace(minute=(dt1.minute // 10) * 10,
                             second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(time.mktime(dt.timetuple()))
                dt += d

        elif dx > 120:  # 60s*2 = 2 minutes
            d = datetime.timedelta(minutes=1)
            dt = dt1.replace(second=0, microsecond=0) + d
            while dt < dt2:
                majticks.append(time.mktime(dt.timetuple()))
                dt += d

        elif dx > 20:  # 20s
            d = datetime.timedelta(seconds=10)
            dt = dt1.replace(second=(dt1.second // 10) * 10, microsecond=0) + d
            while dt < dt2:
                majticks.append(time.mktime(dt.timetuple()))
                dt += d

        elif dx > 2:  # 2s
            d = datetime.timedelta(seconds=1)
            majticks = range(int(minVal), int(maxVal))

        else:  # <2s , use standard implementation from parent
            return pyqtgraph.AxisItem.tickValues(self, minVal, maxVal, size)

        L = len(majticks)
        if L > maxMajSteps:
            majticks = majticks[::int(numpy.ceil(float(L) / maxMajSteps))]

        return [(d.total_seconds(), majticks)]

    def tickStrings(self, values, scale, spacing):
        """Reimplemented from PlotItem to adjust to the range"""
        ret = []
        if not values:
            return []

        if spacing >= 31622400:  # 366 days
            fmt = "%Y"

        elif spacing >= 2678400:  # 31 days
            fmt = "%Y %b"

        elif spacing >= 86400:  # = 1 day
            fmt = "%b/%d"

        elif spacing >= 3600:  # 1 h
            fmt = "%b/%d-%Hh"

        elif spacing >= 60:  # 1 m
            fmt = "%H:%M"

        elif spacing >= 1:  # 1s
            fmt = "%H:%M:%S"

        else:
            # less than 2s (show microseconds)
            # fmt = '%S.%f"'
            fmt = '[+%fus]'  # explicitly relative to last second

        for x in values:
            try:
                t = datetime.datetime.fromtimestamp(x)
                ret.append(t.strftime(fmt))
            except ValueError:  # Windows can't handle dates before 1970
                ret.append('')

        return ret

    def attachToPlotItem(self, plotItem):
        """Add this axis to the given PlotItem
        :param plotItem: (PlotItem)
        """
        self.setParentItem(plotItem)
        viewBox = plotItem.getViewBox()
        self.linkToView(viewBox)
        self._oldAxis = plotItem.axes[self.orientation]['item']
        self._oldAxis.hide()
        plotItem.axes[self.orientation]['item'] = self
        pos = plotItem.axes[self.orientation]['pos']
        plotItem.layout.addItem(self, *pos)
        self.setZValue(-1000)

    def detachFromPlotItem(self):
        """Remove this axis from its attached PlotItem
        (not yet implemented)
        """
        raise NotImplementedError()  # TODO


class XYPlot(pyqtgraph.GraphicsLayoutWidget):

    def __init__(self, args):
        pyqtgraph.GraphicsLayoutWidget.__init__(self)
        self.args = args
        self.num_channels = 0  # start with 0 channels so any increase triggers re-initialization
        self.n = 1000  # number of points to keep

    def data_changed(self, data, mods, title):

        # load new data
        try:
            y = data[self.args.y][1]
        except KeyError:
            return
        # expect a 1D array
        if not len(y.shape) == 1:
            print("data is not 1D array of length=num_channels")
            return

        # update the plot structure only for a new number of channels
        if self.num_channels != len(y):
            self.num_channels = len(y)

            # re-initialize the data arrays
            self.clear()
            self.y = np.full((self.n, self.num_channels), np.nan, dtype=np.float64)
            self.x = np.full(self.n, timestamp(), dtype=np.float64)

            # create the plot widgets
            self.plots = []
            self.lines = []
            for i in range(self.num_channels):
                self.plots += [self.addPlot(labels={'left': 'channel {}'.format(i)}, axisItems={'bottom': DateAxisItem(orientation='bottom')})]
                # link x-axes of all plots to the top one
                if i > 0:
                    self.plots[i].setXLink(self.plots[0])
                # create the elements of each plot widget
                self.lines += [self.plots[i].plot(pen=i, symbol='o', symbolPen=('w'))]
                self.nextRow()

        # roll the arrays back and replace the latest value
        self.x = np.roll(self.x, -1)
        self.y = np.roll(self.y, -1, axis=0)
        self.x[-1] = time.time()  # new x-value is a timestamp
        self.y[-1] = y  # latest values from the 'detectors' dataset

        # iterate over channels and set the plot data
        for i in range(self.num_channels):
            self.lines[i].setData(self.x, self.y[:, i])


def main():
    applet = TitleApplet(XYPlot)
    applet.add_dataset("y", "Y values")
    applet.run()

if __name__ == "__main__":
    main()
