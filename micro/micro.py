import serial
from serial.tools.list_ports import comports


class MicroManager:
    def __init__(self):
        print(*self.scan(), sep='\n')

    @staticmethod
    def scan():
        return tuple(serial.Serial(usb.device, 115200) for usb in comports())


if __name__ == '__main__':
    MicroManager()