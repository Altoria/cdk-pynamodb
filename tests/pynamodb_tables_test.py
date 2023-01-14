import unittest
import uuid
from pynamodb_tables import *
from datetime import datetime, timezone


class MyTestCase(unittest.TestCase):
    def test_user_table_example(self):
        data = {
            "user_id": str(uuid.uuid4()),
            "username": "test_username",
            "email": "test@example.com",
        }

        UserTable.create_table()

        UserTable(**data).save()

        self.assertEqual(data, UserTable.get(data["user_id"]).attribute_values)

    def test_thread_table_example(self):
        data = {
            "created_at": datetime.now(tz=timezone.utc),
            "category": "social",
            "user_id": str(uuid.uuid4()),
            "content": "test contents...",
        }

        Thread.create_table()

        Thread(**data).save()

        self.assertEqual(
            data,
            Thread.get(data["created_at"], range_key=data["category"]).attribute_values,
        )


if __name__ == "__main__":
    unittest.main()
