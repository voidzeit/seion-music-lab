# device_SEION_Controller.py
# FL Studio MIDI Controller script (sketch / Phase 4).
#
# This runs inside FL Studio's MIDI scripting host and is intended for transport
# and macro control of the SEION workflow from a hardware controller — NOT for
# composition (that happens outside FL). It is a starting point, not wired to a
# real device yet.
#
# Planned mapping:
#   button 1  -> request a variation (writes a trigger file SEION watches)
#   button 2  -> accept current idea
#   button 3  -> mark "make it darker"
#   knob 1    -> energy
#   knob 2    -> density
#   knob 3    -> swing
#
# FL MIDI scripting targets controllers/events; keep heavy logic outside FL.

import device  # noqa: F401  (provided by FL Studio at runtime)

# Example CC map (edit to match your controller).
CC_ENERGY = 21
CC_DENSITY = 22
CC_SWING = 23

NOTE_VARIATION = 36
NOTE_ACCEPT = 37
NOTE_DARKER = 38


def OnInit():
    print("SEION Controller loaded.")


def OnMidiMsg(event):
    # Knobs -> macros (0-127 normalised to 0-1 by the host side later).
    if event.midiId == 0xB0:  # control change
        if event.data1 in (CC_ENERGY, CC_DENSITY, CC_SWING):
            event.handled = True
            print("SEION macro CC", event.data1, "=", event.data2)
            return

    # Pads/buttons -> actions.
    if event.midiId == 0x90 and event.data2 > 0:  # note on
        if event.data1 == NOTE_VARIATION:
            print("SEION: request variation")
        elif event.data1 == NOTE_ACCEPT:
            print("SEION: accept idea")
        elif event.data1 == NOTE_DARKER:
            print("SEION: make it darker")
        event.handled = True
