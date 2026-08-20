import unittest
from src.engine.models import Check, Severity
from src.engine.rules import generic_findings

class DiagnosticTruthTests(unittest.TestCase):
    def test_unknown_evidence_is_not_reported_as_ok(self):
        checks=[Check("Camera / Webcam",Severity.UNKNOWN,"Windows returned no usable device inventory.")]
        findings=generic_findings(checks)
        self.assertEqual(findings[0].severity, Severity.UNKNOWN)
        self.assertIn("inconclusive", findings[0].title.lower())

    def test_all_ok_can_report_ok(self):
        checks=[Check("Camera / Webcam",Severity.OK,"1 device found and no device-level error was reported.")]
        findings=generic_findings(checks)
        self.assertEqual(findings[0].severity, Severity.OK)

if __name__=="__main__": unittest.main()
