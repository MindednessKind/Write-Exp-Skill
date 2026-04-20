from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WRITE_EXP = ROOT / "skills" / "write-exp"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class SkillContractTests(unittest.TestCase):
    def test_write_exp_skill_exists_with_expected_core_files(self):
        self.assertTrue((WRITE_EXP / "SKILL.md").is_file())
        self.assertTrue((WRITE_EXP / "agents/openai.yaml").is_file())
        self.assertTrue((WRITE_EXP / "references/mypwn-template.py").is_file())

    def test_repository_contains_no_symlinks(self):
        symlinks = [path for path in ROOT.rglob("*") if path.is_symlink()]
        self.assertEqual(symlinks, [])

    def test_skill_bans_new_start_helper_and_prefers_inline_iopen(self):
        text = _read(WRITE_EXP / "SKILL.md")

        self.assertIn("Do not introduce a fresh `start()` helper", text)
        self.assertIn("io = iopen(...)", text)

    def test_unknown_libc_guidance_does_not_assign_libc_address_without_an_elf(self):
        text = _read(WRITE_EXP / "SKILL.md")

        self.assertNotIn('libc.address = puts_addr - db.symbols["puts"]', text)
        self.assertIn('libc_base = puts_addr - db.symbols["puts"]', text)
        self.assertIn('system_addr = libc_base + db.dump("system")', text)

    def test_template_uses_inline_iopen_and_requires_explicit_pack_arch_for_remote_only(self):
        text = _read(WRITE_EXP / "references/mypwn-template.py")

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
