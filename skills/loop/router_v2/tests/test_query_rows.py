import sqlite3
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from query_rows import query_rows


class QueryRowsTest(unittest.TestCase):
    def test_grouped_sum(self):
        result = query_rows([{"x": 8}, {"x": 9}], "SELECT sum(x) AS total FROM input_rows")
        self.assertEqual(result["rows"], [{"total": 17}])

    def test_denies_other_resources_or_mutation(self):
        for sql in ["ATTACH ':memory:' AS other", "DELETE FROM input_rows",
                    "SELECT name FROM sqlite_master", "SELECT load_extension('x')"]:
            with self.subTest(sql=sql), self.assertRaises(sqlite3.Error):
                query_rows([{"x": 1}], sql)

    def test_rejects_inconsistent_rows(self):
        with self.assertRaises(ValueError):
            query_rows([{"x": 1}, {"y": 3}], "SELECT * FROM input_rows")


if __name__ == "__main__":
    unittest.main()
