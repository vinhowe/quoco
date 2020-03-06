import argparse
import datetime
import tempfile
from typing import List, Tuple

from perora.document_manager import open_service_interactive, write_document, edit_document, document_in_catalog

temp_edit_files: List[Tuple[tempfile.NamedTemporaryFile, str]] = []

journal_service_name = "journal"


def jour_one() -> datetime.date:
    """
    My "day one."
    :return:
    """
    # TODO: Obviously make this configurable
    return datetime.date(2020, 1, 17)


def today_date_string() -> str:
    now = datetime.datetime.now()

    return now.strftime("%-m.%-d.%Y")


def open_journal_entry(date, key) -> None:
    if not document_in_catalog(journal_service_name, date, key):
        days_since_jour_one = (datetime.datetime.now().date() - jour_one()).days
        header = f"# {date} \nday {days_since_jour_one}\n\n\n"
        write_document(header, journal_service_name, date, key)
    edit_document(journal_service_name, date, key)


def launch_journal_editor(date_string=None) -> None:
    key, catalog = open_service_interactive(journal_service_name)

    date = date_string if date_string is not None else today_date_string()

    open_journal_entry(date, key)


# TODO: remove this because we don't call "journal.py" directly
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="lj - personal encrypted journal")
    group = parser.add_mutually_exclusive_group()
    # no-op
    # group.add_argument(
    #     "-l",
    #     action="store_true",
    #     default=False,
    #     help="list all entries",
    # )
    group.add_argument(
        "-d",
        action="store",
        help="get entry for specific date",
    )

    args = parser.parse_args()
    launch_journal_editor(args.d)
