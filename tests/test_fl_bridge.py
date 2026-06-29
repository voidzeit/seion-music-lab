"""Sprint 4: FL Studio drop folder + Piano Roll script install."""

from __future__ import annotations

from app.export.fl_script_writer import write_all_piano_roll_scripts
from app.fl_bridge import install_piano_roll_scripts, update_drop_folder
from app.fl_bridge.piano_roll_script_template import build_import_script


def test_drop_folder_mirrors_latest(tmp_path):
    project = tmp_path / "idea_x"
    project.mkdir()
    (project / "idea.json").write_text('{"id": "idea_x", "tracks": []}', encoding="utf-8")
    (project / "chords.mid").write_bytes(b"MThd")  # stand-in MIDI bytes

    drop = update_drop_folder(project)

    assert (drop / "latest_idea.json").exists()
    assert (drop / "latest_chords.mid").exists()


def test_install_scripts_into_dest(tmp_path):
    installed = install_piano_roll_scripts(dest=tmp_path)
    names = {p.name for p in installed}
    assert "SEION Import Idea.pyscript" in names
    assert "SEION Humanize.pyscript" in names
    # Files actually landed.
    for path in installed:
        assert path.exists()


def test_build_import_script_sets_role():
    chords = build_import_script("harmony")
    assert 'TRACK_ROLE = "harmony"' in chords
    assert "flpianoroll" in chords

    all_script = build_import_script("all")
    assert 'TRACK_ROLE = "all"' in all_script


def test_write_all_scripts_bundle(tmp_path):
    written = write_all_piano_roll_scripts(tmp_path)
    assert len(written) == 5  # 4 imports + humanize
    assert (tmp_path / "SEION Generate Bass.pyscript").exists()
    assert 'TRACK_ROLE = "bass"' in (tmp_path / "SEION Generate Bass.pyscript").read_text("utf-8")
