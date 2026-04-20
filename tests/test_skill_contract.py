from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MIRRORS = [ROOT / "write-exp", ROOT / "Write-Exp-Skill", ROOT / "skills" / "write-exp"]
SYNCED_FILES = [
    Path("SKILL.md"),
    Path("references/mypwn-template.py"),
    Path("agents/openai.yaml"),
]
SHARED = ROOT / "_shared" / "write-exp"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_compatibility_directories_match_root(self):
        for rel_path in SYNCED_FILES:
            root_text = _read(ROOT / rel_path)
            self.assertEqual(root_text, _read(SHARED / rel_path))
            for mirror in MIRRORS:
                self.assertEqual(_read(mirror / rel_path), root_text)

    def test_repository_contains_no_symlinks(self):
        symlinks = [path for path in ROOT.rglob("*") if path.is_symlink()]
        self.assertEqual(symlinks, [])

    def test_skill_bans_new_start_helper_and_prefers_inline_iopen(self):
        text = _read(ROOT / "SKILL.md")

        self.assertIn("Do not introduce a fresh `start()` helper", text)
        self.assertIn("io = iopen(...)", text)

    def test_unknown_libc_guidance_does_not_assign_libc_address_without_an_elf(self):
        text = _read(ROOT / "SKILL.md")

        self.assertNotIn('libc.address = puts_addr - db.symbols["puts"]', text)
        self.assertIn('libc_base = puts_addr - db.symbols["puts"]', text)
        self.assertIn('system_addr = libc_base + db.dump("system")', text)

    def test_template_uses_inline_iopen_and_requires_explicit_pack_arch_for_remote_only(self):
        text = _read(ROOT / "references/mypwn-template.py")

        self.assertNotIn("def start(", text)
        self.assertIn("PACK_ARCH = None", text)
        self.assertIn(
            "Set FILE_NAME or PACK_ARCH before using Tool.get_arch_packer().",
            text,
        )
        self.assertNotIn("unpk, dopk, word_size = Tool.get_arch_packer(elf)", text)
        self.assertIn("unpk, dopk, word_size = resolve_packers()", text)
        self.assertIn("io = iopen(", text)


if __name__ == "__main__":
    unittest.main()
