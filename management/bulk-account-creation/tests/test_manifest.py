import textwrap

import pytest

from create_accounts import AccountSpec, parse_manifest


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
