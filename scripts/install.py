#!/usr/bin/env python3
"""为当前用户安装仓库中的指定技能。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
# 仓库按用途分类，安装后仍使用技能的英文标识作为目录名。
SOURCES = {
    "review-flow": REPO_ROOT / "skills" / "development" / "review-flow",
    "re-notes": REPO_ROOT / "skills" / "reverse-engineering" / "re-notes",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="安装本仓库的 Codex 技能：独立代码审阅或逆向分析笔记整理。"
    )
    parser.add_argument("--skill", choices=SOURCES, default="review-flow", help="技能标识（默认：review-flow 独立代码审阅）")
    parser.add_argument("--model", help="审阅模型 ID，仅用于 review-flow")
    parser.add_argument("--effort", help="审阅推理强度，例如 xhigh（极高），仅用于 review-flow")
    parser.add_argument(
        "--dest",
        type=Path,
        help="安装目录（默认：~/.agents/skills/<技能标识>）",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="替换已有技能安装目录及其中的本地配置",
    )
    return parser.parse_args()


def install(args: argparse.Namespace) -> None:
    SOURCE = SOURCES[args.skill]
    skill_file = SOURCE / "SKILL.md"
    if not skill_file.is_file():
        raise RuntimeError(f"Skill source not found at {SOURCE}")

    config_path = SOURCE / "references" / "config.json"
    config = None
    if args.skill == "review-flow":
        with config_path.open(encoding="utf-8") as handle:
            config = json.load(handle)
    elif args.model or args.effort:
        raise RuntimeError("--model and --effort apply only to review-flow")

    if args.model:
        config["reviewer_model"] = args.model
    if args.effort:
        config["reviewer_reasoning_effort"] = args.effort
    if config is not None and (not config.get("reviewer_model") or not config.get(
        "reviewer_reasoning_effort"
    )):
        raise RuntimeError(f"Reviewer configuration is incomplete: {config_path}")

    destination = (
        args.dest.expanduser().resolve()
        if args.dest
        else (Path.home() / ".agents" / "skills" / args.skill).resolve()
    )
    # 仅允许安装到同名目录，且不得与仓库中的源目录重叠。
    if destination.name != args.skill:
        raise RuntimeError(
            f"Refusing to install to a directory not named {args.skill}: {destination}"
        )
    if destination == SOURCE or destination in SOURCE.parents or SOURCE in destination.parents:
        raise RuntimeError("Installation destination must not overlap skill source")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not args.force:
            raise RuntimeError(
                f"{destination} already exists. Re-run with --force to replace it."
            )
        shutil.rmtree(destination)

    shutil.copytree(SOURCE, destination)
    if config is not None:
        installed_config = destination / "references" / "config.json"
        with installed_config.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    print(f"Installed {args.skill} to {destination}")
    if config is not None:
        print(f"reviewer_model            = {config['reviewer_model']}")
        print(f"reviewer_reasoning_effort = {config['reviewer_reasoning_effort']}")
    print("Restart Codex or start a new chat if the skill does not appear.")


def main() -> int:
    try:
        install(parse_args())
    except (OSError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Install failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
