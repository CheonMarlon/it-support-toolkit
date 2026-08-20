import tempfile, unittest
from pathlib import Path
from src.engine.models import Check, Severity
from src.engine.rules import network_findings
from src.reports.io import save_session, export_text, export_json, export_html

class CoreTests(unittest.TestCase):
    def test_network_failure_rule(self):
        checks=[Check("IP Configuration",Severity.OK,"IPv4 available"),
                Check("Gateway Reachability",Severity.FAIL,"Gateway did not respond")]
        f=network_findings(checks)
        self.assertTrue(f)
        self.assertIn("gateway",f[0].title.lower())

    def test_report_files(self):
        with tempfile.TemporaryDirectory() as d:
            data={"ticket":"TEST","ticket_info":{"computer":"PC"},
                  "checks":[],"findings":[],"actions":[],"verification":"Not resolved"}
            self.assertTrue(save_session(d,data).exists())
            self.assertTrue(export_text(d,data).exists())
            self.assertTrue(export_json(d,data).exists())
            self.assertTrue(export_html(d,data).exists())

if __name__=="__main__":
    unittest.main()
