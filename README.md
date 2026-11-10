# Local diagram MCP servers (Podman + Quadlet + Pi)

Two self-hosted MCP servers so diagrams never leave this machine. Pi connects to
both over streamable HTTP.

| Server | Endpoint | Image | Source |
|---|---|---|---|
| draw.io | `http://127.0.0.1:3001/mcp` | `docker.io/jgraph/drawio-mcp:latest` (1.5.0) | https://github.com/jgraph/drawio-mcp |
| Mermaid | `http://127.0.0.1:1122/mcp` | `localhost/mcp-mermaid:0.4.1` (built from source) | https://github.com/hustcc/mcp-mermaid |

## What is running

| Piece | Location |
|---|---|
| Quadlet units | `~/.config/containers/systemd/{drawio-mcp,mcp-mermaid}.container` |
| systemd services | `drawio-mcp.service`, `mcp-mermaid.service` (user scope, generated) |
| Containers | `drawio-mcp` on `127.0.0.1:3001`, `mcp-mermaid` on `127.0.0.1:1122` |
| Pi MCP config | `~/.pi/agent/mcp.json` (servers `drawio` and `mermaid`, `exposure: direct`) |
| Helper scripts | `scripts/drawio-mcp.sh`, `scripts/mermaid-mcp.sh`, `scripts/drawio-export.sh` |
| Mermaid PNG output | `renders/` (mounted at `/app/out` in the container) |
| Mermaid diagram export | `the_meet/export_mermaid/` — `.mmd` sources + PNGs + `render.sh` |

Both containers are loopback-only and stateless (no logs of diagram content).
**Nothing starts automatically** — not at boot, not at login, not even when you
open a Pi session. The Quadlet units have no `[Install]` section, so they are
strictly on-demand: `./scripts/<name>.sh up` when you want them, `down` when you
don't. `./scripts/<name>.sh boot` prints the current policy.

### Why mcp-mermaid is built locally

Docker Hub `susuperli/mcp-mermaid:latest` is version 0.2.3 and advertises only
`outputType: png|svg|mermaid`. Upstream source/npm is 0.4.1, which adds
`outputType: base64|file|svg_url|png_url`. The unit therefore runs a local image
built from tag `0.4.1` (`scripts/mermaid-mcp.sh build` rebuilds it):

```bash
./scripts/mermaid-mcp.sh build && ./scripts/mermaid-mcp.sh restart
```

Note: upstream hardcodes `serverInfo.version = 0.1.3` in `src/server.ts`, so the
handshake reports 0.1.3 regardless of the built tag.

## How the agent sees diagrams

**Mermaid** — `generate_mermaid_diagram` with the default `outputType: base64`
returns an `image/png` content block, which Pi hands to the model directly. No
extra step needed. Use `outputType: file` to also keep the PNG in `renders/`.

**draw.io** — `create_diagram` only returns an `app.diagrams.net` link (Pi has no
MCP Apps inline viewer), so verify visually by rendering to PNG with the headless
export container (`rlespinasse/drawio-export`, draw.io Desktop + xvfb):

```bash
./scripts/drawio-export.sh -f png -s 2 diagram.drawio   # → diagram/export/diagram-*.png
```

Then read the PNG. The exporter runs per invocation (`--rm`) — nothing stays up.

Workflow for draw.io: author XML (or use MCP tools) → export PNG → read → fix
overlaps/edges → re-export. Structural mistakes (e.g. `src=` instead of `source=`
on an `mxCell` edge) render as missing edges and are only caught visually.

## Daily commands

```bash
# lifecycle (both scripts take the same verbs)
./scripts/drawio-mcp.sh up          # start now — nothing starts on its own
./scripts/drawio-mcp.sh down        # stop (mermaid takes ~5s; node ignores SIGTERM)
./scripts/drawio-mcp.sh boot        # is it set to autostart? (off by default)
./scripts/drawio-mcp.sh boot-on     # opt in: start at boot/login
./scripts/drawio-mcp.sh boot-off    # opt out again (default state)

# draw.io
./scripts/drawio-mcp.sh status      # boot policy + unit + /health + pi tool list
./scripts/drawio-mcp.sh restart     # after changing the Quadlet file
./scripts/drawio-mcp.sh logs        # follow container logs
./scripts/drawio-mcp.sh update      # podman pull + restart
./scripts/drawio-export.sh diagram.drawio               # PNG for visual check
./scripts/drawio-export.sh -f svg -s 2 diagram.drawio   # svg, with options

# mermaid
./scripts/mermaid-mcp.sh status
./scripts/mermaid-mcp.sh restart
./scripts/mermaid-mcp.sh logs
./scripts/mermaid-mcp.sh build      # rebuild image from tag 0.4.1
./scripts/mermaid-mcp.sh renders    # list PNGs from outputType=file
```

A third-party `drawio-skill` (authoring/sync/query workflows) is installed at
`~/.pi/agent/skills/drawio-skill` — reachable via `/skill:drawio-skill`.

## Tools exposed to the model

Pi registers them as `mcp__<server>__<tool>`.

**drawio** (`mcp__drawio__*`):
- `create_diagram` — draw.io XML or Mermaid (28 diagram types); returns an
  `app.diagrams.net` `#create=` link.
- `search_shapes` — searches 10,000+ shapes (AWS/Azure/GCP/K8s/BPMN/UML/…) and
  returns exact style strings to paste into XML.
- `get_drawio_reference` — XML/Mermaid generation reference; read once per format.

Flow: `get_drawio_reference` → `search_shapes` (optional) → `create_diagram`.

**mermaid** (`mcp__mermaid__*`):
- `generate_mermaid_diagram` — `mermaid` (required), `theme`
  (`default|base|forest|dark|neutral`), `backgroundColor`, `outputType`
  (`base64` → inline PNG, `file` → `renders/`, `svg`, `mermaid`, `svg_url`,
  `png_url`).

## Configuration knobs

**draw.io** — `[Container]` in `drawio-mcp.container`, then
`./scripts/drawio-mcp.sh restart`:

| Variable | Current / default | Notes |
|---|---|---|
| `PORT` | `3001` | Listening port inside the container |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | Rejects requests whose `Host` header differs |
| `DRAWIO_BASE_URL` | `https://app.diagrams.net/` | Editor opened by "Open in draw.io" links |
| `DRAWIO_ICON_SERVICE_URL` | unset | `off` stops `search_shapes` from querying `icons.diagrams.net` |

**mermaid** — CLI flags in `Exec=` (`mcp-mermaid.container`):

| Flag | Current | Notes |
|---|---|---|
| `-t` | `streamable` | `sse` (`/sse`, port 3033) or `stdio` also supported |
| `-p` | `1122` | Port inside the container |
| `-H` | `0.0.0.0` | Container-internal bind; `PublishPort` decides exposure |
| `-e` | `/mcp` (default) | Endpoint path |

Both publish on `127.0.0.1` only. Changing that to a bare `3001:3001` /
`1122:1122` exposes unauthenticated servers to the whole network — don't, unless
they sit behind an authenticating proxy.

## Verify by hand

```bash
curl -s -o /dev/null -w 'drawio health: %{http_code}\n' http://127.0.0.1:3001/health

# mermaid handshake
curl -s -X POST http://127.0.0.1:1122/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"smoke","version":"1"}}}'

# mermaid render (writes into ./renders/)
curl -s -X POST http://127.0.0.1:1122/mcp \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_mermaid_diagram","arguments":{"mermaid":"flowchart LR\n  A[Prompt] --> B[Mermaid MCP]","outputType":"file"}}}'
```

draw.io tools/call needs an `Mcp-Session-Id` from the initialize response header
(mermaid's streamable transport is stateless and needs none).

## Autostart (opt-in only)

Default state: **off**. The Quadlet files deliberately end before any `[Install]`
section; that alone is what keeps systemd from pulling them into `default.target`
at boot. `Restart=on-failure` means a deliberate `down` stays down.

To opt in later:

```bash
./scripts/drawio-mcp.sh boot-on      # adds [Install] WantedBy=default.target
./scripts/mermaid-mcp.sh boot-on
sudo loginctl enable-linger "$USER"  # also start before you log in (headless)
```

Undo with `boot-off` on both. Currently off, per preference for nothing running
continuously.

## Pi-side notes

- Config lives in `~/.pi/agent/mcp.json`; inside a session use `/mcp` to inspect,
  `/reload` after external config changes.
- `exposure: direct` declares the tools to the model (four tools total). Switch to
  `codemode` or `deferred` if these grow.
- To use the hosted draw.io instance instead, change its `url` to
  `https://mcp.draw.io/mcp` — diagram XML then leaves the machine.
- Alternative for local `.drawio` files instead of browser links: the stdio tool
  server (`npx @drawio/mcp`) or the `drawio` assistant plugin.
