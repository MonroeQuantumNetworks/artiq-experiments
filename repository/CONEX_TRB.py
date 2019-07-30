import time
import serial
import serial.tools.list_ports

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
            'FTZ7NHMR': ('TRB12CC_PN:B159480_UD:16071', 'lens_focus', 0, 0.000, 12),
            'FTZ7NMS4': ('TRB12CC_PN:B159486_UD:16071', 'lens_Y', -1, 0.000, 1),
            'FTZ7NHXU': ('TRB12CC_PN:B159482_UD:16071', 'lens_tilt_X', -1, 0.000, 1),
            'FT04S9W7': ('TRB12CC_PN:B161825_UD:16233', 'lens_tilt_Y', -1, 0.000, 1),
            'FT2NWUSQ': ('TRB25CC_PN:B188347_UD:18288', 'lens_X', -1, 0, 1),
            'FT2NGKOY': ('TRB25CC_PN:B188345_UD:18288', 'fiber_tilt_H', 0, 0, 25),
            'FT2FWBPV': ('TRB25CC_PN:B185321_UD:18255', 'fiber_H', 0, 0, 25),
            'FT2NUQ0P': ('TRB25CC_PN:B188349_UD:18288', 'fiber_V', 0, 0, 25),
            'FT2FW2TH': ('TRB25CC_PN:B185319_UD:18255', 'fiber_tilt_V', 0 ,0, 25),
            'FT2S568Q': ('TRB12CC_PN:B191291_UD:19013', 'fiber_focus', 0, 0, 12)
            }

        for port in serial.tools.list_ports.comports():
            if port.serial_number in axes:
                print(port.serial_number)
                read_ID = self.quick_command(port.device, '1ID?')
                record_ID = axes[port.serial_number][0]
                name = axes[port.serial_number][1]
                SL = axes[port.serial_number][2]
                SR = axes[port.serial_number][4]
                if read_ID != record_ID:
                    print('Read ID:', read_ID, ' does not match recorded ID:', record_ID)
                else:
                    print('matches:', name)
                    print('device:', port.device)
                    # create an object for this motor, add it to our motor dict
                    self.motors[name] = motor(name, port.serial_number, port.device, read_ID, SL, SR)
                print()

        return self.motors

    def close(self):
        for m in self.motors.values():
            m.close()

    def list_motor_limits(self):
        for m in self.motors.values():
            print(m.name, '\t', m.ID, m.command('1SL?'), m.command('1SR?'))

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

    def __init__(self, name, serial_number, device, ID, SL, SR):

        self.name = name
        self.serial_number = serial_number
        self.device = device
        self.ID = ID
        self.SL = SL
        self.SR = SR

        self.open()

    def open(self):
        # open serial connection to motor
        print('opening', self.name)
        self.ser = serial.Serial(self.device, baudrate=921600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1, xonxoff=True, write_timeout=1)
        # get status
        status = self.status()
        print('status:', status)
        unreferenced = ('0xa', '0xb', '0xc', '0xd', '0xe', '0xf', '0x10')
        ready = ('0x32', '0x33', '0x34')

        if status in unreferenced:
            print('State is NOT REFERENCED.  Homing:', self.command('1OR'))
            while not (status in ready):
                time.sleep(1)
                status = self.status()
                print(status, end=' ')
            print('ready')
        elif status in ready:
            print('ready')
        else:
            print('Failed to open ', self.name)

        if status in ready:
            print('absolute position: ', self.get_position())

            # set limits
            if self.SL > self.get_minimum():
                self.set_minimum(self.SL)
            if self.SR < self.get_maximum():
                self.set_maximum(self.SR)

    def close(self):
        self.ser.close()

    def command(self, command):
        self.ser.write((command + '\r\n').encode('utf-8'))
        # Read back response, but strip command echo, and strip whitespace at end
        return self.read()

    def command_noread(self, command):
        self.ser.write((command + '\r\n').encode('utf-8'))
        return

    def read(self):
        return self.ser.read_until('\r\n'.encode('utf-8')).decode('utf-8')[3:-2]

    def ID(self):
        return self.command('1ID?')

    def status(self):
        return hex(int(self.command('1TS?'), 16))

    def set_position(self, pos):
        print(self.name, 'setting position: {:f}'.format(pos), self.command_noread('1PA{:f}'.format(pos)))

    def get_position(self):
        return float(self.command('1PA?'))

    def get_minimum(self):
        return float(self.command('1SL?'))

    def set_minimum(self, value):
        self.command('1SL{:f}'.format(value))

    def get_maximum(self):
        return float(self.command('1SR?'))

    def set_maximum(self, value):
        self.command('1SR{:f}'.format(value))

    def get_all_motor_settings(name):
        print(self.name, 'config:')
        reads = []
        read = self.command('1ZT?')
        while read != '':
            reads.append(read)
            read = self.read()
        print(reads)
        return reads


