CSI, FORMATTER = '\x1b[', '{}'

HIDE, SHOW, ERASE, CLEAR = f'{CSI}?25l', f'{CSI}?25h', f'{CSI}K', f'{CSI}0J'

CURSOR_COUNTDOWN_LENGTH, DRAW_TIMER = 8, .05

red, green, yellow, blue = (
    (lambda t: f'{CSI}91m{t}{CSI}0m'),
    (lambda t: f'{CSI}92m{t}{CSI}0m'),
    (lambda t: f'{CSI}93m{t}{CSI}0m'),
    (lambda t: f'{CSI}94m{t}{CSI}0m')
)

up, right = (
    (lambda n: f'{CSI}{n}A' if n else ""),
    (lambda n: f'{CSI}{n}C' if n else "")
)


def special_len(string: str):
    parts = string.split(CSI)[1:]
    res = len(string) - 2 * len(parts) - string.count('{{') - string.count('}}')
    for part in parts:
        res -= part.index('m') + 1
    return res
