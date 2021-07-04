% VHT(1) vht 0.3
% Remigiusz Dybka
% June 2021

# NAME
**vht** - a minimalistic MIDI sequencer for JACK/GNOME

# SYNOPSIS
**vht** [file]

# DESCRIPTION
**vht** (Valhalla Tracker) is a live MIDI sequencing application for GNU/Linux audio setups.
Main motivation behind developing it was to create a fast workflow for putting down musical
ideas, exploring exotic time signatures and generally playing with sound. It can be seen as a helper app 
for the most rebellious of musicians.

## The Paradigm
The module consists of sequences, sequences of tracks, tracks of rows and envelopes, row is basically a midi message.
Module also has a timeline, made of strips, which themselves really are sequences. Main window always edits a sequence,
either a main sequence (top right pane) or one in timeline (bottom right). There are two playing modes, looping or
timeline. Current mode is indicated by the loop toggle button in right pane. Main sequences can be assigned
triggers in their menu. The trigger assigned to the the right mouse button (denoted by **r**)
will be activated with keypad number corresponding to it's position.

There are two recording modes. One, where all input goes into the active track, toggled by space,
and one which will create tracks based on midi input (ctrl+space).

## Interface
Throughout the program, right mouse button resets, exits or deletes depending on context. Current keyboard focus
as well as track armed for midi recording is denoted by a bar under track name. As great care has been taken to
display tooltips for every operation, this will only list less obvious functions.

- Sequence
    - F1-F10 - mute/unmute tracks
    - ctrl-drag in leftmost column rotates active tracks
- Track
    - ctrl-click + drag in time field will work on selection
    - ctrl-click + drag in velocity field will too
- Controllers
    - ctrl-click - add controller node
    - double click a node to link/unlink
    - inner nodes can be smoothed with wouse wheel
- Timeline
    - left-click on a hint - create a clone of main sequence
    - ctrl+left-click on a strip - place clone
    - ctrl+left-click on a hint - place empty
    - shift+left-drag - shift time
    - mid-click - move play-head
    - mid-click on loop marker - on and off
    - mid-click strip - silence
    - ctrl+mid-click strip - silence all
    - alt+scroll - snapping
    - ctrl+alt+scroll - fine snapping
    - L loops current sequence
- Mandy
    - mid-click and drag - translate
    - shift while dragging - rotate
    - ctrl while dragging - zoom
    - right-click - reset position
    - left-click on hint - set new start position
    - hold e and drag to move julia (e)

## Bpm nodes
Bpm nodes are shown as circles in timeline. There is always a node zero on top (which can't be moved).
If a node is selected, bpm field in status bar will control it's tempo. Ctrl-left-clicking will place
a new node. An empty node will set new tempo at it's position. A filled node (double click) will
interpolate tempo from last one.

## Mandy
Mandy, if active, will strum it's track with playhead based on bearing of an imaginary turtle trapped on boundary of a
low-iteration wobbling fractal. It's limited by FPU, unprecise, unpredictable and it has been requested
that users refrain from utilising it as a fractal explorer. Tinkering introduces chaos. Good luck.

## Rendering
All rendering depends on jack_capture. Live mode will record what you hear in real-time. The other three modes
(Sequence, Timeline, What u'd hear) will switch JACK into freewheeling mode, which not all soft synths support.

# SEE ALSO
jack_capture qjackctl qsynth zynaddsubfx carla

# COPYRIGHT
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

