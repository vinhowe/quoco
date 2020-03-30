lines_written = 0


def clear_term() -> None:
    global lines_written
    if lines_written == 0:
        return
    print(f"\u001b[{lines_written}A", end="")
    print("\u001b[0J", end="")
    lines_written = 0


def secure_print(*args, sep=" ", end="\n") -> None:
    print(*args, sep=sep, end=end)
    new_lines = end.count("\n")
    for arg in args:
        if arg is str:
            new_lines += arg.count("\n")

    add_lines(new_lines)


def secure_input(prompt: str) -> str:
    add_lines(1 + prompt.count("\n"))
    return input(prompt)


def add_lines(lines=1) -> None:
    global lines_written
    lines_written += lines
