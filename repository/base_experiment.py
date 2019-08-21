"""
This program brings in all the settings for the IonPhoton experiment.  It never needs to be run directly.
Use settings.py for initialization and changing settings.

Every other experiment should:
1. Be a subclass of this.
2. Should call super().build() if build is overwritten.  This ensures that globals are loaded from the datasets.
3. Should overwrite run().
4. Should call super.prepare() if prepare is overwritten.  This ensures that globals are written to the datasets.

M. Lichtman updated 2019-08-02
"""

import traceback

from artiq.language.core import kernel, delay, at_mu, now_mu
from artiq.language.environment import HasEnvironment, EnvExperiment
from artiq.experiment import NumberValue, BooleanValue, TerminationRequested
from artiq.language.units import s, ms, us, ns, MHz, V
from artiq.coredevice.comm_analyzer import (get_analyzer_dump, decode_dump, decoded_dump_to_vcd)
import numpy as np


class base_experiment(EnvExperiment):

    core_ip_address = '192.168.1.98'

    # these lists contain default values, they will be overwritten by what is in the datasets and then what is typed in the GUI

    urukul_cpld_list = [
        'urukul0_cpld',
        'urukul1_cpld',
        'urukul2_cpld',
        'urukul3_cpld'
    ]

    DDS_list = [
        ('493__Alice__sigma_1', 'urukul0_ch0', 75*MHz, 1.0, 10.0, True),
        ('493__Alice__sigma_2', 'urukul0_ch1', 85*MHz, 1.0, 10.0, True),
        ('493__Bob__sigma_1', 'urukul0_ch2', 79*MHz, 1.0, 10.0, True),
        ('493__Bob__sigma_2', 'urukul0_ch3', 81*MHz, 1.0, 10.0, True),
        ('650__sigma_1', 'urukul1_ch0', 81.5*MHz, 1.0, 10.0, True),
        ('650__sigma_2', 'urukul1_ch1', 78.5*MHz, 1.0, 10.0, True),
        ('650__Alice__pi', 'urukul1_ch2', 80*MHz, 1.0, 10.0, True),
        ('650__Bob__pi', 'urukul1_ch3', 82*MHz, 1.0, 10.0, True),
        ('650__fast_AOM', 'urukul2_ch0', 400*MHz, 1.0, 10.0, True),
        ('493__Alice__cooling', 'urukul2_ch1', 80*MHz, 1.0, 10.0, True),
        ('532__tone_1', 'urukul2_ch2', 110*MHz, 0.5, 19.5, False),
        ('532__tone_2', 'urukul2_ch3', 110*MHz, 0.5, 19.5, False),
        ('Alice_trap_RF', 'urukul3_ch0', 18.624*MHz, 0.491, 13.0, True),
        ('Bob_trap_RF', 'urukul3_ch1', 14.0111*MHz, 0.51, 20.0, True),
        ('urukul3_ch2', 'urukul3_ch2', 10 * MHz, 0.5, 10.0, False),
        ('urukul3_ch3', 'urukul3_ch3', 10 * MHz, 0.5, 10.0, False)
    ]

    TTL_input_list = [
        #('HOM0', 'ttl0'),
        #('HOM1', 'ttl1'),
        #('HOM2', 'ttl2'),
        #('HOM3', 'ttl3'),
        ('Alice_camera_side_APD', 'ttl4'),
        ('Bob_camera_side_APD', 'ttl5'),
        ('Alice_PMT', 'ttl6'),
        ('Bob_PMT', 'ttl7')
        ]

    TTL_output_list = [
        ('ttl8', 'ttl8', False),
        ('tll9', 'ttl9', False),
        ('ttl10', 'ttl10', False),
        ('ttl11', 'ttl11', False),
        ('ttl12', 'ttl12', False),
        ('ttl13', 'ttl13', False),
        ('ttl14', 'ttl14', False),
        ('ttl15', 'ttl15',  False)
    ]

    DAC_list = [
        ('Alice_camera_DC_bias', 0, -0.15),
        ('Alice_camera_RF_bias', 1, 0.18),
        ('Alice_big_lens_RF_bias', 2, -0.03),
        ('Alice_big_lens_DC_bias', 3, 0.12),
        ('Bob_RF_bias_0', 4, 0.27),
        ('Bob_RF_bias_1', 5, 0.169),
        ('Bob_Dsub_side_ground_bias', 6, 0.083),
        ('Bob_resonator_side_ground_bias', 7, 0.165),
        ('DAC8', 8, 0.0),
        ('DAC9', 9, 0.0),
        ('DAC10', 10, 0.0),
        ('DAC11', 11, 0.0),
        ('DAC12', 12, 0.0),
        ('DAC13', 13, 0.0),
        ('DAC14', 14, 0.0),
        ('DAC15', 15, 0.0)
    ]

    num_DAC_channels = 16

    def build(self):

        self.load_globals_from_dataset()
        self.build_common()
        #print('base_experiment.build() done for {}'.format(self.__class__))

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
            print("Could not load globals!!!")
            if key is not None:
                print("Error in key:", key)
            traceback.print_exc()

        #print("Loaded {} globals.".format(i))

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

        self.number_argument('globals__timing__cooling_time', 10*us, unit='us', ndecimals=9, min=0.0, step=1.0)
        self.number_argument('globals__timing__pumping_time', 10*us, unit='us', ndecimals=9, min=0.0, step=1.0)
        self.number_argument('globals__timing__excitation_pulse_time', 10*ns, unit='ns', ndecimals=9, min=0.0, step=1.0)
        self.number_argument('globals__timing__detection_time', 10*us, unit='us', ndecimals=9, min=0.0, step=1.0)

        # TTL output #

        for name, hardware, default in self.TTL_output_list:
            self.boolean_argument('globals__TTL_output__'+name, default, tooltip=hardware)

        # DDS #

        for name, hardware, freq_default, amp_default, att_default, sw_default in self.DDS_list:
            self.number_argument('globals__DDS__' + name + '__frequency', freq_default, tooltip=hardware, unit='MHz', ndecimals=9, min=0.0*MHz, max=500.0*MHz, step=0.01*MHz)
            self.number_argument('globals__DDS__' + name + '__amplitude', amp_default, tooltip=hardware, scale=1.0, ndecimals=9, min=0.0, max=1.0, step=0.1)
            self.number_argument('globals__DDS__' + name + '__attenuation', att_default, tooltip=hardware, unit='dB', scale=1.0, ndecimals=9, min=0.0, max=31.5, step=0.5)
            self.boolean_argument('globals__DDS__' + name + '__switch', sw_default, tooltip=hardware)

        # DAC #

        for name, channel, voltage_default in self.DAC_list:
            self.number_argument('globals__DAC__'+name, voltage_default, tooltip='zotino0_ch'+str(channel), unit='V', ndecimals=9, min=-10*V, max=9.999*V, step=1*V)

    def build_common(self):

        # base functionality #

        self.setattr_device('core')
        self.setattr_device('scheduler')
        self.setattr_device('led0')
        self.setattr_device('led1')

        # TTL inputs #

        self.globals__TTL_input__num_channels = len(self.TTL_input_list)
        self.globals__TTL_input__channel_names = []
        self.TTL_input_channels = []
        for name, hardware in self.TTL_input_list:
            # register hardware name
            self.setattr_device(hardware)
            # setup alias
            setattr(self, name, getattr(self, hardware))
            # create list in hardware order
            self.globals__TTL_input__channel_names.append(name)
            self.TTL_input_channels.append(getattr(self, hardware))

        # TTL outputs #

        self.globals__TTL_output__num_channels = len(self.TTL_output_list)
        self.globals__TTL_output__channel_names = []
        self.TTL_output_channels = []
        for name, hardware, default in self.TTL_output_list:
            # register hardware name
            self.setattr_device(hardware)
            # setup alias
            setattr(self, name, getattr(self, hardware))
            # create list in hardware order
            self.globals__TTL_output__channel_names.append(bytes(name, 'utf-8'))
            self.TTL_output_channels.append(getattr(self, hardware))

        # DDS channels #

        self.urukul_cplds = []
        for name in self.urukul_cpld_list:
            self.setattr_device(name)
            self.urukul_cplds.append(getattr(self, name))

        self.DDS_device_list = []
        self.DDS_name_list = []

        for name, hardware, freq_default, amp_default, att_default, sw_default in self.DDS_list:
            # setup device with real hardware name
            self.setattr_device(hardware)
            # setup alias
            alias_name = "DDS__" + name
            setattr(self, alias_name, getattr(self, hardware))
            #kernel_invariants = getattr(self, "kernel_invariants", set())
            #self.kernel_invariants = kernel_invariants | {alias_name}
            # add device to lists
            self.DDS_name_list.append(name)
            self.DDS_device_list.append(getattr(self, hardware))

        # DAC #

        self.setattr_device('zotino0')

    def write_globals_to_datasets(self, archive=False):
        # Write globals to datasets.  This will take care of things added both programatically and through arguments.
        for key in dir(self):
            if key.startswith('globals__'):
                key2 = '.'.join(key.split('__'))
                value = getattr(self, key)
                if isinstance(value, (bool, int, float, np.ndarray)):
                    self.set_dataset(key2, value, broadcast=True, persist=True, archive=archive)
                elif isinstance(value, list):
                    if isinstance(value[0], (bool, int, float, bytes)):
                        self.set_dataset(key2, value, broadcast=True, persist=True, archive=archive)
                    elif isinstance(value[0], str):
                        self.set_dataset(key2, [bytes(i, 'utf-8') for i in value], broadcast=True, persist=True, archive=archive)
                    else:
                        print('attempting to store dataset with list of type:', type(value[0]))
                        try:
                            self.set_dataset(key2, value, broadcast=True, persist=True, archive=archive)
                        except:
                            print('fail')
                else:
                    print('attempting to store dataset of type:', type(value))
                    try:
                        self.set_dataset(key2, value, broadcast=True, persist=True, archive=archive)
                    except:
                        print('fail')

    @kernel
    def DDS_setup(self, i):
        """
        Sets up one DDS channel based on passed in info
        :param i:  The index for the matching lists of DDS info created during build().
        :return:
        """

        delay_mu(10000)
        # name = self.DDS_name_list[i]
        channel = self.DDS_device_list[i]
        freq = self.DDS_freq_list[i]
        amp = self.DDS_amp_list[i]
        att = self.DDS_att_list[i]
        sw = self.DDS_sw_list[i]

        if not sw:
            channel.sw.off()


        delay_mu(41000)
        channel.set_att(att)
        delay_mu(4000)

        delay_mu(95000)
        channel.set(freq, amplitude=amp)
        delay_mu(6000)

        delay_mu(10000)

        if sw:
            channel.sw.on()

    def coreanalyzer_purge(self):
        get_analyzer_dump(self.core_ip_address)

    def coreanalyzer_write(self):
        with open('/home/monroe/Documents/github/artiq-experiments/rtio.vcd', "w") as f:
            decoded_dump_to_vcd(f, self.get_device_db(), decode_dump(get_analyzer_dump(self.core_ip_address)))


    def setup(self):

        # Store a list of DDS values, which are harder to access on the kernel.
        self.DDS_freq_list = [getattr(self, 'globals__DDS__' + name + '__frequency') for name in self.DDS_name_list]
        self.DDS_amp_list = [getattr(self, 'globals__DDS__' + name + '__amplitude') for name in self.DDS_name_list]
        self.DDS_att_list = [getattr(self, 'globals__DDS__' + name + '__attenuation') for name in self.DDS_name_list]
        self.DDS_sw_list = [getattr(self, 'globals__DDS__' + name + '__switch') for name in self.DDS_name_list]

        # Store a list of TTL values, which are harder to access on the kernel.
        self.TTL_output_sw_list = [getattr(self, 'globals__TTL_output__' + str(name, 'utf-8')) for name in self.globals__TTL_output__channel_names]

        # DAC #
        self.DAC_voltage_list = [getattr(self, 'globals__DAC__'+name) for name, channel, voltage_default in self.DAC_list]
        self.DAC_channel_list = [channel for name, channel, voltage_default in self.DAC_list]

        self.kernel_setup()

    @kernel
    def kernel_setup(self):

        self.core.reset()

        # DDS channels #

        delay_mu(86000)
        for i in range(len(self.DDS_device_list)):
            self.DDS_setup(i)

        # TTL outputs #

        for i in range(self.globals__TTL_output__num_channels):
            channel = self.TTL_output_channels[i]
            if self.TTL_output_sw_list[i]:
                channel.on()
            else:
                channel.off()

        # DAC #

        #self.core.break_realtime()
        delay_mu(1000000)
        self.zotino0.set_dac(self.DAC_voltage_list, self.DAC_channel_list)

    def run(self):
        # subclasses should override run_worker(), not run()
        self.write_globals_to_datasets()
        self.run_worker()
        self.write_globals_to_datasets(archive=True)

    def run_worker(self):
        # subclasses should override run_worker(), not run()
        pass