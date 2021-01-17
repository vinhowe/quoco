from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from dateutil.relativedelta import *

from perora.document import (
    open_service_interactive,
    edit_documents, document_in_catalog, write_document,
)

plan_service_name = "plan"


@dataclass
class PlanType(ABC):

    @property
    @abstractmethod
    def char_name(self):
        ...

    @abstractmethod
    def name(self):
        ...

    @abstractmethod
    def default_content(self):
        ...


@dataclass
class PlanWithDate(PlanType, ABC):
    plan_date: datetime

    def date_add(self, n):
        """
        Logic for incrementing plan by some dates
        :return:
        """
        return self.plan_date + timedelta(days=n)


class CachePlan(PlanWithDate):
    char_name = "c"

    def name(self):
        return f"cache_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"cache: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class DayPlan(PlanWithDate):
    char_name = "d"

    def name(self):
        return f"day_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"day plan: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class DecisionStreamPlan(PlanWithDate):
    """Decision stream--a place to make decisions made throughout the day
    """

    char_name = "t"

    def name(self):
        return f"decision_stream_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"decision stream: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class JournalPlan(PlanWithDate):
    """Journal--non-organizational dump
    """

    char_name = "j"

    def name(self):
        return f"journal_{self.plan_date.day}_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"journal: {self.plan_date.strftime('%a').lower()} {self.plan_date.day} {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"


class WeekPlan(PlanWithDate):
    char_name = "w"

    def name(self):
        month_week = self._week_number_of_month(self.plan_date)
        return (
            f"week_{month_week}_{self.plan_date.month}_{self.plan_date.year}"
        )

    def default_content(self):
        # Do some logic so that the week starts on Sunday
        day_of_week = (
            (self.plan_date.weekday() + 1)
            if self.plan_date.weekday() < 6
            else 0
        )
        first_date = self.plan_date - timedelta(days=day_of_week)
        last_date = self.plan_date + timedelta(days=6 - day_of_week)
        date_range_str = self._format_date_range(first_date, last_date)
        pretty_name = f"week plan: {date_range_str}"
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        return self.plan_date + timedelta(weeks=n)

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


class MonthPlan(PlanWithDate):
    char_name = "m"

    def name(self):
        return f"month_{self.plan_date.month}_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"month plan: {self.plan_date.strftime('%b').lower()} {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        return self.plan_date + relativedelta(
            months=n
        )


class SemesterPlan(PlanWithDate):
    char_name = "s"

    def name(self):
        # TODO: Hardcoded for BYU because I need this to solve a problem
        #  for me right now and I don't have time to figure out how this is
        #  supposed to work beautifully for everyone everywhere.
        #  I'm only taking F/W, so this doesn't account for Sp/Su
        current_semester_name: str = "winter" if self.plan_date.month < 5 else "fall"
        return (
            f"semester_{current_semester_name}_{self.plan_date.year}"
        )

    def default_content(self):
        current_semester_name: str = "winter" if self.plan_date.month < 5 else "fall"
        pretty_name = (
            f"semester plan: {current_semester_name} {self.plan_date.year}"
        )
        return f"# {pretty_name}\n\n\n"

    def date_add(self, _):
        # No quick and easy way to increment semesters other than just going to the last semester
        return self.plan_date


class YearPlan(PlanWithDate):
    char_name = "y"

    def name(self):
        return f"year_{self.plan_date.year}"

    def default_content(self):
        pretty_name = f"year plan: {self.plan_date.year}"
        return f"# {pretty_name}\n\n\n"

    def date_add(self, n):
        return self.plan_date + relativedelta(
            years=n
        )


class LifePlan(PlanType):
    char_name = "l"

    def name(self):
        return "life"

    def default_content(self):
        return f"# life plan\n\n\n"


class ClutterPlan(PlanType):
    """
    Place to put "stuff" I don't want to get rid of but that I don't want to clutter `s` or `l` with.
    This will probably get pretty big.
    """

    char_name = "x"

    def name(self):
        return "clutter"

    def default_content(self):
        return "# clutter\n\n\n"


class PersistentWeeklyPlan(PlanType):
    char_name = "x"

    def name(self):
        return "persistent_weekly"

    def default_content(self):
        return "# persistent weekly structure\n\n\n"


PLAN_TYPES: List[PlanType] = [
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
    PersistentWeeklyPlan
]


def whats_the_plan(args: str = None) -> None:
    key, catalog = open_service_interactive(plan_service_name)
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

    date = (
        datetime.strptime(arg_parts[1], "%m.%d.%Y")
        if len(arg_parts) > 1
        else datetime.now()
    )

    names_to_open = []

    for plan_arg in plan_args:
        signed_difference = 0

        if len(plan_arg) > 1 and plan_arg[1] in ["+", "-"]:
            operator = plan_arg[1]
            # We hope plan_arg[2:] is a number but we don't really check
            signed_difference = eval(f"{operator}{plan_arg[2:]}")

        target_plan_type = None
        for plan_type in PLAN_TYPES:
            if plan_type.char_name == plan_arg[0]:
                target_plan_type = plan_type
                break

        if not target_plan_type:
            continue

        if issubclass(target_plan_type, PlanWithDate):
            plan_handler = target_plan_type(date)
            plan_handler.plan_date = plan_handler.date_add(signed_difference)
        else:
            plan_handler = target_plan_type()

        plan_name = plan_handler.name()
        if not document_in_catalog(
                plan_service_name, plan_name, key
        ):
            write_document(
                plan_handler.default_content(), plan_service_name, plan_name, key
            )

        names_to_open.append(plan_handler.name())

    edit_documents(plan_service_name, names_to_open, key)
