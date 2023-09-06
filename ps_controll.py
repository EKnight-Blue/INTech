from controller import Controller
import controller.constants as c_cst
from micro import Order, MicroManager
import micro.consts as m_cst


class RobotController(Controller, MicroManager):
    def __init__(self):
        Controller.__init__(self)
        MicroManager.__init__(self)

    def mainloop(self):
        self.start()
        try:
            while True:
                for event in self.get_events():
                    pass
        except KeyboardInterrupt:
            print("Closing")
        self.terminate()


if __name__ == '__main__':
    c = Controller()
    c.start()
    try:
        while True:
            for ev in c.get_events():
                print(ev)
    except KeyboardInterrupt:
        c.terminate()
