"""Render the ten ACFA Manim scenes and assemble the original 14-chapter structure."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project", required=True)
    ap.add_argument("--data-video", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--manim-python", default=sys.executable)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=24)
    args = ap.parse_args()
    project = Path(args.project).resolve()
    data = Path(args.data_video).resolve()
    if not data.is_file():
        ap.error("Render the full 180-second data video first")
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=False)
    scenes = Path(__file__).with_name("scenes.py")
    options = ["--width", str(args.width), "--height", str(args.height), "--fps", str(args.fps)]
    sequence = [
        ("Chunk ownership and scale", "ChunkState"),
        ("Standard GPSFactor on Pose3", "RigidGPS"),
        ("Why a rigid transform cannot fix size", "RigidDistance"),
        ("The controlled ACFA experiment", "ACFAProtocol"),
        ("ACFA: fixed-scale map inconsistency", (20, 42)),
        ("Scale-aware GPS observation", "ScaleAwareGPS"),
        ("Correct cameras and dense geometry together", "SharedCorrection"),
        ("ACFA: optimize chunk scale", (52, 66)),
        ("Measured scale-freedom ablation", "ACFAFinding"),
        ("Same-camera GPS control", (84, 100)),
        ("Direct cross-robot surface factor", "DirectReferenceFactor"),
        ("Add reference evidence to the graph", "FullGraph"),
        ("Recorded Starling–Spirit alignment", (136, 170)),
        ("Externally corrected chunks", "Contribution"),
    ]
    clips = []
    for title, source in sequence:
        if isinstance(source, str):
            movie = output / f"{source}.mp4"
            subprocess.run([sys.executable, "-m", "fgeful_kit", "manim", str(scenes), source,
                            "--project", str(project), "--python", args.manim_python,
                            "--output", str(movie), *options], check=True)
            clips.append({"title": title, "file": movie.name})
        else:
            # Relative paths keep the generated edit portable when parent folders move together.
            import os
            clips.append({"title": title, "file": os.path.relpath(data, output), "start": source[0], "end": source[1]})
    manifest = output / "sequence.json"
    manifest.write_text(json.dumps({"clips": clips}, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "fgeful_kit", "assemble", str(manifest),
                    "--output", str(output / "ACFA_explainer.mp4"), *options], check=True)


if __name__ == "__main__":
    main()
