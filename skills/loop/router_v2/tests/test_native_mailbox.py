import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class NativeMailboxTest(unittest.TestCase):
    def test_model_replay_and_fresh_verification(self):
        script = Path(__file__).resolve().parents[1] / "native_mailbox.py"
        with tempfile.TemporaryDirectory() as directory:
            def call(action, *args, data=None):
                return subprocess.run([sys.executable, str(script), action, directory, *args],
                                      input=json.dumps(data), text=True, capture_output=True, check=True).stdout

            def issue(kind):
                return json.loads(call("issue", kind, data={"task": "read copy"}))["id"]

            route = issue("select")
            self.assertEqual(route, issue("select"))
            self.assertNotEqual(issue("verify"), issue("verify"))
            call("reply", route, data={"blocked": "provider unavailable"})
            self.assertEqual(json.loads(call("receive", route)), {"blocked": "provider unavailable"})
            self.assertNotIn(route, [item["id"] for item in json.loads(call("pending"))])
            with self.assertRaises(subprocess.CalledProcessError):
                call("reply", route, data={"rewritten": True})


if __name__ == "__main__":
    unittest.main()
