#!/usr/bin/env bash
# drawio-mcp.sh — manage the self-hosted draw.io MCP server (Quadlet-managed).
set -euo pipefail

UNIT=drawio-mcp
ENDPOINT=http://127.0.0.1:3001/mcp
IMAGE=docker.io/jgraph/drawio-mcp:latest

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

  up        Start the container (systemd user unit)
  down      Stop the container
  restart   Restart the container
  status    Show unit status + health + MCP handshake
  logs      Follow container logs
  update    Pull $IMAGE and restart
  enable    Reload Quadlet units and print the linger command for boot start
  endpoint  Print the MCP endpoint URL
EOF
}

case "${1:-}" in
  up)      systemctl --user start "$UNIT.service" ;;
  down)    systemctl --user stop "$UNIT.service" ;;
  restart) systemctl --user restart "$UNIT.service" ;;
  enable)  # Quadlet units auto-enable via their [Install] WantedBy= key.
           systemctl --user daemon-reload
           systemctl --user is-enabled "$UNIT.service" || true
           echo "To start at boot without logging in, run once as root:"
           echo "  sudo loginctl enable-linger $USER" ;;
  update)  podman pull "$IMAGE"
           systemctl --user restart "$UNIT.service" ;;
  logs)    podman logs -f "$UNIT" ;;
  endpoint) echo "$ENDPOINT" ;;
  status)
    systemctl --user --no-pager status "$UNIT.service" | head -5 || true
    echo -n "health: "
    curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3001/health || echo "unreachable"
    echo -n "tools:  "
    pi mcp list 2>/dev/null | grep -E '^drawio:' || echo "pi mcp list unavailable"
    ;;
  *) usage; exit 1 ;;
esac
