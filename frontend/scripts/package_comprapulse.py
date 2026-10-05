"""Create a deterministic, fail-closed Hostinger upload archive."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASE = ROOT / "release"
ARCHIVE = RELEASE / "comprapulse-hostinger.zip"
CHECKSUM = RELEASE / "comprapulse-hostinger.sha256"
MANIFEST = DIST / ".vite" / "manifest.json"

REQUIRED_FILES = {Path("index.html"), Path(".htaccess"), Path("comprapulse-icon.svg")}
ALLOWED_ROOT_FILES = REQUIRED_FILES
REJECTED_NAMES = {".env", ".env.local", ".env.production", ".DS_Store"}
REJECTED_SUFFIXES = {".map", ".pem", ".key", ".p12", ".pfx"}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"sk-[A-Za-z0-9]{20,}"),
)


def fail(message: str) -> None:
    raise SystemExit(f"CompraPulse package rejected: {message}")


def collect_files() -> list[tuple[Path, Path, bytes]]:
    if not DIST.is_dir():
        fail("dist/ is missing; run npm run build:comprapulse first")
    if not MANIFEST.is_file():
        fail("standalone Vite manifest is missing; run npm run build:comprapulse first")

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        fail(f"invalid standalone Vite manifest: {error}")

    selected = set(REQUIRED_FILES)
    for entry in manifest.values():
        for field in ("file", "css", "assets"):
            values = entry.get(field, [])
            if isinstance(values, str):
                values = [values]
            selected.update(Path(value) for value in values)

    files: list[tuple[Path, Path, bytes]] = []
    for relative in sorted(selected):
        source = DIST / relative
        if not source.is_file():
            fail(f"manifest output is missing: {relative}")
        if source.is_symlink():
            fail(f"symlink is not allowed: {relative}")
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"unsafe path: {relative}")
        if len(relative.parts) == 1 and relative not in ALLOWED_ROOT_FILES:
            fail(f"unexpected root file: {relative}")
        if len(relative.parts) > 1 and relative.parts[0] != "assets":
            fail(f"unexpected directory: {relative}")
        if source.name in REJECTED_NAMES or source.suffix.lower() in REJECTED_SUFFIXES:
            fail(f"sensitive or development file: {relative}")

        content = source.read_bytes()
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            fail(f"possible secret in {relative}")
        files.append((relative, source, content))

    present = {relative for relative, _, _ in files}
    missing = REQUIRED_FILES - present
    if missing:
        fail("missing required file(s): " + ", ".join(sorted(map(str, missing))))
    if not any(relative.parts[0] == "assets" for relative in present):
        fail("compiled assets are missing")
    return files


def build_archive(files: list[tuple[Path, Path, bytes]]) -> str:
    RELEASE.mkdir(exist_ok=True)
    for output in (ARCHIVE, CHECKSUM):
        if output.exists():
            output.unlink()

    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for relative, source, content in files:
            info = zipfile.ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = stat.S_IMODE(source.stat().st_mode) or 0o644
            info.external_attr = mode << 16
            bundle.writestr(info, content, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    archive_path = ARCHIVE.relative_to(ROOT).as_posix()
    CHECKSUM.write_text(f"{digest}  {archive_path}\n", encoding="utf-8")
    return digest


def main() -> None:
    files = collect_files()
    digest = build_archive(files)
    print(f"Created {ARCHIVE.relative_to(ROOT)} ({len(files)} files)")
    print(f"SHA-256 {digest}")


if __name__ == "__main__":
    main()
