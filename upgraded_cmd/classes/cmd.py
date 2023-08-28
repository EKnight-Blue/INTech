import asyncio
import os
from upgraded_cmd.classes.entry import Entry, new_command, add_completion
from upgraded_cmd.constants import SHOW


@new_command('help')
def _(self: Entry, *args):
    """help\nShows all available commands\n\nhelp <command>\nShows <command> description if available"""
    if len(args) > 1:
        return print("Expected at most 1 argument")
    if not args:
        return print("Command list :", *self.commands, sep='\n')
    comm, = args
    if comm not in self.commands:
        return print(f"Unknown command {comm}")
    doc = self.commands[comm].__doc__
    print("No documentation available" if doc is None else doc)


@add_completion('help')
def _(self: Entry, args):
    if len(args) > 1:
        return ()
    return (comm for comm in self.commands if comm.startswith(args[0]))


@new_command('exit')
def _(self: Entry, *args):
    """exit\nCloses the app"""
    self.running = False


class CMD(Entry):

    def __init__(self, prompt):
        os.system('color')
        Entry.__init__(self)
        self.prompt = prompt

    async def display_loop(self):
        while self.running:
            self.prompt.display(self.text, self.index)
            await asyncio.sleep(.05)
        if self.text:
            self.prompt.display_old_line(self.text + SHOW)
        else:
            print(self.prompt.pre_display, end=SHOW)

    async def main_loop(self):
        await asyncio.gather(self.display_loop(), self.read_loop())

    def run(self):
        asyncio.run(self.main_loop())

    def k_return(self):
        self.prompt.display_old_line(self.text)
        Entry.k_return(self)

