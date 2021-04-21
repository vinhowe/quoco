import json
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List, Optional, Type

import quocofs
from dateutil.relativedelta import *

from quoco.quocofs_manager import QuocoFsManager

PLAN_CATALOG_NAME = "plan_catalog"
PLAN_DATE_FORMAT = "%d-%m-%Y"
PLAN_CATALOG_ENTRIES_KEY = "entries"
DEFAULT_PLAN_CATALOG_DATA = {"version": 3, PLAN_CATALOG_ENTRIES_KEY: {}}


@dataclass
class PlanEntry(ABC):
    @property
    @abstractmethod
    def type_name(self) -> str:
        ...

    @property
    @abstractmethod
    def char_name(self) -> str:
        ...

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def default_content(self) -> str:
        ...

    def serialize(self) -> dict:
        return {"type": self.type_name}


@dataclass
class PlanEntryWithDate(PlanEntry, ABC):
    plan_date: date

    @property
    @abstractmethod
    def legacy_name_format(self) -> str:
        ...

    def date_add(self, n) -> date:
        """
        Logic for incrementing plan by some dates
        :return:
        """
        return self.plan_date + timedelta(days=n)

    def plan_date_from_date(self) -> date:
        return self.plan_date

    @classmethod
    def date_from_legacy_name(
        cls,
        legacy_name,
    ):
        return datetime.strptime(legacy_name, cls.legacy_name_format).date()

    def serialize(self):
        return super().serialize() | {
            "date": self.plan_date_from_date().strftime(PLAN_DATE_FORMAT),
        }


class CachePlan(PlanEntryWithDate):
    type_name = "cache"
    char_name = "c"
    legacy_name_format = f"{type_name}_%d_%m_%Y"

    def name(self):
        return (
            f"cache_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"
        )

    def default_content(self):
        pretty_name = f"cache: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class DayPlan(PlanEntryWithDate):
    type_name = "day"
    char_name = "d"
    legacy_name_format = f"{type_name}_%d_%m_%Y"

    def name(self):
        return f"day_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"day plan: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class DecisionStreamPlan(PlanEntryWithDate):
    """Decision stream--a place to make decisions made throughout the day"""

    type_name = "decision_stream"
    char_name = "t"
    legacy_name_format = f"{type_name}_%d_%m_%Y"

    def name(self):
        return f"decision_stream_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"decision stream: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class JournalPlan(PlanEntryWithDate):
    """Journal--non-organizational dump"""

    type_name = "journal"
    char_name = "j"
    legacy_name_format = f"{type_name}_%d_%m_%Y"

    def name(self):
        return (
            f"journal_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"
        )

    def default_content(self):
        pretty_name = f"journal: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class WeekPlan(PlanEntryWithDate):
    type_name = "week"
    char_name = "w"
    legacy_name_format = f"{type_name}_%d_%m_%Y"

    def plan_date_from_date(self):
        return datetime.fromisocalendar(
            self.plan_date.year, self.plan_date.isocalendar()[1], 1
        ).date()

    def name(self):
        month_week = self._week_number_of_month(self.plan_date)
        return f"week_{month_week}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        # Do some logic so that the week starts on Sunday
        day_of_week = (
            (self.plan_date.weekday() + 1) if self.plan_date.weekday() < 6 else 0
        )
        first_date = self.plan_date - timedelta(days=day_of_week)
        last_date = self.plan_date + timedelta(days=6 - day_of_week)
        date_range_str = self._format_date_range(first_date, last_date)
        pretty_name = f"week plan: {date_range_str}"
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        return self.plan_date + timedelta(weeks=n)

    @classmethod
    def date_from_legacy_name(
        cls,
        legacy_name,
    ):
        # This is a crazyyy wild hack. We store the week of the month in the day field so we can use strptime formatting
        temp_date = datetime.strptime(legacy_name, cls.legacy_name_format)
        week = temp_date.day
        temp_date.replace(day=1)
        first_week_of_month = temp_date.isocalendar()[1]
        week_of_year = week + first_week_of_month
        return datetime.fromisocalendar(temp_date.year, week_of_year, 1) - timedelta(
            days=2
        )

    @staticmethod
    def _week_number_of_month(date) -> int:
        """
        Thanks https://www.mytecbits.com/internet/python/week-number-of-month
        :param date:
        :return:
        """
        # Gets year week number of first day of the month and subtracts it from current
        #  year week number
        # The reason that we add a day is because the ISO calendar starts on Monday, and
        #  thus we need to shift the week forward by one day. Sunday + 1 = Monday, which
        #  gives us the alignment we want.
        return (date + timedelta(days=1)).isocalendar()[1] - date.replace(
            day=1
        ).isocalendar()[1]

    @staticmethod
    def _format_date_range(date_1: datetime.date, date_2: datetime.date) -> str:
        """
        Pretty format a date range
        :param date_1:
        :param date_2:
        :return:
        """

        date_1 = date_1 if date_1 is datetime.date else date_1.date()
        date_2 = date_2 if date_2 is datetime.date else date_2.date()

        if date_1 == date_2:
            return date_1.strftime("%d %b %Y").lower()

        date_1_elements = [str(date_1.day)]
        date_2_elements = [str(date_2.day)]
        shared_elements = []

        if date_1.month == date_2.month:
            shared_elements.append(date_1.strftime("%b").lower())
        else:
            date_1_elements.append(date_1.strftime("%b").lower())
            date_2_elements.append(date_2.strftime("%b").lower())

        if date_1.year == date_2.year:
            shared_elements.append(str(date_1.year))
        else:
            date_1_elements.append(str(date_1.year))
            date_2_elements.append(str(date_2.year))

        date_1_str = " ".join(date_1_elements)
        date_2_str = " ".join(date_2_elements)
        shared_str = " " + " ".join(shared_elements) if shared_elements else ""

        return f"{date_1_str}-{date_2_str}{shared_str}"


class MonthPlan(PlanEntryWithDate):
    type_name = "month"
    char_name = "m"
    legacy_name_format = f"{type_name}_%m_%Y"

    def name(self):
        return f"month_{self.plan_date.month}_{self.plan_date.year}"

    def plan_date_from_date(self):
        return self.plan_date.replace(day=1)

    def default_content(self):
        pretty_name = (
            f"month plan: {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        )
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        return self.plan_date + relativedelta(months=n)


class SemesterPlan(PlanEntryWithDate):
    type_name = "semester"
    char_name = "s"
    legacy_name_format = None

    semester_month_map = {
        "winter": 1,
        "spring": 5,
        "summer": 7,
        "fall": 9,
    }

    def plan_date_from_date(self):
        month = next(
            (
                m
                for m in reversed(self.semester_month_map.values())
                if m <= self.plan_date.month
            ),
            date.month,
        )
        return self.plan_date.replace(month=month, day=1)

    def name(self):
        # TODO: Hardcoded for BYU because I need this to solve a problem
        #  for me right now and I don't have time to figure out how this is
        #  supposed to work beautifully for everyone everywhere.
        #  I'm only taking F/W, so this doesn't account for Sp/Su
        current_semester_name: str = "winter" if self.plan_date.month < 5 else "fall"
        return f"semester_{current_semester_name}_{self.plan_date.year}"

    def default_content(self):
        current_semester_name: str = "winter" if self.plan_date.month < 5 else "fall"
        pretty_name = f"semester plan: {current_semester_name} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        if n == 0:
            return self.plan_date

        month_map_items = list(self.semester_month_map.items())
        month_map_length = len(month_map_items)
        new_semester_index = (
            next(
                i
                for (i, item) in enumerate(month_map_items)
                if item[1] == self.plan_date.month
            )
            + n
        )
        new_semester_index = (
            new_semester_index % month_map_length
            if new_semester_index >= 0
            else month_map_length - (abs(new_semester_index) % month_map_length)
        )
        return self.plan_date.replace(
            month=self.semester_month_map[month_map_items[new_semester_index][0]]
        )

    @classmethod
    def date_from_legacy_name(
        cls,
        legacy_name,
    ):
        name_split = legacy_name.split("_")
        year = int(name_split[-1])
        semester = name_split[1]
        if semester not in cls.semester_month_map:
            raise NotImplementedError(f"'{semester}' is not a recognized semester/term")

        month = cls.semester_month_map[semester]
        return datetime(year, month, 1)


class YearPlan(PlanEntryWithDate):
    type_name = "year"
    char_name = "y"
    legacy_name_format = f"{type_name}_%Y"

    def plan_date_from_date(self):
        return self.plan_date.replace(month=1, day=1)

    def name(self):
        return f"year_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"year plan: {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        return self.plan_date + relativedelta(years=n)


class LifePlan(PlanEntry):
    type_name = "life"
    char_name = "l"

    def name(self):
        return self.type_name

    def default_content(self):
        return f"# life plan\n\n\n"


class ClutterPlan(PlanEntry):
    """
    Place to put "stuff" I don't want to get rid of but that I don't want to clutter `s` or `l` with.
    This will probably get pretty big.
    """

    type_name = "clutter"
    char_name = "x"

    def name(self):
        return self.type_name

    def default_content(self):
        return "# clutter\n\n\n"


class PersistentWeeklyPlan(PlanEntry):
    type_name = "persistent_weekly"
    char_name = "x"

    def name(self):
        return self.type_name

    def default_content(self):
        return "# persistent weekly structure\n\n\n"


PLAN_TYPES: List[Type[PlanEntry]] = [
    CachePlan,
    DayPlan,
    DecisionStreamPlan,
    JournalPlan,
    WeekPlan,
    MonthPlan,
    SemesterPlan,
    YearPlan,
    LifePlan,
    ClutterPlan,
    PersistentWeeklyPlan,
]


def _load_plan_catalog_interactive():
    manager = QuocoFsManager(
        QuocoFsManager.default_base_path(), QuocoFsManager.DEFAULT_SALT
    )

    catalog_id = manager.session.object_id_with_name(PLAN_CATALOG_NAME)
    if catalog_id:
        catalog_data = json.loads(manager.session.object(catalog_id))
    else:
        # TODO: Figure out why I have to use bytes() here
        catalog_id = bytes(
            manager.session.create_object(
                json.dumps(DEFAULT_PLAN_CATALOG_DATA).encode("utf-8")
            )
        )
        manager.session.set_object_name(catalog_id, PLAN_CATALOG_NAME)
        catalog_data = DEFAULT_PLAN_CATALOG_DATA

    return manager, catalog_data, catalog_id


# TODO: This, but object-oriented
def _plan_entry_in_catalog(entry: PlanEntry, catalog_data):
    return next(
        (
            (bytes.fromhex(x[0]), x[1])
            for x in catalog_data[PLAN_CATALOG_ENTRIES_KEY].items()
            # https://stackoverflow.com/a/41579450/1979008
            if entry.serialize().items() <= x[1].items()
        ),
        (None, None),
    )


def _last_nth_entry_in_catalog(
    entry_type: Type[PlanEntryWithDate], n: int, catalog_data
) -> Optional[PlanEntryWithDate]:
    date_descending_entries = sorted(
        (
            datetime.strptime(e["date"], PLAN_DATE_FORMAT)
            for e in catalog_data[PLAN_CATALOG_ENTRIES_KEY].values()
            if e["type"] == entry_type.type_name
        ),
        reverse=True,
    )

    if n >= len(date_descending_entries):
        return None

    return entry_type(date_descending_entries[n])


def _put_plan_entry_in_catalog(
    document_id: bytes,
    plan: PlanEntry,
    catalog_data: dict,
):
    if _plan_entry_in_catalog(plan, catalog_data)[0] is not None:
        return catalog_data
    hex_id = document_id.hex()
    catalog_data[PLAN_CATALOG_ENTRIES_KEY][hex_id] = plan.serialize() | {"id": hex_id}
    return catalog_data


def whats_the_plan(args: str = None) -> None:
    manager, catalog_data, catalog_id = _load_plan_catalog_interactive()

    default_layout = "p d s c c+1"
    cache_triad_layout = "c-1 c c+1"
    telescope_layout = "d w m y l"
    args = (
        f"{default_layout} -- {datetime.now().strftime('%m.%d.%Y')}"
        if args is None
        else args
    )

    arg_parts = args.split(" -- ")
    plan_args = arg_parts[0]

    # Shortcut for default layout--redundant by itself but useful when
    # comparing plans from past/future dates
    if len(plan_args) > 0:
        plan_args = plan_args.replace("k", default_layout)
        plan_args = plan_args.replace("C", cache_triad_layout)
        plan_args = plan_args.replace("t", telescope_layout)

    plan_args = plan_args.split(" ")

    plan_date = (
        datetime.strptime(arg_parts[1], "%m.%d.%Y")
        if len(arg_parts) > 1
        else datetime.now()
    )

    with manager:
        names_to_open = []

        for plan_arg in plan_args:
            entry_type: Optional[Type[PlanEntry]] = None
            for plan_type in PLAN_TYPES:
                if plan_type.char_name == plan_arg[0]:
                    entry_type = plan_type
                    break

            if not entry_type:
                continue

            if issubclass(entry_type, PlanEntryWithDate):
                entry = entry_type(plan_date)
                if len(plan_arg) > 1:
                    operator = plan_arg[1]
                    value = abs(int(plan_arg[2:]))
                    if operator in ["+", "-"]:
                        # Yes eval is potentially dangerous, but both operator and value are checked and I can't think of
                        #  any specific vector for abuse here anyway.
                        signed_difference = eval(f"{operator}{value}")
                        entry.plan_date = entry.date_add(signed_difference)
                    elif operator == "~":
                        entry = _last_nth_entry_in_catalog(
                            entry_type, value, catalog_data
                        )
                        if entry is None:
                            print(
                                f'Couldn\'t find last entry #{value} of type "{entry_type.type_name}"',
                                file=sys.stderr,
                            )
                            return
            else:
                entry = entry_type()

            document_id, _ = _plan_entry_in_catalog(entry, catalog_data)

            if document_id is None:
                document_id = manager.session.create_object(
                    entry.default_content().encode("utf-8")
                )
                catalog_data = _put_plan_entry_in_catalog(
                    document_id, entry, catalog_data
                )

            names_to_open.append(document_id)

        manager.edit_documents_vim(names_to_open)
        manager.session.modify_object(
            catalog_id, json.dumps(catalog_data).encode("utf-8")
        )
