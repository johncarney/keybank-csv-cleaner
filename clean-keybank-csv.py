#!/usr/bin/env python3
import csv
import re
import sys

from collections.abc import Iterable
from datetime        import datetime
from io              import StringIO
from typing          import TextIO


REQUIRED_COLUMNS: list[str] = ["Date", "Description", "Amount", "Ref.#"]


class MissingRequiredColumnsError(Exception):
    pass


type Transaction = dict[str, str]


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: [python3] {sys.argv[0]} <input file> [<output file>]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = input_file
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        transactions = read_transactions(input_file, required_columns=REQUIRED_COLUMNS)
        cleaned_transactions = (fix_transaction_date(transaction) for transaction in transactions)
        write_transactions(
            cleaned_transactions, output_file=output_file, column_names=REQUIRED_COLUMNS
        )
    except MissingRequiredColumnsError as e:
        print(f"{input_file} is not a valid KeyBank CSV file.", file=sys.stderr)
        sys.exit(1)


def fix_transaction_date(transaction: Transaction) -> Transaction:
    """
    Convert a transaction record's "Date" field from MM/DD/YYYY to
    YYYY-MM-DD. If the transaction does not have a date field, or its
    format does not match MM/DD/YYYY, it will be returned unchanged.

    Note that this function does not attempt to distinguish between
    MM/DD/YYYY dates and DD/MM/YYYY dates, so it will treat the latter
    as if they were the former. This may result in a ValueError
    exception being raised for DD/MM/YYYY dates.

    Args:
        transaction (Transaction): The transaction record to fix.

    Returns:
        Transaction: The fixed transaction record.
    """
    date = transaction.get("Date", "").strip()
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", date) is None:
        return transaction

    date = datetime.strptime(date, "%m/%d/%Y")
    return transaction | {"Date": date.strftime("%Y-%m-%d")}


def read_transactions(input_file: str, required_columns: list[str]) -> list[Transaction]:
    """
    Read transactions from a CSV file.

    First looks for a CSV header line containing at least the
    required_columns, then reads the rest of the file as transactions.

    If there is no header line with the required columns, a
    MissingRequiredColumnsError exception will be raised.

    Args:
        input_file (str): The path to the input CSV file.
        required_columns (list[str]): A list of required column names.

    Returns:
        list[Transaction]: A list of transactions read from the file.
    """
    with open(input_file, mode="r") as input:
        column_names = read_column_names_from_file(input, required_columns=required_columns)
        reader = csv.DictReader(input, fieldnames=column_names)
        return [transaction for transaction in reader]


def write_transactions(
    transactions: Iterable[Transaction],
    output_file:  str,
    column_names: list[str]
) -> None:
    """
    Write transactions to a CSV file.

    Args:
        transactions (Iterable[Transaction]): The transactions to write.
        output_file (str): The path to the output CSV file.
        column_names (list[str]): A list of column names to include in the output.
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
