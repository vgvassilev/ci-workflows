#!/usr/bin/env python3
"""The patches a recipe applies to a version, read without a YAML parser.

Two things need them and must agree: the recipe's build, to apply them,
and compute_key.py, to hash them. Chosen by two pieces of code they would
drift, and the consequence is silent -- a key that does not move when a
patch the build applies does.

A recipe whose patches are per version names them in recipe.yaml:

  patches:
    glob: 'emscripten-clang{major}-*.patch'

`{major}` is the leading number of the cell's version and `{version}` the
version itself. Without the block, every file under patches/ applies.

Deliberately not under actions/lib/: every .py there is hashed into every
recipe's key, so a module added for one recipe would republish them all.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from bootstrap_block import grep_yaml_block_field


def selected_patches(recipe_dir: Path, version: str) -> list[Path]:
    """The files under `recipe_dir`/patches/ a cell of `version` applies.

    Sorted by their path relative to patches/, which is the order they
    apply in and the order compute_key hashes them in.
    """
    patches_dir = recipe_dir / "patches"
    if not patches_dir.is_dir():
        return []
    files = [p for p in patches_dir.rglob("*") if p.is_file()]
    pattern = grep_yaml_block_field(recipe_dir / "recipe.yaml",
                                    "patches", "glob")
    if pattern is not None:
        major = re.match(r"\d+", version)
        if "{major}" in pattern and major is None:
            raise ValueError(
                f"selected_patches: {recipe_dir / 'recipe.yaml'} selects "
                f"patches by {{major}}, but version '{version}' does not "
                f"start with one")
        pattern = pattern.replace("{version}", version)
        if major is not None:
            pattern = pattern.replace("{major}", major.group(0))
        files = [p for p in files if fnmatch.fnmatchcase(
            p.relative_to(patches_dir).as_posix(), pattern)]
    return sorted(files, key=lambda p: p.relative_to(patches_dir).as_posix())
