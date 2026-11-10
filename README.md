# Local draw.io MCP server (Podman + Quadlet + Pi)

The official draw.io MCP server, self-hosted on this machine so diagram data never
leaves it. Pi connects over streamable HTTP at `http://127.0.0.1:3001/mcp`.

- Image: `docker.io/jgraph/drawio-mcp:latest` (v1.5.0, linux/amd64 + arm64)
- Source: https://github.com/jgraph/drawio-mcp (`mcp-app-server/`)
- Hub: https://hub.docker.com/r/jgraph/drawio-mcp

## What is running

| Piece | Location |
|---|---|
| Quadlet unit | `~/.config/containers/systemd/drawio-mcp.container` |
| systemd service | `drawio-mcp.service` (user scope, generated from the Quadlet) |
| Container | `drawio-mcp`, published only on `127.0.0.1:3001` |
| Pi MCP config | `~/.pi/agent/mcp.json` (server name `drawio`, `exposure: direct`) |
| Helper script | `scripts/drawio-mcp.sh` |

The container is stateless: no volume, no diagram content in logs, and it needs no
outbound network access to render diagrams. Nothing runs at boot (no linger); the
server starts on login and can be stopped anytime with `./scripts/drawio-mcp.sh down`.

## How the agent sees diagrams

Authoring from MCP `create_diagram` alone produces browser links; to visually
verify work, render `.drawio` files to PNG with the headless export container
(`rlespinasse/drawio-export`, draw.io Desktop + xvfb, pulled as
`docker.io/rlespinasse/drawio-export:v4.60.0`) and read the image:

```bash
./scripts/drawio-export.sh -f png -s 2 diagram.drawio   # → diagram/export/diagram-*.png
```

Then read the PNG (image files are rendered to the model). The render
container runs only per invocation — nothing stays running.

Workflow: author XML (or ask MCP tools) → export PNG → read → fix overlaps/edges
→ re-export. Note `%>[]` mistakes like `src=` vs `source=` on `mxCell` edges only
show up visually — the render step is the check.

## Daily commands

```bash
./scripts/drawio-mcp.sh status      # unit + /health + pi tool list
./scripts/drawio-mcp.sh restart     # after changing the Quadlet file
./scripts/drawio-mcp.sh logs        # follow container logs
./scripts/drawio-mcp.sh update      # podman pull + restart
./scripts/drawio-export.sh diagram.drawio               # render to PNG for visual check
./scripts/drawio-export.sh -f svg -s 2 diagram.drawio   # svg format, scale options
```

A third-party `drawio-skill` (authoring/sync/query workflows) is installed at
`~/.pi/agent/skills/drawio-skill` — reachable via `/skill:drawio-skill`.

## Verify by hand

Quick checks without Pi:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3001/health   # 200
```

```bash
systemctl --user status drawio-mcp.service
systemctl --user restart drawio-mcp.service
journalctl --user -u drawio-mcp.service -f
```

## Optional: start at boot without logging in

Quadlet auto-enables the unit for the login session. For a headless/boot start:

```bash
sudo loginctl enable-linger "$USER"
```

## Tools exposed to the model

Pi registers them as `mcp__drawio__<tool>`:

- `create_diagram` — draw.io XML or Mermaid (28 diagram types); returns an
  `app.diagrams.net` `#create=` link because Pi has no MCP Apps inline viewer.
- `search_shapes` — searches 10,000+ shapes across AWS/Azure/GCP/K8s/BPMN/UML/etc.
  and returns exact style strings to paste into XML.
- `get_drawio_reference` — the XML/Mermaid generation reference; read once per
  format before the first diagram.

Typical flow: `get_drawio_reference` → `search_shapes` (optional) → `create_diagram`.

## Configuration knobs

Set in the `[Container]` section of the Quadlet file, then `./scripts/drawio-mcp.sh restart`:

| Variable | Current / default | Notes |
|---|---|---|
| `PORT` | `3001` | Listening port inside the container |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Rejects requests whose `Host` header differs |
| `DRAWIO_BASE_URL` | `https://app.diagrams.net/` | Editor opened by "Open in draw.io" links |
| `DRAWIO_ICON_SERVICE_URL` | unset | `off` stops `search_shapes` from querying `icons.diagrams.net` |

Publishing is `127.0.0.1:3001:3001`, i.e. this machine only. Changing it to
`3001:3001` exposes an unauthenticated server to the whole network — don't, unless
it sits behind an authenticating proxy.

## Verify by hand

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3001/health   # 200

SID=$(curl -s -D- -o /dev/null -X POST http://127.0.0.1:3001/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}' \
  | grep -i '^mcp-session-id' | tr -d '\r' | awk '{print $2}')

curl -s -X POST http://127.0.0.1:3001/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -H "Mcp-Session-Id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"create_diagram","arguments":{"mermaid":"flowchart LR\n  A[Prompt] --> B[LLM]\n  B --> C[draw.io MCP]"}}}'
```

## Pi-side notes

- Config lives in `~/.pi/agent/mcp.json`; inside a session use `/mcp` to inspect,
  `/reload` after external config changes.
- `exposure: direct` declares all three tools to the model (small, frequently used
  set). Switch to `codemode` or `deferred` if the tool list grows.
- To use the hosted instance instead of this container, change `url` to
  `https://mcp.draw.io/mcp` — note that diagram XML then leaves the machine.
- Alternative for local `.drawio` files instead of browser links: the stdio tool
  server (`npx @drawio/mcp`) or the `drawio` assistant plugin.
