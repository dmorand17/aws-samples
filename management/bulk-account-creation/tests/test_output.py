import csv
import io
import json
from create_accounts import AccountResult, format_results


RESULTS = [
    AccountResult("Dev", "111111111111", "SUCCEEDED", None),
    AccountResult("Prod", None, "FAILED", "EMAIL_ALREADY_EXISTS"),
]


def test_format_results_json_roundtrips():
    parsed = json.loads(format_results(RESULTS, "json"))
    assert parsed == [
        {"account_name": "Dev", "account_id": "111111111111",
         "status": "SUCCEEDED", "reason": None},
        {"account_name": "Prod", "account_id": None,
         "status": "FAILED", "reason": "EMAIL_ALREADY_EXISTS"},
    ]


def test_format_results_csv_has_header_and_rows():
    rows = list(csv.reader(io.StringIO(format_results(RESULTS, "csv"))))
    assert rows[0] == ["account_name", "account_id", "status", "reason"]
    assert rows[1] == ["Dev", "111111111111", "SUCCEEDED", ""]
    assert rows[2] == ["Prod", "", "FAILED", "EMAIL_ALREADY_EXISTS"]


def test_format_results_stdout_contains_names_and_status():
    text = format_results(RESULTS, "stdout")
    assert "Dev" in text and "SUCCEEDED" in text
    assert "Prod" in text and "FAILED" in text
