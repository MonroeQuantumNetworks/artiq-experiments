from artiq.experiment import *
from artiq.coredevice.exceptions import RTIOOverflow

# for motors
import serial
import serial.tools.list_ports

# for optimizer
import optimizer

class fiber_optimizer(EnvExperiment):

    def build(self):
        self.setattr_device("core")
        self.setattr_device("ttl0")

    @kernel
    def prep_kernel(self):
        self.core.reset()
        self.ttl0.input()

    def run(self):
        self.prep_kernel()

        # setup motors

        self.motor_helper = motor_helper()
        self.motors = self.motor_helper.open_motors()

        variable_names = ['lens_focus']
        initial_values = [self.motors[name].get_position() for name in variable_names]
        variable_min =   np.maximum(np.array([self.motors[name].get_minimum()  for name in variable_names]), initial_values-1.0)
        variable_max =   np.minimum(np.array([self.motors[name].get_maximum()  for name in variable_names]), initial_values+1.0)

        self.optimizer = optimizer.Optimizer('simplex', self.count, self.set_position, variable_names, initial_values, variable_min, variable_max)
        self.optimizer.simplex()

        self.motor_helper.close()

    @kernel
    def count(self):

        self.core.break_realtime()

        # get detector counts
        error = True
        while error:
            try:
                gate_end_mu = self.ttl0.gate_rising(100*ms)
                num_rising_edges = self.ttl0.count(gate_end_mu)
            except RTIOOverflow:
                print("RTIO input overflow, attenuate signal!")
                # drain counters
                num_rising_edges = 1
                while num_rising_edges != 0:
                    try:
                        num_rising_edges = self.ttl0.count(now_mu())
                    except RTIOOverflow:
                        pass
                        print("RTIO input overflow, attenuate signal!")
            else:
                error = False
                print('counts', num_rising_edges)
                return num_rising_edges

    @rpc(flags={"async"})
    def set_position(self, name, value):
        self.motors.set_position(name, value)


class motor_helper():

    def __init__(self):
        self.motors = {}

    def list_all_ports_and_data(self):
        # used when adding new motors to identify their USB serial numbers
        for port in serial.tools.list_ports.comports():
            print(port.device)
            print(port.name)
            print(port.description)
            print(port.hwid)
            print(port.vid)
            print(port.pid)
            print(port.serial_number)
            print(port.location)
            print(port.manufacturer)
            print(port.product)
            print(port.interface)
            print()

    def open_motors(self):
        # go through the USB ports and connect to known motors

        # list of known motors
        # key: USB serial, item: motor serial, motor name, motor left limit, motor base position, motor right limit
        axes = {
            'FTZ7NHMR': ('TRB12CC_PN:B159480_UD:16071', 'fiber_H', -3.5, 0.008, 8.5),
            'FTZ7NMS4': ('TRB12CC_PN:B159486_UD:16071', 'fiber_V', -4.0, 1.0, 8.0),
            'FTZ7NHXU': ('TRB12CC_PN:B159482_UD:16071', 'lens_tilt', -4.05, 0.0, 7.95),
            'FT04S9W7': ('TRB12CC_PN:B161825_UD:16233', 'lens_tip', -4.5, -0.048, 7.5),
            'FT2NWUSQ': ('TRB25CC_PN:B188347_UD:18288', 'lens_focus', 0, 0, 25)
            }
        #   '':         ('TRB12CC_PN:B161827_UD:16233', 'stuck1')}

        for port in serial.tools.list_ports.comports():
            if port.serial_number in axes:
                print(port.serial_number)
                read_ID = self.quick_command(port.device, '1ID?')
                record_ID = axes[port.serial_number][0]
                name = axes[port.serial_number][1]
                if read_ID != record_ID:
                    print('Read ID:', read_ID, ' does not match recorded ID:', record_ID)
                else:
                    print('matches:', name)
                    print('device:', port.device)
                    # create an object for this motor, add it to our motor dict
                    self.motors[name] = motor(name, port.serial_number, port.device, read_ID)
                print()

        return self.motors

    def close(self):
        for m in self.motors.values():
            m.close()

    def list_motor_limits(self):
        for m in self.motors.values():
            print(m.name, '\t', m.ID(), m.command('1SL?'), m.command('1SR?'))

    def get_positions(self):
        for m in self.motors.values():
            print('{} {:.5f}   '.format(m.name, m.get_position()), end='')

    def quick_command(self, device, command):
        # opens and closes a motor connection to execute one command
        with serial.Serial(device, baudrate=921600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1, xonxoff=True, write_timeout=1) as ser:
            ser.write((command + '\r\n').encode('utf-8'))
            # read input buffer, strip command echo, and strip whitespace at end
            return ser.read_until('\r\n'.encode('utf-8')).decode('utf-8')[3:-2]

class motor():

    def __init__(self, name, serial_number, device, ID):

        self.name = name
        self.serial_number = serial_number
        self.device = device
        self.ID = ID

        self.open()

    def open(self):
        # open serial connection to motor
        print('opening', self.name)
        self.ser = serial.Serial(self.device, baudrate=921600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1, xonxoff=True, write_timeout=1)
        # get status
        status = self.status()
        print('status:', status)
        if status in ('0A', '0B', '0C', '0D', '0E', '0F', '10'):
            print('State is NOT REFERENCED.  Homing:', self.command('1OR'))
            while not (status in ('32', '33', '34')):
                print(status, end=' ')
                time.sleep(1)
                status = self.status()
                print(status, end=' ')
                print(' home.')
                if (status in ('32', '33', '34')):
                    print('ready')
                    print('absolute position: ', self.get_position())
                else:
                    print('Unhandled status, not ready:', status)
                print()
            else:
                print('Failed to open ', self.name)

    def close(self):
        self.ser.close()

    def command(self, command):
        self.ser.write((command + '\r\n').encode('utf-8'))
        # Read back response, but strip command echo, and strip whitespace at end
        return self.read()

    def read(self):
        return self.ser.read_until('\r\n'.encode('utf-8')).decode('utf-8')[3:-2]

    def ID(self):
        return self.command('1ID?')

    def status(self):
        return self.command('1TS?')

    def set_position(self, pos):
        print(self.name, 'setting position:', self.command('1PA{:f}'.format(pos)))

    def get_position(self):
        return float(self.command('1PA?'))

    def get_minimum(self):
        return float(self.command('1SL?'))

    def get_maximum(self):
        return float(self.command('1SR?'))

    def get_all_motor_settings(name):
        print(self.name, 'config:')
        reads = []
        read = self.command('1ZT?')
        while read != '':
            reads.append(read)
            read = self.read()
        print(reads)
        return reads


