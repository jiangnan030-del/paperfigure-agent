# SPDX-License-Identifier: MIT
import unittest

from paperfig.qa import audit_spec
from paperfig.spec import load_spec


class QATests(unittest.TestCase):
    def test_unknown_reference_license_is_informational_when_nothing_is_copied(self) -> None:
        spec = load_spec("examples/specs/grouped_bar.yaml")
        issues = audit_spec(spec)
        relevant = [item for item in issues if item.rule_id == "REFERENCE_LICENSE_UNVERIFIED"]
        self.assertEqual(1, len(relevant))
        self.assertEqual("info", relevant[0].severity)
        self.assertFalse(any(item.severity == "error" for item in issues))


if __name__ == "__main__":
    unittest.main()
