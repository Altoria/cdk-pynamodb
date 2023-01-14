============
CDK PynamoDB
============

AWS CDK Construct for DynamoDB Table from PynamoDB Model.

Streamline DynamoDB create and deploy with PynamoDB and AWS CDK.

This package provides a construct for creating a DynamoDB table using the AWS CDK and PynamoDB models.
It simplifies the process of creating and deploying DynamoDB tables in your AWS environment.

Define your tables in a reusable and predictable way with infrastructure-as-code.


Installation
============
From PyPi::

    $ pip install cdk-pynamodb

From GitHub::

    $ pip install git+https://github.com/altoria/cdk-pynamoDB#egg=cdk-pynamodb



Basic Usage
===========

Create a model that describes your DynamoDB table.

.. code-block:: python3

    from pynamodb.models import Model

    class UserTable(Model):
        class Meta:
            host = "http://localhost:8000"
            table_name = "user-table"
            billing_mode = PROVISIONED_BILLING_MODE
            read_capacity_units = 10
            write_capacity_units = 3

        user_id = UnicodeAttribute(hash_key=True)
        email = UnicodeAttribute(null=True)

Now, you can import and construct model in AWS CDK

.. code-block:: python3

    from cdk_pynamodb import PynamoDBTable

    from models import UserTable

    from aws_cdk import Stack
    from constructs import Construct

    class Database(Stack):
        def __init__(self, scope: Construct, id_: str):
            super().__init__(scope, id_)

            self.table = PynamoDBTable.from_pynamodb_model(self, pynamodb_model=UserTable)
