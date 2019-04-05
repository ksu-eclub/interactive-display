#!/bin/bash
set -e

Xvfb :1 -screen 0 1x1x8 &
export DISPLAY=:1
sleep 1
export $(dbus-launch)
pulseaudio &
sleep 1
amixer -D pulse sset Master 100%
