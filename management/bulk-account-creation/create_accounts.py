"""Bulk-create AWS accounts from a CSV manifest and move each into an OU."""
import csv
import io
import json
import time
from dataclasses import dataclass, field

_REQUIRED_COLUMNS = ("account_name", "email")
_RESERVED_COLUMNS = ("account_name", "email", "ou_id")


@dataclass
class AccountSpec:
    account_name: str
    email: str
    ou_id: str | None
    tags: dict = field(default_factory=dict)


@dataclass
class AccountResult:
    account_name: str
    account_id: str | None
    status: str
    reason: str | None = None


_RESULT_FIELDS = ("account_name", "account_id", "status", "reason")


def format_results(results, output_format):
    if output_format == "json":
        return json.dumps(
            [
                {
                    "account_name": r.account_name,
                    "account_id": r.account_id,
                    "status": r.status,
                    "reason": r.reason,
                }
                for r in results
            ],
            indent=2,
        )
    if output_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_RESULT_FIELDS)
        for r in results:
            writer.writerow(
                [r.account_name, r.account_id or "", r.status, r.reason or ""]
            )
        return buffer.getvalue()
    # stdout: aligned table
    header = f"{'ACCOUNT':<24}{'ACCOUNT ID':<16}{'STATUS':<12}REASON"
    lines = [header]
    for r in results:
        lines.append(
            f"{r.account_name:<24}{(r.account_id or '-'):<16}"
            f"{r.status:<12}{r.reason or ''}"
        )
    return "\n".join(lines)


def verify_ous(client, ou_ids):
    missing = []
    for ou_id in ou_ids:
        try:
            client.describe_organizational_unit(OrganizationalUnitId=ou_id)
        except client.exceptions.OrganizationalUnitNotFoundException:
            missing.append(ou_id)
    if missing:
        raise ValueError(f"OU(s) not found: {', '.join(sorted(missing))}")


def provision_account(client, spec, poll_interval, timeout):
    kwargs = {"AccountName": spec.account_name, "Email": spec.email}
    if spec.tags:
        kwargs["Tags"] = [
            {"Key": k, "Value": v} for k, v in spec.tags.items()
        ]
    request_id = client.create_account(**kwargs)["CreateAccountStatus"]["Id"]

    deadline = time.monotonic() + timeout
    while True:
        status = client.describe_create_account_status(
            CreateAccountRequestId=request_id
        )["CreateAccountStatus"]
        state = status["State"]
        if state == "SUCCEEDED":
            account_id = status["AccountId"]
            break
        if state == "FAILED":
            return AccountResult(
                spec.account_name, None, "FAILED",
                status.get("FailureReason", "unknown"),
            )
        if time.monotonic() >= deadline:
            return AccountResult(
                spec.account_name, None, "FAILED",
                "timed out waiting for provisioning",
            )
        time.sleep(poll_interval)

    parent_id = client.list_parents(ChildId=account_id)["Parents"][0]["Id"]
    client.move_account(
        AccountId=account_id,
        SourceParentId=parent_id,
        DestinationParentId=spec.ou_id,
    )
    return AccountResult(spec.account_name, account_id, "SUCCEEDED", None)


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
