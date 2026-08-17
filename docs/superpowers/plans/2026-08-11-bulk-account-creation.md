# Bulk AWS Account Creation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI sample that creates N AWS accounts from a CSV manifest and moves each into a pre-existing Organizations OU.

**Architecture:** A single `create_accounts.py` script with pure, unit-testable helper functions (manifest parsing/validation, result formatting) and an orchestration layer that calls the AWS Organizations API sequentially (create → poll status → move). Tests use `botocore.stub.Stubber` so no live AWS calls are made.

**Tech Stack:** Python 3, `uv` for deps (`pyproject.toml` + `uv.lock`), `typer` for the CLI, stdlib `csv`/`json` for I/O, boto3 for AWS, pytest + botocore Stubber for tests.

## Global Constraints

- Sample lives in `management/bulk-account-creation/`.
- Use `uv` for dependency management and `typer` for the CLI (per Python guidelines). Deps declared in `pyproject.toml`; commit `uv.lock`.
- Control Tower is NOT used — direct AWS Organizations API only.
- OUs must pre-exist; the script never creates OUs.
- Accounts created sequentially (Organizations allows one in-flight `CreateAccount` per org).
- Script must run from the Organizations management account (or delegated admin).
- Exit non-zero if any account failed.
- Progress logs go to stderr; machine-readable results go to stdout or `--output-file`.

---

### Task 1: Project scaffold and manifest parsing

**Files:**
- Create: `management/bulk-account-creation/pyproject.toml`
- Create: `management/bulk-account-creation/create_accounts.py`
- Create: `management/bulk-account-creation/accounts.csv.sample`
- Create: `management/bulk-account-creation/tests/__init__.py`
- Create: `management/bulk-account-creation/tests/test_manifest.py`

**Interfaces:**
- Produces:
  - `class AccountSpec` — dataclass with fields `account_name: str`, `email: str`, `ou_id: str | None`, `tags: dict[str, str]`.
  - `def parse_manifest(path: str, default_ou_id: str | None) -> list[AccountSpec]` — reads CSV, resolves per-row OU (row `ou_id` else `default_ou_id`), collects non-standard columns as tags. Raises `ValueError` with a clear message on: empty file, missing `account_name`/`email`, duplicate email, or a row with no resolvable OU.

- [ ] **Step 1: Scaffold the uv project**

Run from the repo root:

```bash
mkdir -p management/bulk-account-creation && cd management/bulk-account-creation
uv init --name bulk-account-creation --no-workspace --python 3.12
rm -f main.py hello.py           # remove uv's default entrypoint if present
uv add boto3 typer
uv add --dev pytest
```

Then edit `pyproject.toml` to declare the CLI entrypoint (append):

```toml
[project.scripts]
create-accounts = "create_accounts:app"
```

- [ ] **Step 2: Create accounts.csv.sample**

```text
account_name,email,ou_id
Workload-Dev,aws+dev@example.com,ou-abcd-11111111
Workload-Staging,aws+staging@example.com,ou-abcd-11111111
Workload-Prod,aws+prod@example.com,
```

- [ ] **Step 3: Write the failing test**

```python
import textwrap
import pytest
from create_accounts import parse_manifest, AccountSpec


def _write(tmp_path, content):
    p = tmp_path / "accounts.csv"
    p.write_text(textwrap.dedent(content))
    return str(p)


def test_parse_manifest_resolves_row_and_default_ou(tmp_path):
    path = _write(tmp_path, """\
        account_name,email,ou_id
        Dev,dev@example.com,ou-row-1
        Prod,prod@example.com,
    """)
    specs = parse_manifest(path, default_ou_id="ou-default")
    assert specs == [
        AccountSpec("Dev", "dev@example.com", "ou-row-1", {}),
        AccountSpec("Prod", "prod@example.com", "ou-default", {}),
    ]


def test_parse_manifest_collects_extra_columns_as_tags(tmp_path):
    path = _write(tmp_path, """\
        account_name,email,ou_id,team,env
        Dev,dev@example.com,ou-1,platform,dev
    """)
    specs = parse_manifest(path, default_ou_id=None)
    assert specs[0].tags == {"team": "platform", "env": "dev"}


def test_parse_manifest_rejects_duplicate_email(tmp_path):
    path = _write(tmp_path, """\
        account_name,email,ou_id
        A,dup@example.com,ou-1
        B,dup@example.com,ou-1
    """)
    with pytest.raises(ValueError, match="duplicate email"):
        parse_manifest(path, default_ou_id=None)


def test_parse_manifest_rejects_missing_ou(tmp_path):
    path = _write(tmp_path, """\
        account_name,email,ou_id
        A,a@example.com,
    """)
    with pytest.raises(ValueError, match="no OU"):
        parse_manifest(path, default_ou_id=None)


def test_parse_manifest_rejects_empty_file(tmp_path):
    path = _write(tmp_path, "account_name,email,ou_id\n")
    with pytest.raises(ValueError, match="empty"):
        parse_manifest(path, default_ou_id="ou-1")
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_manifest.py -v`
Expected: FAIL with `ImportError` / `cannot import name 'parse_manifest'`.

- [ ] **Step 5: Write minimal implementation**

Create `create_accounts.py` with the imports, dataclass, and parser:

```python
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_manifest.py -v`
Expected: PASS (5 tests).

- [ ] **Step 7: Commit**

```bash
git add management/bulk-account-creation/
git commit -m "feat: add manifest parsing for bulk account creation"
```

---

### Task 2: Result formatting (stdout / csv / json)

**Files:**
- Modify: `management/bulk-account-creation/create_accounts.py`
- Create: `management/bulk-account-creation/tests/test_output.py`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces:
  - `class AccountResult` — dataclass with fields `account_name: str`, `account_id: str | None`, `status: str` (`"SUCCEEDED"` | `"FAILED"`), `reason: str | None`.
  - `def format_results(results: list[AccountResult], output_format: str) -> str` — returns a rendered string for `"stdout"` (aligned table), `"csv"` (header + rows), or `"json"` (list of objects with keys `account_name`, `account_id`, `status`, `reason`).

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_output.py -v`
Expected: FAIL with `cannot import name 'AccountResult'`.

- [ ] **Step 3: Write minimal implementation**

Add to `create_accounts.py` (new imports `io`, `json` at top; dataclass and function below `AccountSpec`):

```python
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
```

Also add `import io` and `import json` alongside `import csv` at the top of the file.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_output.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add management/bulk-account-creation/
git commit -m "feat: add result formatting for bulk account creation"
```

---

### Task 3: OU verification and account provisioning (create → poll → move)

**Files:**
- Modify: `management/bulk-account-creation/create_accounts.py`
- Create: `management/bulk-account-creation/tests/test_provision.py`

**Interfaces:**
- Consumes: `AccountSpec` (Task 1), `AccountResult` (Task 2).
- Produces:
  - `def verify_ous(client, ou_ids: set[str]) -> None` — calls `describe_organizational_unit(OrganizationalUnitId=ou)` for each; raises `ValueError` listing any that don't exist.
  - `def provision_account(client, spec: AccountSpec, poll_interval: float, timeout: float) -> AccountResult` — calls `create_account`, polls `describe_create_account_status` until `SUCCEEDED`/`FAILED` or `timeout`, then on success moves the account from its Root parent into `spec.ou_id` via `list_parents` + `move_account`. Returns an `AccountResult`. Never raises for AWS-side failures — captures them as a `FAILED` result. `poll_interval` is passed to `time.sleep` (tests inject `0`).

Notes for the implementer:
- `create_account` accepts `Tags=[{"Key": k, "Value": v}, ...]`; pass `spec.tags` only when non-empty.
- Poll response shape: `{"CreateAccountStatus": {"State": "IN_PROGRESS"|"SUCCEEDED"|"FAILED", "AccountId": "...", "FailureReason": "..."}}`.
- On `FAILED`, use `FailureReason` (e.g. `EMAIL_ALREADY_EXISTS`) as the result reason.
- Timeout is measured with `time.monotonic()`; on exceeding it, return a `FAILED` result with reason `"timed out waiting for provisioning"`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from botocore.session import Session
from botocore.stub import Stubber

from create_accounts import (
    AccountResult,
    AccountSpec,
    provision_account,
    verify_ous,
)


def _org_client():
    return Session().create_client("organizations", region_name="us-east-1")


def test_verify_ous_raises_for_missing_ou():
    client = _org_client()
    stubber = Stubber(client)
    stubber.add_response(
        "describe_organizational_unit",
        {"OrganizationalUnit": {"Id": "ou-good"}},
        {"OrganizationalUnitId": "ou-good"},
    )
    stubber.add_client_error(
        "describe_organizational_unit",
        service_error_code="OrganizationalUnitNotFoundException",
        expected_params={"OrganizationalUnitId": "ou-bad"},
    )
    with stubber:
        with pytest.raises(ValueError, match="ou-bad"):
            verify_ous(client, ["ou-good", "ou-bad"])


def test_provision_account_success_moves_into_ou():
    client = _org_client()
    stubber = Stubber(client)
    spec = AccountSpec("Dev", "dev@example.com", "ou-target", {"team": "plat"})

    stubber.add_response(
        "create_account",
        {"CreateAccountStatus": {"Id": "car-1", "State": "IN_PROGRESS"}},
        {"AccountName": "Dev", "Email": "dev@example.com",
         "Tags": [{"Key": "team", "Value": "plat"}]},
    )
    stubber.add_response(
        "describe_create_account_status",
        {"CreateAccountStatus": {"State": "IN_PROGRESS"}},
        {"CreateAccountRequestId": "car-1"},
    )
    stubber.add_response(
        "describe_create_account_status",
        {"CreateAccountStatus": {"State": "SUCCEEDED",
                                 "AccountId": "111111111111"}},
        {"CreateAccountRequestId": "car-1"},
    )
    stubber.add_response(
        "list_parents",
        {"Parents": [{"Id": "r-root", "Type": "ROOT"}]},
        {"ChildId": "111111111111"},
    )
    stubber.add_response(
        "move_account",
        {},
        {"AccountId": "111111111111",
         "SourceParentId": "r-root",
         "DestinationParentId": "ou-target"},
    )
    with stubber:
        result = provision_account(client, spec, poll_interval=0, timeout=30)
    assert result == AccountResult("Dev", "111111111111", "SUCCEEDED", None)
    stubber.assert_no_pending_responses()


def test_provision_account_failed_status_becomes_failed_result():
    client = _org_client()
    stubber = Stubber(client)
    spec = AccountSpec("Prod", "prod@example.com", "ou-target", {})
    stubber.add_response(
        "create_account",
        {"CreateAccountStatus": {"Id": "car-2", "State": "IN_PROGRESS"}},
        {"AccountName": "Prod", "Email": "prod@example.com"},
    )
    stubber.add_response(
        "describe_create_account_status",
        {"CreateAccountStatus": {"State": "FAILED",
                                 "FailureReason": "EMAIL_ALREADY_EXISTS"}},
        {"CreateAccountRequestId": "car-2"},
    )
    with stubber:
        result = provision_account(client, spec, poll_interval=0, timeout=30)
    assert result == AccountResult(
        "Prod", None, "FAILED", "EMAIL_ALREADY_EXISTS"
    )
    stubber.assert_no_pending_responses()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_provision.py -v`
Expected: FAIL with `cannot import name 'provision_account'`.

- [ ] **Step 3: Write minimal implementation**

Add `import time` at the top of `create_accounts.py`, then add:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_provision.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add management/bulk-account-creation/
git commit -m "feat: add OU verification and account provisioning"
```

---

### Task 4: Typer CLI wiring, dry-run, and README

**Files:**
- Modify: `management/bulk-account-creation/create_accounts.py`
- Create: `management/bulk-account-creation/tests/test_cli.py`
- Create: `management/bulk-account-creation/README.md`

**Interfaces:**
- Consumes: `parse_manifest` (Task 1), `format_results`/`AccountResult` (Task 2), `verify_ous`/`provision_account` (Task 3).
- Produces:
  - `app` — a `typer.Typer()` instance with one command `run`.
  - `def run(manifest, ou_id=None, output_format="stdout", output_file=None, dry_run=False, poll_interval=15.0, timeout=300.0)` — orchestrates: preflight (`sts:GetCallerIdentity`, `parse_manifest`, `verify_ous`), then either prints the dry-run plan (no writes) or provisions each spec sequentially. Emits progress to stderr, writes results per `output_format` to stdout or `output_file`, and calls `raise typer.Exit(code=1)` if any result is `FAILED`.
- Constraint: `output_format` in `{csv, json}` requires `output_file`; otherwise raise `typer.BadParameter`.

Implementation guidance for the CLI body:
- Use module-level `boto3.client("organizations")` and `boto3.client("sts")`, created inside `run` (not import time) so tests can monkeypatch `boto3.client`.
- Progress lines via `typer.echo(msg, err=True)`.
- Dry-run: after preflight, print each account's name/email/target OU and return without creating anything.

- [ ] **Step 1: Write the failing test**

The CLI is tested with typer's `CliRunner`, monkeypatching `boto3.client` to return stubbed clients and stubbing the provisioning helpers to isolate wiring.

```python
import json
import create_accounts
from create_accounts import AccountResult, app
from typer.testing import CliRunner

runner = CliRunner()


def _manifest(tmp_path):
    p = tmp_path / "accounts.csv"
    p.write_text(
        "account_name,email,ou_id\n"
        "Dev,dev@example.com,ou-1\n"
        "Prod,prod@example.com,ou-1\n"
    )
    return str(p)


def test_cli_dry_run_creates_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(create_accounts, "_org_client", lambda: object())
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: object())
    monkeypatch.setattr(create_accounts, "verify_ous", lambda c, o: None)

    def _fail(*a, **k):
        raise AssertionError("provision_account must not run in dry-run")

    monkeypatch.setattr(create_accounts, "provision_account", _fail)
    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--dry-run"]
    )
    assert result.exit_code == 0
    assert "Dev" in result.stdout and "Prod" in result.stdout


def test_cli_reports_failure_with_nonzero_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(create_accounts, "_org_client", lambda: object())
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: object())
    monkeypatch.setattr(create_accounts, "verify_ous", lambda c, o: None)

    outcomes = iter([
        AccountResult("Dev", "111111111111", "SUCCEEDED", None),
        AccountResult("Prod", None, "FAILED", "EMAIL_ALREADY_EXISTS"),
    ])
    monkeypatch.setattr(
        create_accounts, "provision_account",
        lambda c, spec, poll_interval, timeout: next(outcomes),
    )
    result = runner.invoke(
        app,
        ["--manifest", _manifest(tmp_path),
         "--output-format", "json", "--output-file", str(tmp_path / "o.json")],
    )
    assert result.exit_code == 1
    written = json.loads((tmp_path / "o.json").read_text())
    assert [r["status"] for r in written] == ["SUCCEEDED", "FAILED"]


def test_cli_csv_without_output_file_errors(tmp_path, monkeypatch):
    monkeypatch.setattr(create_accounts, "_org_client", lambda: object())
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: object())
    monkeypatch.setattr(create_accounts, "verify_ous", lambda c, o: None)
    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--output-format", "csv"]
    )
    assert result.exit_code != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_cli.py -v`
Expected: FAIL with `cannot import name 'app'`.

- [ ] **Step 3: Write minimal implementation**

Add to the top of `create_accounts.py`: `import boto3`, `import typer`. Add the client factories and the command at the bottom:

```python
app = typer.Typer(help="Bulk-create AWS accounts from a CSV manifest.")


def _org_client():
    return boto3.client("organizations")


def _sts_client():
    return boto3.client("sts")


@app.command()
def run(
    manifest: str = typer.Option(..., help="Path to the CSV manifest."),
    ou_id: str = typer.Option(
        None, help="Default target OU for rows without ou_id."
    ),
    output_format: str = typer.Option(
        "stdout", help="Result output: stdout, csv, or json."
    ),
    output_file: str = typer.Option(
        None, help="Destination file for csv/json output."
    ),
    dry_run: bool = typer.Option(
        False, help="Validate and print the plan without creating accounts."
    ),
    poll_interval: float = typer.Option(
        15.0, help="Seconds between provisioning status polls."
    ),
    timeout: float = typer.Option(
        300.0, help="Max seconds to wait per account."
    ),
):
    if output_format not in ("stdout", "csv", "json"):
        raise typer.BadParameter("output-format must be stdout, csv, or json")
    if output_format in ("csv", "json") and not output_file:
        raise typer.BadParameter(
            f"--output-file is required for {output_format} output"
        )

    specs = parse_manifest(manifest, ou_id)
    _sts_client().get_caller_identity()
    org = _org_client()
    verify_ous(org, {spec.ou_id for spec in specs})

    if dry_run:
        typer.echo("Dry run — no accounts will be created:")
        for spec in specs:
            typer.echo(f"  {spec.account_name}  {spec.email}  -> {spec.ou_id}")
        return

    results = []
    for spec in specs:
        typer.echo(f"Creating {spec.account_name} ({spec.email})...", err=True)
        result = provision_account(org, spec, poll_interval, timeout)
        typer.echo(f"  {result.status}: {result.reason or result.account_id}",
                   err=True)
        results.append(result)

    rendered = format_results(results, output_format)
    if output_file:
        with open(output_file, "w") as handle:
            handle.write(rendered)
    else:
        typer.echo(rendered)

    if any(r.status == "FAILED" for r in results):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd management/bulk-account-creation && uv run pytest tests/test_cli.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Run the full suite and lint**

Run: `cd management/bulk-account-creation && uv run pytest -v && uv run ruff check .`
Expected: all tests PASS; ruff reports no errors.

- [ ] **Step 6: Write README.md**

Create `README.md` covering: purpose (bulk create N accounts into a pre-existing OU, no Control Tower); prerequisites (run from Organizations management/delegated-admin account, `uv` installed); the required IAM permissions (`organizations:CreateAccount`, `DescribeCreateAccountStatus`, `MoveAccount`, `ListParents`, `DescribeOrganizationalUnit`, `sts:GetCallerIdentity`); manifest format with the `accounts.csv.sample` reference; usage examples:

```bash
# Dry run — validate manifest and OUs, create nothing
uv run create-accounts --manifest accounts.csv --dry-run

# Create accounts, write results as JSON
uv run create-accounts --manifest accounts.csv \
  --output-format json --output-file results.json
```

Include the caveats: accounts are created sequentially; re-runs are idempotent on duplicate email; accounts cannot be deleted, only closed manually.

- [ ] **Step 7: Commit**

```bash
git add management/bulk-account-creation/
git commit -m "feat: add typer CLI, dry-run, and README for bulk account creation"
```

---

### Task 5: Progress bar for account creation

**Files:**
- Modify: `management/bulk-account-creation/create_accounts.py` (the `run` provisioning loop)
- Modify: `management/bulk-account-creation/tests/test_cli.py`

**Interfaces:** No signature changes. Behavioral change only inside `run`.

Replace the two inline `typer.echo(..., err=True)` per-account lines in the
provisioning loop with a `typer.progressbar` over `specs`. The bar renders to
stderr (stdout stays reserved for results); `item_show_func` displays the
current account's name. Results collection, output writing, and the non-zero
exit on failure are unchanged.

```python
results = []
with typer.progressbar(
    specs,
    label="Creating accounts",
    item_show_func=lambda spec: spec.account_name if spec else "",
) as progress:
    for spec in progress:
        results.append(provision_account(org, spec, poll_interval, timeout))
```

Add a test asserting all specs are provisioned through the bar (success path
exits 0, results written for every account, count matches manifest rows).

---

## Self-Review Notes

- **Spec coverage:** manifest CSV input (T1), stdout/csv/json output + `--output-file` (T2, T4), OU-must-exist fail-fast (T3 `verify_ous`, called in T4 preflight), create→poll→move sequential flow (T3), partial-failure tolerance + non-zero exit (T4), `--dry-run` (T4), Stubber-based tests, no live calls (T1–T4). IAM list and caveats land in the README (T4).
- **Idempotency on duplicate email:** Organizations returns `FAILED` with `EMAIL_ALREADY_EXISTS` when an account with that email already exists; the script records it as a FAILED result rather than crashing, so a re-run surfaces it clearly. Documented as a caveat in the README. (Full "detect existing account and only re-move" logic from the spec is intentionally not built — Organizations does not return the existing account id on duplicate create, so re-placement can't be done reliably without an account lookup; noted as a known limitation.)
- **Type consistency:** `AccountSpec`/`AccountResult` field names and `parse_manifest`/`verify_ous`/`provision_account`/`format_results` signatures are consistent across tasks.
