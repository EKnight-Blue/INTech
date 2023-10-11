from controller import Controller
import controller.constants as c_cst
from micro import Order, MicroManager
import micro.consts as m_cst
import time
import os


class RobotController(Controller, MicroManager):
    send_arc = running = False

    def __init__(self):
        Controller.__init__(self)
        MicroManager.__init__(self)
        self.dist_incr = self.dir_incr = 0

    def do_nothing(self, event):
        pass

    def joy_ly(self, event):
        self.dist_incr = -event.value
        self.send_arc = True

    def joy_rx(self, event):
        self.dir_incr = -event.value // 4 
        self.send_arc = True

    def options(self, event):
        self.running = False

    mapping = {
        (c_cst.ANALOG, c_cst.LY): 'joy_ly',
        (c_cst.ANALOG, c_cst.RX): 'joy_rx',
        (c_cst.DIGITAL, c_cst.OPTIONS): 'options'
    }

    def mainloop(self):
        self.start()
        self.running = True
        while self.running and self.is_alive():
            for event in self.get_events():
                getattr(self, self.mapping.get((event.type, event.button), 'do_nothing'))(event)
            if self.send_arc:
                print(f'sent {self.dist_incr = }; {self.dir_incr = }')
                if not self.dir_incr and not self.dist_incr:
                    self.send_order(m_cst.MOTION_UC, Order.to_bytes(m_cst.RAW_MOVE, 0, arg=0))
                else:
                    self.send_order(m_cst.MOTION_UC, Order.to_bytes(
                        m_cst.ARC, m_cst.DEFINED,
                        arg2=Order.unsigned_short(self.dist_incr),
                        arg1=Order.unsigned_short(self.dir_incr)
                    ))
                # self.send_order(m_cst.MOTION_UC, Order.to_bytes(
                #     m_cst.RAW_MOVE, 0,
                #     arg1=Order.unsigned_short((self.dist_incr - self.dir_incr) // 2),
                #     arg2=Order.unsigned_short((self.dist_incr + self.dir_incr) // 2)
                # ))
            self.send_arc = False
            date = time.perf_counter()
            while time.perf_counter() - date < 0.05:
                self.receive()

        self.send_order(m_cst.MOTION_UC, Order.to_bytes(m_cst.RAW_MOVE, 0, arg=0))
        date = time.perf_counter()
        while time.perf_counter() - date < 1:
            self.receive()
        self.terminate()


if __name__ == '__main__':
    while True:
        try:
            while not os.path.exists('/dev/input/js0') or not os.path.exists('/dev/input/mouse0'):
                continue
        except KeyboardInterrupt:
            break
        r = RobotController()
        try:
            r.mainloop()
        except KeyboardInterrupt:
            r.terminate()
