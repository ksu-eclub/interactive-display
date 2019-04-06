#!/bin/bash
set -e

cd "$(dirname "$0")"

for file in *.service; do
    if [ ! -L "/lib/systemd/system/$file" ]; then
        echo "Installing $file..."
        ln -sf "$(readlink -f "$file")" "/lib/systemd/system/$file"
        systemctl daemon-reload
        systemctl enable "$file"
        systemctl start "$file"
    fi
done
