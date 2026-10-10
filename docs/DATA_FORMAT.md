# Portable project format, version 1

```text
project/
  assets/story.json
  assets/chunks.bin
  assets/spirit.bin
  assets/poses.bin
  story.html           optional authored presentation; otherwise generated
  story.js             optional authored presentation; otherwise generated
```

The binary filenames retain the original workflow's names: `spirit.bin` means fixed reference geometry and need not represent a Spirit aircraft. It may be an empty file. All data arrays are **little-endian float32**. Each point row is `x,y,z,r,g,b`; RGB is in `[0,1]`. Local points concatenate in chunk order; each JSON chunk specifies a contiguous `offset` and `count` in point rows.

Transforms are homogeneous 4×4 local-to-world matrices: `p_world = M[:3,:3] @ p_local + M[:3,3]`. Positive uniform scale is allowed; shear, reflection, and anisotropic scale are rejected. The bottom row is `[0,0,0,1]`. Store each matrix column-major for WebGL:

```python
# matrices shape: (total_recorded_states, chunk_count, 4, 4), ordinary NumPy row/column indexing
matrices.transpose(0, 1, 3, 2).astype('<f4').tofile(assets / 'poses.bin')
points_xyz_rgb.astype('<f4').tofile(assets / 'chunks.bin')
reference_xyz_rgb.astype('<f4').tofile(assets / 'spirit.bin')
```

`story.json` contains:

| Field | Contract |
|---|---|
| `schemaVersion` | Integer `1` |
| `title`, `duration` | Story name and positive duration in seconds |
| `provenance` | `kind`: `measured` or `synthetic`; describe origin, transformations, units, and evidence. Source hashes are recommended. |
| `chunkCount`, `chunks` | Number of chunks and contiguous point ranges |
| `spiritCount` | Number of fixed-reference point rows |
| `stages` | Map from stable stage names to `offset` and `count` in the recorded-state axis; optional `cost`, `gpsMode: anchor`, `showReference: true` |
| `pipelines` | Optional map from replay name to sequential stage names. Adjacent endpoints must agree. Rerun adds a continuous replay tab. |
| `cameras` | Optional map of chunk-index strings to local camera-center arrays |
| `images` | Optional `{file, label}` records for Rerun image views; files must be within `assets/` |
| `gpsGroups` | Optional `{k, local: Nx3, gps: Nx3}` observations; local centers belong to chunk `k`, GPS positions are world coordinates |
| `links` | Optional `{i, a: Nx3, b: Nx3, j?, kind, color?, stages?}`. `a` belongs to chunk `i`; `b` belongs to chunk `j` if supplied, otherwise is already world-fixed. |
| `view` | Default orthographic view: `center: [x,y,z]`, positive `height`, `az`, `el` in degrees. Right-handed, Z up. |
| `scenes` | Ordered array, starting at `0`, of `{start, title, subtitle?, insight?, panels}` |
| `notes` | Optional interpretation and limitations, displayed in Rerun |

Each scene has one or two `panels`. A panel contains `stage`, optional `label`, `active` chunk indices, `view`, `reference`, `rgb`, `gps`, and `progress`. Without `progress`, its scene interval runs from stage progress 0 to 1; `progress: 0` or `1` holds the initial or final state. The same view should be used for a matched comparison.

State selection is `floor(clamp(progress,0,1)*(count-1)+0.5)`. This matches JavaScript `Math.round`; Python's default tie-to-even `round` does not. The frame at exact story duration uses the last scene at progress 1. Video frames are sampled at `start + frame/fps` and do not include an extra endpoint frame; add a final hold scene when the last state needs reading time.

Use stable safe stage names (`letters`, `digits`, `_`, `-`). Keep asset paths local to the project. Inputs are validated before rendering/export, and output reports record input hashes. Validation covers geometric consistency, not whether a measurement is ground truth.

For a complete generated example, run `fgeful-kit demo output/demo` and inspect `output/demo/assets/story.json`. The source generator is `src/fgeful_kit/demo.py`. It provides an adapter-sized reference without bundled research data.

An assembly manifest is separate from the data schema:

```json
{"clips": [
  {"title": "Mechanism", "file": "scene.mp4"},
  {"title": "Recorded solve", "file": "data.mp4", "start": 5, "end": 12}
]}
```

Paths resolve relative to the manifest. Every clip is normalized, audio is omitted, and embedded chapter boundaries use the actual encoded clip durations.
