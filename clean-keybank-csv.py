#!/usr/bin/env python3
import csv
import functools
import re
import sys

from collections.abc import Iterable, Collection
from datetime        import datetime
from functools       import cached_property
from io              import StringIO
from typing          import TextIO


class MissingRequiredColumnsError(Exception):
    pass


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: [python3] {sys.argv[0]} <input file> [<output file>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = input_file
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        transactions = read_transactions(input_file, required_columns=Transaction.KEY_COLUMNS)
        write_transactions(
            sorted(transactions, reverse=True),
            output_file=output_file,
            column_names=Transaction.KEY_COLUMNS
        )
    except MissingRequiredColumnsError as e:
        print(f"{input_file} is not a valid KeyBank CSV file.", file=sys.stderr)
        sys.exit(1)


@functools.total_ordering
class Transaction(dict[str, str]):
    """
    A transaction record, represented as a dictionary with string keys
    and values. This class is used to represent a single transaction
    read from a KeyBank CSV file.
    """

    KEY_COLUMNS: tuple[str, ...] = ("Date", "Description", "Amount", "Ref.#")

    def __init__(self, attrs: dict[str, str] | None = None) -> None:
        attrs = attrs or {}
        if "Date" in attrs:
            attrs = attrs | {"Date": self.iso_date(attrs["Date"])}
        super().__init__(attrs)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented

        return self._index == other._index

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented

        return self._index < other._index

    @classmethod
    def iso_date(cls, raw_date: str) -> str:
        """
        Return the given date in ISO format (YYYY-MM-DD).
        If the date is not in the expected format, return an empty string.
        """
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw_date) is None:
            return raw_date

        date = datetime.strptime(raw_date, "%m/%d/%Y")
        return date.strftime("%Y-%m-%d")

    @cached_property
    def _index(self) -> tuple[str, ...]:
        return tuple([self[key] for key in self.KEY_COLUMNS])


def read_transactions(input_file: str, required_columns: Collection[str]) -> list[Transaction]:
    """
    Read transactions from a CSV file.

    First looks for a CSV header line containing at least the
    required_columns, then reads the rest of the file as transactions.

    If there is no header line with the required columns, a
    MissingRequiredColumnsError exception will be raised.

    Args:
        input_file (str): The path to the input CSV file.
        required_columns (Collection[str]): A collection of required column names.

    Returns:
        list[Transaction]: A list of transactions read from the file.
    """
    with open(input_file, mode="r") as input:
        column_names = read_column_names_from_file(input, required_columns=required_columns)
        reader = csv.DictReader(input, fieldnames=column_names)
        return [Transaction(transaction) for transaction in reader]


def write_transactions(
    transactions: Iterable[Transaction],
    output_file:  str,
    column_names: Collection[str]
) -> None:
    """
    Write transactions to a CSV file.

    Args:
        transactions (Iterable[Transaction]): The transactions to write.
        output_file (str): The path to the output CSV file.
        column_names (Collection[str]): A collection of column names to include in the output.
    """
    with open(output_file, mode="w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=column_names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(transactions)


def read_column_names_from_file(file: TextIO, required_columns: list[str]) -> list[str]:
    """
    Read the column names from a KeyBank CSV file. The columns must
    include at least the columns given in required_columns. If no such
    columns are found, an MissingRequiredColumnsError exception will be
    raised.

    As a useful side effect of this operation, the file pointer will be
    advanced to the first row after the header.

    Args:
        file (file-like object): The file to read from.

    Returns:
        list[str]: The column names found in the file.
    """
    column_set = frozenset(required_columns)
    for row in file:
        column_names = parse_csv_row(row)
        if column_set.issubset(column_names):
            return column_names

    raise MissingRequiredColumnsError("No valid column names found in the file.")


def parse_csv_row(row: str) -> list[str]:
    """
    Parse a CSV row and return the values as a list.

    Args:
        row (str): The CSV row to parse.

    Returns:
        list[str]: The values from the CSV row.
    """
    io = StringIO(row)
    reader = csv.reader(io)
    return next(reader, [])


if __name__ == "__main__":
    main()
