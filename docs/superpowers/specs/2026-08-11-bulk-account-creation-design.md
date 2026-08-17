# Bulk AWS Account Creation Script — Design

**Date:** 2026-08-11
**Location:** `management/bulk-account-creation/`
**Status:** Approved for planning

## Purpose

Provide a reusable sample that creates *N* AWS accounts from a manifest and places
each into a specified, pre-existing Organizational Unit (OU). Control Tower is **not**
used — the script talks directly to the AWS Organizations API.

## Approach decision: script (not Terraform)

The intent is **one-time bulk creation** (fire-and-forget). AWS accounts cannot be
deleted — only closed, via a manual and throttled process — so a declarative,
stateful tool like Terraform would carry permanent state for resources it cannot
meaningfully destroy. A script matches the lifecycle intent and this repo's existing
script-based samples. Language is **Python (boto3)**, which handles the asynchronous
`CreateAccount` → poll → `MoveAccount` flow more cleanly than bash.

## Components

| File | Purpose |
|---|---|
| `create_accounts.py` | Main script: parse args, read manifest, orchestrate create→poll→move per account |
| `accounts.csv.sample` | Example manifest (`account_name,email,ou_id` + optional tag columns) |
| `requirements.txt` | `boto3` |
| `README.md` | Prereqs, IAM permissions, usage, caveats |
| `tests/` | Unit tests for pure logic using `botocore.stub.Stubber` |

## Inputs (CLI)

- `--manifest <path>` (required) — CSV manifest. Each row: `account_name`, `email`,
  and either a per-row `ou_id` or reliance on the global `--ou-id`.
- `--ou-id ou-xxxx` (optional) — default target OU for rows that omit `ou_id`.
- `--output-format {stdout,csv,json}` (default `stdout`) — result output format.
- `--output-file <path>` — destination for `csv`/`json` output (required when format is
  `csv` or `json`; ignored for `stdout`).
- `--dry-run` — validate manifest and verify referenced OU(s) exist; print planned
  actions; create nothing.
- `--timeout <seconds>` — max wait per account for provisioning (default 300).

The script must run from the AWS Organizations **management account** (or a delegated
administrator).

## Manifest format (CSV)

Required columns: `account_name`, `email`. Optional: `ou_id` (per-row override of
`--ou-id`). Optional additional columns interpreted as account tags. Emails must be
unique within the manifest.

## Flow

### Preflight (once)
1. `sts:GetCallerIdentity` to confirm credentials.
2. Parse and validate the manifest: non-empty, required fields present, emails unique.
3. Resolve the effective target OU per row (row `ou_id` or global `--ou-id`); error if a
   row has neither.
4. `DescribeOrganizationalUnit` for every referenced OU — **fail fast** if any is
   missing. OUs must already exist; the script never creates them.

### Per account (sequential)
Accounts are created one at a time — Organizations allows only one in-flight
`CreateAccount` per org, so concurrency provides no benefit.

1. `create_account(email, account_name, tags)` → returns `CreateAccountRequestId`.
2. Poll `describe_create_account_status` with exponential backoff until `SUCCEEDED` or
   `FAILED`, bounded by `--timeout`.
3. On `SUCCEEDED`: `move_account` from the org Root into the target OU.
4. Record result: account name, account id, status, and failure reason if any.

## Error handling

- **Idempotency:** Organizations returns the existing account for a duplicate email
  rather than erroring. On re-run of a partially failed manifest, the script detects the
  existing account and ensures correct OU placement instead of failing.
- **Partial failure:** a single account failure (e.g. `EMAIL_ALREADY_EXISTS`,
  throttling, provisioning failure) does not abort the run. The script continues,
  collects all results, prints/writes a summary, and exits non-zero if any account
  failed.
- **Throttling:** exponential backoff on `create_account` and status polling.

## Output

Per-account progress lines are logged to stderr during the run so they don't pollute
machine-readable output. Final results are emitted per `--output-format`:

- `stdout` (default): human-readable summary table (name / account id / status / reason).
- `csv`: rows written to `--output-file` with a header.
- `json`: array of result objects written to `--output-file`.

Exit code is non-zero if any account failed.

## IAM permissions required

`organizations:CreateAccount`, `organizations:DescribeCreateAccountStatus`,
`organizations:MoveAccount`, `organizations:ListRoots`,
`organizations:DescribeOrganizationalUnit`, `organizations:ListParents`,
`sts:GetCallerIdentity`.

## Testing

The script makes real, hard-to-undo AWS calls, so tests cover pure logic only, with no
live account creation:

- Manifest parsing and validation (missing fields, duplicate emails, tag columns,
  per-row vs. global OU resolution).
- Status-polling state machine and the create→poll→move orchestration, using
  `botocore.stub.Stubber` to simulate Organizations responses (`IN_PROGRESS` →
  `SUCCEEDED`, `FAILED`, duplicate-email idempotency).
- Output formatting for `stdout`, `csv`, and `json`.

Manual verification is documented via `--dry-run`.

## Out of scope

- Creating or modifying OU structure (OUs must pre-exist).
- Closing/deleting accounts.
- Control Tower / Account Factory integration.
- Baseline provisioning inside new accounts (guardrails, roles, networking).
