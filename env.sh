#!/bin/bash
set -e

export DISPLAY=:1
export $(dbus-launch)
. /etc/environment
export GOPATH

"$@"
