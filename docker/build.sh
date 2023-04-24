#!/bin/bash
(
    cd "$(realpath "$(dirname "$0")")/.." &&
    docker build -f docker/Dockerfile -t gymbank . &&
    if [[ "$1" == "--run" ]]; then
      ./docker/start.sh "$2"
    fi
)
