"""Publish single-file exports only after the replacement is complete."""

from pathlib import Path
from uuid import uuid4


def write_atomic_output(path, writer):
    """Run writer(staging_path), validate its output, then replace *path*.

    The staging file has the same extension and directory as the destination,
    so CAD translators choose the right format and replacement stays on one
    filesystem. A failed export or replacement leaves the old output intact.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(f".{path.stem}-{uuid4().hex}{path.suffix}")
    try:
        result = writer(staging)
        if not staging.is_file() or staging.stat().st_size == 0:
            raise RuntimeError(f"Export produced no data for {path}")
        staging.replace(path)
        return result
    finally:
        if staging.exists():
            staging.unlink()
