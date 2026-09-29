"""Canonical filesystem identity shared by the H-MAD TDD gates."""
from __future__ import annotations

import fcntl
import os
import stat
from typing import NamedTuple


PY_SUFFIXES = (".py", ".pY", ".Py", ".PY")


class Identity(NamedTuple):
    root: str
    target: str
    prefix: str
    names: tuple[str, ...]
    unresolvable: bool
    arm: int
    component: str


def _path_from_fd(fd: int, fallback: str) -> str:
    if not hasattr(fcntl, "F_GETPATH"):
        return os.path.realpath(fallback)
    path = fcntl.fcntl(fd, fcntl.F_GETPATH, bytes(1024))
    return os.fsdecode(path.rstrip(b"\0"))


def canonical_directory(path: str) -> str:
    fd = os.open(path, os.O_RDONLY)
    try:
        return _path_from_fd(fd, path)
    finally:
        os.close(fd)


def canonicalise(root: str, target: str, cwd: str | None = None) -> Identity:
    spelled_root = os.path.abspath(root)
    try:
        canonical_root = canonical_directory(spelled_root)
    except OSError:
        return Identity(spelled_root, "", spelled_root, (), True, 2, spelled_root)

    if not target:
        return Identity(canonical_root, "", canonical_root, (), False, 0, "")

    base = canonical_root
    if cwd and not os.path.isabs(target):
        resolved_cwd = os.path.realpath(cwd)
        if (os.path.isdir(resolved_cwd)
                and os.path.commonpath((canonical_root, resolved_cwd)) == canonical_root):
            try:
                base = canonical_directory(cwd)
            except OSError:
                base = resolved_cwd

    spelled_target = os.path.normpath(os.path.join(base, target))
    current = os.path.sep
    deepest_directory = current
    referent_stat = None
    absent = False
    for part in spelled_target.split(os.path.sep):
        if not part:
            continue
        current = os.path.join(current, part)
        try:
            os.lstat(current)
        except OSError:
            absent = True
            break
        try:
            referent_stat = os.stat(current)
        except FileNotFoundError:  # M:TI4
            try:
                prefix = canonical_directory(deepest_directory)
            except OSError:
                return Identity(canonical_root, "", deepest_directory, (), True, 2,
                                deepest_directory)
            return Identity(canonical_root, "", prefix, (), True, 1, current)
        except OSError:  # M:TI5
            try:
                prefix = canonical_directory(deepest_directory)
            except OSError:
                return Identity(canonical_root, "", deepest_directory, (), True, 2,
                                deepest_directory)
            return Identity(canonical_root, "", prefix, (), True, 1, current)
        if stat.S_ISDIR(referent_stat.st_mode):
            deepest_directory = current

    if absent:
        try:
            prefix = canonical_directory(deepest_directory)
        except OSError:
            return Identity(canonical_root, "", deepest_directory, (), True, 2,
                            deepest_directory)
        canonical_target = os.path.join(prefix, os.path.relpath(spelled_target, deepest_directory))
        return Identity(canonical_root, canonical_target, prefix,
                        (os.path.basename(spelled_target),), False, 0, "")

    if referent_stat is None:
        referent_stat = os.stat(current)

    if stat.S_ISDIR(referent_stat.st_mode):
        try:
            canonical_target = canonical_directory(current)
        except OSError:
            return Identity(canonical_root, "", current, (), True, 2, current)
        return Identity(canonical_root, canonical_target, canonical_target, (), False, 0, "")

    referent_path = current
    if stat.S_ISLNK(os.lstat(current).st_mode):
        try:
            fd = os.open(current, os.O_RDONLY)
            try:
                referent_path = _path_from_fd(fd, current)
                referent_stat = os.fstat(fd)
            finally:
                os.close(fd)
        except OSError:
            return Identity(canonical_root, "", current, (), True, 2, current)

    parent = os.path.dirname(referent_path)
    try:
        prefix = canonical_directory(parent)
    except OSError:
        return Identity(canonical_root, "", parent, (), True, 2, parent)
    try:
        with os.scandir(prefix) as entries:
            matching = []
            for entry in entries:
                if entry.is_symlink():
                    continue
                info = entry.stat(follow_symlinks=False)
                if (info.st_dev, info.st_ino) == (referent_stat.st_dev,
                                                   referent_stat.st_ino):
                    matching.append(entry.name)
            names = tuple(sorted(matching))
    except OSError:
        return Identity(canonical_root, "", prefix, (), True, 2, parent)
    if not names:
        return Identity(canonical_root, "", prefix, (), True, 2, parent)
    return Identity(canonical_root, os.path.join(prefix, names[0]), prefix,
                    names, False, 0, "")


def fold_py_suffix(name: str) -> str:
    for suffix in PY_SUFFIXES:
        if name.endswith(suffix):
            return name[:-len(suffix)] + ".py"
    return name


def _encode_field(value: str) -> str:
    return "".join(
        chr(byte) if (48 <= byte <= 57 or 65 <= byte <= 90
                      or 97 <= byte <= 122 or byte in b"/-._")
        else f"%{byte:02X}"
        for byte in os.fsencode(value)
    )


def emit_canon(identity: Identity) -> None:
    print("CANON 1")
    print("root " + _encode_field(identity.root))
    print("target " + _encode_field(identity.target))
    print("prefix " + _encode_field(identity.prefix))
    print("unresolvable " + ("yes" if identity.unresolvable else "no"))
    print("arm " + str(identity.arm))
    print("component " + _encode_field(identity.component))
    print("names " + str(len(identity.names)))
    for name in identity.names:
        print("name " + _encode_field(name))
