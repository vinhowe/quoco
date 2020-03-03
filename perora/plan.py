from datetime import datetime, timedelta
from dateutil.relativedelta import *

from perora.document_manager import (
    document_in_catalog,
    password_prompt,
    write_document,
    edit_documents,
)

plan_service_name = "plan"


def week_number_of_month(date) -> int:
    """
    Thanks https://www.mytecbits.com/internet/python/week-number-of-month
    :param date:
    :return:
    """
    # Gets year week number of first day of the month and subtracts it from current year week number
    # Pretty clever
    return date.isocalendar()[1] - date.replace(day=1).isocalendar()[1] + 1


def format_date_range(date_1: datetime.date, date_2: datetime.date) -> str:
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


def whats_the_plan(args: str = None) -> None:
    key, catalog = password_prompt(plan_service_name)
    args = (
        f"d w m y l -- {datetime.now().strftime('%m.%d.%Y')}" if args is None else args
    )

    arg_parts = args.split(" -- ")

    plan_args = arg_parts[0]

    if len(plan_args) > 0:
        plan_args = plan_args.replace("k", "d w m y l")

    plan_args.split(" ")

    date = (
        datetime.strptime(arg_parts[1], "%m.%d.%Y")
        if len(arg_parts) > 1
        else datetime.now()
    )

    names_to_open = []

    for plan_arg in plan_args:
        current_plan_date = date
        signed_difference = 0

        if len(plan_arg) > 1 and plan_arg[1] in ["+", "-"]:
            operator = plan_arg[1]
            # We hope plan_arg[2:] is a number but we don't really check
            signed_difference = eval(f"{operator}{plan_arg[2:]}")

        if plan_arg[0] == "d":
            current_plan_date = current_plan_date + timedelta(days=signed_difference)

            day_plan_key = f"day_{current_plan_date.day}_{current_plan_date.month}_{current_plan_date.year}"

            if not document_in_catalog(plan_service_name, day_plan_key, key):
                pretty_name = f"day plan: {current_plan_date.strftime('%a').lower()} {current_plan_date.day} {current_plan_date.strftime('%b').lower()} {current_plan_date.year} "
                header = f"# {pretty_name}\n\n\n"
                write_document(header, plan_service_name, day_plan_key, key)
            names_to_open.append(day_plan_key)
        elif plan_arg[0] == "w":
            current_plan_date = current_plan_date + timedelta(weeks=signed_difference)

            week = week_number_of_month(current_plan_date)

            week_plan_key = f"week_{week}_{current_plan_date.month}_{current_plan_date.year}"
            if not document_in_catalog(plan_service_name, week_plan_key, key):
                # Do some logic so that the week starts on Sunday
                day_of_week = (current_plan_date.weekday() + 1) if current_plan_date.weekday() < 6 else 0
                first_date = current_plan_date - timedelta(days=day_of_week)
                last_date = current_plan_date + timedelta(days=6 - day_of_week)
                date_range_str = format_date_range(first_date, last_date)
                pretty_name = f"week plan: {date_range_str}"
                header = f"# {pretty_name}\n\n\n"
                write_document(header, plan_service_name, week_plan_key, key)

            day_plan_key = f"day_{current_plan_date.day}_{current_plan_date.month}_{current_plan_date.year}"

            if not document_in_catalog(plan_service_name, day_plan_key, key):
                pretty_name = f"day plan: {current_plan_date.strftime('%a').lower()} {current_plan_date.day} {current_plan_date.strftime('%b').lower()} {current_plan_date.year} "
                header = f"# {pretty_name}\n\n\n"
                write_document(header, plan_service_name, day_plan_key, key)

            names_to_open.append(week_plan_key)
        elif plan_arg[0] == "m":
            current_plan_date = current_plan_date + relativedelta(months=signed_difference)
            month_plan_key = f"month_{current_plan_date.month}_{current_plan_date.year}"
            if not document_in_catalog(plan_service_name, month_plan_key, key):
                pretty_name = f"month plan: {current_plan_date.strftime('%b').lower()} {current_plan_date.year}"
                header = f"# {pretty_name}\n\n\n"
                write_document(header, plan_service_name, month_plan_key, key)

            names_to_open.append(month_plan_key)
        elif plan_arg[0] == "y":
            current_plan_date = current_plan_date + relativedelta(years=signed_difference)

            year_plan_key = f"year_{current_plan_date.year}"
            if not document_in_catalog(plan_service_name, year_plan_key, key):
                pretty_name = f"year plan: {current_plan_date.year}"
                header = f"# {pretty_name}\n\n\n"
                write_document(header, plan_service_name, year_plan_key, key)
            names_to_open.append(year_plan_key)
        elif plan_arg[0] == "l":
            life_plan_key = "life"
            if not document_in_catalog(plan_service_name, life_plan_key, key):
                pretty_name = f"life plan"
                header = f"# {pretty_name}\n\n\n"
                write_document(header, plan_service_name, life_plan_key, key)
            names_to_open.append(life_plan_key)


    # life_plan_key = "life"
    # if not document_in_catalog(plan_service_name, life_plan_key, key):
    #     pretty_name = f"life plan"
    #     header = f"# {pretty_name}\n\n\n"
    #     write_document(header, plan_service_name, life_plan_key, key)
    #
    # year_plan_key = f"year_{date.year}"
    # if not document_in_catalog(plan_service_name, year_plan_key, key):
    #     pretty_name = f"year plan: {date.year}"
    #     header = f"# {pretty_name}\n\n\n"
    #     write_document(header, plan_service_name, year_plan_key, key)
    #
    # month_plan_key = f"month_{date.month}_{date.year}"
    # if not document_in_catalog(plan_service_name, month_plan_key, key):
    #     pretty_name = f"month plan: {date.strftime('%b').lower()} {date.year}"
    #     header = f"# {pretty_name}\n\n\n"
    #     write_document(header, plan_service_name, month_plan_key, key)
    #
    # week = week_number_of_month(date)
    # week_plan_key = f"week_{week}_{date.month}_{date.year}"
    # if not document_in_catalog(plan_service_name, week_plan_key, key):
    #     # Do some logic so that the week starts on Sunday
    #     day_of_week = (date.weekday() + 1) if date.weekday() < 6 else 0
    #     first_date = date - timedelta(days=day_of_week)
    #     last_date = date + timedelta(days=6 - day_of_week)
    #     date_range_str = format_date_range(first_date, last_date)
    #     pretty_name = f"week plan: {date_range_str}"
    #     header = f"# {pretty_name}\n\n\n"
    #     write_document(header, plan_service_name, week_plan_key, key)
    #
    # names_to_open = [
    #     day_plan_key,
    #     week_plan_key,
    #     month_plan_key,
    #     year_plan_key,
    #     life_plan_key,
    # ]

    edit_documents(plan_service_name, names_to_open, key)
