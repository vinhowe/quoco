import os
from datetime import datetime
from typing import List, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding.vi_state import InputMode

from perora.secure_term import secure_print, clear_term

import hashlib
import time

sha1 = hashlib.sha1()

_log_file_name = "log.txt"
_max_last_log_entries = 40


# TODO: Create an API for Vim-like prompts
def get_prompt_text() -> List[Tuple[str, str]]:
    input_mode_map = {
        InputMode.INSERT: ("bg:ansigreen fg:white bold", "[I]"),
        InputMode.NAVIGATION: ("bg:ansired fg:white bold", "[N]"),
        InputMode.REPLACE: ("bg:ansigreen fg:white bold", "[R]"),
        InputMode.INSERT_MULTIPLE: ("bg:ansigreen fg:white bold", "[II]"),
    }
    input_mode = input_mode_map[get_app().vi_state.input_mode]
    # Make escape key register instantly--this is hacky but I don't want to
    # make a full-fledged Prompt Toolkit Application until I absolutely have
    # to
    get_app().ttimeoutlen = 0
    # input_mode = 'I' if get_app().vi_state.input_mode == InputMode.INSERT
    return [
        input_mode,
        ("", " "),
        ("fg:ansibrightyellow bold", f"log: "),
    ]


def formatted_date(date: datetime = None):
    return (date if date else datetime.now()).strftime("%x")


def write_to_log(entry):
    now = datetime.now()
    formatted_time_now = now.strftime("%X")
    formatted_date_now = formatted_date(now)
    sum_line = f"{int(time.time())} {entry}"
    sha1.update(bytes(sum_line, "utf-8"))
    line = (
        f"{formatted_date_now} @ {formatted_time_now} .{sha1.hexdigest()}: {entry}\n"
    )
    with open(_log_file_name, "a") as log_file:
        log_file.write(line)


def format_log_line(line: str) -> str:
    # [:-1] removes endline char that messes up printing
    line = line[:-1]
    line_text = line.split(": ", maxsplit=1)[1]
    line_time_info = line[11:19]
    line_id = line[21:61]
    line_info = f"{line_time_info} ({line_id[:7]})"
    if line_text.startswith("#"):
        pound_count = len(line_text.split(" ", maxsplit=1)[0])
        # It's a comment, skip the timestamp
        formatted_line = f"{' ' * (len(line_info)-pound_count)} {line_text}"
    else:
        formatted_line = f"{line_info}: {line_text}"
    return formatted_line


def print_log_history(n_lines: int):
    if not os.path.exists(_log_file_name):
        return

    formatted_date_now = formatted_date()

    with open(_log_file_name, "r") as log_file:
        # Find all entries for today
        matching_lines: List[str] = [
            line for line in log_file.readlines() if line.startswith(formatted_date_now)
        ]
        if len(matching_lines) == 0:
            return
        max_last_entries = min(n_lines, len(matching_lines))
        # entries_with_plurality = "entry" if max_last_entries == 1 else "entries"
        # secure_print(
        #     f"last {max_last_entries} {entries_with_plurality} ({n_lines} max):"
        # )
        last_lines = matching_lines[-max_last_entries:]
        for line in last_lines:
            secure_print(format_log_line(line))


def main() -> None:
    prompt_session = PromptSession()
    # This seems necessary
    try:
        while True:
            secure_print()
            secure_print("perora attention log")
            secure_print()
            print_log_history(_max_last_log_entries)
            secure_print()
            entry: str = prompt_session.prompt(
                get_prompt_text, multiline=False, vi_mode=True
            )
            if entry is None:
                continue
            single_line_entry = entry.replace("\n", "").replace("\r", "").strip()

            if single_line_entry.lower() in ["q", "exit", "quit", ":q", "close"]:
                clear_term()
                exit()

            # Replace all spaces
            if single_line_entry.replace(" ", "").replace("\t", "") == "":
                continue

            write_to_log(single_line_entry)
            clear_term()
    except KeyboardInterrupt:
        # Hide nasty error
        clear_term()
        exit()


if __name__ == "__main__":
    main()
