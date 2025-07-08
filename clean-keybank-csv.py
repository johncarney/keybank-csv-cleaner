#!/usr/bin/env python3

import csv
import functools
import re
import sys

from collections.abc import Iterable, Collection
from datetime        import datetime
from functools       import cached_property
from itertools       import zip_longest
from typing          import IO


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


def read_transactions(input_file: str, required_columns: Collection[str]) -> list["Transaction"]:
    with open(input_file, mode="r") as input:
        reader = TransactionReader(input, required_columns=required_columns)
        return list(reader)


def write_transactions(
    transactions: Iterable["Transaction"],
    output_file:  str,
    column_names: Collection[str]
) -> None:
    with open(output_file, mode="w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=column_names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows((transaction.data for transaction in transactions))


@functools.total_ordering
class Transaction:
    KEY_COLUMNS: tuple[str, ...] = ("Date", "Description", "Amount", "Ref.#")
    DATE_COLUMN: str             = "Date"

    def __init__(self, data: dict[str, str] | None = None) -> None:
        self.data = data or {}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented

        return self._index == other._index

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Transaction):
            return NotImplemented

        return self._index < other._index

    @cached_property
    def _index(self) -> tuple[str, ...]:
        return tuple([self.data[key] for key in self.KEY_COLUMNS])


class TransactionReader:
    def __init__(
        self,
        input_io:         IO,
        required_columns: Collection[str] = Transaction.KEY_COLUMNS,
        date_column:      str = Transaction.DATE_COLUMN
    ) -> None:
        self.input_io = input_io
        self.required_columns = required_columns
        self.date_column = date_column
        self._reader = csv.reader(self.input_io)

    def __iter__(self):
        return self

    @cached_property
    def column_names(self) -> list[str]:
        column_set = frozenset(self.required_columns)
        for row in self._reader:
            if column_set.issubset(row):
                return row

        raise MissingRequiredColumnsError("Required columns not found in the file.")

    def dialect(self):
        return self._reader.dialect

    def line_num(self):
        return self._reader.line_num

    def __next__(self) -> Transaction:
        column_count = len(self.column_names)

        row = next(self._reader)[:column_count]
        transaction = dict(zip_longest(self.column_names, row, fillvalue=""))
        if self.date_column in transaction:
            transaction[self.date_column] = self.iso_date(transaction[self.date_column])
        return Transaction(transaction)

    @staticmethod
    def iso_date(raw_date: str) -> str:
        """
        Convert a date string in MM/DD/YYYY format to ISO format (YYYY-MM-DD).
        If the date is not in the expected format, return it unchanged.
        """
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", raw_date) is None:
            return raw_date

        date = datetime.strptime(raw_date, "%m/%d/%Y")
        return date.strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()
