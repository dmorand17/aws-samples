"""Bulk-create IAM Identity Center users from a CSV manifest.

Each row describes a user and the group(s) they should belong to. Users are
created in the Identity Store and added to their groups. Re-runs are
idempotent: an existing user is not re-created, and only missing group
memberships are added.
"""
import csv
import io
import json
import sys
from dataclasses import dataclass, field

import boto3
import botocore.exceptions
import typer

_REQUIRED_COLUMNS = ("first_name", "last_name", "username", "email")
_GROUP_DELIMITER = ";"


@dataclass
class UserSpec:
    first_name: str
    last_name: str
    display_name: str
    username: str
    email: str
    groups: list[str] = field(default_factory=list)


@dataclass
class UserResult:
    username: str
    user_id: str | None
    status: str
    reason: str | None = None


_RESULT_FIELDS = ("username", "user_id", "status", "reason")


def format_results(results: list[UserResult], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(
            [
                {
                    "username": r.username,
                    "user_id": r.user_id,
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
                [r.username, r.user_id or "", r.status, r.reason or ""]
            )
        return buffer.getvalue()
    # stdout: aligned table
    header = f"{'USERNAME':<28}{'USER ID':<40}{'STATUS':<10}REASON"
    lines = [header]
    for r in results:
        lines.append(
            f"{r.username:<28}{(r.user_id or '-'):<40}"
            f"{r.status:<10}{r.reason or ''}"
        )
    return "\n".join(lines)


def resolve_identity_store_id(ssoadmin_client, override: str | None) -> str:
    """Return the Identity Store ID, discovering it if not supplied."""
    if override:
        return override
    instances = ssoadmin_client.list_instances()["Instances"]
    if not instances:
        raise ValueError(
            "No IAM Identity Center instance found in this account/region."
        )
    if len(instances) > 1:
        found = ", ".join(i["IdentityStoreId"] for i in instances)
        raise ValueError(
            "Multiple Identity Center instances found "
            f"({found}); pass --identity-store-id to choose one."
        )
    return instances[0]["IdentityStoreId"]


def existing_users(client, identity_store_id: str) -> dict[str, str]:
    """Map lowercased username -> user_id for every user in the store."""
    mapping = {}
    paginator = client.get_paginator("list_users")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        for user in page["Users"]:
            mapping[user["UserName"].lower()] = user["UserId"]
    return mapping


def existing_groups(client, identity_store_id: str) -> dict[str, str]:
    """Map lowercased group display name -> group_id for the store."""
    mapping = {}
    paginator = client.get_paginator("list_groups")
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        for group in page["Groups"]:
            mapping[group["DisplayName"].lower()] = group["GroupId"]
    return mapping


def _member_group_ids(client, identity_store_id: str, user_id: str) -> set[str]:
    """Return the set of group IDs the user already belongs to."""
    group_ids = set()
    paginator = client.get_paginator("list_group_memberships_for_member")
    for page in paginator.paginate(
        IdentityStoreId=identity_store_id, MemberId={"UserId": user_id}
    ):
        for membership in page["GroupMemberships"]:
            group_ids.add(membership["GroupId"])
    return group_ids


def _add_memberships(
    client, identity_store_id, user_id, target_group_ids, current_ids
) -> list[str]:
    """Add the user to each target group they are not already in."""
    added = []
    for name, group_id in target_group_ids.items():
        if group_id in current_ids:
            continue
        client.create_group_membership(
            IdentityStoreId=identity_store_id,
            GroupId=group_id,
            MemberId={"UserId": user_id},
        )
        added.append(name)
    return added


def _membership_reason(added: list[str], existing: bool) -> str | None:
    if added:
        return "added to: " + ", ".join(added)
    return "already in all groups" if existing else None


def provision_user(
    client,
    identity_store_id: str,
    spec: UserSpec,
    existing_user_id: str | None,
    group_map: dict[str, str],
) -> UserResult:
    """Create or reconcile one user and its group memberships.

    ``group_map`` maps lowercased group name -> group_id for existing groups.
    Every group named in the spec must already exist; a missing one fails the
    row without creating the user.
    """
    try:
        missing = [g for g in spec.groups if g.lower() not in group_map]
        if missing:
            return UserResult(
                spec.username,
                existing_user_id,
                "FAILED",
                f"group(s) not found: {', '.join(missing)}",
            )
        target_group_ids = {g: group_map[g.lower()] for g in spec.groups}

        if existing_user_id:
            current = _member_group_ids(
                client, identity_store_id, existing_user_id
            )
            added = _add_memberships(
                client, identity_store_id, existing_user_id,
                target_group_ids, current,
            )
            status = "UPDATED" if added else "SKIPPED"
            return UserResult(
                spec.username, existing_user_id, status,
                _membership_reason(added, existing=True),
            )

        user_id = client.create_user(
            IdentityStoreId=identity_store_id,
            UserName=spec.username,
            Name={
                "GivenName": spec.first_name,
                "FamilyName": spec.last_name,
            },
            DisplayName=spec.display_name,
            Emails=[{"Value": spec.email, "Type": "work", "Primary": True}],
        )["UserId"]
        added = _add_memberships(
            client, identity_store_id, user_id, target_group_ids, set()
        )
        return UserResult(
            spec.username, user_id, "CREATED",
            _membership_reason(added, existing=False),
        )
    except botocore.exceptions.ClientError as exc:
        return UserResult(
            spec.username, existing_user_id, "FAILED",
            exc.response["Error"]["Code"],
        )


def parse_manifest(path: str) -> list[UserSpec]:
    with open(path, newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("manifest is empty")

    specs = []
    seen_usernames = set()
    for index, row in enumerate(rows, start=2):  # row 1 is the header
        for column in _REQUIRED_COLUMNS:
            if not (row.get(column) or "").strip():
                raise ValueError(f"row {index}: missing {column}")
        username = row["username"].strip()
        if username.lower() in seen_usernames:
            raise ValueError(f"row {index}: duplicate username {username}")
        seen_usernames.add(username.lower())

        first_name = row["first_name"].strip()
        last_name = row["last_name"].strip()
        display_name = (
            (row.get("display_name") or "").strip()
            or f"{first_name} {last_name}"
        )
        groups = [
            g.strip()
            for g in (row.get("memberOf") or "").split(_GROUP_DELIMITER)
            if g.strip()
        ]
        specs.append(
            UserSpec(
                first_name,
                last_name,
                display_name,
                username,
                row["email"].strip(),
                groups,
            )
        )
    return specs


app = typer.Typer(
    help="Bulk-create IAM Identity Center users from a CSV manifest."
)


def _identitystore_client():
    return boto3.client("identitystore")


def _ssoadmin_client():
    return boto3.client("sso-admin")


def _sts_client():
    return boto3.client("sts")


@app.command()
def run(
    manifest: str = typer.Option(..., help="Path to the CSV manifest."),
    identity_store_id: str = typer.Option(
        None, help="Identity Store ID; auto-discovered when omitted."
    ),
    output_format: str = typer.Option(
        "stdout", help="Result output: stdout, csv, or json."
    ),
    output_file: str = typer.Option(
        None, help="Destination file for csv/json output."
    ),
    dry_run: bool = typer.Option(
        False, help="Validate and print the plan without creating users."
    ),
):
    if output_format not in ("stdout", "csv", "json"):
        raise typer.BadParameter("output-format must be stdout, csv, or json")

    try:
        specs = parse_manifest(manifest)
    except OSError as e:
        typer.echo(f"Cannot read manifest '{manifest}': {e.strerror}.", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    try:
        _sts_client().get_caller_identity()
    except (
        botocore.exceptions.NoCredentialsError,
        botocore.exceptions.ClientError,
    ) as exc:
        typer.echo(
            f"AWS credentials error: {exc}. Run 'aws login' (or refresh your "
            "session) and try again.",
            err=True,
        )
        raise typer.Exit(1)

    try:
        store_id = resolve_identity_store_id(
            _ssoadmin_client(), identity_store_id
        )
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1)

    idstore = _identitystore_client()
    try:
        users = existing_users(idstore, store_id)
        groups = existing_groups(idstore, store_id)
    except botocore.exceptions.ClientError as exc:
        typer.echo(
            "Unable to read the Identity Store (needs identitystore:ListUsers "
            f"and identitystore:ListGroups): {exc}",
            err=True,
        )
        raise typer.Exit(1)

    if dry_run:
        typer.echo("Dry run — no users will be created:")
        for spec in specs:
            missing = [g for g in spec.groups if g.lower() not in groups]
            existing_user_id = users.get(spec.username.lower())
            if missing:
                typer.echo(
                    f"  FAIL    {spec.username}  "
                    f"(missing groups: {', '.join(missing)})"
                )
            elif existing_user_id and spec.groups:
                typer.echo(
                    f"  UPDATE  {spec.username}  "
                    f"(exists: {existing_user_id}; ensure {', '.join(spec.groups)})"
                )
            elif existing_user_id:
                typer.echo(
                    f"  SKIP    {spec.username}  (exists: {existing_user_id})"
                )
            else:
                groups_note = (
                    f" -> {', '.join(spec.groups)}" if spec.groups else ""
                )
                typer.echo(f"  CREATE  {spec.username}{groups_note}")
        return

    results = []
    with typer.progressbar(
        specs,
        label="Creating users",
        item_show_func=lambda spec: spec.username if spec else "",
        file=sys.stderr,
    ) as progress:
        for spec in progress:
            results.append(
                provision_user(
                    idstore,
                    store_id,
                    spec,
                    users.get(spec.username.lower()),
                    groups,
                )
            )

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
