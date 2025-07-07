#!/usr/bin/env python3
import csv
import re
import sys

from contextlib import contextmanager
from datetime   import datetime
from io         import StringIO


REQUIRED_COLUMNS: list[str] = ["Date", "Description", "Amount", "Ref.#"]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: [python3] {sys.argv[0]} <input file> [<output file>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".csv", "-cleaned.csv")
    clean_csv(input_file, output_file)


# Clean a Keybank CSV file by removing unnecessary lines, reformatting
# dates, and ensuring the correct order of columns.
def clean_csv(input_file: str, output_file: str) -> None:
    with open(input_file, mode="r") as input:
        with column_names_from_file(input) as column_names:
            reader = csv.DictReader(input, fieldnames=column_names)
            with open(output_file, mode="w", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS, extrasaction="ignore")
                writer.writeheader()
                for row in reader:
                    writer.writerow(clean_row(row))


# Clean a single row of a Keybank CSV file by reformatting the date from
# MM/DD/YYYY to YYYY-MM-DD. If the Date fields is empty, or does not
# match MM/DD/YYYY format, then return the row unaltered.
def clean_row(row: dict[str, str]) -> dict[str, str]:
    date = row.get("Date", "").strip()
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", date) is None:
        return row

    date = datetime.strptime(date, "%m/%d/%Y")
    return row | {"Date": date.strftime("%Y-%m-%d")}


@contextmanager
def column_names_from_file(file):
        column_names = get_column_names_from_file(file)
        if column_names:
            yield column_names


# Return the column names from the file. If there are no valid column
# names, return an empty list.
def get_column_names_from_file(file) -> list[str]:
    for row in file:
        columns = get_column_names_from_row(row)
        if columns:
            return columns

    return []


# Return the column names from a CSV row. If the row does not contain
# the required columns, return an empty list.
def get_column_names_from_row(row: str) -> list[str]:
    io = StringIO(row)
    reader = csv.reader(io)
    columns = next(reader, [])
    if set(columns).issuperset(REQUIRED_COLUMNS):
        return columns

    return []


if __name__ == "__main__":
    main()
