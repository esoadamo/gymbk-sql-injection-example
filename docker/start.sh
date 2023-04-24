#!/bin/bash
DIR_DATA="$1"

set -euo pipefail
DIR_DATA="$(realpath "$DIR_DATA")"
[ -z "$DIR_DATA" -o ! -d "$DIR_DATA" ] && { echo "ERR: Given data path '$DIR_DATA' is invalid"; exit 1; }

echo "Selected options are"
echo "- DATA: $DIR_DATA"

docker stop gymbank &>/dev/null || true
docker rm gymbank &>/dev/null || true
docker run \
  -p 8927:8927 \
  -v "$DIR_DATA:/opt/app/data/" \
  -it \
  --cap-add NET_ADMIN \
  --name gymbank \
  gymbank
