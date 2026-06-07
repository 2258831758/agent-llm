from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.scanners import baseline
from backend.app.services.vulnerability_catalog import enrich_finding


class BaselineScannerTests(unittest.TestCase):
    def test_detects_php_unserialize(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "index.php").write_text(
                "<?php\n$payload = $_POST['payload'];\n$data = unserialize($payload);\n",
                encoding="utf-8",
            )

            findings = baseline.run(project_path)
            titles = [item["title"] for item in findings]
            self.assertIn("Unsafe PHP Deserialization", titles)

            finding = next(item for item in findings if item["title"] == "Unsafe PHP Deserialization")
            enriched = enrich_finding(finding, project_path)
            self.assertEqual(enriched["cwe_id"], "CWE-502")

    def test_detects_dom_xss_and_maps_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "app.js").write_text(
                "const target = document.getElementById('out');\n"
                "target.innerHTML = location.search;\n",
                encoding="utf-8",
            )

            findings = baseline.run(project_path)
            xss_finding = next(item for item in findings if item["title"] == "Potential Cross-Site Scripting (XSS)")
            enriched = enrich_finding(xss_finding, project_path)
            self.assertEqual(enriched["cwe_id"], "CWE-79")
            self.assertEqual(enriched["owasp_id"], "A03:2021")

    def test_detects_path_traversal_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "download.php").write_text(
                "<?php\n$file = $_GET['file'];\nreadfile($file);\n",
                encoding="utf-8",
            )

            findings = baseline.run(project_path)
            self.assertTrue(any(item["title"] == "Potential Path Traversal / File Inclusion" for item in findings))


if __name__ == "__main__":
    unittest.main()
