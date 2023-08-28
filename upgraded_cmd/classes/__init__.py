from upgraded_cmd.classes.prompt import AnimatedPrompt, BasePrompt, SimplePrompt
from upgraded_cmd.classes.entry import Entry, new_command, add_completion, MetaCMD
from upgraded_cmd.classes.cmd import CMD


class SimpleCmd(CMD):
    def __init__(self):
        CMD.__init__(self, SimplePrompt(' > '))
