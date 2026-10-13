-- SEION: build the Ardour seed session (run ONCE, inside the Ardour GUI).
--
-- Why: headless ardour9-lua cannot create tracks or import MIDI, so the GUI
-- imports one seed .mid per role as a MIDI track with General MIDI Synth.
-- Headless renders later copy this session and rewrite the region notes.
--
-- How: create an empty session (48 kHz) named "seion_seed", open
-- Window > Scripting, paste this file, set SEED_DIR below, press Run,
-- then Session > Save and close Ardour.

local SEED_DIR = [[D:\Documents\voidzeit\repos\seion-music-lab\connectors\ardour\seed]]
local ROLES = { "drums", "latin_perc", "bass", "chords", "arp", "lead" }
local GMSYNTH = "http://gareus.org/oss/lv2/gmsynth"

local synth = ARDOUR.LuaAPI.new_plugin_info(GMSYNTH, ARDOUR.PluginType.LV2)
assert(not synth:isnil(), "General MIDI Synth (gmsynth.lv2) not found")

for _, role in ipairs(ROLES) do
	local files = C.StringVector()
	files:push_back(SEED_DIR .. "\\" .. role .. ".mid")
	local pos = Temporal.timepos_t(0)
	Editor:do_import(files,
		Editing.ImportDistinctFiles, Editing.ImportAsTrack, ARDOUR.SrcQuality.SrcBest,
		ARDOUR.MidiTrackNameSource.SMFTrackName, ARDOUR.MidiTempoMapDisposition.SMFTempoIgnore,
		pos, synth, ARDOUR.Track(), false)
end

for t in Session:get_tracks():iter() do
	local n = 0
	for _ in t:to_track():playlist():region_list():iter() do n = n + 1 end
	print("SEION seed track:", t:name(), "regions:", n)
end

Session:save_state("", false, false, false, false, false)
print("SEION seed session saved")
