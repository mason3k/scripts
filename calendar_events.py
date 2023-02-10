import csv
from datetime import date, datetime, timedelta

import pyperclip

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
    with open(r"C:\Users\sjones\Downloads\test_calendar.CSV", encoding="utf-8") as csv_file, open(
        r"C:\Users\sjones\Downloads\daily_tasks\\" + filename, "w"
    ) as output_file:
        csv_reader = csv.DictReader(csv_file, delimiter=",")
        no_lunch = False

        todays_events = list(filter(good_row, csv_reader))

        for row in todays_events:
            if row['\ufeff"Subject"'] == "Lunch":
                no_lunch = True
                if "Gritters" in row["Meeting Organizer"]:
                    row['\ufeff"Subject"'] = "Matt Lunch"
            for key in ("Start Time", "End Time"):
                _convert_to_datetime(row, key)
            if (
                "Gritters" in row["Meeting Organizer"]
                or "Standup" in row['\ufeff"Subject"']
                or "Madeleine" in row["Required Attendees"]
            ):
                row["Start Time"] = row["Start Time"] - timedelta(hours=1)
                row["End Time"] = row["End Time"] - timedelta(hours=1)
            if row["Start Time"].hour == 11:
                no_lunch = True
        if not no_lunch:
            todays_events.append(
                {
                    '\ufeff"Subject"': "Lunch",
                    "Start Time": datetime(1900, 1, 1, 11, 0, 0),
                    "End Time": datetime(1900, 1, 1, 11, 30, 0),
                }
            )
        todays_events.sort(key=lambda one_row: one_row["Start Time"])

        for row in todays_events:
            if row["Start Time"].hour > 17:
                break
            start_time = datetime.strftime(row["Start Time"], "%H:%M")
            end_time = datetime.strftime(row["End Time"], "%H:%M")
            subject = row['\ufeff"Subject"']
            line = f"- [ ] {start_time} {subject} \n- [ ] {end_time}"
            print(line)
            output_file.write("\n" + line)
            output += f"\n{line}"
        print("- [ ] 17:00 BREAK")
        output += "\n- [ ] 17:00 BREAK"
        output_file.write("\n- [ ] 17:00 BREAK")

        print(f"\n\nProcessed {len(todays_events)} lines.")
        pyperclip.copy(output)


def good_row(row):
    return _row_is_today(row) and _not_filtered_subject(row) and _not_all_day(row)


def _convert_to_datetime(row, key):
    string_time = row[key]
    row[key] = datetime.strptime(string_time, "%I:%M:%S %p")


def _not_filtered_subject(row):
    try:
        return row['\ufeff"Subject"'] not in FILTERED_SUBJECTS
    except KeyError:
        return True


def _not_all_day(row):
    return row["All day event"] is not False


def _row_is_today(row):
    event_date = _convert_string_to_datetime(row["Start Date"])
    if event_date == TODAY:
        return True

    reminder_date = _convert_string_to_datetime(row["Reminder Date"])
    return event_date < TODAY and reminder_date == TODAY


def _convert_string_to_datetime(date_str):
    event_month, event_day, event_year = date_str.split("/")
    return date(int(event_year), int(event_month), int(event_day))


if __name__ == "__main__":
    main()
