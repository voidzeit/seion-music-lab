"""FL Studio integration: drop folder + Piano Roll script installation.

The MVP path is file-based and robust: SEION writes MIDI/JSON, you import into
FL. Direct Piano Roll scripting is the next phase.
"""

from app.fl_bridge.install_scripts import install_piano_roll_scripts
from app.fl_bridge.midi_drop_folder import update_drop_folder

__all__ = ["install_piano_roll_scripts", "update_drop_folder"]
