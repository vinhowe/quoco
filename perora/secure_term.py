lines_written = 0


def clear_term() -> None:
    global lines_written
    print(f"\u001b[{lines_written}A", end='')
    print("\u001b[0J", end='')
    lines_written = 0


def secure_print(*args, sep=' ', end='') -> None:
    if len(end) == 0:
        print(*args, sep)
    else:
        print(*args, sep, end)
    new_lines = 1
    for arg in args:
        if arg is str:
            new_lines += arg.count("/n")

    add_lines(new_lines)


def add_lines(lines=1) -> None:
    global lines_written
    lines_written += lines
