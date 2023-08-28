from upgraded_cmd.constants import *


class BasePrompt:
    pre_display, old_line_prompt, cursor, cursor_cd = '', FORMATTER, True, CURSOR_COUNTDOWN_LENGTH

    def display_cursor(self):
        # decrease countdown
        self.cursor_cd -= 1
        # update cursor visibility
        self.cursor, res, self.cursor_cd = (
            self.cursor ^ (not self.cursor_cd),
            (HIDE, SHOW)[not self.cursor] * (not self.cursor_cd),
            self.cursor_cd + CURSOR_COUNTDOWN_LENGTH * (not self.cursor_cd)
        )
        return res

    def display(self, text: str, index: int):
        print(f'{self.pre_display}{self.get_prompt().format(text)}{self.display_cursor()}{right(index)}', end='')

    def display_old_line(self, text):
        print(f'{self.pre_display}{self.old_line_prompt.format(text)}')
        self.pre_display = ''

    @classmethod
    def instructions(cls, prompt: str):
        lines, y = prompt.split('\n'), len(prompt.split(FORMATTER)[1].split('\n')) - 1
        x = special_len(lines[-1-y][:lines[-1-y].index(FORMATTER)])
        # replace cursor on the text,  get_back to the starting point to clear
        return f'\r{up(y)}{right(x)}', f'\r{up(len(lines) - 1 - y)}{CLEAR}'

    def get_prompt(self) -> str:
        return FORMATTER


class AnimatedPrompt(BasePrompt):
    state = 0

    def __init__(self, prompts, old_line_prompt):
        *self.prompts, self.old_line_prompt = tuple(
            p + FORMATTER * (FORMATTER not in p) for p in prompts + (old_line_prompt,)
        )
        self.instr = tuple(self.instructions(p) for p in self.prompts)

    def display(self, text: str, index: int):
        BasePrompt.display(self, text, index)
        self.pre_display = self.instr[self.state][1]
        self.state = (self.state + 1) % len(self.prompts)

    def get_prompt(self) -> str:
        return self.prompts[self.state] + self.instr[self.state][0]


class SimplePrompt(BasePrompt):
    def __init__(self, prompt):
        self.old_line_prompt = self.prompt = prompt + (FORMATTER if FORMATTER not in prompt else '')
        self.instr = self.instructions(self.prompt)

    def display(self, text: str, index: int):
        BasePrompt.display(self, text, index)
        self.pre_display = self.instr[1]

    def get_prompt(self) -> str:
        return self.prompt + self.instr[0]
