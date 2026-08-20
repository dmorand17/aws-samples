import json

import botocore.exceptions
import pytest
from typer.testing import CliRunner

import create_idc_users
from create_idc_users import UserResult, app, parse_manifest

runner = CliRunner()


class _FakeSts:
    def get_caller_identity(self):
        return {}


def _patch_common(monkeypatch, users=None, groups=None):
    """Stub AWS access so the CLI runs offline."""
    monkeypatch.setattr(
        create_idc_users, "_identitystore_client", lambda: object()
    )
    monkeypatch.setattr(
        create_idc_users, "_ssoadmin_client", lambda: object()
    )
    monkeypatch.setattr(create_idc_users, "_sts_client", lambda: _FakeSts())
    monkeypatch.setattr(
        create_idc_users, "resolve_identity_store_id",
        lambda c, o: "d-1234567890",
    )
    monkeypatch.setattr(
        create_idc_users, "existing_users", lambda c, s: users or {}
    )
    monkeypatch.setattr(
        create_idc_users, "existing_groups",
        lambda c, s: groups or {"admins": "g-1", "developers": "g-2"},
    )


def _manifest(tmp_path):
    p = tmp_path / "users.csv"
    p.write_text(
        "first_name,last_name,display_name,username,email,memberOf\n"
        "Ada,Lovelace,Ada Lovelace,alovelace,ada@example.com,Admins;Developers\n"
        "Grace,Hopper,,ghopper,grace@example.com,Developers\n"
    )
    return str(p)


def test_parse_manifest_splits_groups_and_defaults_display_name(tmp_path):
    specs = parse_manifest(_manifest(tmp_path))
    assert [s.username for s in specs] == ["alovelace", "ghopper"]
    assert specs[0].groups == ["Admins", "Developers"]
    assert specs[1].groups == ["Developers"]
    # Blank display_name falls back to "first last".
    assert specs[1].display_name == "Grace Hopper"


def test_parse_manifest_rejects_duplicate_username(tmp_path):
    p = tmp_path / "dup.csv"
    p.write_text(
        "first_name,last_name,display_name,username,email,memberOf\n"
        "Ada,Lovelace,,alovelace,ada@example.com,\n"
        "Ada,Byron,,ALovelace,ada2@example.com,\n"
    )
    with pytest.raises(ValueError, match="duplicate username"):
        parse_manifest(str(p))


def test_parse_manifest_requires_email(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text(
        "first_name,last_name,display_name,username,email,memberOf\n"
        "Ada,Lovelace,,alovelace,,Admins\n"
    )
    with pytest.raises(ValueError, match="missing email"):
        parse_manifest(str(p))


def test_cli_dry_run_creates_nothing(tmp_path, monkeypatch):
    _patch_common(monkeypatch)

    def _fail(*a, **k):
        raise AssertionError("provision_user must not run in dry-run")

    monkeypatch.setattr(create_idc_users, "provision_user", _fail)
    result = runner.invoke(app, ["--manifest", _manifest(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "CREATE" in result.stdout
    assert "alovelace" in result.stdout and "ghopper" in result.stdout


def test_cli_dry_run_flags_missing_group(tmp_path, monkeypatch):
    # 'developers' is absent, so Ada's row should be flagged FAIL.
    _patch_common(monkeypatch, groups={"admins": "g-1"})
    result = runner.invoke(app, ["--manifest", _manifest(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "FAIL" in result.stdout
    assert "missing groups: Developers" in result.stdout


def test_cli_dry_run_marks_existing_user(tmp_path, monkeypatch):
    _patch_common(monkeypatch, users={"alovelace": "u-1"})
    result = runner.invoke(app, ["--manifest", _manifest(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "UPDATE" in result.stdout  # alovelace exists, has groups
    assert "CREATE" in result.stdout  # ghopper is new


def test_cli_json_to_stdout_without_output_file(tmp_path, monkeypatch):
    _patch_common(monkeypatch)
    monkeypatch.setattr(
        create_idc_users, "provision_user",
        lambda c, s, spec, uid, gm: UserResult(
            spec.username, "u-x", "CREATED", "added to: Developers"
        ),
    )
    result = runner.invoke(
        app, ["--manifest", _manifest(tmp_path), "--output-format", "json"]
    )
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert [r["username"] for r in parsed] == ["alovelace", "ghopper"]


def test_cli_reports_failure_with_nonzero_exit(tmp_path, monkeypatch):
    _patch_common(monkeypatch)
    outcomes = iter([
        UserResult("alovelace", "u-1", "CREATED", None),
        UserResult("ghopper", None, "FAILED", "group(s) not found: Developers"),
    ])
    monkeypatch.setattr(
        create_idc_users, "provision_user",
        lambda c, s, spec, uid, gm: next(outcomes),
    )
    out = tmp_path / "o.json"
    result = runner.invoke(
        app,
        ["--manifest", _manifest(tmp_path),
         "--output-format", "json", "--output-file", str(out)],
    )
    assert result.exit_code == 1
    written = json.loads(out.read_text())
    assert [r["status"] for r in written] == ["CREATED", "FAILED"]


def test_cli_expired_credentials_exit_cleanly(tmp_path, monkeypatch):
    class _ExpiredSts:
        def get_caller_identity(self):
            raise botocore.exceptions.ClientError(
                {"Error": {"Code": "ExpiredToken", "Message": "token expired"}},
                "GetCallerIdentity",
            )

    monkeypatch.setattr(create_idc_users, "_sts_client", lambda: _ExpiredSts())
    result = runner.invoke(app, ["--manifest", _manifest(tmp_path), "--dry-run"])
    assert result.exit_code == 1
    assert "Traceback" not in (result.output or "")
    assert "credential" in result.output.lower()


def test_cli_missing_credentials_exit_cleanly(tmp_path, monkeypatch):
    class _NoCredsSts:
        def get_caller_identity(self):
            raise botocore.exceptions.NoCredentialsError()

    monkeypatch.setattr(create_idc_users, "_sts_client", lambda: _NoCredsSts())
    result = runner.invoke(app, ["--manifest", _manifest(tmp_path), "--dry-run"])
    assert result.exit_code == 1
    assert "Traceback" not in (result.output or "")
    assert "credential" in result.output.lower()


def test_cli_manifest_value_error_exits_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr(create_idc_users, "_sts_client", lambda: _FakeSts())
    bad = tmp_path / "bad.csv"
    bad.write_text(
        "first_name,last_name,display_name,username,email,memberOf\n"
        "Ada,Lovelace,,dup,a@example.com,\n"
        "Grace,Hopper,,dup,b@example.com,\n"
    )
    result = runner.invoke(app, ["--manifest", str(bad)])
    assert result.exit_code == 1
    assert "Traceback" not in (result.output or "")
