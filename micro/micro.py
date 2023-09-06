import serial
import time
import struct
from serial.tools.list_ports import comports
import sys
import os
from micro.consts import *

if sys.platform == 'win32':
    os.system('color')


class Order:
    @staticmethod
    def to_bytes(id_, comp, *, arg=None, arg1=None, arg2=None, f_arg=None):
        if f_arg is not None:
            return int.to_bytes((id_ << 4) | comp, 1, 'big') + struct.pack('!f', f_arg)
        if arg is None:
            if arg1 is None or arg2 is None:
                raise ValueError("Incomplete order")
            arg = (arg1 << 16) | arg2
        return int.to_bytes((((id_ << 4) | comp) << 32) | arg, 5, 'big')

    @staticmethod
    def read(message: bytes):
        if message is None:
            return
        arg1, arg2 = (message[1] << 8) | message[2], (message[3] << 8) | message[4]
        return message[0] >> 4, message[0] & 0xf, {
            'arg1': arg1,
            'arg2': arg2,
            'arg': (arg1 << 16) | arg2,
            'f_arg': struct.unpack('!f', message[1:])[0]
        }

    @staticmethod
    def is_complete(id_, comp, arg, arg1, arg2, f_arg):
        return (id_ is not None) and (comp is not None) and (
            (arg is not None) or (f_arg is not None) or ((arg1 is not None) and (arg2 is not None))
        )

    @staticmethod
    def unsigned_short(value):
        value = int(value)
        return value + 0x10000 * (value < 0)

    @staticmethod
    def unsigned_int(value):
        value = int(value)
        return value + 0x100000000 * (value < 0)

    @staticmethod
    def signed_short(value):
        value = int(value)
        return value - 0x10000 * (value > 0x7fff)

    @staticmethod
    def signed_int(value):
        value = int(value)
        return value - 0x100000000 * (value > 0x7fffffff)


class Micro:
    id_ = 0

    def __init__(self, s: serial.Serial, manager):
        self.serial_connection = s
        self.manager = manager
        self.variables = [None] * 16

    def receive(self):
        if self.serial_connection.in_waiting < 5:
            return
        return self.serial_connection.read(5)

    def send(self, message: bytes):
        self.serial_connection.write(message)

    def pre_sync(self):
        self.serial_connection.write(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')

    def clear(self):
        self.serial_connection.read(self.serial_connection.in_waiting)

    def sync(self):
        self.pre_sync()
        time.sleep(1.)
        self.clear()

    def acknowledge(self, id_, comp, arg=None, arg1=None, arg2=None, f_arg=None):
        print(f'ACK {ORDER_NAMES[comp]}')

    def identify(self, id_, comp, arg=None, arg1=None, arg2=None, f_arg=None):
        self.id_ = comp

    def terminate(self, id_, comp, arg=None, arg1=None, arg2=None, f_arg=None):
        self.manager.waiting &= comp != self.manager.waited_id

    def variable(self, id_, comp, arg=None, arg1=None, arg2=None, f_arg=None):
        self.variables[comp] = f_arg
        print(f'{VARIABLE_NAMES[comp]} = {f_arg}')

    def track_error(self, id_, comp, arg=None, arg1=None, arg2=None, f_arg=None):
        self.manager.dir_errors[:] = (*self.manager.dir_errors[-3999:], Order.signed_short(arg1))
        self.manager.dist_errors[:] = (*self.manager.dist_errors[-3999:], Order.signed_short(arg2))

    def read_feedback(self, message: bytes):
        id_, comp, args = Order.read(message)
        if id_ >= len(FEEDBACK_CALLBACKS):
            return
        getattr(self, FEEDBACK_CALLBACKS[id_])(id_, comp, **args)


class MicroManager:
    log_method = print
    micro_class = Micro
    waiting, waited_id = False, None
    track = False

    def __init__(self):
        self.dir_errors, self.dist_errors = [], []
        self.usb_connections = self.reset()

    def reset(self):
        usb_connections = tuple(self.micro_class(usb, self) for usb in self.scan())
        # send sync string
        for usb in usb_connections:
            usb.pre_sync()
        time.sleep(1.)

        message = Order.to_bytes(0, 0, arg=0)
        for usb in usb_connections:
            # clear buffers
            usb.clear()
            # ask for identification
            usb.send(message)

        date = time.perf_counter()
        while time.perf_counter() - date < 5. and any(not usb.id_ for usb in usb_connections):
            for usb in usb_connections:
                if (message := usb.receive()) is not None:
                    usb.read_feedback(message)
        return tuple(usb for usb in usb_connections if usb.id_)

    @staticmethod
    def scan():
        return tuple(serial.Serial(usb.device, 115200, writeTimeout=0) for usb in comports() if 'AMA' not in usb.device)

    def receive(self):
        for usb in self.usb_connections:
            if (message := usb.receive()) is not None:
                # print(message, list(message))
                usb.read_feedback(message)

    def send_order(self, target, message: bytes):
        # print(message, tuple(message))
        for usb in self.usb_connections:
            if usb.id_ == target or target is None:
                usb.send(message)

    def wait(self, order_id):
        try:
            self.waiting, self.waited_id = True, order_id
            while self.waiting:
                self.receive()
        except KeyboardInterrupt:
            self.waiting = False


if __name__ == '__main__':
    MicroManager()
