from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[1]


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def sync_write_exp() -> None:
    shared = ROOT / "_shared" / "write-exp"

    copy_file(shared / "SKILL.md", ROOT / "SKILL.md")
    copy_file(shared / "agents" / "openai.yaml", ROOT / "agents" / "openai.yaml")
    copy_file(
        shared / "references" / "mypwn-template.py",
        ROOT / "references" / "mypwn-template.py",
    )

    for mirror in [ROOT / "write-exp", ROOT / "Write-Exp-Skill"]:
        copy_file(shared / "SKILL.md", mirror / "SKILL.md")
        copy_file(shared / "agents" / "openai.yaml", mirror / "agents" / "openai.yaml")
        copy_file(
            shared / "references" / "mypwn-template.py",
            mirror / "references" / "mypwn-template.py",
        )


def sync_write_wp() -> None:
    shared = ROOT / "_shared" / "write-wp"

    for mirror in [ROOT / "write-wp", ROOT / "Write-WP-Skill"]:
        copy_tree(shared, mirror)


def main() -> None:
    sync_write_exp()
    sync_write_wp()


if __name__ == "__main__":
    main()
