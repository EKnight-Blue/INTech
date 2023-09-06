from controller import Controller
import controller.constants as c_cst
from micro import Order, MicroManager
import micro.consts as m_cst
import time


class RobotController(Controller, MicroManager):
    send_arc = False

    def __init__(self):
        Controller.__init__(self)
        MicroManager.__init__(self)
        self.dist_incr = self.dir_incr = 0

    def do_nothing(self, event):
        pass

    def joy_ly(self, event):
        self.dist_incr = event.value
        self.send_arc = True

    def joy_rx(self, event):
        self.dir_incr = event.value // 2
        self.send_arc = True

    mapping = {
        (c_cst.ANALOG, c_cst.LY): 'joy_ly',
        (c_cst.ANALOG, c_cst.RX): 'joy_rx'
    }

    def mainloop(self):
        self.start()
        try:
            while True:
                for event in self.get_events():
                    getattr(self, self.mapping.get((event.type, event.button), 'do_nothing'))(event)
                if self.send_arc:
                    self.send_order(m_cst.MOTION_UC, Order.to_bytes(
                        m_cst.ARC, m_cst.INCR,
                        arg1=Order.unsigned_short(self.dir_incr),
                        arg2=Order.unsigned_short(self.dist_incr)
                    ))
                date = time.perf_counter()
                while time.perf_counter() - date < 0.05:
                    self.receive()
        except KeyboardInterrupt:
            print("Closing")
        self.terminate()


if __name__ == '__main__':
    RobotController().mainloop()
