import csv
from datetime import date, datetime, timedelta, timezone
import pyperclip
import dateutil.parser
from typing import TextIO

TODAY = date.today()
FILTERED_SUBJECTS = [
    "ADI Grooming",
    "Add Comments to tickets",
    "Create Tickets for Grooming",
    "Focus time",
    "Team Maverick Lunch",
    "Add Comments to tickets",
]


def main():
    filename = TODAY.strftime("%Y_%m_%d") + ".txt"
    output = ""
    with (
        open(r"/Users/sjones/Downloads/calendar.csv", "r", encoding="utf-8") as csv_file,
        open(f"/Users/sjones/Downloads/daily_tasks/{filename}", "w") as output_file,
    ):
        csv_reader = csv.DictReader(csv_file, delimiter=",")

        todays_events = list(filter(good_row, csv_reader))
        handle_lunch(todays_events)
        todays_events.sort(key=lambda one_row: one_row["Start Time"])

        for row in todays_events:
            if row["Start Time"].hour > 17:
                break
            start_time = datetime.strftime(row["Start Time"], "%H:%M")
            end_time = datetime.strftime(row["End Time"], "%H:%M")
            subject = row["Event Title"]
            output = write_out(
                f"- [ ] {start_time} {subject} \n- [ ] {end_time}", output_file, output
            )

        write_out("- [ ] 17:00 BREAK", output_file, output)
        print(f"\n\nProcessed {len(todays_events)} lines.")
        pyperclip.copy(output)


def write_out(text: str, output_file: TextIO, running_output: str):
    print(text)
    output_file.write(f"\ntext")
    running_output += f"\n{text}"
    return running_output


def handle_lunch(todays_events):
    no_lunch = False
    for row in todays_events:
        if row["Event Title"] == "Lunch":
            no_lunch = True
            row["Event Title"] = "Matt Lunch"
        if row["Start Time"].hour == 11:
            no_lunch = True
    if not no_lunch:
        todays_events.append(
            {
                "Event Title": "Lunch",
                "Start Time": datetime(
                    day=TODAY.day,
                    month=TODAY.month,
                    year=TODAY.year,
                    hour=11,
                    minute=0,
                    tzinfo=timezone(-timedelta(hours=6)),
                ),
                "End Time": datetime(
                    day=TODAY.day,
                    month=TODAY.month,
                    year=TODAY.year,
                    hour=11,
                    minute=30,
                    tzinfo=timezone(-timedelta(hours=6)),
                ),
            }
        )


def good_row(row):
    return _row_is_today(row) and _not_filtered_subject(row)


def _convert_to_datetime(row, key):
    string_time = row[key]
    row[key] = dateutil.parser.isoparse(string_time)


def _not_filtered_subject(row):
    try:
        return row["Event Title"] not in FILTERED_SUBJECTS
    except KeyError:
        return True


def _row_is_today(row):
    for key in ["Start Time", "End Time"]:
        _convert_to_datetime(row, key)
    event_date = row["Start Time"].date()
    return event_date == TODAY


if __name__ == "__main__":
    main()
