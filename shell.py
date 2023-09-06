import cmd
from micro import *
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json

def is_flag(string: str):
    if not string.startswith('-'):
        return False
    string = string[1:]
    if string.count('.') < 2 and all(x.isdigit() for x in string.split('.')):
        return False
    return True


def parse_arg_kwargs(args: list[str], types: tuple, flags: dict):
    iterator, arguments, kw_arguments = iter(args), [], {}
    while True:
        try:
            current = next(iterator)
        except StopIteration:
            break
        if is_flag(current):
            flag = current[1:]
            if flag not in flags:
                return print(f'Unknown flag {flag}')
            if flags[flag] is bool:
                kw_arguments[flag] = True
                continue
            try:
                arg = next(iterator)
            except StopIteration:
                return print(f'Missing argument for {flag}')
            try:
                kw_arguments[flag] = flags[flag](arg)
                continue
            except ValueError as e:
                return print(f'Invalid argument ({arg}) for {flag}, {e}')
        try:
            arguments.append(types[len(arguments)](current))
        except ValueError as e:
            return print(f'Invalid argument {current}, {e}')
        except IndexError:
            return print(f'Too many arguments, expected {len(types)}')
    if len(arguments) != len(types):
        return print(f'Expected {len(types)} arguments got {len(arguments)} instead')
    return arguments, kw_arguments


def parse(*types, **flags):
    def decor(func):
        def result(self: BaseShell, line: str):
            res = parse_arg_kwargs(line.split(), types, flags)
            if res is None:
                return
            return func(self, *res[0], **res[1])

        result.__name__ = func.__name__
        return result
    return decor


class BaseShell(MicroManager):

    def wait_track(self):
        self.send_order(MOTION_UC, Order.to_bytes(TRACK_ERROR, 0, arg=0))
        fig, ax = plt.figure(), plt.axes(xlim=(-20., 0), ylim=(-500, 500))
        dist_line, = ax.plot([], [], label='distance error')
        dir_line, = ax.plot([], [], label='direction error')
        plt.plot((-20., 0), (0, 0), 'r--')
        plt.legend()

        def animate(_):
            dist_line.set_data([x * -0.005 for x in range(len(self.dist_errors)-1, -1, -1)], self.dist_errors)
            dir_line.set_data([x * -0.005 for x in range(len(self.dir_errors)-1, -1, -1)], self.dir_errors)
            # if self.dist_errors or self.dir_errors:
            #     x = max(self.dist_errors + self.dir_errors, key=abs)
            #     ax.set_ylim(-abs(x), abs(x))
            date = time.perf_counter()
            while time.perf_counter() - date < 0.05:
                self.receive()
            return dist_line, dir_line

        _ = FuncAnimation(fig, animate, interval=50, blit=True, save_count=5)
        plt.show()

        self.send_order(MOTION_UC, Order.to_bytes(TRACK_ERROR, 0, arg=0))

        while self.dist_errors or self.dir_errors:
            self.dist_errors = []
            self.dir_errors = []
            date = time.perf_counter()
            while time.perf_counter() - date < 0.05:
                self.receive()


cmds = {'__init__': lambda self: (BaseShell.__init__(self), cmd.Cmd.__init__(self))[0]}


def command(func):
    cmds[f'do_{func.__name__.strip("_")}'] = func
    return func


@command
@parse(
    int, int,
    arg=int, s_arg=Order.unsigned_int,
    arg1=int, s_arg1=Order.unsigned_short,
    arg2=int, s_arg2=Order.unsigned_short,
    f_arg=float
)
def order(self: BaseShell, id_, comp, arg=None, s_arg=None, arg1=None, arg2=None, f_arg=None, s_arg1=None, s_arg2=None):
    arg, arg1, arg2 = (
        arg if s_arg is None else s_arg, arg1 if s_arg1 is None else s_arg1, arg2 if s_arg2 is None else s_arg2
    )
    self.send_order(None, Order.to_bytes(id_, comp, arg=arg, arg1=arg1, arg2=arg2, f_arg=f_arg))


@command
@parse()
def stop(self: BaseShell):
    self.send_order(MOTION_UC, Order.to_bytes(RAW_MOVE, 0, arg=0))


@command
@parse()
def resume(self: BaseShell):
    self.send_order(MOTION_UC, Order.to_bytes(RAW_MOVE, 0xf, arg=0))


@command
@parse()
def reset(self: BaseShell):
    for usb in self.usb_connections:
        usb.serial_connection.close()
    self.usb_connections = self.reset()
    print(len(self.usb_connections))
    for usb in self.usb_connections:
        print(usb.serial_connection.port)


@command
@parse(Order.signed_short, Order.signed_short, time=bool, dist=bool, dire=bool, ali=bool)
def raw(self: BaseShell, left, right, timer=False, dist=False, dire=False, ali=False):
    self.send_order(MOTION_UC, Order.to_bytes(RAW_MOVE,  8 * timer + 4 * dist + 2 * dire + ali, arg1=left, arg2=right))


def name_to_int(string: str):
    return VARIABLE_NAMES.index(string)


@command
@parse(name_to_int)
def get(self: BaseShell, variable):
    self.send_order(None, Order.to_bytes(GET_VAR, variable, arg=0))
    self.wait(GET_VAR)


@command
@parse(name_to_int, float)
def _set(self: BaseShell, variable, value):
    self.send_order(None, Order.to_bytes(SET_VAR, variable, f_arg=value))
    self.wait(SET_VAR)


@command
@parse(Order.unsigned_short, Order.unsigned_short, append=bool)
def arc(self: BaseShell, distance, direction, append=False):
    self.send_order(MOTION_UC, Order.to_bytes(ARC, append, arg1=direction, arg2=distance))
    if self.track:
        self.wait_track()


@command
@parse()
def track(self: BaseShell):
    self.track = not self.track


@command
@parse()
def show(self: BaseShell):
    for var in range(len(VARIABLE_NAMES)):
        self.send_order(None, Order.to_bytes(GET_VAR, var, arg=0))
        self.wait(GET_VAR)


@command
@parse(str)
def save(self: BaseShell, file_name):
    for var in range(len(VARIABLE_NAMES)):
        self.send_order(None, Order.to_bytes(GET_VAR, var, arg=0))
        self.wait(GET_VAR)
    with open(f'{file_name}.json', 'w') as f:
        json.dump({usb.id_: usb.variables for usb in self.usb_connections}, f)


@command
@parse(str)
def load(self: BaseShell, file_name):
    with open(f'{file_name}.json', 'r') as f:
        data: dict = json.load(f)
    for key, var_list in data.items():
        for var_i, value in enumerate(var_list):
            if value is not None:
                self.send_order(int(key), Order.to_bytes(SET_VAR, var_i, f_arg=value))
                self.wait(SET_VAR)


@command
@parse(s=bool)
def _exit(self, s=False):
    if s:
        save(self, 'default')
    return 1


Shell = type('Shell', (BaseShell, cmd.Cmd), cmds)

if __name__ == '__main__':
    Shell().cmdloop()