import csv
from datetime import date, datetime, time
from typing import TextIO
from pathlib import Path
import dateutil.parser
import pyperclip
from dataclasses import dataclass

TODAY = date.today()
FILTERED_SUBJECTS = [
    "ADI Grooming",
    "Add Comments to tickets",
    "Create Tickets for Grooming",
    "Focus time",
    "Team Maverick Lunch",
    "Add Comments to tickets",
]


@dataclass
class Event:
    title: str
    start_time_str: str
    end_time_str: str

    def __post_init__(self):
        self.start_time = dateutil.parser.isoparse(self.start_time_str)
        self.end_time = dateutil.parser.isoparse(self.end_time_str)

    def __bool__(self) -> bool:
        return self.title in FILTERED_SUBJECTS

    @property
    def is_today(self) -> bool:
        return self.start_time.date() == TODAY


def main():
    output = ""
    with (
        Path(r"/Users/sjones/Downloads/calendar.csv").open(encoding="utf-8") as csv_file,
        Path(f"/Users/sjones/Downloads/daily_tasks/{TODAY.strftime('%Y_%m_%d')}.txt").open(
            "w"
        ) as output_file,
    ):
        csv_reader = csv.DictReader(csv_file, delimiter=",")

        todays_events = []
        no_lunch = False
        for row in csv_reader:
            event = Event(row["Event Title"], row["Start Time"], row["End Time"])
            if event and event.is_today:
                todays_events.append(event)
                if event.title == "Lunch" or event.start_time.hour == 11:
                    no_lunch = True
                if event.title == "Lunch":
                    event.title = "Matt Lunch"

        if not no_lunch:
            todays_events.append(
                Event(
                    "Lunch",
                    str(datetime.combine(TODAY, time(hour=11))),
                    str(datetime.combine(TODAY, time(hour=11, minute=30))),
                )
            )

        todays_events.sort(key=lambda event: event.start_time)

        for event in todays_events:
            if event.start_time.hour > 17:
                break
            output = write_out(
                f"- [ ] {datetime.strftime(event.start_time, '%H:%M')} {event.title} "
                f"\n- [ ] {datetime.strftime(event.end_time, '%H:%M')}",
                output_file,
                output,
            )

        write_out("- [ ] 17:00 BREAK", output_file, output)
        print(f"\n\nProcessed {len(todays_events)} lines.")
        pyperclip.copy(output)


def write_out(text: str, output_file: TextIO, all_lines: str):
    print(text)
    output_file.write(f"\ntext")
    all_lines += f"\n{text}"
    return all_lines


if __name__ == "__main__":
    main()
