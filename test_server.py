import unittest
from unittest.mock import patch, MagicMock

import server


class FakeCursor:
    def __init__(self, result):
        self._result = result
        self.description = result[0]

    def execute(self, sql, params):
        pass

    def fetchall(self):
        return self._result[1]

    @property
    def rowcount(self):
        return len(self._result[1]) if self._result[1] else 1


class FakeConn:
    def __init__(self, result=([("a",)], [(1,)])):
        self._result = result
        self.committed = False

    def cursor(self):
        return FakeCursor(self._result)

    def commit(self):
        self.committed = True

    def close(self):
        pass


class TestServer(unittest.TestCase):
    @patch("server.psycopg2.connect", return_value=FakeConn())
    def test_query_select(self, _connect):
        req = server.QueryRequest(sql="SELECT a FROM t", database="zscan_app")
        out = server.execute_query(req)
        self.assertEqual(out["columns"], ["a"])
        self.assertEqual(out["rows"], [[1]])
        self.assertEqual(out["rowcount"], 1)

    @patch("server.psycopg2.connect", return_value=FakeConn(result=(None, None)))
    def test_query_write_commits(self, _connect):
        req = server.QueryRequest(sql="UPDATE t SET a=1", database="zscan_app")
        out = server.execute_query(req)
        self.assertEqual(out["columns"], [])
        self.assertTrue(_connect.return_value.committed)

    @patch("server.psycopg2.connect", side_effect=Exception("boom"))
    def test_query_error(self, _connect):
        req = server.QueryRequest(sql="BAD", database="zscan_app")
        with self.assertRaises(Exception):
            server.execute_query(req)

    def test_batch_partial_failure(self):
        def fake_connect(**kwargs):
            return FakeConn(result=(None, None))

        with patch("server.psycopg2.connect", side_effect=[fake_connect(), Exception("fail")]):
            req = server.BatchQueryRequest(
                queries=[
                    server.QueryRequest(sql="UPDATE t SET a=1"),
                    server.QueryRequest(sql="BAD"),
                ]
            )
            out = server.execute_batch(req)
        self.assertTrue(out["results"][0]["ok"])
        self.assertFalse(out["results"][1]["ok"])
        self.assertIn("fail", out["results"][1]["error"])


if __name__ == "__main__":
    unittest.main()