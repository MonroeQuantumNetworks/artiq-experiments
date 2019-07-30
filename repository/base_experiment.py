"""
This program contains all the settings for an Ion-Photon experiment.

This should be run once at the beginning of operations to set up the appropriate DDS frequencies and TTL states.
It should be used as the startup kernel (untested).

Every other experiment should:
1. Be a subclass of this.
2. Should overwrite build(), but should not call super().build(), and should call at the beginning:
        super().load_globals_from_dataset()
        super().build_common()
3. Should overwrite run(), and NOT call super().run().
4. Should call super.prepare() if prepare is overwritten.  This ensures that globals are written to the datasets.

M. Lichtman 2019-07-15
"""

import traceback

from artiq.language.core import kernel, delay
from artiq.language.environment import HasEnvironment, EnvExperiment
from artiq.experiment import NumberValue, BooleanValue, TerminationRequested
from artiq.language.units import s, ms, us, ns, MHz


class base_experiment(EnvExperiment):

    # these lists contain default values, they will be overwritten by what is in the datasets and then what is typed in the GUI

    DDS_list = [
        ('493__sigma_minus', 'urukul0_ch0', 10*MHz, 10.0, True),
        ('493__pi', 'urukul0_ch1', 10*MHz, 10.0, True),
        ('493__sigma_plus', 'urukul0_ch2', 10 * MHz, 10.0, True),
        ('urukul0_ch3', 'urukul0_ch3', 10*MHz, 10.0, True),
        ('urukul1_ch0', 'urukul1_ch0', 10*MHz, 10.0, True),
        ('urukul1_ch1', 'urukul1_ch1', 10*MHz, 10.0, True),
        ('urukul1_ch2', 'urukul1_ch2', 10*MHz, 10.0, True),
        ('urukul1_ch3', 'urukul1_ch3', 10*MHz, 10.0, True),
        ('urukul2_ch0', 'urukul2_ch0', 10*MHz, 10.0, True),
        ('urukul2_ch1', 'urukul2_ch1', 10*MHz, 10.0, True),
        ('urukul2_ch2', 'urukul2_ch2', 10*MHz, 10.0, True),
        ('urukul2_ch3', 'urukul2_ch3', 10*MHz, 10.0, True)
    ]

    counter_inputs = [
        ('HOM1', 'ttl0'),
        ('HOM2', 'ttl1')
    ]

    TTL_output = [
        ('ttl8', 'ttl8', False),
        ('tll9', 'ttl9', False),
        ('ttl10', 'ttl10', False),
        ('ttl11', 'ttl11', False),
        ('ttl12', 'ttl12', False),
        ('ttl13', 'ttl13', False),
        ('ttl14', 'ttl14', False),
        ('ttl15', 'ttl15',  False)
    ]

    def build(self):

        self.load_globals_from_dataset()
        self.build_globals_arguments()
        self.build_common()

    def load_globals_from_dataset(self):

        # search the DatasetDB directly
        try:

            i = 0  # counter for number of loaded globals
            for key in self.get_dataset_db():
                if key.startswith('globals.'):

                    # Create an attribute for every globals dataset.
                    # Do not archive now, because we will archive in prepare() after changes may have been made.

                    # The datasets use '.' as the group delimiter, but for the namespace we replace this with '__' to make access easier
                    key2 = '__'.join(key.split('.'))
                    setattr(self, key2, self.get_dataset(key, archive=False))

                    i += 1

        except Exception as e:
            print("Could not load globals!!!  Error in key:", key)
            traceback.print_exc()

        print("Loaded {} globals.".format(i))

    def number_argument(self, arg, default, tooltip=None, **kwargs):
        """Create a new GUI entry for a NumberValue.
        :param arg: The name that will be given to the argument
        :param default: The default value to use.  This will be overridden if a globals exists, or if the GUI value is changed.
        :param tooltip: A text string for the tooltip, typically used for the hardware name.
        :param kwargs: passed directly to NumberValue"""

        # use 2nd entry as group
        argsplit = arg.split('__')
        if len(argsplit) > 2:
            group = argsplit[1]
        elif len(argsplit) == 1:
            group = argsplit[0]

        # if the argument exists in the globals database, use that as the default
        if hasattr(self, arg):
            default = getattr(self, arg)

        self.setattr_argument(arg, NumberValue(default, **kwargs), group=group, tooltip=tooltip)

    def boolean_argument(self, arg, default, tooltip=None):
        """Create a new GUI entry for a BooleanValue.
        :param arg: The name that will be given to the argument
        :param default: The default value to use.  This will be overridden if a globals exists, or if the GUI value is changed.
        :param tooltip: A text string for the tooltip, typically used for the hardware name."""

        # use 2nd entry as group
        argsplit = arg.split('__')
        if len(argsplit) > 2:
            group = argsplit[1]
        elif len(argsplit) == 1:
            group = argsplit[0]

        # if the argument exists in the globals database, use that as the default
        if hasattr(self, arg):
            default = getattr(self, arg)

        self.setattr_argument(arg, BooleanValue(default), group=group, tooltip=tooltip)

    def build_globals_arguments(self):
        """
        Create a GUI entry for each globals.
        This is the preferred way to add globals to our system.
        So to add a new globals, start by creating an argument for it here.
        If it begins with 'globals__' it will automatically be added to the globals datasets.
        It is also possible to add a global to the namespace with no GUI entry by:

        if not hasattr(self, 'globals__mygroup__myglobal'):
            setattr(self, 'globals__mygroup__myglobal', default)
        """

        # timing variables #

        self.number_argument('globals__cooling__cooling_time', 10*us, unit='us', ndecimals=9, min=0.0, step=1.0)
        self.number_argument('globals__pumping__pumping_time', 10*us, unit='us', ndecimals=9, min=0.0, step=1.0)
        self.number_argument('globals__detection__detection_time', 10*us, unit='us', ndecimals=9, min=0.0, step=1.0)

        # TTL output #

        for name, hardware, default in self.TTL_output:
            self.boolean_argument('globals__TTL_output__'+name, default, tooltip=hardware)

        # DDS #

        for name, hardware, freq_default, att_default, sw_default in self.DDS_list:
            self.number_argument('globals__DDS__' + name + '__frequency', freq_default, tooltip=hardware, unit='MHz', ndecimals=9, min=0.0*MHz, max=500.0*MHz, step=1.0*MHz)
            self.number_argument('globals__DDS__' + name + '__attenuation', att_default, tooltip=hardware, unit='dB', scale=1.0, ndecimals=9, min=0.0, max=31.5, step=0.5)
            self.boolean_argument('globals__DDS__' + name + '__switch', sw_default, tooltip=hardware)

    def build_common(self):

        # base functionality #

        self.setattr_device('core')
        self.setattr_device('led0')
        self.setattr_device('led1')

        # TTL inputs #

        self.num_counter_channels = len(self.counter_inputs)
        self.counter_channels = []
        for name, hardware in self.counter_inputs:
            # register hardware name
            self.setattr_device(hardware)
            # setup alias
            setattr(self, name, getattr(self, hardware))
            # create list in hardware order
            self.counter_channels.append(getattr(self, hardware))

        # TTL outputs #

        for name, hardware, default in self.TTL_output:
            self.setattr_device(hardware)
            setattr(self, name, getattr(self, hardware))

        # DDS channels #

        self.setattr_device('urukul0_cpld')
        self.setattr_device('urukul1_cpld')
        self.setattr_device('urukul2_cpld')

        self.DDS_device_list = []
        self.DDS_name_list = []

        for name, hardware, freq_default, att_default, sw_default in self.DDS_list:
            # setup device with real hardware name
            self.setattr_device(hardware)
            # setup alias
            setattr(self, name, getattr(self, hardware))
            # add device to lists
            self.DDS_name_list.append(name)
            self.DDS_device_list.append(getattr(self, hardware))

    def write_globals_to_datasets(self):
        # Write globals to datasets.  This will take care of things added both programatically and through arguments.
        for key in dir(self):
            if key.startswith('globals__'):
                key2 = '.'.join(key.split('__'))
                self.set_dataset(key2, getattr(self, key), broadcast=True, persist=True, archive=True)

    def prepare(self):
        self.write_globals_to_datasets()

    @kernel
    def DDS_setup(self, i):
        """
        Sets up one DDS channel based on passed in info
        :param i:  The index for the matching lists of DDS info created during build().
        :return:
        """

        # name = self.DDS_name_list[i]
        channel = self.DDS_device_list[i]
        freq = self.DDS_freq_list[i]
        att = self.DDS_att_list[i]
        sw = self.DDS_sw_list[i]

        # setup the channel
        channel.init()

        if not sw:
            channel.sw.off()

        delay(10*us)
        channel.set_att(att)
        delay(10*us)
        channel.set(freq)
        delay(10*us)

        if sw:
            channel.sw.on()

    def run(self):
        """This run method is used as the startup kernel.  It should be run whenever settings are changed. Otherwise,
        all other experiments overwrite it without calling super(). and so these commands are not repeated every
        experiment."""

        # self.set_dataset('counter_channels', self.counter_channel_names, persist=True, broadcast=True)

        # To make it easy to run through all the DDS and turn them on, create a list of the default parameters

        self.DDS_freq_list = [getattr(self, 'globals__DDS__' + name + '__frequency') for name in self.DDS_name_list]
        self.DDS_att_list = [getattr(self, 'globals__DDS__' + name + '__attenuation') for name in self.DDS_name_list]
        self.DDS_sw_list = [getattr(self, 'globals__DDS__' + name + '__switch') for name in self.DDS_name_list]

        self.kernel_run()


    @kernel
    def kernel_run(self):

        self.core.reset()

        # TTL inputs #

        for channel in self.counter_channels:
            channel.input()

        # TTL outputs #

        # DDS channels #

        self.urukul0_cpld.init()
        self.urukul1_cpld.init()
        self.urukul2_cpld.init()

        for i in range(len(self.DDS_device_list)):
            self.DDS_setup(i)

        self.ttl8.pulse(10*us)
        delay(10*us)
        self.ttl8.pulse(10*us)
