"""Runtime settings. Secrets come from env (local override) or SSM Parameter Store."""

from __future__ import annotations

import os

import boto3

DEFAULT_REGION = "us-east-2"
DEFAULT_API_KEY_PARAM = "/invoiceflow/dev/anthropic-api-key"


def aws_region() -> str:
    return os.environ.get("AWS_REGION", DEFAULT_REGION)


def anthropic_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    ssm = boto3.client("ssm", region_name=aws_region())
    name = os.environ.get("ANTHROPIC_API_KEY_PARAM", DEFAULT_API_KEY_PARAM)
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response["Parameter"]["Value"]
