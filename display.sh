#!/bin/bash
set -e

Xvfb :1 -screen 0 1x1x8 &
export DISPLAY=:1
sleep 2
export $(dbus-launch)
pulseaudio &
sleep 2
pactl set-sink-volume 0 115%
