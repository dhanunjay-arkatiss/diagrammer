#!/usr/bin/env bash
# render.sh — render every .mmd in this folder to PNG via the local Mermaid MCP.
#
#   ./render.sh                 # all *.mmd
#   ./render.sh 02-bots.mmd     # just one
#   THEME=forest ./render.sh    # override the mermaid theme
#
# Requires: mcp-mermaid.service up (scripts/mermaid-mcp.sh status), curl, jq.
set -euo pipefail
cd "$(dirname "$0")"

ENDPOINT=${ENDPOINT:-http://127.0.0.1:1122/mcp}
THEME=${THEME:-neutral}
BG=${BG:-white}

if [ $# -gt 0 ]; then
  FILES=("$@")
else
  mapfile -t FILES < <(ls -1 *.mmd)
fi

[ ${#FILES[@]} -gt 0 ] || { echo "no .mmd files found" >&2; exit 1; }

fail=0
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; fail=1; continue; }
  name=${f%.mmd}
  payload=$(jq -n --rawfile src "$f" --arg theme "$THEME" --arg bg "$BG" '{
    jsonrpc: "2.0", id: 1, method: "tools/call",
    params: { name: "generate_mermaid_diagram", arguments: {
      mermaid: $src, theme: $theme, backgroundColor: $bg, outputType: "base64" } }
  }')

  resp=$(curl -sS -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -H 'Accept: application/json, text/event-stream' \
    --data-binary "$payload")

  # Streamable transport answers as SSE; take the first data: line.
  json=${resp#*$'\n'data: }
  [ "$json" = "$resp" ] && json=${resp#data: }

  if err=$(jq -er '.error.message' <<<"$json" 2>/dev/null); then
    echo "FAIL $name: ${err:0:300}" >&2
    fail=1
    continue
  fi

  if ! jq -e '.result.content[0].data' <<<"$json" >/dev/null 2>&1; then
    echo "FAIL $name: unexpected response: ${json:0:300}" >&2
    fail=1
    continue
  fi

  jq -r '.result.content[0].data' <<<"$json" | base64 -d > "$name.png"
  printf '%-28s %s\n' "$name.png" "$(du -h "$name.png" | cut -f1)"
done

exit $fail
