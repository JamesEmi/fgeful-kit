"""A deterministic, explicitly synthetic example requiring no research dataset."""
from pathlib import Path

import numpy as np

from .data import Project, write_json


def create_demo(destination):
    root = Path(destination)
    root.mkdir(parents=True, exist_ok=False)
    assets = root / "assets"
    assets.mkdir()
    rng = np.random.default_rng(430)
    x, y = np.meshgrid(np.linspace(-3, 3, 45), np.linspace(-2, 2, 28))
    surface = np.c_[x.ravel(), y.ravel(), (.5 * np.sin(x) + .15 * y).ravel()]
    color = np.c_[.3 + .4 * (surface[:, 0] + 3) / 6, np.full(len(surface), .75), np.full(len(surface), .6)]
    cloud = np.c_[surface, color].astype("<f4")
    np.concatenate([cloud, cloud]).tofile(assets / "chunks.bin")
    cloud.tofile(assets / "spirit.bin")
    start = np.repeat(np.eye(4)[None], 2, axis=0)
    start[1, :3, :3] *= 1.3
    start[1, :3, 3] = [1.4, .5, .4]
    fixed, corrected = [], []
    for u in np.linspace(0, 1, 13):
        rigid = start.copy()
        rigid[1, :3, 3] *= 1 - u
        scale = rigid.copy()
        scale[1, :3, :3] = np.eye(3) * (1.3 - .3 * u)
        fixed.append(rigid)
        corrected.append(scale)
    matrices = np.array(fixed + corrected)
    matrices.transpose(0, 1, 3, 2).astype("<f4").tofile(assets / "poses.bin")
    selected = surface[rng.choice(len(surface), 12, replace=False)].tolist()
    cameras = [[-2, -1, 1], [0, -1, 1], [2, -1, 1]]
    view = {"center": [0, 0, 0], "height": 8, "az": -65, "el": 35}
    def panel(stage, progress=None):
        p = {"stage": stage, "active": [0, 1], "view": view, "label": stage.replace('_', ' ').title()}
        if progress is not None:
            p["progress"] = progress
        return p
    meta = {
        "schemaVersion": 1, "title": "One state corrects cameras and surfaces", "duration": 12,
        "provenance": {"kind": "synthetic", "description": "Deterministic teaching geometry; scripted transforms, not optimizer results.", "seed": 430},
        "chunkCount": 2, "chunks": [{"offset": 0, "count": len(cloud)}, {"offset": len(cloud), "count": len(cloud)}],
        "spiritCount": len(cloud), "stages": {"fixed_scale": {"offset": 0, "count": 13}, "corrected_scale": {"offset": 13, "count": 13}},
        "gpsGroups": [{"k": 1, "local": cameras, "gps": cameras}],
        "cameras": {"0": cameras, "1": cameras},
        "links": [{"i": 0, "j": 1, "a": selected, "b": selected, "kind": "evaluation", "color": "#ca9aff"}],
        "view": view,
        "scenes": [
            {"start": 0, "title": "A local map carries its own scale.", "subtitle": "Two copies of the same surface start with different placement and size.", "insight": "SYNTHETIC EXAMPLE · both camera centers and surface points share a chunk transform.", "panels": [panel("fixed_scale", 0)]},
            {"start": 3, "title": "Compare the same geometry and view.", "subtitle": "Left: translation changes. Right: translation and scale change.", "insight": "Scripted state sequences illustrate the mechanism; these are not measured results.", "panels": [panel("fixed_scale"), panel("corrected_scale")]},
            {"start": 9, "title": "A shared correction aligns the surface.", "subtitle": "The Rerun recording and this film use identical points and transforms.", "insight": "Purple links are illustrative checks. A real experiment must supply its own evidence.", "panels": [panel("corrected_scale", 1)]},
        ],
    }
    write_json(assets / "story.json", meta)
    return Project(root)
