# Original ACFA presentation

These are the authored browser scenes and ten Manim scenes used for the October 3, 2026 chunk-scale explanation, adapted for the portable package. They retain the case study's narrative, numbers, camera choreography, image matching, and factor illustrations. They are a detailed example, not the generic renderer's default narrative.

## Import the data separately

From the repository root:

```bash
fgeful-kit import-acfa /path/to/acfa_scale_ablation_20261003 output/acfa \
  --template-dir examples/acfa --local-preview /path/to/local_chunk.png
```

The source needs `assets/story.json`, `chunks.bin`, `spirit.bin`, `poses.bin`, `reference_216.png`, and `exploring_1710.png`. Source files may originally be symlinks; the importer makes real copies. It does not read the original graph pickle or require GTSAM. Images and geometry remain in your ignored data project, outside the source archive.

`--local-preview` supplies the local-reconstruction image for the opening scene. If omitted, that scene uses a clearly labeled schematic placeholder. The image-match scene uses the actual image correspondences already recorded in `story.json`.

The importer adds a versioned data contract without changing the archived points or transforms. The Rerun export contains the four GPS controls, two reference solves, and a continuous free-scale GPS-to-reference replay. Camera markers use the sampled local camera centers available in the portable story; the original RRD additionally logged every camera from its graph pickle. This package does not require that pickle.

## Render

```bash
fgeful-kit preview output/acfa --output output/acfa-previews
fgeful-kit render output/acfa --output output/acfa-data.mp4
fgeful-kit rerun output/acfa --output output/acfa.rrd --point-stride 5
python examples/acfa/build_film.py --project output/acfa \
  --data-video output/acfa-data.mp4 --output-dir output/acfa-film
```

The script renders all ten native Manim scenes and inserts four measured excerpts at their original times. The assembled film has fourteen named chapters. The original timings are approximately three minutes for the data film and three minutes fifteen seconds for the combined explanation; encoding/frame-rate changes can shift exact duration.

Individual scenes can be rendered with `fgeful-kit manim examples/acfa/scenes.py SCENE --project output/acfa --output output/scene.mp4`. Available classes are `ChunkState`, `RigidGPS`, `RigidDistance`, `ACFAProtocol`, `ScaleAwareGPS`, `SharedCorrection`, `ACFAFinding`, `DirectReferenceFactor`, `FullGraph`, and `Contribution`.

## Interpret the case study correctly

- The matched comparison fixes the GPS observation set and varies scale freedom. The standard one-anchor comparison also changes GPS sampling.
- Displayed map states are recorded accepted solver states. No geometric interpolation is introduced by the film.
- The custom factor's heading terms were disabled for this position-only comparison.
- GTSAM's stock Similarity3 and expression machinery can express the same scale-aware position residual. The film explains a state/model choice, not the absence of that library capability or proof of novelty.
- Revisit/overlap numbers are agreement diagnostics. Cross-reference results are development fits, not independently surveyed absolute accuracy. The reference continuation increases GPS/overlap disagreement; consult the underlying experiment report for all metrics.
- Six illustrated image matches and a sparse set of links explain the factors; they are not the full optimization input.

When adapting this example, update both the source metadata and the authored narrative. Do not retain ACFA numbers, aircraft names, chunk indices, frame identities, or contribution language in a different experiment.
