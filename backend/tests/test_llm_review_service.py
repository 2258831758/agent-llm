from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.app.services.llm_review_service import build_review_context_memory


class ReviewContextMemoryTests(unittest.TestCase):
    def test_build_review_context_memory_collects_linked_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            (project_path / "api.py").write_text(
                "\n".join(
                    [
                        "from service import process_user",
                        "",
                        "def handle(payload):",
                        "    return process_user(payload['name'])",
                    ]
                ),
                encoding="utf-8",
            )
            (project_path / "service.py").write_text(
                "\n".join(
                    [
                        "from db import run_query",
                        "",
                        "def process_user(name):",
                        "    sql = f\"select * from users where name = '{name}'\"",
                        "    return run_query(sql)",
                    ]
                ),
                encoding="utf-8",
            )
            (project_path / "db.py").write_text(
                "\n".join(
                    [
                        "def run_query(sql):",
                        "    return cursor.execute(sql)",
                    ]
                ),
                encoding="utf-8",
            )

            memory = build_review_context_memory(
                project_path=project_path,
                entrypoint="api.py",
                scan_results=[
                    {
                        "source": "Semgrep",
                        "severity": "HIGH",
                        "title": "Possible SQL injection",
                        "description": "user input reaches SQL string construction",
                        "file_path": "service.py",
                        "line_number": 4,
                        "cvss_score": 0.0,
                    }
                ],
            )

        selected_paths = {context_file.path for context_file in memory.files}
        self.assertIn("service.py", selected_paths)
        self.assertIn("api.py", selected_paths)
        self.assertIn("db.py", selected_paths)
        self.assertIn("entrypoint: api.py", memory.summary)
        self.assertTrue(any(note.startswith("service.py ->") for note in memory.relationship_notes))


if __name__ == "__main__":
    unittest.main()
