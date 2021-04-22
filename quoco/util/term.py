from typing import List


class Colors:
    """
    https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
    """

    WARNING = "\033[93m"
    SUPER_WARNING = "\033[91m"
    OKGREEN = "\033[92m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    INACTIVE = "\u001b[38;5;240m\u001b[2m"
    GROOVY = "\u001b[38;5;105m"
    ULTRA_GROOVY = "\u001b[38;5;51m"
    UNDERLINE = "\033[4m"


def terminal_format(to_format: str, format_options: List[str]):
    return "".join(["".join(format_options), to_format, Colors.ENDC])
