"""The portable v1 project format. No pickle, implicit paths, or optimizer dependency."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sample_index(count: int, progress: float) -> int:
    """Nearest recorded state, with the same half-up rule used in JavaScript."""
    if count < 1 or not math.isfinite(progress):
        raise ValueError("A state sequence needs a positive count and finite progress")
    return min(count - 1, int(math.floor(max(0, min(1, progress)) * (count - 1) + .5)))


def transform(points, matrix):
    return np.asarray(points) @ matrix[:3, :3].T + matrix[:3, 3]


class Project:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.assets = self.root / "assets"
        self.meta = json.loads((self.assets / "story.json").read_text(encoding="utf-8"))
        if self.meta.get("schemaVersion") != 1:
            raise ValueError("Expected schemaVersion 1; use import-acfa for archived ACFA films")
        self.count = self.meta["chunkCount"]
        if not isinstance(self.count, int) or self.count < 1:
            raise ValueError("chunkCount must be positive")
        self.points = np.fromfile(self.assets / "chunks.bin", dtype="<f4").reshape(-1, 6)
        self.reference = np.fromfile(self.assets / "spirit.bin", dtype="<f4").reshape(-1, 6)
        # Each WebGL matrix is stored column-major. Python restores ordinary [row, col].
        self.matrices = np.fromfile(self.assets / "poses.bin", dtype="<f4").reshape(
            -1, self.count, 4, 4
        ).transpose(0, 1, 3, 2)
        self.validate()

    def validate(self):
        m = self.meta
        for name, a in [("points", self.points), ("reference", self.reference), ("poses", self.matrices)]:
            if not np.isfinite(a).all():
                raise ValueError(f"Nonfinite {name}")
        for a in [self.points, self.reference]:
            if ((a[:, 3:] < 0) | (a[:, 3:] > 1)).any():
                raise ValueError("RGB values must be in [0,1]")
        if len(m["chunks"]) != self.count:
            raise ValueError("One chunk descriptor is required per transform")
        end = 0
        for chunk in m["chunks"]:
            if chunk["offset"] != end or chunk["count"] < 0:
                raise ValueError("Chunk ranges must be contiguous and nonnegative")
            end += chunk["count"]
        if end != len(self.points) or m["spiritCount"] != len(self.reference):
            raise ValueError("Point counts disagree with the binary files")
        if not np.allclose(self.matrices[:, :, 3], [0, 0, 0, 1], atol=1e-6):
            raise ValueError("Expected homogeneous transforms with bottom row [0,0,0,1]")
        linear = self.matrices[:, :, :3, :3].astype(float)
        determinant = np.linalg.det(linear)
        if (determinant <= 0).any():
            raise ValueError("Transforms must preserve handedness and have positive scale")
        rotation = linear / np.cbrt(determinant)[..., None, None]
        if not np.allclose(rotation.swapaxes(-1, -2) @ rotation, np.eye(3), atol=2e-4):
            raise ValueError("Transforms must be similarities, without anisotropic scale or shear")
        if not m["stages"]:
            raise ValueError("At least one recorded stage is required")
        for name, stage in m["stages"].items():
            if stage["offset"] < 0 or stage["count"] < 1 or stage["offset"] + stage["count"] > len(self.matrices):
                raise ValueError(f"Invalid state range for {name}")
            costs = stage.get("cost", [])
            if costs and (len(costs) != stage["count"] or not np.isfinite(costs).all()):
                raise ValueError(f"Invalid cost record for {name}")
        for name, sequence in m.get("pipelines", {}).items():
            if name in m["stages"] or not sequence or any(s not in m["stages"] for s in sequence):
                raise ValueError(f"Invalid continuation pipeline {name}")
            for before, after in zip(sequence, sequence[1:]):
                if not np.allclose(self.state(before, 1)[0], self.state(after, 0)[0], atol=1e-5, rtol=0):
                    raise ValueError(f"Discontinuous recorded states in pipeline {name}")
        if m.get("provenance", {}).get("kind") not in ("synthetic", "measured"):
            raise ValueError("Label provenance.kind as synthetic or measured")
        if m.get("duration", 0) <= 0:
            raise ValueError("duration must be positive")
        for group in m.get("gpsGroups", []):
            self._owner(group["k"])
            self._pairs(group["local"], group["gps"])
        for group in m.get("links", []):
            self._owner(group["i"])
            if "j" in group:
                self._owner(group["j"])
            self._pairs(group["a"], group["b"])
        for item in m.get("images", []):
            image = (self.assets / item["file"]).resolve()
            if not image.is_relative_to(self.assets.resolve()) or not image.is_file():
                raise ValueError("Image references must resolve to files within assets/")
        scenes = m.get("scenes", [])
        starts = [s["start"] for s in scenes]
        if not starts or starts[0] != 0 or starts != sorted(set(starts)) or starts[-1] >= m["duration"]:
            raise ValueError("Scenes must begin at 0 and increase strictly within duration")
        for scene in scenes:
            panels = scene.get("panels", [])
            if not 1 <= len(panels) <= 2:
                raise ValueError("Each scene needs one or two panels")
            for panel in panels:
                if panel["stage"] not in m["stages"]:
                    raise ValueError("Scene references an unknown stage")
                for k in panel.get("active", range(self.count)):
                    self._owner(k)

    def _owner(self, k):
        if not isinstance(k, int) or not 0 <= k < self.count:
            raise ValueError(f"Invalid chunk owner {k}")

    @staticmethod
    def _pairs(a, b):
        a, b = np.asarray(a), np.asarray(b)
        if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 3 or not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("Correspondences must be paired finite Nx3 arrays")

    def state(self, stage, progress):
        s = self.meta["stages"][stage]
        index = sample_index(s["count"], progress)
        return self.matrices[s["offset"] + index], index

    def replay(self, name, progress):
        """Equal-duration stages in a declared continuous pipeline, or one stage."""
        sequence = self.meta.get("pipelines", {}).get(name, [name])
        position = max(0, min(1, progress)) * len(sequence)
        phase = min(len(sequence) - 1, int(position))
        stage = sequence[phase]
        matrix, index = self.state(stage, min(1, position - phase))
        return stage, matrix, index

    def report(self):
        return {"schema": 1, "chunks": self.count, "points": len(self.points),
                "reference_points": len(self.reference), "recorded_states": len(self.matrices),
                "stages": list(self.meta["stages"]), "kind": self.meta["provenance"]["kind"],
                "sha256": {p.name: sha256(p) for p in sorted(self.assets.iterdir()) if p.is_file()}}
