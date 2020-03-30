import os
from datetime import datetime
from typing import List, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding.vi_state import InputMode

from log.secure_term import secure_print, add_lines, clear_term

_log_file_name = "log.txt"
_max_last_log_entries = 20


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
        ("fg:ansibrightcyan bold", f"log: "),
    ]


def formatted_date(date: datetime = None):
    return (date if date else datetime.now()).strftime("%x")


def write_to_log(entry):
    now = datetime.now()
    formatted_time_now = now.strftime("%X")
    formatted_date_now = formatted_date(now)
    line = f'{formatted_date_now} @ {formatted_time_now}: {entry}\n'
    with open(_log_file_name, "a") as log_file:
        log_file.write(line)
    secure_print(f'"{entry}" at {formatted_time_now} on {formatted_date_now}')


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
        entries_with_plurality = "entry" if max_last_entries == 1 else "entries"
        secure_print(
            f"last {max_last_entries} {entries_with_plurality} ({n_lines} max):"
        )
        add_lines()
        last_lines = matching_lines[-max_last_entries:]
        for line in last_lines:
            # Remove extra endline on the end
            secure_print(line[:-1])


def main() -> None:
    prompt_session = PromptSession()
    try:
        while True:
            print_log_history(_max_last_log_entries)
            entry: str = prompt_session.prompt(
                get_prompt_text, multiline=False, vi_mode=True
            )
            if entry is None:
                continue
            single_line_entry = entry.replace("\n", "").replace("\r", "").strip()

            if single_line_entry.lower() in ["q", "exit", "quit", ":q", "close"]:
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
