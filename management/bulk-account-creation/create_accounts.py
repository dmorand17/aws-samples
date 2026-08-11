"""Bulk-create AWS accounts from a CSV manifest and move each into an OU."""
import csv
from dataclasses import dataclass, field

_REQUIRED_COLUMNS = ("account_name", "email")
_RESERVED_COLUMNS = ("account_name", "email", "ou_id")


@dataclass
class AccountSpec:
    account_name: str
    email: str
    ou_id: str | None
    tags: dict = field(default_factory=dict)


def parse_manifest(path, default_ou_id):
    with open(path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("manifest is empty")

    specs = []
    seen_emails = set()
    for index, row in enumerate(rows, start=2):  # row 1 is the header
        for column in _REQUIRED_COLUMNS:
            if not (row.get(column) or "").strip():
                raise ValueError(f"row {index}: missing {column}")
        email = row["email"].strip()
        if email in seen_emails:
            raise ValueError(f"row {index}: duplicate email {email}")
        seen_emails.add(email)

        ou_id = (row.get("ou_id") or "").strip() or default_ou_id
        if not ou_id:
            raise ValueError(f"row {index}: no OU (set ou_id or --ou-id)")

        tags = {
            key: value.strip()
            for key, value in row.items()
            if key not in _RESERVED_COLUMNS and (value or "").strip()
        }
        specs.append(
            AccountSpec(row["account_name"].strip(), email, ou_id, tags)
        )
    return specs
