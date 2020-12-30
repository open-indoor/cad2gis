#!/bin/bash

set -e
set -x

rm -rf /tmp/.X99-lock
Xvfb :99 -screen 0 1024x768x16 &
while [ ! -e /tmp/.X11-unix/X99 ]; do sleep 0.1; done

export DXF_ENCODING=UTF-8
export XDG_RUNTIME_DIR='/tmp/runtime-root'

for folder in $(find /data -type f -name "*.dwg" -exec dirname {} \; | sort -u); do
    DISPLAY=:99.0 ODAFileConverter \
        "${folder}" \
        "${folder}" \
        ACAD2018 DXF 1 1 "*.dwg"
done

echo "finished !"