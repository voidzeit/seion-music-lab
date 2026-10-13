-- SEION: turn a copy of seed v1 into seed v2 (run ONCE, inside the Ardour GUI).
--
-- Structure only; sounds are picked by ear afterwards in each Surge XT window:
--   * bass, chords, arp, lead: General MIDI Synth -> Surge XT
--   * new "kick" track (Surge XT + Surge XT Effects for distortion)
--   * bass also gets Surge XT Effects
--   * drums and latin_perc keep General MIDI Synth (hats, claps, congas, guiro)
--
-- Needs a VST3 scan first (Window > Plugin Manager > Scan for new plugins).
-- Paste in Window > Scripting, Run, then close the Scripting window BEFORE
-- quitting Ardour (closing Ardour with it open crashes on exit).

local SEED_DIR = [[D:\Documents\voidzeit\repos\seion-music-lab\connectors\ardour\seed]]
local SURGE_ROLES = { bass = true, chords = true, arp = true, lead = true }
local FX_ROLES = { bass = true, kick = true }

local surge = ARDOUR.LuaAPI.new_plugin_info("Surge XT", ARDOUR.PluginType.VST3)
assert(not surge:isnil(), "Surge XT VST3 not found: scan plugins first")

local function role_of(route)
	return route:name():match("^(.-)%-%d+%-t%d+$") or route:name()
end

local function add_surge_fx(route)
	local fx = ARDOUR.LuaAPI.new_plugin(Session, "Surge XT Effects", ARDOUR.PluginType.VST3, "")
	assert(not fx:isnil(), "Surge XT Effects VST3 not found")
	route:add_processor_by_index(fx, 1, nil, true) -- right after the instrument
end

-- 1. kick track from the seed kick.mid, with Surge XT as instrument
local has_kick = false
for r in Session:get_routes():iter() do
	if role_of(r) == "kick" then has_kick = true end
end
if not has_kick then
	local files = C.StringVector()
	files:push_back(SEED_DIR .. "\\kick.mid")
	local pos = Temporal.timepos_t(0)
	Editor:do_import(files,
		Editing.ImportDistinctFiles, Editing.ImportAsTrack, ARDOUR.SrcQuality.SrcBest,
		ARDOUR.MidiTrackNameSource.SMFTrackName, ARDOUR.MidiTempoMapDisposition.SMFTempoIgnore,
		pos, surge, ARDOUR.Track(), false)
end

-- 2. swap instruments / add effects
for r in Session:get_routes():iter() do
	local role = role_of(r)
	if SURGE_ROLES[role] then
		local old = r:nth_plugin(0)
		if not old:isnil() and old:display_name() ~= "Surge XT" then
			r:remove_processor(old, nil, true)
			local p = ARDOUR.LuaAPI.new_plugin(Session, "Surge XT", ARDOUR.PluginType.VST3, "")
			r:add_processor_by_index(p, 0, nil, true)
		end
	end
	if FX_ROLES[role] and r:nth_plugin(1):isnil() then
		add_surge_fx(r)
	end
end

for r in Session:get_routes():iter() do
	if not r:to_track():isnil() then
		local chain = {}
		local i = 0
		while not r:nth_plugin(i):isnil() do
			chain[#chain + 1] = r:nth_plugin(i):display_name()
			i = i + 1
		end
		print("SEION v2:", r:name(), table.concat(chain, " -> "))
	end
end

Session:save_state("", false, false, false, false, false)
print("SEION seed v2 saved - now pick a patch in each Surge XT window and save again")
