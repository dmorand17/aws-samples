"""Set dummy AWS credentials so botocore doesn't try live credential providers."""
import os

import pytest


@pytest.fixture(autouse=True)
def _aws_dummy_creds(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
