import unittest
from typing import Optional

import aws_cdk as core
import pynamodb.models
from aws_cdk import Stack
from aws_cdk.assertions import Match, Template
from constructs import Construct

from cdk_pynamodb.cdk_pynamodb import PynamoDBTable
from ..pynamodb_tables import *

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_pynamodb/cdk_pynamodb_stack.py

CF_KEY_DYNAMODB = "AWS::DynamoDB::Table"


class PynamoDBTableStack(Stack):
    def __init__(self, scope: Construct, id_: str, model: pynamodb.models.Model):
        super().__init__(scope, id_)

        self.table = PynamoDBTable.from_pynamodb_model(self, pynamodb_model=model)


class TableTestCase(object):
    TABLE: pynamodb.models.Model

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.template: Optional[Template] = None

    def setUp(self) -> None:
        app = core.App()
        usertable_stack = PynamoDBTableStack(app, "cdk-pynamodb", model=self.TABLE)
        self.template = Template.from_stack(usertable_stack)

    def test_table_scheme(self):
        target_keys = [
            "KeySchema",
            "AttributeDefinitions",
        ]
        pynamodb_template: dict = self.TABLE.describe_table()

        for k, v in pynamodb_template.items():
            if k not in target_keys:
                continue
            if isinstance(v, list):
                for i in v:
                    self.template.has_resource_properties(
                        CF_KEY_DYNAMODB,
                        Match.object_like({k: Match.array_with([i])}),
                    )
            else:
                self.template.has_resource_properties(
                    CF_KEY_DYNAMODB, Match.object_like({k: v})
                )

    def test_index_scheme(self):
        index_keys = [
            "GlobalSecondaryIndexes",
            "LocalSecondaryIndexes",
        ]

        index_sub_keys = ["IndexName", "KeySchema", "Projection"]

        pynamodb_template: dict = self.TABLE.describe_table()

        for idx_key, idx_list in pynamodb_template.items():
            if idx_key not in index_keys:
                continue
            for idx in idx_list:
                for sk, sv in idx.items():
                    if sk not in index_sub_keys:
                        continue
                    if isinstance(sv, list):
                        for i in sv:
                            self.template.has_resource_properties(
                                CF_KEY_DYNAMODB,
                                Match.object_like(
                                    {
                                        idx_key: Match.array_with(
                                            [
                                                Match.object_like(
                                                    {sk: Match.array_with([i])}
                                                )
                                            ]
                                        )
                                    }
                                ),
                            )
                    else:
                        self.template.has_resource_properties(
                            CF_KEY_DYNAMODB,
                            Match.object_like(
                                {
                                    idx_key: Match.array_with(
                                        [Match.object_like({sk: sv})]
                                    )
                                }
                            ),
                        )

    def test_table_options(self):
        target_keys = ["ProvisionedThroughput", "BillingModeSummary"]
        pynamodb_template: dict = self.TABLE.describe_table()
        for k, v in pynamodb_template.items():
            if k not in target_keys:
                continue
            billingMode = pynamodb_template.get("BillingModeSummary", {}).get(
                "BillingMode", None
            )
            if k == "ProvisionedThroughput":
                if billingMode == "PAY_PER_REQUEST":
                    continue
                v = {
                    _k: _v
                    for _k, _v in v.items()
                    if _k in ("ReadCapacityUnits", "WriteCapacityUnits")
                }
            if k == "BillingModeSummary":
                k, v = "BillingMode", billingMode

            self.template.has_resource_properties(
                CF_KEY_DYNAMODB, Match.object_like({k: v})
            )


class UserTableTest(TableTestCase, unittest.TestCase):
    TABLE = UserTable


class ThreadTableTest(TableTestCase, unittest.TestCase):
    TABLE = Thread
