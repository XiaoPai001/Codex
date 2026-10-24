#!/usr/bin/env python3
"""Install the review-flow skill for the current user."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SOURCE = REPO_ROOT / "skill" / "review-flow"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the review-flow Codex skill."
    )
    parser.add_argument("--model", help="Reviewer model ID")
    parser.add_argument("--effort", help="Reviewer reasoning effort")
    parser.add_argument(
        "--dest",
        type=Path,
        help="Install directory (default: ~/.agents/skills/review-flow)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing installation",
    )
    return parser.parse_args()


def install(args: argparse.Namespace) -> None:
    skill_file = SOURCE / "SKILL.md"
    if not skill_file.is_file():
        raise RuntimeError(f"Skill source not found at {SOURCE}")

    config_path = SOURCE / "references" / "config.json"
    with config_path.open(encoding="utf-8") as handle:
        config = json.load(handle)

    if args.model:
        config["reviewer_model"] = args.model
    if args.effort:
        config["reviewer_reasoning_effort"] = args.effort
    if not config.get("reviewer_model") or not config.get(
        "reviewer_reasoning_effort"
    ):
        raise RuntimeError(f"Reviewer configuration is incomplete: {config_path}")

    destination = (
        args.dest.expanduser().resolve()
        if args.dest
        else (Path.home() / ".agents" / "skills" / "review-flow").resolve()
    )
    if destination.name != "review-flow":
        raise RuntimeError(
            f"Refusing to install to a directory not named review-flow: {destination}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if not args.force:
            raise RuntimeError(
                f"{destination} already exists. Re-run with --force to replace it."
            )
        shutil.rmtree(destination)

    shutil.copytree(SOURCE, destination)
    installed_config = destination / "references" / "config.json"
    with installed_config.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(config, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Installed review-flow to {destination}")
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
