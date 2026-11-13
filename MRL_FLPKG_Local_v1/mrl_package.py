"""Streaming FLPKG v2 writer and verifier with legacy SHA-1 support."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import zipfile

BLOCK = 1024 * 1024
METADATA = {"manifest.json", "index.md"}


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def safe_name(name):
    parts = name.split("/")
    win = PureWindowsPath(name)
    if (not name or "\\" in name or win.drive or name.startswith("/") or
            any(p in ("", ".", "..") or p.endswith((".", " ")) or
                any(ord(ch) < 32 or ch in '<>:"|?*' for ch in p) or
                PureWindowsPath(p).is_reserved() for p in parts)):
        raise ValueError(f"Unsafe member: {name!r}")
    return name


def inventory(root, forbidden):
    root = root.resolve(strict=True)
    if not root.is_dir() or forbidden.is_relative_to(root) or root.is_relative_to(forbidden):
        raise ValueError("Input directory must be separate from the runtime data directory")
    files = {}
    seen = {x.casefold() for x in METADATA}
    for parent, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = Path(parent) / name
            mode = path.lstat().st_mode
            if (path.is_symlink() or not path.resolve().is_relative_to(root) or
                    getattr(path.lstat(), "st_file_attributes", 0) & 0x400):
                raise ValueError("Symlinks and reparse points are not supported")
            if stat.S_ISDIR(mode):
                continue
            if not stat.S_ISREG(mode):
                raise ValueError("Only regular input files are supported")
            rel = safe_name(path.relative_to(root).as_posix())
            if rel.casefold() in seen:
                raise ValueError(f"Duplicate or reserved member: {rel}")
            seen.add(rel.casefold())
            files[rel] = path
    if not files:
        raise ValueError("Input directory is empty")
    return files


def publish(staged, destination):
    # Same filesystem hard link: existing destination is never overwritten.
    os.link(staged, destination)


def create_package(target, files, parent, check, label=None):
    entries = []
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, path in sorted(files.items()):
            check()
            before = path.stat()
            if not before.st_size:
                raise ValueError(f"Empty payload: {name}")
            sha256, sha1 = hashlib.sha256(), hashlib.sha1()
            size = 0
            member = zipfile.ZipInfo(name)
            member.file_size = before.st_size
            with path.open("rb") as src, archive.open(member, "w", force_zip64=True) as dst:
                opened = os.fstat(src.fileno())
                while chunk := src.read(BLOCK):
                    check()
                    size += len(chunk)
                    if size > before.st_size:
                        raise ValueError(f"Input grew: {name}")
                    sha256.update(chunk)
                    sha1.update(chunk)
                    dst.write(chunk)
                after = os.fstat(src.fileno())
            fields = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
            if size != before.st_size or not fields(before) == fields(opened) == fields(after) == fields(path.stat()):
                raise ValueError(f"Input changed: {name}")
            entries.append({"path": name, "size": size, "sha256": sha256.hexdigest(),
                            "sha1": sha1.hexdigest()})
        manifest = {"schema": "MRL_FLPKG/v2", "origin_signature": "MrLiouWord",
                    "parent_job": parent, "files": entries}
        if label is not None:
            manifest["label"] = label
        archive.writestr("manifest.json", json_bytes(manifest))
        archive.writestr("index.md", "# FLPKG Index\n\n" + "\n".join(
            f"- {item['path']} ({item['size']} bytes)" for item in entries) + "\n")


def verify_package(path, extract=None, check=lambda: None):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = {}
        folded = set()
        for info in entries:
            name = safe_name(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or name.casefold() in folded:
                raise ValueError("Symlink or duplicate archive member")
            folded.add(name.casefold())
            names[name] = info
        manifest_info = names.get("manifest.json")
        if not manifest_info or manifest_info.file_size > 32 * 1024 * 1024:
            raise ValueError("Missing or oversized manifest")
        manifest = json.loads(archive.read(manifest_info))
        expected = {}
        for entry in manifest["files"]:
            name = safe_name(entry["path"])
            if name in expected or name in METADATA:
                raise ValueError("Duplicate or reserved manifest entry")
            expected[name] = entry
        if not expected or set(names) != set(expected) | METADATA:
            raise ValueError("Manifest and ZIP inventory differ")
        for name in names:
            for parent in PurePosixPath(name).parents:
                if parent.as_posix().casefold() in folded:
                    raise ValueError("File conflicts with member directory")
        for name, entry in expected.items():
            check()
            info = names[name]
            if info.file_size != entry["size"] or info.file_size <= 0:
                raise ValueError(f"Invalid size: {name}")
            exact = entry.get("sha256")
            if manifest.get("schema") == "MRL_FLPKG/v2" and not exact:
                raise ValueError("Missing SHA-256")
            algorithm = hashlib.sha256() if exact else hashlib.sha1()
            dst = extract.joinpath(*PurePosixPath(name).parts) if extract else None
            if dst:
                dst.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source:
                if dst:
                    with dst.open("xb") as out:
                        _consume(source, algorithm, check, out)
                else:
                    _consume(source, algorithm, check)
            if algorithm.hexdigest() != (exact or entry.get("sha1")):
                raise ValueError(f"Digest mismatch: {name}")
        if names["index.md"].file_size > 32 * 1024 * 1024:
            raise ValueError("Oversized index")
        archive.read("index.md")
        return manifest


def _consume(source, algorithm, check, out=None):
    while chunk := source.read(BLOCK):
        check()
        algorithm.update(chunk)
        if out:
            out.write(chunk)


def extract_verified(path, destination):
    destination = destination.absolute()
    # Reserve the output name exclusively before extraction. A failing
    # extraction removes only the directory allocated by this call.
    destination.mkdir()
    try:
        return verify_package(path, destination)
    except BaseException:
        shutil.rmtree(destination)
        raise
