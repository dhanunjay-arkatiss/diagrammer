#!/usr/bin/env bash
# render.sh — render every Mermaid source in this folder.
#
#   ./render.sh                 # all *.mmd
#   ./render.sh 02-bots.mmd     # just one
#   THEME=forest ./render.sh    # override the mermaid theme
#
# Output goes to out/exec/aidesk/mermaid/:
#   <name>.png       rendered by the Mermaid service itself, so HTML labels keep
#                    their text (flowcharts lose text if you rasterise their SVG)
#   hi/<name>.png    only for sequence diagrams, rasterised from SVG at HI px
#   hi/<name>.svg    the vector source, for zooming and printing
#
# Requires: the mermaid service up (scripts/mermaid-mcp.sh up), curl, jq, and
# rsvg-convert for the hi/ step.
set -euo pipefail
cd "$(dirname "$0")"

ROOT=$(cd ../../../.. && pwd)           # src/exec/aidesk/mermaid -> repo root
OUT="$ROOT/out/exec/aidesk/mermaid"
HI_DIR="$OUT/hi"
mkdir -p "$OUT" "$HI_DIR"

ENDPOINT=${ENDPOINT:-http://127.0.0.1:1122/mcp}
THEME=${THEME:-neutral}
BG=${BG:-white}
HI=${HI:-3400}

if [ $# -gt 0 ]; then
  FILES=("$@")
else
  mapfile -t FILES < <(ls -1 *.mmd)
fi
[ ${#FILES[@]} -gt 0 ] || { echo "no .mmd files found" >&2; exit 1; }

# Fail fast with a useful message rather than a JSON parse error per file.
if ! curl -s -o /dev/null --max-time 3 -X POST "$ENDPOINT" \
     -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"render","version":"1"}}}'; then
  echo "mermaid service unreachable at $ENDPOINT — run scripts/mermaid-mcp.sh up" >&2
  exit 1
fi

call_service() {  # $1=file  $2=outputType
  local payload resp
  payload=$(jq -n --rawfile src "$1" --arg theme "$THEME" --arg bg "$BG" --arg ot "$2" '{
    jsonrpc: "2.0", id: 1, method: "tools/call",
    params: { name: "generate_mermaid_diagram", arguments: {
      mermaid: $src, theme: $theme, backgroundColor: $bg, outputType: $ot } }
  }')
  resp=$(curl -sS -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    --data-binary "$payload")
  # Streamable transport answers as SSE; take the first data: line.
  local json=${resp#*$'\n'data: }
  [ "$json" = "$resp" ] && json=${resp#data: }
  printf '%s' "$json"
}

fail=0
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; fail=1; continue; }
  name=${f%.mmd}
  base=$(basename "$name")

  json=$(call_service "$f" base64)
  if err=$(jq -er '.error.message' <<<"$json" 2>/dev/null); then
    echo "FAIL $base: ${err:0:300}" >&2; fail=1; continue
  fi
  if ! jq -e '.result.content[0].data' <<<"$json" >/dev/null 2>&1; then
    echo "FAIL $base: unexpected response: ${json:0:200}" >&2; fail=1; continue
  fi
  jq -r '.result.content[0].data' <<<"$json" | base64 -d > "$OUT/$base.png"
  printf '  %-34s %s\n' "out/exec/aidesk/mermaid/$base.png" "$(du -h "$OUT/$base.png" | cut -f1)"

  # Sequence diagrams are pure SVG text, so a vector raster gives a true hi-res
  # copy. Flowcharts use HTML labels that rsvg-convert cannot read — skip them.
  if grep -q 'sequenceDiagram' "$f" && command -v rsvg-convert >/dev/null; then
    svg=$(call_service "$f" svg | jq -r '.result.content[0].text')
    printf '%s' "$svg" > "$HI_DIR/$base.svg"
    rsvg-convert -w "$HI" -b "$BG" -o "$HI_DIR/$base.png" "$HI_DIR/$base.svg"
    printf '  %-34s %s\n' "out/exec/aidesk/mermaid/hi/$base.png" "$(du -h "$HI_DIR/$base.png" | cut -f1)"
  fi
done

exit $fail
