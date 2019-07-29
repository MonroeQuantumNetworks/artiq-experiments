"""
This program contains all the settings for an Ion-Photon experiment.

This should be run once at the beginning of operations to set up the appropriate DDS frequencies and TTL states.
It should be used as the startup kernel (untested).

Every other experiment should:
1. Be a subclass of this.
2. Should overwrite build(), should not call super().build(), and should call at the beginning:
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
from artiq.language.units import s, ms, us, MHz


class base_experiment(EnvExperiment):

    DDS_list = [
        ('493__sigma_minus', 'urukul0_ch0', 100*MHz, 10.0, True),
        ('493__pi', 'urukul0_ch1', 100*MHz, 10.0, True),
        ('493__sigma_plus', 'urukul0_ch2', 100*MHz, 10.0, True)
    ]

    counter_channel_names = ['ttl0', 'ttl1']

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

        self.globals_keys = []  # TODO: unused

        # search the DatasetDB directly
        try:
            for key in self.get_dataset_db():
                if key.startswith('globals.'):

                    # Create an attribute for every globals dataset.
                    # Do not archive now, because we will archive in prepare() after changes may have been made.

                    # The datasets use '.' as the group delimiter, but for the namespace we replace this with '__' to make access easier
                    key2 = '__'.join(key.split('.'))
                    setattr(self, key2, self.get_dataset(key, archive=False))

                    self.globals_keys.append(key2)  # TODO: is this used?

        except Exception as e:
            print("Could not load globals!!!  Error in key:", key)
            traceback.print_exc()

        print("Loaded {} globals.".format(len(self.globals_keys)))

    # TODO: don't require a default
    def number_argument(self, arg, default, tooltip=None, **kwargs):
        """Create a new GUI entry for a NumberValue.
        :param arg: The name that will be given to the argument
        :param default: The default value to use.  This will be overridden if a globals exists, or if the GUI value is changed.
        :param tooltip: A text string for the tooltip, typically used for the hardware name.
        :param kwargs: passed directly to NumberValue"""

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

        # Create a GUI entry for each globals.  This is the primary way that globals will be added to our system.
        # So every globals will be entered here manually at first.

        # We could create an argument for every globals in the database like this:
        # for key in self.globals_keys:
        #    self.setattr_argument(key)
        # But then we would need another way to add new globals variables to the database.  This way we don't have to
        # guess at GUI parameters (units, max, min, step).

        # TODO: use groups
        # split = arg.split('__')
        # if len(split)>2: group=split[1]

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

        self.num_counter_channels = len(self.counter_channel_names)
        for ch in self.counter_channel_names:
            self.setattr_device(ch)
        self.counter_channels = [getattr(self, ch) for ch in self.counter_channel_names]

        # aliases
        self.detector0 = self.ttl0
        self.detector1 = self.ttl1

        # TTL outputs #

        for name, hardware, default in self.TTL_output:
            self.setattr_device(hardware)
            setattr(self, name, getattr(self, hardware))

        # DDS channels #

        self.setattr_device('urukul0_cpld')
        self.setattr_device('urukul1_cpld')
        self.setattr_device('urukul2_cpld')

        self.DDS_device_list = []
        self.DDS_name_list = [i[0] for i in self.DDS_list]

        for DDS in self.DDS_list:
            name = DDS[0]
            hardware = DDS[1]
            self.setattr_device(hardware)  # setup device with real hardware name
            setattr(self, name, getattr(self, hardware))  # setup alias
            self.DDS_device_list.append(getattr(self, hardware))  # add device to list

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

        name = self.DDS_name_list[i]
        print(name)
        channel = self.DDS_device_list[i]
        freq = self.DDS_freq_list[i]
        att = self.DDS_att_list[i]
        sw = self.DDS_sw_list[i]
        print(freq)
        print(att)
        print(sw)

        # setup the channel
        self.core.break_realtime()
        channel.init()
        self.core.break_realtime()
        delay(100*ms)
        if not sw:
            channel.sw.off()
        channel.set_att(att)
        channel.set(freq)
        if sw:
            channel.sw.on()

    def run(self):

        # self.set_dataset('counter_channels', self.counter_channel_names, persist=True, broadcast=True)

        self.DDS_freq_list = [getattr(self, 'globals__DDS__' + name + '__frequency') for name in self.DDS_name_list]
        self.DDS_att_list = [getattr(self, 'globals__DDS__' + name + '__attenuation') for name in self.DDS_name_list]
        self.DDS_sw_list = [getattr(self, 'globals__DDS__' + name + '__switch') for name in self.DDS_name_list]

        print('493 sigma - from run():', self.globals__DDS__493__sigma_minus__frequency)

        self.kernel_run()


    @kernel
    def kernel_run(self):
        """This run method is used as the startup kernel.  It should be run whenever settings are changed. Otherwise,
        all other experiments overwrite it without calling super(). and so these commands are not repeated every
        experiment."""

        print('493 sigma - from kernel_run():', self.globals__DDS__493__sigma_minus__frequency)

        self.core.reset()
        start_time = now_mu() + self.core.seconds_to_mu(500*ms)
        while self.core.get_rtio_counter_mu() < start_time:
            pass
        self.core.break_realtime()

        # TTL inputs #

        for channel in self.counter_channels:
            channel.input()

        # TTL outputs #

        # DDS channels #

        # it seems like we only need to initialize a single CPLD?  Otherwise we get an error.
        self.urukul0_cpld.init()
        #self.urukul1_cpld.init()
        #self.urukul2_cpld.init()

        for i in range(len(self.DDS_device_list)):
            self.DDS_setup(i)

        print('here')

        self.ttl8.pulse(1*s)
        delay(1*s)
        self.ttl8.pulse(1*s)

        print('done')
