"""Export the same chunk ownership and recorded transforms to Rerun 0.24.1."""
from pathlib import Path
import re

import numpy as np

from .data import Project, transform, write_json


def export_rrd(root, output, steps=101, point_stride=1):
    import rerun as rr
    import rerun.blueprint as rb
    import rerun.dataframe as rdf

    if steps < 2 or point_stride < 1:
        raise ValueError("Use at least two replay steps and a positive point stride")
    p = Project(root)
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    m = p.meta
    stages = list(m["stages"]) + list(m.get("pipelines", {}))
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", stage) for stage in stages):
        raise ValueError("Stage names must be safe Rerun entity segments")
    rr.init(m["title"], spawn=False)
    rr.save(str(output))
    records = []
    try:
        for i, item in enumerate(m.get("images", [])):
            rr.log(f"/images/{i}", rr.ImageEncoded(path=str(p.assets / item["file"])), static=True)
        for name in stages:
            first_stage, _, _ = p.replay(name, 0)
            rr.log(f"/{name}", rr.ViewCoordinates.RIGHT_HAND_Z_UP, static=True)
            for k, chunk in enumerate(m["chunks"]):
                cloud = p.points[chunk["offset"]:chunk["offset"] + chunk["count"]:point_stride]
                path = f"/{name}/chunks/{k:03d}"
                rr.log(path + "/points", rr.Points3D(cloud[:, :3], colors=(cloud[:, 3:] * 255).astype(np.uint8), radii=.04), static=True)
                cameras = m.get("cameras", {}).get(str(k), [])
                if cameras:
                    rr.log(path + "/cameras", rr.Points3D(cameras, colors=[255, 210, 117], radii=.10), static=True)
            for i, group in enumerate(m.get("gpsGroups", [])):
                observations = group["gps"][:1] if m["stages"][first_stage].get("gpsMode") == "anchor" else group["gps"]
                rr.log(f"/{name}/gps/{i}/observations", rr.Points3D(observations, colors=[255, 207, 113], radii=.1), static=True)
        previous_stages = {}
        for step in range(steps):
            rr.set_time("replay_step", sequence=step)
            indices = {}
            for name in stages:
                stage, matrices, index = p.replay(name, step / (steps - 1))
                indices[name] = {"stage": stage, "index": index}
                if previous_stages.get(name) != stage:
                    rr.log(f"/{name}/reference", rr.Clear(recursive=True))
                    rr.log(f"/{name}/links", rr.Clear(recursive=True))
                    if m["stages"][stage].get("showReference", False) and len(p.reference):
                        ref = p.reference[::point_stride]
                        rr.log(f"/{name}/reference", rr.Points3D(ref[:, :3], colors=(ref[:, 3:] * 255).astype(np.uint8), radii=.04))
                    previous_stages[name] = stage
                for k, mat in enumerate(matrices):
                    rr.log(f"/{name}/chunks/{k:03d}", rr.Transform3D(mat3x3=mat[:3, :3], translation=mat[:3, 3]))
                for i, group in enumerate(m.get("gpsGroups", [])):
                    local, observed = np.asarray(group["local"]), np.asarray(group["gps"])
                    if m["stages"][stage].get("gpsMode") == "anchor":
                        local, observed = local[:1], observed[:1]
                    rr.log(f"/{name}/gps/{i}/residuals", rr.LineStrips3D(np.stack([transform(local, matrices[group["k"]]), observed], axis=1), colors=[255, 207, 113], radii=.015))
                for i, link in enumerate(m.get("links", [])):
                    if "stages" in link and stage not in link["stages"]:
                        continue
                    a = transform(link["a"], matrices[link["i"]])
                    b = transform(link["b"], matrices[link["j"]]) if "j" in link else np.asarray(link["b"])
                    color = [int(link.get("color", "#ca9aff")[n:n+2], 16) for n in [1, 3, 5]]
                    rr.log(f"/{name}/links/{link.get('kind', 'surface')}/{i}", rr.LineStrips3D(np.stack([a, b], axis=1), colors=color, radii=.015))
                cost = m["stages"][stage].get("cost", [])
                if cost:
                    rr.log(f"/cost/{name}/{stage}", rr.Scalars(cost[index]))
            records.append(indices)
            rr.log("/details", rr.TextDocument(
                f"# {m['title']}\n\n**{m['provenance']['kind'].upper()}**: {m['provenance'].get('description', '')}\n\n"
                f"Replay step {step}/{steps-1}; recorded indices: {indices}.\n\n"
                "Chunks own their local cameras and points. Both inherit the same transform. "
                "Geometry is not interpolated between recorded states. Replay progress is normalized, not wall-clock solver time. "
                "Costs from different objectives are not automatically comparable.\n\n"
                + m.get("notes", ""), media_type="text/markdown"))
        views = [rb.Spatial3DView(name=name.replace('_', ' '), origin=f"/{name}", contents=[f"/{name}/**"]) for name in stages]
        tabs = rb.Tabs(rb.Horizontal(*views[:2], name="Compare") if len(views) > 1 else views[0], *views[2:])
        side = rb.Vertical(rb.TextDocumentView(origin="/details"),
                           *[rb.Spatial2DView(name=item.get("label", item["file"]), origin=f"/images/{i}") for i, item in enumerate(m.get("images", []))])
        rr.send_blueprint(rb.Blueprint(rb.Horizontal(tabs, side, column_shares=[4, 1]), collapse_panels=False))
    finally:
        rr.disconnect()
    recording = rdf.load_recording(str(output))
    columns = len(recording.schema().component_columns())
    if not columns:
        raise RuntimeError("Saved recording has no component columns")
    report = {"file": output.name, "bytes": output.stat().st_size, "steps": steps,
              "component_columns": columns, "dataframe_load_passed": True,
              "point_stride": point_stride, "accepted_state_indices": records, "inputs": p.report()["sha256"]}
    write_json(output.with_suffix(".rrd.json"), report)
    return report
