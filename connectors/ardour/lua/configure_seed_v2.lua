-- SEION: build seed v2 from a copy of seed v1, fully headless (no GUI).
--
-- usage: ardour9-lua configure_seed_v2.lua <session_dir> <session_name> <log_file>
--
-- * latin_perc track becomes "kick" (its notes are merged into drums at render time)
-- * kick, bass, chords, arp, lead: General MIDI Synth -> Surge XT
-- * sounds are NOT chosen here: seion_ardour.surge_state writes a .fxp patch per
--   role into the saved plugin state (MIDI program changes sent from headless
--   Lua did not reach Surge, so the state route is the reliable one).
-- Headless track *creation* crashes on Windows, so the kick reuses a track.

local session_dir, session_name, log_path = arg[1], arg[2], arg[3]
local SURGE_ROLES = { kick = true, bass = true, chords = true, arp = true, lead = true }

local lf = io.open(log_path, "w")
local function log(...)
	local t = {}
	for i = 1, select("#", ...) do t[#t + 1] = tostring(select(i, ...)) end
	lf:write(table.concat(t, "\t"), "\n")
	lf:flush()
end

local function role_of(route)
	return route:name():match("^(.-)%-%d+%-t%d+$") or route:name()
end

assert(load_session(session_dir, session_name), "load_session failed")
log("loaded", session_name)

for t in Session:get_tracks():iter() do
	if role_of(t) == "latin_perc" then
		t:set_name("kick-1-t1")
		log("renamed latin_perc -> kick")
	end
end

for t in Session:get_tracks():iter() do
	local role = role_of(t)
	if SURGE_ROLES[role] then
		local old = t:nth_plugin(0)
		if not old:isnil() and old:display_name() ~= "Surge XT" then
			t:remove_processor(old, nil, true)
			t:add_processor_by_index(ARDOUR.LuaAPI.new_plugin(Session, "Surge XT", ARDOUR.PluginType.VST3, ""), 0, nil, true)
		end
		log("surge", role)
	end
end

for t in Session:get_tracks():iter() do
	log("chain", t:name(), t:nth_plugin(0):display_name())
end

Session:save_state("", false, false, false, false, false)
log("saved")
close_session()
log("done")
