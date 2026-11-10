#!/usr/bin/env bash
# drawio-export.sh — render .drawio files to PNG/SVG/PDF headlessly via podman.
# Uses rlespinasse/drawio-export (draw.io Desktop + xvfb inside the container).
# Runs only on demand; nothing stays running afterwards.
#
# Usage: scripts/drawio-export.sh [-f png|svg|pdf|jpg|pdf] [-s scale] [-b border]
#                                 [-o outdir] [-t(transparent)] file.drawio [more.drawio...]
set -euo pipefail

FORMAT=png; SCALE=; BORDER=; OUTDIR=export; EXTRA=()
while getopts "f:s:b:o:t" opt; do
  case $opt in
    f) FORMAT=$OPTARG ;;
    s) SCALE=$OPTARG ;;
    b) BORDER=$OPTARG ;;
    o) OUTDIR=$OPTARG ;;
    t) EXTRA+=(--transparent) ;;
    *) echo "unknown option: $opt" >&2; exit 2 ;;
  esac
done
shift $((OPTIND-1))
[ $# -ge 1 ] || { echo "usage: $(basename "$0") [-f png|svg|pdf] [-s scale] [-b border] [-o dir] file.drawio..." >&2; exit 2; }

IMAGE=docker.io/rlespinasse/drawio-export:v4.60.0
MAP=(-f "$FORMAT")
[ -n "$SCALE" ]  && MAP+=(-s "$SCALE")
[ -n "$BORDER" ] && MAP+=(-b "$BORDER")
[ ${#EXTRA[@]} -gt 0 ] && MAP+=("${EXTRA[@]}")

# All inputs must live under one directory (mounted read/write at /data).
INPUTS=("$@")
for f in "${INPUTS[@]}"; do
  [ -f "$f" ] || { echo "not a file: $f" >&2; exit 2; }
done
HOSTDIR=$(realpath "$(dirname "${INPUTS[0]}")")
BASENAMES=()
for f in "${INPUTS[@]}"; do
  BASENAMES+=("$(basename "$f")")
done

podman run --rm -i \
  -v "$HOSTDIR":/data:Z \
  "${IMAGE}" \
  "${MAP[@]}" "${BASENAMES[@]}"

echo "Exported to: $HOSTDIR/$OUTDIR/"
