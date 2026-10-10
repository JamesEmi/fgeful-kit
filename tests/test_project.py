import json
from pathlib import Path

import numpy as np
import pytest

from fgeful_kit.data import Project, sample_index, transform, write_json
from fgeful_kit.demo import create_demo


def test_binary_convention_and_physical_geometry(tmp_path):
    project = create_demo(tmp_path / "demo")
    initial, _ = project.state("corrected_scale", 0)
    final, _ = project.state("corrected_scale", 1)
    # This point has a known world location; a transposed matrix fails this check.
    np.testing.assert_allclose(transform([[2, 0, 0]], initial[1]), [[4, .5, .4]], atol=1e-6)
    np.testing.assert_allclose(transform([[2, 0, 0]], final[1]), [[2, 0, 0]], atol=1e-6)
    rigid, _ = project.state("fixed_scale", 1)
    span = np.array([[0, 0, 0], [2, 0, 0]])
    assert np.linalg.norm(np.diff(transform(span, rigid[1]), axis=0)) == pytest.approx(2.6)
    assert np.linalg.norm(np.diff(transform(span, final[1]), axis=0)) == pytest.approx(2.)


def test_python_and_javascript_half_up_sampling():
    # Python round uses ties-to-even; JavaScript Math.round does not.
    assert sample_index(3, .25) == 1
    assert sample_index(13, -1) == 0
    assert sample_index(13, 1.1) == 12
    with pytest.raises(ValueError):
        sample_index(0, .5)


@pytest.mark.parametrize("corruption", ["nan", "shear", "reflection", "bad_bottom_row", "wrong_size"])
def test_rejects_misleading_or_corrupt_geometry(tmp_path, corruption):
    project = create_demo(tmp_path / "demo")
    matrices = project.matrices.copy()
    if corruption == "nan":
        matrices[0, 0, 0, 0] = np.nan
    elif corruption == "shear":
        matrices[0, 0, 0, 1] = .2
    elif corruption == "reflection":
        matrices[0, 0, 0, 0] = -1
    elif corruption == "bad_bottom_row":
        matrices[0, 0, 3, 0] = 1
    else:
        matrices = matrices[:1]
    matrices.transpose(0, 1, 3, 2).astype("<f4").tofile(project.assets / "poses.bin")
    with pytest.raises(ValueError):
        Project(project.root)


def test_relocation_and_provenance(tmp_path):
    import shutil
    original = create_demo(tmp_path / "one")
    shutil.copytree(original.root, tmp_path / "elsewhere" / "with spaces")
    relocated = Project(tmp_path / "elsewhere" / "with spaces")
    assert original.report() == relocated.report()
    meta = relocated.meta
    meta["provenance"]["kind"] = "unknown"
    write_json(relocated.assets / "story.json", meta)
    with pytest.raises(ValueError, match="provenance"):
        Project(relocated.root)


def test_continuations_require_an_exact_shared_endpoint(tmp_path):
    project = create_demo(tmp_path / "demo")
    meta = project.meta
    # The two demo controls start together but neither continues from the other.
    meta["pipelines"] = {"invalid_continuation": ["fixed_scale", "corrected_scale"]}
    write_json(project.assets / "story.json", meta)
    with pytest.raises(ValueError, match="Discontinuous"):
        Project(project.root)
