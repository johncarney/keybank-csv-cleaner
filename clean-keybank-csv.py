#!/usr/bin/env python3
import csv
import sys

from datetime import datetime


def clean_row(row: dict[str, str]) -> dict[str, str]:
    date = row.get("Date", "").strip()
    if not date:
        return row

    date = datetime.strptime(date, "%m/%d/%Y")
    return row | {"Date": date.strftime("%Y-%m-%d")}


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: [python3] {sys.argv[0]} <input file> [<output file>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace(".csv", "-cleaned.csv")

    with open(input_file, mode="r") as file:
        for _ in range(2):
            next(file)

        reader = csv.DictReader(file)
        cleaned_data = [clean_row(row) for row in reader]

    columns = [column for column in cleaned_data[0].keys() if column and column.strip()]
    if columns[1:3] == ["Amount", "Description"]:
        columns[1:3] = reversed(columns[1:3])
    with open(output_file, mode="w") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(cleaned_data)


if __name__ == "__main__":
    main()
