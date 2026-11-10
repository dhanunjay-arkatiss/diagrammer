#!/usr/bin/env bash
# build.sh — regenerate everything in out/ from src/.
#
#   ./scripts/build.sh                # all three packs
#   ./scripts/build.sh exec           # one pack: exec | tech | aidesk
#   ./scripts/build.sh -s 4           # print master (pages at 6402px, ~480 dpi)
#   ./scripts/build.sh --no-mermaid   # skip the Mermaid set
#   ./scripts/build.sh --no-deck      # skip the pptx
#
# Steps: copy/author the .drawio -> export every page to PNG + SVG -> render the
# Mermaid set -> build the deck. Needs podman (drawio-export image), python-pptx,
# and the mermaid service on 127.0.0.1:1122 for the Mermaid step.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD

SCALE=2
DO_MERMAID=1
DO_DECK=1
PACKS=(exec tech aidesk)
while [ $# -gt 0 ]; do
  case $1 in
    -s|--scale) SCALE=$2; shift 2 ;;
    --no-mermaid) DO_MERMAID=0; shift ;;
    --no-deck)    DO_DECK=0; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    exec|tech|aidesk) PACKS=("$1"); shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

IMAGE=${IMAGE:-docker.io/rlespinasse/drawio-export:v4.60.0}
TMP="$ROOT/out/.pages"

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

export_pack() {  # $1=.drawio source  $2=out dir  $3=scale
  local src=$1 outdir=$2 scale=$3 base n
  base=$(basename "$src" .drawio)
  step "$base  ->  ${outdir#$ROOT/}"
  rm -rf "$TMP"; mkdir -p "$TMP" "$outdir/export"
  cp "$src" "$TMP/$base.drawio"

  # one file per page: a page exports in seconds, and one bad page cannot take
  # the rest down (nor deadlock a shared :Z mount the way parallel runs do)
  python3 - "$TMP/$base.drawio" <<'PY'
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
src = path.read_text(encoding="utf-8")
head, tail = src[:src.index("<diagram")], "\n</mxfile>\n"
pages = re.findall(r"<diagram\b.*?</diagram>", src, re.S)
for i, page in enumerate(pages, 1):
    (path.parent / f"{path.stem}.p{i}.drawio").write_text(head + page + tail, encoding="utf-8")
print(f"  {len(pages)} pages")
PY

  for page in "$TMP/$base".p*.drawio; do
    n=$(basename "$page" .drawio); n=${n#"$base".}
    for fmt in png svg; do
      local args=(-f "$fmt" "$(basename "$page")")
      [ "$fmt" = png ] && args=(-f png -s "$scale" "$(basename "$page")")
      timeout 600 podman run --rm -i -v "$TMP":/data:Z "$IMAGE" "${args[@]}" >/dev/null 2>&1 \
        || { echo "  FAILED: $base page $n ($fmt)" >&2; exit 1; }
      local produced
      produced=$(ls "$TMP"/export/"$base.$n"-*."$fmt" 2>/dev/null | head -1)
      [ -n "$produced" ] || { echo "  FAILED: $base page $n ($fmt) produced nothing" >&2; exit 1; }
      mv "$produced" "$outdir/export/$base-${produced##*"$base.$n"-}"
    done
  done
  # the generated packs already sit in out/; only copied sources need placing
  [ "$(cd "$(dirname "$src")" && pwd)" = "$(cd "$outdir" && pwd)" ] || cp "$src" "$outdir/$base.drawio"
  printf '  %s files in export/\n' "$(ls "$outdir/export" | wc -l)"
  rm -rf "$TMP"
}

step "checking podman image"
if ! podman image exists "$IMAGE" 2>/dev/null; then
  echo "  pulling $IMAGE"; podman pull -q "$IMAGE" >/dev/null
else
  echo "  $IMAGE present"
fi

for pack in "${PACKS[@]}"; do
  case $pack in
    exec)   export_pack "$ROOT/src/exec/datahub-exec-pack.drawio" "$ROOT/out/exec" 3 ;;
    tech)   export_pack "$ROOT/src/tech/datahub-tech-pack.drawio" "$ROOT/out/tech" 2 ;;
    aidesk)
      step "aidesk  ->  out/exec/aidesk"
      python3 src/exec/aidesk/generate.py
      export_pack "$ROOT/out/exec/aidesk/aidesk-pack.drawio" "$ROOT/out/exec/aidesk" "$SCALE"
      if [ "$DO_MERMAID" = 1 ]; then
        step "mermaid  ->  out/exec/aidesk/mermaid"
        ./src/exec/aidesk/mermaid/render.sh
      fi
      if [ "$DO_DECK" = 1 ]; then
        step "deck"
        python3 src/exec/aidesk/make_pptx.py
      fi
      ;;
  esac
done

step "done"
find out -type f \( -name '*.drawio' -o -name '*.pptx' \) | sort | sed 's/^/  /'
printf '  %s PNG + %s SVG in export/\n' \
  "$(find out -path '*/export/*' -name '*.png' | wc -l)" \
  "$(find out -path '*/export/*' -name '*.svg' | wc -l)"
