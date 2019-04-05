#!/bin/bash
set -e

launch_app() {
    name="$1"
    shift
    (
        (
            "$@" 2>&1
        ) | while read line; do
            echo "[$name] $line"
        done
    ) &
}

python() {
    launch_app "$1" "$(which python)" "$1"
}

java() {
    launch_app "$1" "$(which java)" -cp build/libs/*.jar "$1"
}

trap 'kill $(jobs -p)' EXIT
. modules.txt
while [ "x$(jobs -p)" != "x" ]; do
    sleep 1s
done
