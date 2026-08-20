import pytest
from botocore.session import Session
from botocore.stub import Stubber

from create_accounts import (
    AccountResult,
    AccountSpec,
    existing_account_emails,
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
    with stubber, pytest.raises(ValueError, match="ou-bad"):
        verify_ous(client, ["ou-good", "ou-bad"])


def test_existing_account_emails_maps_lowercased_email_to_id():
    client = _org_client()
    stubber = Stubber(client)
    stubber.add_response(
        "list_accounts",
        {"Accounts": [
            {"Id": "111111111111", "Email": "Dev@Example.com"},
            {"Id": "222222222222", "Email": "prod@example.com"},
        ]},
        {},
    )
    with stubber:
        mapping = existing_account_emails(client)
    assert mapping == {
        "dev@example.com": "111111111111",
        "prod@example.com": "222222222222",
    }
    stubber.assert_no_pending_responses()


def test_provision_account_success_moves_into_ou():
    client = _org_client()
    stubber = Stubber(client)
    spec = AccountSpec("Dev", "dev@example.com", "ou-target", {"team": "plat"})

    stubber.add_response(
        "create_account",
        {"CreateAccountStatus": {"Id": "car-1", "State": "IN_PROGRESS"}},
        {"AccountName": "Dev", "Email": "dev@example.com",
         "RoleName": "OrganizationAccountAccessRole",
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
        {"AccountName": "Prod", "Email": "prod@example.com",
         "RoleName": "OrganizationAccountAccessRole"},
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


def test_provision_account_client_error_returns_failed_result():
    """A ClientError (e.g. throttle) must not propagate — returns FAILED result."""
    client = _org_client()
    stubber = Stubber(client)
    spec = AccountSpec("Throttled", "throttled@example.com", "ou-target", {})
    stubber.add_client_error(
        "create_account",
        service_error_code="TooManyRequestsException",
        expected_params={
            "AccountName": "Throttled",
            "Email": "throttled@example.com",
            "RoleName": "OrganizationAccountAccessRole",
        },
    )
    with stubber:
        result = provision_account(client, spec, poll_interval=0, timeout=30)
    assert result.status == "FAILED"
    assert result.reason == "TooManyRequestsException"
    assert result.account_id is None
    stubber.assert_no_pending_responses()
