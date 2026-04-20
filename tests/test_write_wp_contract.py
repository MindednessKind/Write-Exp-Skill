from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRITE_WP = ROOT / "write-wp"
WRITE_WP_MIRROR = ROOT / "Write-WP-Skill"
WRITE_WP_SHARED = ROOT / "_shared" / "write-wp"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class WriteWpContractTests(unittest.TestCase):
    def test_write_wp_skill_exists_with_expected_core_files(self):
        self.assertTrue((WRITE_WP / "SKILL.md").is_file())
        self.assertTrue((WRITE_WP / "agents/openai.yaml").is_file())
        self.assertTrue((WRITE_WP / "references/style-signals.md").is_file())
        self.assertTrue((WRITE_WP / "references/sample-library/index.md").is_file())

    def test_write_wp_compatibility_directory_matches_primary(self):
        mirrored_paths = [
            "SKILL.md",
            "agents/openai.yaml",
            "references/style-signals.md",
            "references/sample-library/index.md",
        ]
        for rel_path in mirrored_paths:
            self.assertEqual(
                _read(WRITE_WP / rel_path),
                _read(WRITE_WP_SHARED / rel_path),
            )
            self.assertEqual(
                _read(WRITE_WP / rel_path),
                _read(WRITE_WP_MIRROR / rel_path),
            )

    def test_write_wp_skill_references_primary_and_expanded_corpus(self):
        text = _read(WRITE_WP / "SKILL.md")

        self.assertIn("待发表 Blog", text)
        self.assertIn("DailyNote", text)
        self.assertIn("Study -> Heap / Stack / Kernel", text)

    def test_sample_library_index_contains_study_sections(self):
        text = _read(WRITE_WP / "references/sample-library/index.md")

        self.assertIn("## Study", text)
        self.assertIn("### Heap", text)
        self.assertIn("### Stack", text)
        self.assertIn("### Kernel", text)
        self.assertIn("study.heap=", text)
        self.assertIn("study.stack=", text)


if __name__ == "__main__":
    unittest.main()
