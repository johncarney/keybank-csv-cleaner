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

    required_columns = KeyBankTransaction.KEY_COLUMNS

    try:
        transactions = read_transactions(input_file, required_columns=required_columns)
        write_transactions(
            sorted(transactions, reverse=True),
            output_file=output_file,
            column_names=required_columns
        )
    except MissingRequiredColumnsError as e:
        print(f"{input_file} is not a valid KeyBank CSV file.", file=sys.stderr)
        sys.exit(1)


def read_transactions(
    input_file:       str,
    required_columns: Collection[str]
) -> list["KeyBankTransaction"]:
    with open(input_file, mode="r") as input:
        reader = KeyBankTransactionReader(input, required_columns=required_columns)
        return list(reader)


def write_transactions(
    transactions: Iterable["KeyBankTransaction"],
    output_file:  str,
    column_names: Collection[str]
) -> None:
    with open(output_file, mode="w", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=column_names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(
            (transaction.data for transaction in transactions if not transaction.is_blank)
        )


@functools.total_ordering
class KeyBankTransaction:
    KEY_COLUMNS: tuple[str, ...] = ("Date", "Description", "Amount", "Ref.#")
    DATE_COLUMN: str             = "Date"

    def __init__(self, data: dict[str, str] | None = None) -> None:
        self.data = data or {}

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyBankTransaction):
            return NotImplemented

        return self._index == other._index

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, KeyBankTransaction):
            return NotImplemented

        return self._index < other._index

    @cached_property
    def is_blank(self) -> bool:
        return all(value == "" for value in self._index)

    @cached_property
    def _index(self) -> tuple[str, ...]:
        return tuple([self.data.get(key, "").strip() for key in self.KEY_COLUMNS])


class KeyBankTransactionReader:
    """
    A CSV reader for KeyBank transaction files that ensures required
    columns are present and converts date formats to ISO format.

    Required columns are specified by the `required_columns` parameter,
    and the date column is specified by the `date_column` parameter.

    If the required columns are not found in the file, a
    MissingRequiredColumnsError is raised. The date in the specified
    date column is converted from MM/DD/YYYY format to ISO format
    (YYYY-MM-DD).

    Example usage:

    ```python
    with open("transactions.csv", mode="r") as input_file:
        reader = TransactionReader(input_file)
        for transaction in reader:
            print(transaction)
    ```
    """
    def __init__(
        self,
        input_io:         IO,
        required_columns: Collection[str] = KeyBankTransaction.KEY_COLUMNS,
        date_column:      str = KeyBankTransaction.DATE_COLUMN
    ) -> None:
        self.input_io = input_io
        self.required_columns = required_columns
        self.date_column = date_column
        self._reader = csv.reader(self.input_io)

    def __iter__(self):
        return self

    @cached_property
    def column_names(self) -> list[str]:
        """
        Return the column names from the CSV file.

        Each line of the file is read until a header row containing all
        required columns is found. If no such header is found, a
        MissingRequiredColumnsError is raised. The header row may
        contain additional columns beyond the required ones and the
        columns do not need to be in any particular order.

        Returns:
            list[str]: A list of column names from the CSV file.

        Raises:
            MissingRequiredColumnsError: If the required columns are not found in the file.
        """
        column_set = frozenset(self.required_columns)
        for row in self._reader:
            if column_set.issubset(row):
                return row

        raise MissingRequiredColumnsError("Required columns not found in the file.")

    def __next__(self) -> KeyBankTransaction:
        column_count = len(self.column_names)

        row = next(self._reader)
        transaction = dict(zip_longest(self.column_names, row[:column_count], fillvalue=""))
        if self.date_column in transaction:
            transaction[self.date_column] = self.iso_date(transaction[self.date_column])
        return KeyBankTransaction(transaction)

    def dialect(self):
        return self._reader.dialect

    def line_num(self):
        return self._reader.line_num

    @staticmethod
    def iso_date(raw_date: str) -> str:
        """
        Converts a date string in MM/DD/YYYY format to ISO format
        (YYYY-MM-DD). If the date is not in the expected format, returns
        it unchanged.

        Note that this function does not attempt to distinguish between
        MM/DD/YYYY and DD/MM/YYYY dates and will treat the later as if
        they were the former.
        """
        return re.sub(r"\A\s*(\d{2})/(\d{2})/(\d{4})\s*\Z", r"\3-\1-\2", raw_date)


if __name__ == "__main__":
    main()
