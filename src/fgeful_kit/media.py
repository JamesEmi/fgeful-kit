"""FFmpeg normalization, frame verification, and chapter-aware assembly."""
from fractions import Fraction
from pathlib import Path
import json
import math
import subprocess
import tempfile

from .data import sha256, write_json


def run(command):
    result = subprocess.run([str(x) for x in command], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:] or f"Command failed: {command[0]}")
    return result


def probe(path, count=False):
    return json.loads(run(["ffprobe", "-v", "error", *(["-count_frames"] if count else []),
                           "-show_streams", "-show_format", "-show_chapters", "-of", "json", path]).stdout)


def verify_video(path, *, width=None, height=None, fps=None):
    path = Path(path)
    info = probe(path, count=True)
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    for key, expected in [("width", width), ("height", height)]:
        if expected is not None and stream[key] != expected:
            raise ValueError(f"Unexpected {key}: {stream[key]}")
    if fps is not None and abs(float(Fraction(stream["avg_frame_rate"])) - fps) > .001:
        raise ValueError("Unexpected frame rate")
    if stream["pix_fmt"] != "yuv420p" or stream["codec_name"] != "h264":
        raise ValueError("Expected H.264 / yuv420p")
    decoded = run(["ffmpeg", "-hide_banner", "-v", "error", "-i", path, "-f", "null", "-"])
    if decoded.stderr.strip():
        raise RuntimeError(decoded.stderr)
    report = {"file": path.name, "sha256": sha256(path), "duration_s": float(info["format"]["duration"]),
              "frames": int(stream["nb_read_frames"]), "dimensions": [stream["width"], stream["height"]],
              "fps": str(stream["avg_frame_rate"]), "chapters": len(info.get("chapters", [])), "full_decode_passed": True}
    write_json(path.with_suffix(".validation.json"), report)
    return report


def escape_metadata(text):
    return str(text).replace("\\", "\\\\").replace("\n", " ").replace("\r", " ").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#")


def assemble(manifest, output, *, width=1920, height=1080, fps=24):
    manifest = Path(manifest).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(output)
    if fps <= 0 or width < 2 or height < 2 or width % 2 or height % 2:
        raise ValueError("Use positive fps and even dimensions")
    sequence = json.loads(manifest.read_text(encoding="utf-8"))
    if not sequence.get("clips"):
        raise ValueError("Assembly needs at least one clip")
    output.parent.mkdir(parents=True, exist_ok=True)
    chapters, elapsed = [], 0.
    with tempfile.TemporaryDirectory(prefix="fgeful-") as temporary:
        tmp = Path(temporary)
        for i, clip in enumerate(sequence["clips"]):
            source = (manifest.parent / clip["file"]).resolve()
            source_duration = float(probe(source)["format"]["duration"])
            start = float(clip.get("start", 0))
            end = float(clip.get("end", source_duration))
            if not all(math.isfinite(x) for x in [start, end]) or start < 0 or end <= start or end > source_duration + .002:
                raise ValueError(f"Invalid interval for {source.name}")
            path = tmp / f"clip_{i:04d}.mp4"
            vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}"
            run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", start, "-i", source, "-t", end-start, "-map", "0:v:0", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", path])
            duration = float(probe(path)["format"]["duration"])
            chapters.append({"title": clip["title"], "start_s": elapsed, "end_s": elapsed + duration,
                             "source": clip["file"], "source_sha256": sha256(source), "source_start_s": start, "source_end_s": end})
            elapsed += duration
        # Relative generated filenames avoid concat escaping problems in user paths.
        (tmp / "concat.txt").write_text("".join(f"file 'clip_{i:04d}.mp4'\n" for i in range(len(chapters))), encoding="utf-8")
        metadata = ";FFMETADATA1\n"
        for c in chapters:
            metadata += f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['start_s']*1000)}\nEND={round(c['end_s']*1000)}\ntitle={escape_metadata(c['title'])}\n"
        (tmp / "chapters.txt").write_text(metadata, encoding="utf-8")
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-n", "-f", "concat", "-safe", "0", "-i", tmp / "concat.txt", "-i", tmp / "chapters.txt", "-map", "0:v:0", "-map_metadata", "1", "-map_chapters", "1", "-an", "-c:v", "copy", "-movflags", "+faststart", output])
    write_json(output.with_suffix(".chapters.json"), chapters)
    return verify_video(output, width=width, height=height, fps=fps)
