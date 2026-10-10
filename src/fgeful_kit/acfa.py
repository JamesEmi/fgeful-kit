"""Import an existing ACFA delivery as a self-contained, private data project."""
from pathlib import Path
import json
import shutil

from .data import Project, sha256, write_json


def import_acfa(source, destination, template_dir, local_preview=None):
    source, target, template = Path(source).resolve(), Path(destination).resolve(), Path(template_dir).resolve()
    required = ["story.json", "chunks.bin", "spirit.bin", "poses.bin", "reference_216.png", "exploring_1710.png"]
    for name in required:
        if not (source / "assets" / name).is_file():
            raise FileNotFoundError(source / "assets" / name)
    for name in ["story.html", "story.js"]:
        if not (template / name).is_file():
            raise FileNotFoundError(template / name)
    target.mkdir(parents=True, exist_ok=False)
    assets = target / "assets"
    assets.mkdir()
    hashes = {}
    for name in required:
        shutil.copyfile(source / "assets" / name, assets / name)  # dereference all original symlinks
        hashes[name] = sha256(assets / name)
    m = json.loads((assets / "story.json").read_text())
    m.pop("sources", None)  # historical absolute paths are not runtime dependencies or publishable metadata
    m.update(schemaVersion=1, title="ACFA: fixed-scale chunks versus scale correction",
             provenance={"kind": "measured", "description": "ACFA archived accepted GTSAM states; original point identities. No optimizer rerun in this package.", "imported_file_sha256": hashes})
    m["cameras"] = {str(g["k"]): g["local"] for g in m["gpsGroups"]}
    m["images"] = [{"file": "reference_216.png", "label": "Spirit reference"},
                   {"file": "exploring_1710.png", "label": "Starling explorer"}]
    m["links"] = [{**s, "kind": "overlap", "color": "#65dfc4"} for s in m["seams"]]
    m["links"] += [{**m["revisit"], "kind": "evaluation", "color": "#ca9aff"},
                   {**m["anchor"], "kind": "reference", "color": "#72c8f4", "stages": ["rigid_reference", "sim3_reference"]}]
    # Order the first Rerun comparison around the matched camera-observation control.
    order = ["rigid_frame", "sim3_frame", "rigid_anchor", "sim3_anchor", "rigid_reference", "sim3_reference"]
    m["stages"] = {name: {**m["stages"][name], "gpsMode": "anchor" if name.endswith("anchor") else "all", "showReference": name.endswith("reference")} for name in order}
    m["pipelines"] = {"gps_to_reference": ["sim3_frame", "sim3_reference"]}
    for stage in m["stages"].values():
        stage.pop("source", None)
    m["view"] = m["comparison_view"]
    # Chapter starts drive preview coverage; the imported presentation keeps its original authored camera work.
    m["scenes"] = [{"start": t, "title": title, "panels": [{"stage": stage}]} for t, title, stage in [
        (0, "Local chunk ownership", "rigid_anchor"), (10, "Rigid state", "rigid_anchor"),
        (20, "Rigid solve", "rigid_anchor"), (34, "Revisit failure", "rigid_anchor"),
        (42, "Scale variable", "sim3_frame"), (52, "Scale solve", "sim3_frame"),
        (66, "Comparison", "sim3_frame"), (84, "Matched GPS control", "sim3_frame"),
        (100, "Chunk sizes", "sim3_frame"), (112, "Reference continuation", "sim3_reference"),
        (122, "Image matches", "sim3_reference"), (136, "Reference factors", "sim3_reference"),
        (142, "Reference solve", "sim3_reference"), (158, "Agreement", "sim3_reference"), (170, "Takeaway", "sim3_reference")]]
    m["notes"] = "These are agreement diagnostics, not surveyed accuracy. The matched control changes scale freedom with the same GPS samples. GPS and overlap disagreement increase in the reference continuation. GTSAM expression factors can express the same scale-aware position residual. Camera markers in this portable export show the sampled camera centers present in story.json."
    write_json(assets / "story.json", m)
    for name in ["story.html", "story.js"]:
        shutil.copyfile(template / name, target / name)
    if local_preview:
        shutil.copyfile(local_preview, assets / "local_chunk.png")
    for name in ["Lato-Regular.ttf", "Lato-Bold.ttf"]:
        if (source / "assets" / name).exists():
            shutil.copyfile(source / "assets" / name, assets / name)
    return Project(target)
