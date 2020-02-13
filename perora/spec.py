#!/usr/bin/env python3.7
import json
from datetime import datetime, timedelta
from typing import List

import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import (
    NestedCompleter,
    FuzzyWordCompleter,
    FuzzyCompleter,
)
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding.vi_state import InputMode

from perora.document_manager import (
    password_prompt,
    write_document,
    edit_document,
    delete_document,
    rename_document,
    edit_documents,
)
from perora.fs_util import _data_path, _per_ext_file, file_exists
from perora.secure_fs_io import (
    _read_decrypt_file,
    _write_encrypt_file,
)
from perora.secure_term import secure_print, add_lines, clear_term
from perora.util import Colors, terminal_format

spec_service_name = "spec"
data_file_name = "data"
due_dates_file_name = "due_dates"
reminder_config_file_name = "reminder_config"
data_file_path = _data_path(spec_service_name, _per_ext_file(data_file_name))
due_map_file_path = _data_path(spec_service_name, f"{due_dates_file_name}.json")
reminder_config_file_path = f"{reminder_config_file_name}.json"

node_marker = "\000node"

data = {}
key = None
catalog = {}
inactive_after_days = 6
notify_days_ahead = 3

longest_item_length = 0
due_info_padding = 30


def attach_to_tree(path, value, trunk):
    parts = path.split("/", 1)
    if len(parts) == 1:
        value = {**value, node_marker: True}
        trunk[parts[0]] = value
    else:
        node, others = parts
        if node not in trunk:
            trunk[node] = {}
        attach_to_tree(others, value, trunk[node])


def remove_outside_char(input_str: str, char: str = "/"):
    """
    Remove extra characters from start and beginning of string

    :param input_str:
    :param char:
    """
    while input_str[0] == char:
        input_str = input_str[1:]

    while input_str[-1] == char:
        input_str = input_str[:-1]

    return input_str


def build_tree(element_data) -> dict:
    tree = {}
    private_count = 0
    for slug, value in element_data.items():
        if "private" in value and value["private"] and data["privateMode"]:
            slug = f"<sensitive>/{private_count}"
            private_count += 1
        display_element_data = {**value, "path": slug}
        attach_to_tree(slug, display_element_data, tree)
    return tree


def _command_new_spec_element(args_str: str = "") -> None:
    global key
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 2:
        secure_print("new [path] [name]")
        return
    slug = remove_outside_char(args[0]).lower()

    name = args[1]

    if slug in data["specs"]:
        secure_print(f"element '{slug}' already exists, not creating")
        return

    today_str = str(format_config_date(datetime.now()))
    element_data = {"name": name, "created_at": today_str, "due": today_str}

    write_document(f"# {name}\n\n\n", spec_service_name, slug, key)

    data["specs"][slug] = element_data

    _command_review_spec_element(slug)


def _command_remove_spec_element(args_str: str = "") -> None:
    global data, key
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 1:
        secure_print("del [path]")
        return
    slug = remove_outside_char(args[0]).lower()

    if slug not in data["specs"]:
        secure_print(f"element '{slug}' doesn't exist, not deleting")
        return

    if "reviews" in data["specs"][slug]:
        for _, v in data["specs"][slug]["reviews"].items():
            delete_document(spec_service_name, v["slug"], key)

    # Data will be saved after every loop, but if we decide to change this, we should create a function for flushing
    # as needed.
    del data["specs"][slug]

    delete_document(spec_service_name, slug, key)

    # _command_show_tree()


def _command_edit_spec_element(args_str: str = "") -> None:
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 1:
        secure_print("edit [path]")

        return
    slug = remove_outside_char(args[0]).lower()

    if slug not in data["specs"]:
        secure_print(f"element '{slug}' doesn't exist, not editing")
        return

    _edit_spec_doc(slug)


def _command_about(args_str: str = ""):
    secure_print()
    secure_print(
        terminal_format(
            "perora life review system".center(100), [Colors.ULTRA_GROOVY, Colors.BOLD]
        )
    )
    secure_print(terminal_format("vin howe".center(100), [Colors.ITALIC]))


def _command_update_due(args_str: str = ""):
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 1:
        secure_print("due [path] <days until due>")
        return
    slug = args[0]
    days_until_due = None
    if len(args) > 1:
        days_until_due = int(args[1])
    else:
        while days_until_due is None:
            try:
                days_until_due_input = int(
                    input(f"how many days until your next review of `{slug}`? ")
                )
                add_lines()
            except ValueError:
                secure_print(
                    f"{Colors.ENDC + Colors.SUPER_WARNING}invalid input{Colors.ENDC}"
                )
                continue
            days_until_due = days_until_due_input

    data["specs"][slug]["due"] = format_config_date(
        datetime.now() + timedelta(days=days_until_due)
    )


def _today_date_str() -> str:
    return str(format_config_date(datetime.now()))


def _review_slug(spec_slug: str, date: str):
    return f"review--{date}--{spec_slug}"


def _create_review_today_if_not_exist(slug):
    global key
    if "reviews" not in data["specs"][slug]:
        data["specs"][slug]["reviews"] = {}

    today_str = _today_date_str()

    if today_str in data["specs"][slug]["reviews"]:
        return

    review_slug = _review_slug(slug, today_str)
    write_document(
        f"# spec review for `{slug}` on {today_str}\n\n\n",
        spec_service_name,
        review_slug,
        key,
    )

    if "reviews" not in data["specs"][slug]:
        data["specs"][slug]["reviews"] = []

    review_data = {"date": today_str, "slug": review_slug}

    data["specs"][slug]["reviews"][today_str] = review_data


def _command_review_spec_element(args_str: str = "") -> None:
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 1:
        secure_print("review [path]")
        return
    slug = remove_outside_char(args[0]).lower()

    date_str = None
    if len(args) > 1:
        date_str = args[1]
    else:
        date_str = _today_date_str()
        _create_review_today_if_not_exist(slug)

    if slug not in data["specs"]:
        secure_print(f"element '{slug}' doesn't exist, not reviewing")
        return

    _edit_spec_review_doc_side_by_side(slug, date_str)
    if not len(args) > 1:
        _command_update_due(slug)


def _command_reviews_spec_element(args_str: str = "") -> None:
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 1:
        secure_print("reviews [path]")
        return
    slug = remove_outside_char(args[0]).lower()

    if slug not in data["specs"]:
        secure_print(f"element '{slug}' doesn't exist")
        return

    if "reviews" not in data["specs"][slug]:
        secure_print("no past reviews")
        return

    secure_print("")
    secure_print(f"reviews for `{slug}`:")

    for k in sorted(data["specs"][slug]["reviews"]):
        secure_print(f"- {k}")

    secure_print("")


def _command_move_spec_element(args_str: str = "") -> None:
    global key
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 2:
        secure_print("move [path] [new path]")
        return

    slug = remove_outside_char(args[0]).lower()
    new_slug = remove_outside_char(args[1]).lower()

    if new_slug in data:
        secure_print(f"element '{new_slug}' already exists")
        return

    rename_document(spec_service_name, slug, new_slug, key)

    data["specs"][new_slug] = data["specs"][slug]

    del data["specs"][slug]

    # _command_show_tree()


def _command_rename_spec_element(args_str: str = "") -> None:
    global key
    args: List[str] = args_str.split(" ", 1)
    if len(args) < 2:
        secure_print("rename [path] [new name]")
        return

    path = args[0]
    new_name = args[1]

    data["specs"][path]["name"] = new_name


def _command_toggle_privacy(args_str: str = "") -> None:
    global key, data
    args: List[str] = args_str.split(" ", 1)

    if len(args) < 1 or len(args[0]) == 0:
        if "privateMode" not in data:
            data["privateMode"] = True
        else:
            data["privateMode"] = not data["privateMode"]
    elif len(args[0]) > 0:
        slug = args[0]

        element = data["specs"][slug]

        if "private" not in element:
            element["private"] = True
        else:
            element["private"] = not element["private"]


def _command_exit(args_str: str = "") -> None:
    secure_print("exiting...")
    clear_term()
    exit()


def _command_help(args_str: str = ""):
    global commands
    secure_print("commands:")
    secure_print(", ".join(commands))


def show_tree(args_str: str = ""):
    secure_print("")
    print_tree(data["specs"])
    secure_print("")


def _purge_overdue_spec_elements() -> None:
    temp_data = data["specs"].copy()
    for k, v in temp_data.items():
        due_delta = (parse_config_date(v["due"]) - datetime.today().date()).days
        if due_delta <= -7:
            pass
            # _command_remove_spec_element(k)


commands = {
    "new": _command_new_spec_element,
    "del": _command_remove_spec_element,
    "move": _command_move_spec_element,
    "rename": _command_rename_spec_element,
    "edit": _command_edit_spec_element,
    "vi": _command_edit_spec_element,
    "due": _command_update_due,
    "about": _command_about,
    "review": _command_review_spec_element,
    "reviews": _command_reviews_spec_element,
    "private": _command_toggle_privacy,
    # "tree": show_tree,
    # "ls": show_tree,
    "help": _command_help,
    "exit": _command_exit,
    "quit": _command_exit,
    "q": _command_exit,
    ":q": _command_exit,
}


def run_command(command: str):
    args = command.split(" ", 1)
    if len(args) < 1:
        return

    command = args[0]

    if command not in commands:
        secure_print(f"'{command}' is not a known command")
        secure_print("")
        _command_help()
        return

    if len(args) > 1:
        commands[command](args[1])
    else:
        commands[command]()


def spec_item_listing(spec, show_due_info=True, format=True) -> str:
    global longest_item_length
    inactive_extra_length = len(
        "".join([Colors.BOLD, Colors.ULTRA_GROOVY, Colors.ENDC, Colors.ENDC])
    )
    indent = spec["path"].count("/")
    due_delta = (parse_config_date(spec["due"]) - datetime.today().date()).days
    due_info = f"[\u23F0 {due_info_str(due_delta, due_delta >= -7)}]"
    max_name_length = 60
    # https://stackoverflow.com/questions/2872512/python-truncate-a-long-string/39017530
    if "private" in spec and spec["private"] and data["privateMode"]:
        path = "<sensitive>"
        name = "<sensitive>"
    else:
        path = spec["path"]
        name = spec["name"][:max_name_length] + (
            spec["name"][max_name_length:] and "..."
        )
    if due_delta >= -7 and format:
        path = terminal_format(path, [Colors.BOLD])
        name = terminal_format(name, [Colors.ULTRA_GROOVY])

    if show_due_info:
        bullet = "  " * indent + f"--> {name} ({path})"
        inactive_extra_length = inactive_extra_length if due_delta < -7 else 0
        bullet = f"{bullet} {due_info.rjust(longest_item_length + due_info_padding - inactive_extra_length + len(due_info) - len(bullet))}"
    else:
        bullet = "  " * indent + f"--> {name} ({path})"

    if due_delta < -7 and format:
        bullet = terminal_format(bullet, [Colors.INACTIVE])

    return bullet


def compute_longest_item_length():
    longest_length = 0
    for key, element in data["specs"].items():
        element["path"] = key
        spec_string = spec_item_listing(element, show_due_info=False, format=False)
        if len(spec_string) > longest_length:
            longest_length = len(spec_string)
    return longest_length


def print_element_tree(d, indent=0) -> None:
    """
    Print the file tree structure with proper indentation.
    """
    if len(d) == 0:
        secure_print("empty tree")
        return

    for key, value in d.items():
        if node_marker in value:
            secure_print(spec_item_listing(value))
        else:
            secure_print("  " * indent + terminal_format(key, [Colors.GROOVY]))
            if isinstance(value, dict):
                print_element_tree(value, indent + 1)
            else:
                secure_print("  " * (indent + 1) + str(value))


def _edit_spec_doc(slug: str) -> None:
    """

    :param slug:
    :return whether the file was edited:
    """
    global key

    edit_document(spec_service_name, slug, key)


def _edit_spec_review_doc(spec_slug: str, date: str) -> None:
    global key

    review_slug = _review_slug(spec_slug, date)
    edit_document(spec_service_name, review_slug, key)


def _edit_spec_review_doc_side_by_side(spec_slug: str, date: str) -> None:
    global key

    review_slug = _review_slug(spec_slug, date)
    edit_documents(spec_service_name, [spec_slug, review_slug], key)


def _load_data(key: str) -> dict:
    if file_exists(data_file_path):
        data_content = json.loads(_read_decrypt_file(data_file_path, key))
        return data_content
    return {"specs": {}, "privateMode": False}


def _load_due_map() -> dict:
    if file_exists(due_map_file_path):
        with open(due_map_file_path) as due_map_file:
            due_map_content = json.load(due_map_file)
            return due_map_content
    return {"dueDates": {}}


def _load_reminder_config() -> dict:
    if file_exists(reminder_config_file_path):
        with open(reminder_config_file_path) as reminder_config_file:
            reminder_config_config = json.load(reminder_config_file)
            return reminder_config_config
    raise FileNotFoundError(f"{reminder_config_file_path} not found")


def _save_data(data: dict, data_path: str, key: str) -> None:
    # sort specs
    sorted_specs = {}
    for k, v in sorted(data["specs"].items()):
        sorted_specs[k] = v

    data["specs"] = sorted_specs
    json_data = json.dumps(data)
    _write_encrypt_file(json_data, data_path, key)


def _save_due_map_from_data(data: dict, due_map_path: str) -> None:
    due_map = {"dueDates": {}}
    for k, v in sorted(data["specs"].items()):
        due_map["dueDates"][k] = v["due"]

    _save_due_map(due_map, due_map_path)


def _save_due_map(due_map: dict, due_map_path: str) -> None:
    with open(due_map_path, "w") as due_map_file:
        json.dump(due_map, due_map_file)


def check_duplicates(test_list: List[any]) -> bool:
    """
    See https://thispointer.com/python-3-ways-to-check-if-there-are-duplicates-in-a-list/
    :param test_list:
    :return:
    """
    if len(test_list) == len(set(test_list)):
        return False
    return True


def format_config_date(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


def parse_config_date(date_str: str) -> datetime.date:
    due_date_numbers = map(lambda n: int(n), date_str.split("-"))
    return datetime(*due_date_numbers).date()


def due_today(spec: dict) -> bool:
    due_date = parse_config_date(spec["due"])
    return due_date == datetime.today().date()


def due_info_str(remaining_days: int, formatting=True) -> str:
    special_cases = {
        -1: (f"YESTERDAY", [Colors.SUPER_WARNING, Colors.BOLD]),
        0: (f"TODAY", [Colors.WARNING, Colors.BOLD]),
        1: (f"TOMORROW", [Colors.OKGREEN]),
    }

    if remaining_days in special_cases:
        return (
            special_cases[remaining_days][0]
            if not formatting
            else terminal_format(
                special_cases[remaining_days][0], special_cases[remaining_days][1]
            )
        )

    # We do abs(remaining_days) because the if check for negative values will add "ago" to the end
    remaining_days_str = f"{abs(remaining_days)}d"

    if remaining_days < 0:
        remaining_days_str = f"{remaining_days_str} AGO"
        remaining_days_str = (
            remaining_days_str
            if not formatting
            else terminal_format(
                remaining_days_str, [Colors.SUPER_WARNING, Colors.BOLD]
            )
        )
    elif remaining_days < 3:
        remaining_days_str = (
            remaining_days_str
            if not formatting
            else terminal_format(remaining_days_str, [Colors.OKGREEN])
        )

    return remaining_days_str


def print_tree(data: dict) -> None:
    global longest_item_length
    display_tree = build_tree(data)
    longest_item_length = compute_longest_item_length()
    print_element_tree(display_tree)


def get_prompt_text():
    input_mode_map = {
        InputMode.INSERT: ("bg:ansigreen fg:white bold", "[I]"),
        InputMode.NAVIGATION: ("bg:ansired fg:white bold", "[N]"),
        InputMode.REPLACE: ("bg:ansigreen fg:white bold", "[R]"),
        InputMode.INSERT_MULTIPLE: ("bg:ansigreen fg:white bold", "[II]"),
    }
    input_mode = input_mode_map[get_app().vi_state.input_mode]
    # Make escape key register instantly--this is hacky but I don't want to make a full-fledged Prompt Toolkit
    # Application until I absolutely have to
    get_app().ttimeoutlen = 0
    # input_mode = 'I' if get_app().vi_state.input_mode == InputMode.INSERT
    return [
        input_mode,
        ("", " "),
        ("fg:ansibrightcyan bold", f"spec ~~> "),
    ]


def spec() -> None:
    global data, key, catalog
    key, catalog = password_prompt(spec_service_name)
    # first_loop = True

    command_history = InMemoryHistory()

    prompt_session = PromptSession(history=command_history)

    while True:
        data = _load_data(key)

        _purge_overdue_spec_elements()

        # if first_loop:
        secure_print()
        secure_print(
            terminal_format("perora floating spec", [Colors.BOLD, Colors.ULTRA_GROOVY])
        )
        private_mode_on_off_statement = (
            terminal_format("on", [Colors.OKGREEN])
            if data["privateMode"]
            else terminal_format("off", [Colors.SUPER_WARNING, Colors.BOLD])
        )
        secure_print(
            f'private mode {private_mode_on_off_statement} ("private" to toggle)'
        )
        show_tree()
        # first_loop = False
        specs = data["specs"]
        spec_element_slugs = [k for k in specs.keys() if not "private" in specs[k] or not specs[k]["private"]]
        spec_element_slugs_completer = FuzzyWordCompleter(spec_element_slugs)
        spec_element_reviews = {}
        for slug in spec_element_slugs:
            if "reviews" not in specs[slug]:
                spec_element_reviews[slug] = None
                continue
            spec_element_reviews[slug] = {
                k: None for k in specs[slug]["reviews"].keys()
            }
        spec_completer = FuzzyCompleter(
            NestedCompleter.from_nested_dict(
                {
                    "del": spec_element_slugs_completer,
                    "review": spec_element_reviews,
                    "reviews": spec_element_slugs_completer,
                    "edit": spec_element_slugs_completer,
                    "vi": spec_element_slugs_completer,
                    "move": spec_element_slugs_completer,
                    "due": spec_element_slugs_completer,
                    "rename": spec_element_slugs_completer,
                    "private": spec_element_slugs_completer,
                    "about": None,
                    "new": spec_element_slugs_completer,
                    "tree": None,
                    "exit": None,
                }
            )
        )

        command = prompt_session.prompt(
            get_prompt_text, multiline=False, completer=spec_completer, vi_mode=True
        )
        add_lines()
        clear_term()
        run_command(command)

        _save_data(data, data_file_path, key)
        _save_due_map_from_data(data, due_map_file_path)


def post_email(
    domain, api_key, from_addr_name, from_name, to_addr, subject_line, body
) -> requests.Response:
    response = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": f"{from_name} <{from_addr_name}@{domain}>",
            "to": to_addr,
            "subject": subject_line,
            "text": body,
        },
    )
    return response


def review_reminder():
    due_map_data = _load_due_map()
    working_data = due_map_data.copy()

    secure_print("sending review reminder email for today")

    last_reminder = (
        parse_config_date(due_map_data["lastReminder"])
        if "lastReminder" in due_map_data
        else datetime.fromtimestamp(0).date()
    )

    if (last_reminder - datetime.today().date()).days == 0:
        return

    reminder_config = _load_reminder_config()

    domain = reminder_config["mailgun"]["domain"]
    api_key = reminder_config["mailgun"]["apiKey"]

    recipient = reminder_config["recipient"]

    sending_name = "perora spec reviews"
    sending_addr_name = "spec"

    due_dates_map = working_data["dueDates"]

    overdue = []
    due = []
    due_soon = []

    for slug, date in due_dates_map.items():
        due_in = (parse_config_date(date) - datetime.today().date()).days

        if due_in > notify_days_ahead:
            continue

        # TODO: Determine if it's really important to add this here or not
        due_dates_map[slug] = due_in

        if due_in < 0:
            overdue.append(slug)
        elif due_in == 0:
            due.append(slug)
        elif due_in < notify_days_ahead:
            due_soon.append(slug)

    body = ""
    # BIG TODO TODO TODO TODO TODO TODO TODO TODO
    # TODO: TODO: Generalize instead of repeating code here
    if len(overdue) > 0:
        # elements_label = pluralize("element", "elements", len(overdue)).upper()
        body += (
            f"Note: spec elements become inactive after {inactive_after_days} days.\n\n"
        )
        body += f"{len(overdue)} OVERDUE:\n"
        for slug in overdue:
            date = due_dates_map[slug]
            body += f"- {slug} {due_info_str(date, False)}\n"
        body += "\n"

    if len(due) > 0:
        # elements_label = pluralize("element", "elements", len(due))
        body += f"{len(due)} due today:\n"
        for slug in due:
            date = due_dates_map[slug]
            # No need to specify date when due, all in this list are due today
            body += f"- {slug}\n"
        body += "\n"

    if len(due_soon) > 0:
        # elements_label = pluralize("element", "elements", len(due_soon))
        body += f"{len(due_soon)} due soon:\n"
        for slug in due_soon:
            date = due_dates_map[slug]
            # No need to specify date when due, all in this list are due today
            body += f"- {slug} {due_info_str(date, False)}\n"

    subject_line = "perora spec reviews"

    subject_line_due_count_info = []

    if len(due) > 0:
        subject_line_due_count_info.append(f"{len(due)} due")

    if len(overdue) > 0:
        subject_line_due_count_info.append(f"{len(overdue)} OVERDUE")

    if len(subject_line_due_count_info) > 0:
        subject_line = f"{subject_line} ({', '.join(subject_line_due_count_info)})"

    if len(body) > 0:
        post_email(
            domain,
            api_key,
            sending_addr_name,
            sending_name,
            recipient,
            subject_line,
            body,
        )

    due_map_data["lastReminder"] = format_config_date(datetime.now())

    _save_due_map(due_map_data, due_map_file_path)


if __name__ == "__main__":
    spec()
