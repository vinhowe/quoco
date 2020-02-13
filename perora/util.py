from typing import List


class Colors:
    """
    https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
    """
    WARNING = '\033[93m'
    SUPER_WARNING = '\033[91m'
    OKGREEN = '\033[92m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    INACTIVE = '\u001b[38;5;234m'
    GROOVY = '\u001b[38;5;135m'
    UNDERLINE = '\033[4m'


def terminal_format(to_format: str, format_options: List[str]):
    return "".join(["".join(format_options), to_format, Colors.ENDC])
