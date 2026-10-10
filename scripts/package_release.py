"""Build a source-only release with a deliberate file allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP = {"README.md", "AGENTS.md", "pyproject.toml", ".gitignore", ".dockerignore", "Dockerfile", "THIRD_PARTY_NOTICES.md", "constraints-tested.txt"}
EXTENSIONS = {"src": {".py", ".js", ".html", ".ttf", ".txt"}, "examples": {".py", ".md", ".json", ".js", ".html"},
              "docs": {".md", ".json"}, "scripts": {".py"}, "tests": {".py"}, ".github": {".yml", ".yaml"}}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", default="dist/fgeful-kit.zip")
    args = ap.parse_args()
    paths = []
    for p in sorted(ROOT.rglob("*")):
        rel = p.relative_to(ROOT)
        if not p.is_file() or "__pycache__" in rel.parts or any(x.endswith('.egg-info') for x in rel.parts):
            continue
        if str(rel) not in TOP and p.suffix not in EXTENSIONS.get(rel.parts[0], set()):
            continue
        if p.is_symlink():
            raise RuntimeError(f"Refusing symlink in release: {rel}")
        paths.append(p)
    manifest = {p.relative_to(ROOT).as_posix(): {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths}
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for p in paths:
            archive.write(p, "fgeful-kit/" + p.relative_to(ROOT).as_posix())
        archive.writestr("fgeful-kit/SOURCE_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        for name, value in manifest.items():
            assert hashlib.sha256(archive.read("fgeful-kit/" + name)).hexdigest() == value["sha256"]
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".sha256").write_text(f"{digest}  {output.name}\n", encoding="utf-8")
    print(json.dumps({"archive": str(output), "files": len(paths) + 1, "bytes": output.stat().st_size, "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
