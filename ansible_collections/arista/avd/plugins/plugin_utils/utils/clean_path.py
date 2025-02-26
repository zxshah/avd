# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from pathlib import Path


def clean_path(path: Path) -> None:
    """Remove all files and directories from the given Path excluding the path itself."""
    # Return the same tmp_path as last time unless ansible cleaned it up in the meanwhile. Ansible maintains a separate local_tmp folder per play.
    for subpath in path.glob("*"):
        if subpath.is_dir():
            clean_path(subpath)
            subpath.rmdir()
        else:
            subpath.unlink()
