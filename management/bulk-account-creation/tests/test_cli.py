import json

import botocore.exceptions
from typer.testing import CliRunner

import create_accounts
from create_accounts import AccountResult, app

runner = CliRunner()


class _FakeSts:
    def get_caller_identity(self):
        return {}


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
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _FakeSts())
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
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _FakeSts())
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
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _FakeSts())
    monkeypatch.setattr(create_accounts, "verify_ous", lambda c, o: None)
    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--output-format", "csv"]
    )
    assert result.exit_code != 0


def test_cli_success_path_writes_all_results(tmp_path, monkeypatch):
    monkeypatch.setattr(create_accounts, "_org_client", lambda: object())
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _FakeSts())
    monkeypatch.setattr(create_accounts, "verify_ous", lambda c, o: None)

    outcomes = iter([
        AccountResult("Dev", "111111111111", "SUCCEEDED", None),
        AccountResult("Prod", "222222222222", "SUCCEEDED", None),
    ])
    monkeypatch.setattr(
        create_accounts, "provision_account",
        lambda c, spec, poll_interval, timeout: next(outcomes),
    )
    output_file = tmp_path / "out.json"
    result = runner.invoke(
        app,
        ["--manifest", _manifest(tmp_path),
         "--output-format", "json", "--output-file", str(output_file)],
    )
    assert result.exit_code == 0
    written = json.loads(output_file.read_text())
    assert len(written) == 2
    assert all(r["status"] == "SUCCEEDED" for r in written)
    assert [r["account_name"] for r in written] == ["Dev", "Prod"]


def test_cli_role_name_sets_spec_role(tmp_path, monkeypatch):
    """--role-name reaches each spec; default is OrganizationAccountAccessRole."""
    monkeypatch.setattr(create_accounts, "_org_client", lambda: object())
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _FakeSts())
    monkeypatch.setattr(create_accounts, "verify_ous", lambda c, o: None)

    seen = []

    def _capture(c, spec, poll_interval, timeout):
        seen.append(spec.role_name)
        return AccountResult(spec.account_name, "111111111111", "SUCCEEDED", None)

    monkeypatch.setattr(create_accounts, "provision_account", _capture)

    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--role-name", "CustomRole"]
    )
    assert result.exit_code == 0
    assert seen == ["CustomRole", "CustomRole"]

    seen.clear()
    result = runner.invoke(app, ["--manifest", _manifest(tmp_path)])
    assert result.exit_code == 0
    assert seen == ["OrganizationAccountAccessRole", "OrganizationAccountAccessRole"]


def test_cli_expired_credentials_exit_cleanly(tmp_path, monkeypatch):
    """Expired/invalid credentials exit 1 with a friendly message, no traceback."""
    class _ExpiredSts:
        def get_caller_identity(self):
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "ExpiredToken", "Message": "token expired"}},
                "GetCallerIdentity",
            )

    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _ExpiredSts())
    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--dry-run"]
    )
    assert result.exit_code == 1
    assert "Traceback" not in (result.output or "")
    assert "credential" in result.output.lower()


def test_cli_missing_credentials_exit_cleanly(tmp_path, monkeypatch):
    """No configured credentials exit 1 with a friendly message, no traceback."""
    class _NoCredsSts:
        def get_caller_identity(self):
            raise botocore.exceptions.NoCredentialsError()

    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _NoCredsSts())
    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--dry-run"]
    )
    assert result.exit_code == 1
    assert "Traceback" not in (result.output or "")
    assert "credential" in result.output.lower()


def test_cli_manifest_value_error_exits_cleanly(tmp_path, monkeypatch):
    """A duplicate email in the manifest should exit 1 with no traceback."""
    monkeypatch.setattr(create_accounts, "_org_client", lambda: object())
    monkeypatch.setattr(create_accounts, "_sts_client", lambda: _FakeSts())

    bad_manifest = tmp_path / "bad.csv"
    bad_manifest.write_text(
        "account_name,email,ou_id\n"
        "A,dup@example.com,ou-1\n"
        "B,dup@example.com,ou-1\n"
    )
    result = runner.invoke(app, ["--manifest", str(bad_manifest)])
    assert result.exit_code == 1
    assert "Traceback" not in (result.output or "")
