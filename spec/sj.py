#!/usr/bin/env python3.7
import glob
import json
import subprocess
from datetime import datetime, timedelta
from os import path, remove, mkdir
from shutil import copy
from typing import List, Tuple
import filecmp


class Colors:
    """
    https://stackoverflow.com/questions/287871/how-to-print-colored-text-in-terminal-in-python
    """
    WARNING = '\033[93m'
    SUPER_WARNING = '\033[91m'
    OKGREEN = '\033[92m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def edit_file(filename: str):
    command = f"vi + {filename}"

    subprocess.call(command, shell=True)


def edit_spec_doc(filename: str) -> bool:
    """

    :param filename:
    :return whether the file was edited:
    """

    filename_tmp = filename + ".sje"
    copy(filename, filename_tmp)
    edit_file(filename)
    edited = not filecmp.cmp(filename, filename_tmp)

    remove(filename_tmp)

    return edited


def file_exists(filename: str):
    return path.exists(filename)


def slug_from_path(path_str: str) -> str:
    """

    :param path_str:
    :return:
    """
    basename: str = path.basename(path_str)
    slug: str = basename[0: basename.rindex(".spec.md")]
    return slug


def get_sj_path(filename: str) -> str:
    sj_dir_path = '.sj/'

    if not file_exists(sj_dir_path):
        mkdir(sj_dir_path)

    return path.abspath(path.join(sj_dir_path, filename))


def load_data(config_path: str) -> dict:
    if file_exists(config_path):
        with open(config_path) as config_file:
            config_data = json.load(config_file)
            return config_data
    return {"specs": {}}


def save_config(config: dict, config_path: str) -> None:
    with open(config_path, "w") as config_file:
        json.dump(config, config_file, indent=2)


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


def reconcile_config_with_files(
        slug_path_map: List[Tuple[str, str]], specs: dict
) -> dict:
    found_slugs = []
     
    for (slug, path_str) in slug_path_map:
        found_slugs.append(slug)
        if slug in specs:
            # Update paths
            specs[slug]["path"] = path_str
        else:
            today_str = str(format_config_date(datetime.now()))
            specs[slug] = {
                "path": path_str,
                "created_at": str(format_config_date(datetime.now())),
                "due": today_str,
            }

    updated_specs = specs.copy()
    for spec in specs:
        if spec not in found_slugs:
            updated_specs.pop(spec)

    return updated_specs


def due_today(spec: dict) -> bool:
    due_date = parse_config_date(spec["due"])
    return due_date == datetime.today().date()


def due_info_str(remaining_days: int) -> str:
    special_cases = {
        -1: f"{Colors.SUPER_WARNING + Colors.BOLD}YESTERDAY{Colors.ENDC}",
        0: f"{Colors.WARNING + Colors.BOLD}TODAY{Colors.ENDC}",
        1: f"{Colors.OKGREEN}TOMORROW{Colors.ENDC}",
    }

    if remaining_days in special_cases:
        return special_cases[remaining_days]

    # We do abs(remaining_days) because the if check for negative values will add "ago" to the end
    remaining_days_str = f"{abs(remaining_days)}d"

    if remaining_days < 0:
        remaining_days_str = f"{Colors.SUPER_WARNING + Colors.BOLD}{remaining_days_str} AGO{Colors.ENDC}"
    elif remaining_days < 3:
        remaining_days_str = f"{Colors.OKGREEN}{remaining_days_str}{Colors.ENDC}"

    return remaining_days_str


def clear_term() -> None:
    print(chr(27) + "[H" + chr(27) + "[J", end='')


def review_spec_interactive() -> None:
    data_path = get_sj_path("data.json")

    while True:
        config: dict = load_data(data_path)

        # If subdirectory support is needed later, we'll add it
        # file_paths: List[str] = glob.glob("./**/*.spec.md", recursive=True)

        file_paths: List[str] = list(map(lambda p: path.abspath(p), glob.glob("./*.spec.md")))

        slugs: List[str] = list(map(slug_from_path, file_paths))

        slug_path_map = list(zip(slugs, file_paths))

        specs: dict = reconcile_config_with_files(slug_path_map, config["specs"])

        def due_delta_from_spec_config(v) -> int:
            return (parse_config_date(v[1]["due"]) - datetime.today().date()).days

        # https://stackoverflow.com/a/22975080/19790008
        # specs_due_today = {k: v for k, v in specs.items() if due_today(v)}

        sorted_specs = sorted(specs.items(), key=due_delta_from_spec_config)

        if len(specs.items()) > 0:
            clear_term()

            print(f"{Colors.BOLD}type q to exit{Colors.ENDC}")

            print("reviews available:")

            max_name_length = max(map(lambda k: len(k), specs.keys()))

            for i, (k, v) in enumerate(sorted_specs):
                due_delta = (parse_config_date(v["due"]) - datetime.today().date()).days
                due_info = f"(due {due_info_str(due_delta)})"
                rjust_size = max_name_length - len(k) + len(due_info) + 10
                print(f"{i}) {k}{due_info.rjust(rjust_size)}")

            selection = None
            while selection is None:
                try:
                    selection_input = input(f"pick an option: {Colors.BOLD}")

                    if selection_input.lower() == "q":
                        clear_term()
                        exit()

                    # attempt to convert to int
                    selection_input = int(selection_input)

                except ValueError:
                    print(f"{Colors.ENDC + Colors.SUPER_WARNING}invalid input{Colors.ENDC}")
                    continue
                print(Colors.ENDC, end='')
                if selection_input < 0 or selection_input >= len(specs.items()):
                    print(
                        f"{Colors.ENDC + Colors.SUPER_WARNING}not valid in range (0-{len(specs.items()) - 1}){Colors.ENDC}")
                    continue
                selection = selection_input

            selected_doc = sorted_specs[selection]

            edited = edit_spec_doc(selected_doc[1]["path"])

            if edited:
                days_until_due = None
                while days_until_due is None:
                    try:
                        days_until_due_input = int(
                            input(f"how many days until your next review of `{selected_doc[0]}`? "))
                    except ValueError:
                        print(f"{Colors.ENDC + Colors.SUPER_WARNING}invalid input{Colors.ENDC}")
                        continue
                    days_until_due = days_until_due_input

                config["specs"][selected_doc[0]]["due"] = format_config_date(
                    datetime.now() + timedelta(days=days_until_due))

        else:
            print("no reviews due today")
            exit()

        save_config(config, data_path)


if __name__ == "__main__":
    review_spec_interactive()
