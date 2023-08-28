import sys
import asyncio
if sys.platform != 'win32':
    raise ImportError('I only run on windows')
from msvcrt import getch


class Node:
    tag: bytes

    def process(self, entry, string: bytes, entire_string: bytes):
        return True


class Trie(Node):
    def __init__(self, tag, *children, default=Node()):
        self.tag, self.children, self.default = tag, {c: child for child in children for c in child.tag}, default

    def process(self, entry, string: bytes, entire_string: bytes):
        if not string:
            return False  # wait for more bytes
        if string[0] in self.children:
            return self.children[string[0]].process(entry, string[1:], entire_string)
        return self.default.process(entry, string, entire_string)


class Leaf(Node):
    def __init__(self, tag, func):
        self.tag, self.func = tag, func

    def process(self, entry, string: bytes, entire_string: bytes):
        getattr(entry, self.func)()
        return True


class TryDecodeChar(Node):
    tag = b''

    def process(self, entry, string: bytes, entire_string: bytes):
        if not (32 <= string[0] < 127):
            return True
        try:
            s = string.decode()
            entry.append_char(s)
        except UnicodeDecodeError:
            pass
        return True


SPECIAL_CHARS = Trie(
    b'\x00\xe0',
    Leaf(b'H', 'k_up'), Leaf(b'M', 'k_right'), Leaf(b'K', 'k_left'), Leaf(b'P', 'k_down'), Leaf(b'S', 'k_sup')
    # default=TryDecodeChar()
)

TAB, BACKSPACE, RETURN = Leaf(b'\t', 'k_tab'), Leaf(b'\x08', 'k_backspace'), Leaf(b'\r\n', 'k_return')
GLOBAL_TRIE = Trie(
    b'',
    TAB, BACKSPACE, RETURN,
    SPECIAL_CHARS,
    default=TryDecodeChar()
)


class MetaCMD(type):
    commands, complete = {}, {}
    meta_attr = 'Blue'

    def __new__(cls, name, bases, dic: dict):
        commands = {
            name: value for base in bases if hasattr(base, 'commands') for name, value in base.commands.items()
        } | cls.commands | dic.get('commands', {})
        complete = {
            name: value for base in bases if hasattr(base, 'complete') for name, value in base.complete.items()
        } | cls.complete | dic.get('complete', {})
        cls.commands, cls.complete = {}, {}
        return type.__new__(cls, name, bases, dic | {'commands': commands, 'complete': complete})


def new_command(name):
    def decor(func):
        MetaCMD.commands[name] = func
        return func
    return decor


def add_completion(name):
    def decor(func):
        MetaCMD.complete[name] = func
        return func
    return decor


class Entry(metaclass=MetaCMD):
    running, text, old_text, index, history_index = True, '', '', 0, -1
    cycling_index, cycle, old_word = -1, None, ''

    def __init__(self):
        self.history = list()

    def k_sup(self):
        self.text = self.text[:self.index] + self.text[self.index + 1:]

    def k_return(self):
        self.old_word, self.cycle, self.cycling_index = '', None, -1
        if not self.text:
            return

        if self.text in self.history:
            self.history.remove(self.text)
        self.history.insert(0, self.text)

        _command, *words = self.text.split()
        self.text, self.index, self.history_index = '', 0, -1

        if _command not in self.commands:
            return print(f'Unknown command {_command}')
        self.commands[_command](self, *words)
        self.reset_cycle()

    def k_backspace(self):
        if not self.index:
            return
        self.text, self.index = self.text[:self.index - 1] + self.text[self.index:], self.index - 1
        self.reset_cycle()

    def reset_history(self):
        self.history_index, self.old_text = -1, 0

    def reset_cycle(self):
        self.old_word, self.cycle, self.cycling_index = '', None, -1

    def compute_cycle(self):
        if self.cycle is not None:
            return self.cycle
        text = self.text[:self.index]
        words, new_word = text.split(), not text.split(' ')[-1]
        if not words or (len(words) == 1 and not new_word):
            word = words[-1] if words else ''
            return sorted(command for command in self.commands if command.startswith(word))
        command, args = words[0], (*words[1:], *(('',) if new_word else ()))
        if command not in self.complete:
            return ()
        return sorted(self.complete[command](self, args))

    def append_char(self, char: str):
        self.index, self.text = self.index + len(char), f'{self.text[:self.index]}{char}{self.text[self.index:]}'
        self.reset_cycle()

    def k_tab(self):
        self.cycle = self.compute_cycle()
        if not self.cycle:
            return
        text = self.text[:self.index]
        words, new_word = text.split(), not text.split(' ')[-1]
        words += [''] * new_word

        if self.cycling_index == -1:
            self.old_word = words[-1]
        self.cycling_index = (self.cycling_index + 2) % (len(self.cycle) + 1) - 1

        new_words = words[:-1] + [self.old_word if self.cycling_index == -1 else self.cycle[self.cycling_index]]
        self.text = ' '.join(new_words)
        self.index = len(self.text)

    def k_up(self):
        if not self.history:
            return
        if self.history_index == -1:
            self.old_text = self.text
        self.history_index += self.history_index < len(self.history) - 1
        self.text = self.history[self.history_index]
        self.index = len(self.text)
        self.reset_cycle()

    def k_down(self):
        if not self.history:
            return
        self.history_index -= 1
        if self.history_index > -1:
            self.text = self.history[self.history_index]
            self.index = len(self.text)
            return
        self.text, self.history_index = self.old_text if self.history_index == -1 else self.text, -1
        self.index = len(self.text)

    def k_right(self):
        self.index += self.index < len(self.text)
        self.reset_cycle()

    def k_left(self):
        self.index -= not not self.index
        self.reset_cycle()

    @staticmethod
    async def get_char():
        return await asyncio.to_thread(getch)

    def process(self, string: bytes):
        return GLOBAL_TRIE.process(self, string, string)

    async def read_loop(self):
        string = b''
        # quit on ctrl-c
        while self.running and (char := await self.get_char()) != b'\x03':
            string += char
            if self.process(string):
                string = b''
        self.running = False


if __name__ == '__main__':
    print(type(Entry), Entry.meta_attr)
