import json
import shutil
import subprocess

import pytest

from fgeful_kit.media import assemble, probe


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg tools not installed")
def test_assembly_normalizes_clips_preserves_chapters_and_handles_spaces(tmp_path):
    root = tmp_path / "clips with spaces and ' quotes"
    root.mkdir()
    for name, size in [("small", "160x90"), ("large", "320x180")]:
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"color=c=teal:s={size}:r=12:d=0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(root / f"{name}.mp4")], check=True)
    manifest = root / "sequence.json"
    manifest.write_text(json.dumps({"clips": [{"title": "First = # ; \\ clip", "file": "small.mp4"}, {"title": "Second", "file": "large.mp4"}]}))
    output = root / "combined.mp4"
    report = assemble(manifest, output, width=320, height=180, fps=12)
    assert report["frames"] == 12
    assert report["chapters"] == 2
    assert probe(output)["chapters"][0]["tags"]["title"] == "First = # ; \\ clip"
    with pytest.raises(FileExistsError):
        assemble(manifest, output)
