# SPDX-FileCopyrightText: Copyright (c) 2026 Yukihiko Shinoda
# SPDX-License-Identifier: MIT
"""Supplies AWS security credentials to Google workload identity federation through boto3."""

from typing import TYPE_CHECKING
from typing import override

import boto3
from google.auth.aws import AwsSecurityCredentials
from google.auth.aws import AwsSecurityCredentialsSupplier
from google.auth.exceptions import RefreshError

if TYPE_CHECKING:
    from google.auth.external_account import SupplierContext
    from google.auth.transport import Request


class Boto3AwsSecurityCredentialsSupplier(AwsSecurityCredentialsSupplier):
    """Supplies AWS security credentials resolved by boto3's credential provider chain.

    google-auth's built-in AWS credential source reads only environment variables or the EC2 metadata server, so it
    cannot use credentials resolved via credential_process (AWS_CONFIG_FILE), which the development container relies
    on. boto3 resolves both of them, and refreshes temporary credentials on its own, which also satisfies the
    supplier's requirement to cache credentials itself.
    """

    def __init__(self, session: boto3.Session | None = None) -> None:
        self.session = boto3.Session() if session is None else session

    @override
    def get_aws_security_credentials(self, context: "SupplierContext", request: "Request") -> AwsSecurityCredentials:
        credentials = self.session.get_credentials()
        frozen = None if credentials is None else credentials.get_frozen_credentials()
        if frozen is None or frozen.access_key is None or frozen.secret_key is None:
            msg = "AWS credentials were not found by boto3."
            # Reason: mypy strict mode rejects the call since google-auth leaves RefreshError's constructor
            # unannotated, while the supplier contract requires raising RefreshError:
            # - google.auth.aws module — google-auth documentation
            #   https://googleapis.dev/python/google-auth/latest/reference/google.auth.aws.html
            # - Check that no untyped functions are called [no-untyped-call] — mypy documentation
            #   https://mypy.readthedocs.io/en/stable/error_code_list2.html#check-that-no-untyped-functions-are-called-no-untyped-call
            raise RefreshError(msg)  # type: ignore[no-untyped-call]
        return AwsSecurityCredentials(frozen.access_key, frozen.secret_key, frozen.token)

    @override
    def get_aws_region(self, context: "SupplierContext", request: "Request") -> str:
        region = self.session.region_name
        if region is None:
            msg = "AWS region was not found by boto3."
            raise RefreshError(msg)
        return region
