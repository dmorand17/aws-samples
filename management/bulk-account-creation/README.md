# Bulk Account Creation

Bulk-create AWS accounts from a CSV manifest and move each into a pre-existing
Organizational Unit (OU). Uses the AWS Organizations API directly — no Control
Tower required.

## Purpose

Automate the creation of multiple AWS accounts from a single CSV file. Each
account is created sequentially, polled until provisioning completes, and moved
into the target OU. The script exits non-zero if any account failed so it
integrates cleanly with CI pipelines.

## Prerequisites

- Run from the **Organizations management account** or a delegated administrator
  account with the required IAM permissions.
- [`uv`](https://docs.astral.sh/uv/) installed.
- Target OUs must **already exist** before running — this tool does not create OUs.

## Required IAM Permissions

```json
{
  "Effect": "Allow",
  "Action": [
    "organizations:CreateAccount",
    "organizations:DescribeCreateAccountStatus",
    "organizations:MoveAccount",
    "organizations:ListAccounts",
    "organizations:ListParents",
    "organizations:DescribeOrganizationalUnit",
    "sts:GetCallerIdentity"
  ],
  "Resource": "*"
}
```

## Manifest Format

The manifest is a CSV file with the following columns:

| Column         | Required | Description                                              |
|----------------|----------|----------------------------------------------------------|
| `account_name` | Yes      | Display name for the new account                         |
| `email`        | Yes      | Unique root email address for the account                |
| `ou_id`        | No       | Target OU ID; falls back to `--ou-id` if blank           |
| `role_name`    | No       | IAM role created in the account; falls back to `--role-name` if blank |

Any additional columns are passed as account tags.

See [`accounts.csv.sample`](accounts.csv.sample) for an example:

```csv
account_name,email,ou_id
Workload-Dev,aws+dev@example.com,ou-abcd-11111111
Workload-Staging,aws+staging@example.com,ou-abcd-11111111
Workload-Prod,aws+prod@example.com,
```

## Usage

### Run without cloning (uvx)

Run the tool directly from the repository with [`uvx`](https://docs.astral.sh/uv/guides/tools/)
— no clone or install required:

```bash
uvx --from "git+https://github.com/dmorand17/aws-samples.git#subdirectory=management/bulk-account-creation" \
  create-accounts --manifest accounts.csv --dry-run
```

The `--manifest` file is read from your current working directory, so keep your
CSV local. Pin to a tag or commit by appending `@<ref>` before the `#`, e.g.
`...aws-samples.git@v0.1.0#subdirectory=...`.

### Install as a tool

Install once with [`uv tool`](https://docs.astral.sh/uv/guides/tools/) to get a
`create-accounts` command on your `PATH`, then run it without the long URL:

```bash
uv tool install "git+https://github.com/dmorand17/aws-samples.git#subdirectory=management/bulk-account-creation"

create-accounts --manifest accounts.csv --dry-run
```

Upgrade with `uv tool upgrade bulk-account-creation`; remove with
`uv tool uninstall bulk-account-creation`.

### Run from a clone

```bash
# Dry run — validate manifest and OUs, create nothing
uv run create-accounts --manifest accounts.csv --dry-run

# Create accounts, print results as JSON to stdout (pipe or redirect as needed)
uv run create-accounts --manifest accounts.csv --output-format json > results.json

# Or write results directly to a file
uv run create-accounts --manifest accounts.csv \
  --output-format json --output-file results.json

# Use a default OU for rows without an explicit ou_id
uv run create-accounts --manifest accounts.csv \
  --ou-id ou-abcd-11111111 --output-format csv
```

Results in any format go to stdout by default; the progress bar is written to
stderr, so redirecting stdout to a file yields clean `csv`/`json`. Use
`--output-file` to write to a file instead.

### Options

| Option            | Default  | Description                                          |
|-------------------|----------|------------------------------------------------------|
| `--manifest`      | required | Path to the CSV manifest                             |
| `--ou-id`         | —        | Default target OU for rows without `ou_id`           |
| `--output-format` | `stdout` | Result format: `stdout`, `csv`, or `json`            |
| `--output-file`   | —        | Write results to this file instead of stdout         |
| `--dry-run`       | off      | Validate manifest and OUs without creating anything  |
| `--poll-interval` | 15.0     | Seconds between status polls per account             |
| `--timeout`       | 300.0    | Max seconds to wait for each account to provision    |
| `--role-name`     | `OrganizationAccountAccessRole` | IAM role name created in each new account |

## Caveats

- **Sequential creation.** Accounts are provisioned one at a time. AWS
  Organizations does not support concurrent `CreateAccount` requests from the
  same management account.
- **Idempotent re-runs.** Before provisioning, the tool lists existing accounts
  in the organization. Any manifest row whose email already belongs to an
  account is marked `SKIPPED` (with the existing account ID) and never
  re-created. Skips are not failures, so re-running the same manifest exits `0`.
  Email matching is case-insensitive. Note this skips creation only — it does
  **not** reconcile an existing account's OU placement or tags.
- **Accounts cannot be deleted.** AWS accounts can only be closed, not deleted.
  Closing an account is a manual process with a 90-day suspension period. Do not
  create accounts speculatively.

## Development

Dev tooling (`pytest`, `ruff`) is declared in the `dev` dependency group and
installed automatically on first `uv run`.

```bash
# Run the test suite
uv run pytest

# Lint
uv run ruff check
```
