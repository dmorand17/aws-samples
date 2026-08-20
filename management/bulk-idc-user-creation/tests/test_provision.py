import pytest
from botocore.session import Session
from botocore.stub import Stubber

from create_idc_users import (
    UserResult,
    UserSpec,
    existing_groups,
    existing_users,
    provision_user,
    resolve_identity_store_id,
)

STORE_ID = "d-1234567890"


def _idstore_client():
    return Session().create_client("identitystore", region_name="us-east-1")


def _ssoadmin_client():
    return Session().create_client("sso-admin", region_name="us-east-1")


def test_resolve_identity_store_id_uses_override():
    # No API call is made when an override is supplied.
    assert resolve_identity_store_id(None, "d-override") == "d-override"


def test_resolve_identity_store_id_discovers_single_instance():
    client = _ssoadmin_client()
    stubber = Stubber(client)
    stubber.add_response(
        "list_instances",
        {"Instances": [
            {"InstanceArn": "arn:aws:sso:::instance/ssoins-1234567890abcdef",
             "IdentityStoreId": STORE_ID}
        ]},
        {},
    )
    with stubber:
        assert resolve_identity_store_id(client, None) == STORE_ID
    stubber.assert_no_pending_responses()


def test_resolve_identity_store_id_raises_on_multiple_instances():
    client = _ssoadmin_client()
    stubber = Stubber(client)
    stubber.add_response(
        "list_instances",
        {"Instances": [
            {"InstanceArn": "arn:aws:sso:::instance/ssoins-111aaa",
             "IdentityStoreId": "d-111"},
            {"InstanceArn": "arn:aws:sso:::instance/ssoins-222bbb",
             "IdentityStoreId": "d-222"},
        ]},
        {},
    )
    with stubber, pytest.raises(ValueError, match="Multiple"):
        resolve_identity_store_id(client, None)


def test_existing_users_maps_lowercased_username_to_id():
    client = _idstore_client()
    stubber = Stubber(client)
    stubber.add_response(
        "list_users",
        {"Users": [
            {"UserId": "u-1", "UserName": "ALovelace",
             "IdentityStoreId": STORE_ID},
            {"UserId": "u-2", "UserName": "ghopper",
             "IdentityStoreId": STORE_ID},
        ]},
        {"IdentityStoreId": STORE_ID},
    )
    with stubber:
        mapping = existing_users(client, STORE_ID)
    assert mapping == {"alovelace": "u-1", "ghopper": "u-2"}
    stubber.assert_no_pending_responses()


def test_existing_groups_maps_lowercased_name_to_id():
    client = _idstore_client()
    stubber = Stubber(client)
    stubber.add_response(
        "list_groups",
        {"Groups": [
            {"GroupId": "g-1", "DisplayName": "Admins",
             "IdentityStoreId": STORE_ID},
            {"GroupId": "g-2", "DisplayName": "Developers",
             "IdentityStoreId": STORE_ID},
        ]},
        {"IdentityStoreId": STORE_ID},
    )
    with stubber:
        mapping = existing_groups(client, STORE_ID)
    assert mapping == {"admins": "g-1", "developers": "g-2"}
    stubber.assert_no_pending_responses()


def test_provision_user_creates_and_adds_groups():
    client = _idstore_client()
    stubber = Stubber(client)
    spec = UserSpec(
        "Ada", "Lovelace", "Ada Lovelace", "alovelace",
        "ada@example.com", ["Admins", "Developers"],
    )
    stubber.add_response(
        "create_user",
        {"UserId": "u-new", "IdentityStoreId": STORE_ID},
        {
            "IdentityStoreId": STORE_ID,
            "UserName": "alovelace",
            "Name": {"GivenName": "Ada", "FamilyName": "Lovelace"},
            "DisplayName": "Ada Lovelace",
            "Emails": [
                {"Value": "ada@example.com", "Type": "work", "Primary": True}
            ],
        },
    )
    stubber.add_response(
        "create_group_membership",
        {"MembershipId": "m-1", "IdentityStoreId": STORE_ID},
        {"IdentityStoreId": STORE_ID, "GroupId": "g-1",
         "MemberId": {"UserId": "u-new"}},
    )
    stubber.add_response(
        "create_group_membership",
        {"MembershipId": "m-2", "IdentityStoreId": STORE_ID},
        {"IdentityStoreId": STORE_ID, "GroupId": "g-2",
         "MemberId": {"UserId": "u-new"}},
    )
    group_map = {"admins": "g-1", "developers": "g-2"}
    with stubber:
        result = provision_user(client, STORE_ID, spec, None, group_map)
    assert result.username == "alovelace"
    assert result.user_id == "u-new"
    assert result.status == "CREATED"
    assert result.reason == "added to: Admins, Developers"
    stubber.assert_no_pending_responses()


def test_provision_user_missing_group_fails_without_creating():
    client = _idstore_client()
    stubber = Stubber(client)  # no responses added -> no API calls allowed
    spec = UserSpec(
        "Alan", "Turing", "Alan Turing", "aturing",
        "alan@example.com", ["Ghosts"],
    )
    with stubber:
        result = provision_user(
            client, STORE_ID, spec, None, {"admins": "g-1"}
        )
    assert result.status == "FAILED"
    assert "group(s) not found: Ghosts" in result.reason
    assert result.user_id is None
    stubber.assert_no_pending_responses()


def test_provision_user_existing_reconciles_missing_membership():
    client = _idstore_client()
    stubber = Stubber(client)
    spec = UserSpec(
        "Grace", "Hopper", "Grace Hopper", "ghopper",
        "grace@example.com", ["Admins", "Developers"],
    )
    # Already a member of Admins (g-1), needs Developers (g-2).
    stubber.add_response(
        "list_group_memberships_for_member",
        {"GroupMemberships": [
            {"GroupId": "g-1", "MembershipId": "m-x",
             "IdentityStoreId": STORE_ID}
        ]},
        {"IdentityStoreId": STORE_ID, "MemberId": {"UserId": "u-existing"}},
    )
    stubber.add_response(
        "create_group_membership",
        {"MembershipId": "m-new", "IdentityStoreId": STORE_ID},
        {"IdentityStoreId": STORE_ID, "GroupId": "g-2",
         "MemberId": {"UserId": "u-existing"}},
    )
    group_map = {"admins": "g-1", "developers": "g-2"}
    with stubber:
        result = provision_user(
            client, STORE_ID, spec, "u-existing", group_map
        )
    assert result.status == "UPDATED"
    assert result.user_id == "u-existing"
    assert result.reason == "added to: Developers"
    stubber.assert_no_pending_responses()


def test_provision_user_existing_fully_reconciled_is_skipped():
    client = _idstore_client()
    stubber = Stubber(client)
    spec = UserSpec(
        "Grace", "Hopper", "Grace Hopper", "ghopper",
        "grace@example.com", ["Developers"],
    )
    stubber.add_response(
        "list_group_memberships_for_member",
        {"GroupMemberships": [
            {"GroupId": "g-2", "MembershipId": "m-x",
             "IdentityStoreId": STORE_ID}
        ]},
        {"IdentityStoreId": STORE_ID, "MemberId": {"UserId": "u-existing"}},
    )
    with stubber:
        result = provision_user(
            client, STORE_ID, spec, "u-existing", {"developers": "g-2"}
        )
    assert result == UserResult(
        "ghopper", "u-existing", "SKIPPED", "already in all groups"
    )
    stubber.assert_no_pending_responses()


def test_provision_user_client_error_returns_failed_result():
    client = _idstore_client()
    stubber = Stubber(client)
    spec = UserSpec(
        "Ada", "Lovelace", "Ada Lovelace", "alovelace",
        "ada@example.com", [],
    )
    stubber.add_client_error(
        "create_user",
        service_error_code="ConflictException",
        expected_params={
            "IdentityStoreId": STORE_ID,
            "UserName": "alovelace",
            "Name": {"GivenName": "Ada", "FamilyName": "Lovelace"},
            "DisplayName": "Ada Lovelace",
            "Emails": [
                {"Value": "ada@example.com", "Type": "work", "Primary": True}
            ],
        },
    )
    with stubber:
        result = provision_user(client, STORE_ID, spec, None, {})
    assert result.status == "FAILED"
    assert result.reason == "ConflictException"
    assert result.user_id is None
    stubber.assert_no_pending_responses()
