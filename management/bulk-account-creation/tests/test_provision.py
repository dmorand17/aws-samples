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
