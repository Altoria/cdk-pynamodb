from pynamodb.attributes import UnicodeAttribute, UTCDateTimeAttribute
from pynamodb.indexes import (
    GlobalSecondaryIndex,
    LocalSecondaryIndex,
    AllProjection,
    KeysOnlyProjection,
)
from pynamodb.models import Model
from pynamodb.constants import PROVISIONED_BILLING_MODE, PAY_PER_REQUEST_BILLING_MODE
from datetime import datetime, timezone

__all__ = ["UserTable", "Thread"]


class UserTable(Model):
    class Meta:
        host = "http://localhost:8000"
        table_name = "user-table"
        billing_mode = PROVISIONED_BILLING_MODE
        read_capacity_units = 10
        write_capacity_units = 3

    user_id = UnicodeAttribute(hash_key=True)
    username = UnicodeAttribute()
    email = UnicodeAttribute(null=True)


class UserIDGSI(GlobalSecondaryIndex):
    class Meta:
        index_name = "user_id_gsi"
        projection = AllProjection()

    user_id = UnicodeAttribute(hash_key=True)


class UserIDLSI(LocalSecondaryIndex):
    class Meta:
        index_name = "user_id_lsi"
        projection = KeysOnlyProjection()

    created_at = UTCDateTimeAttribute(
        hash_key=True, default_for_new=datetime.now(tz=timezone.utc)
    )
    user_id = UnicodeAttribute(range_key=True)


class Thread(Model):
    class Meta:
        host = "http://localhost:8000"
        table_name = "thread_table"
        billing_mode = PAY_PER_REQUEST_BILLING_MODE

    created_at = UTCDateTimeAttribute(
        hash_key=True, default_for_new=datetime.now(tz=timezone.utc)
    )

    category = UnicodeAttribute(range_key=True)

    gsi_user_id = UserIDGSI()
    lsi_user_id = UserIDLSI()
    user_id = UnicodeAttribute()

    content = UnicodeAttribute(default="")


if __name__ == "__main__":
    UserTable.create_table()
    print(UserTable.describe_table())
    Thread.create_table()
