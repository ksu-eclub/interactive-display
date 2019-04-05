#!/bin/bash
set -e

launch_app() {
    name="$1"
    shift
    (
        "$@" 2>&1
    ) | tee "$name.log" | sed -e "s|^.*$|[$name] &|g" &
}

python() {
    launch_app "$1" "$(which python)" "$2"
}

java() {
    launch_app "$1" "$(which java)" -cp build/libs/*.jar "$2"
}

go() {
    launch_app "$1" "$(which go)" run "$2"
}

gradle build
. /etc/environment
export GOPATH

export DISPLAY=:1
export $(dbus-launch)

trap 'kill $(jobs -p)' EXIT
if [ $# -ge 1 ]; then
    . "$1"
else
    . modules.txt
fi
while [ "x$(jobs -p)" != "x" ]; do
    sleep 1s
done
