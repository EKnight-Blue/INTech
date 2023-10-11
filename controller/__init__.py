from multiprocessing import Process, SimpleQueue
from controller.controller_classes import ControllerButtons, ControllerMouse


class Controller:
    """
    Tool to get events from a ps4 controller, works on UNIX
    """
    
    def __init__(self, joystick_file='/dev/input/js0', mouse_file='/dev/input/mouse0'):
        self.queue = SimpleQueue()
        self.controllerButtonsProcess = Process(target=ControllerButtons(self.queue, joystick_file).mainloop)
        self.controllerMouseProcess = Process(target=ControllerMouse(self.queue, mouse_file).mainloop)

    def get_events(self):
        while not self.queue.empty():
            yield self.queue.get()

    def start(self):
        self.controllerButtonsProcess.start()
        self.controllerMouseProcess.start()

    def terminate(self):
        self.controllerMouseProcess.terminate()
        self.controllerButtonsProcess.terminate()


if __name__ == '__main__':
    print("Creating controller")
    c = Controller()
    print("Controller created")
    c.start()
    print("Now listening")
    try:
        print('Listen')
        for ev in c.get_events():
            print("Got an event")
            print(ev)
        print('Ended')
    except KeyboardInterrupt:
        c.terminate()
