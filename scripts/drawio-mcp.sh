#!/usr/bin/env bash
# drawio-mcp.sh — manage the self-hosted draw.io MCP server (Quadlet-managed).
#
# The unit is ON-DEMAND: it has no [Install] section, so it is never started at
# boot or at login. Start it when you need it, stop it when you don't.
set -euo pipefail

UNIT=drawio-mcp
ENDPOINT=http://127.0.0.1:3001/mcp
IMAGE=docker.io/jgraph/drawio-mcp:latest
QUADLET=${QUADLET_DIR:-$HOME/.config/containers/systemd}/$UNIT.container

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

  up        Start the container now (on demand)
  down      Stop the container
  restart   Restart the container
  status    Show unit status, autostart policy, health and MCP handshake
  logs      Follow container logs
  update    Pull $IMAGE and restart
  boot      Show whether it starts automatically at boot/login
  boot-on   Make it start automatically at boot (opt-in)
  boot-off  Make it on-demand only (default)
  endpoint  Print the MCP endpoint URL
EOF
}

# The only difference between "on-demand" and "at boot" is the [Install]
# section in the Quadlet file, which is what makes systemd enable the unit.
boot_state() {
  if grep -qx 'WantedBy=default.target' "$QUADLET" 2>/dev/null; then
    echo "on   — starts automatically at boot/login"
  else
    echo "off  — on-demand only (start it with: $(basename "$0") up)"
  fi
}

boot_on() {
  [[ -f $QUADLET ]] || { echo "no such file: $QUADLET" >&2; exit 2; }
  if grep -qx 'WantedBy=default.target' "$QUADLET"; then
    echo "already enabled"
  else
    grep -qx '\[Install\]' "$QUADLET" || printf '[Install]\n' >>"$QUADLET"
    printf 'WantedBy=default.target\n' >>"$QUADLET"
    echo "added [Install] WantedBy=default.target -> $QUADLET"
  fi
  systemctl --user daemon-reload
  echo -n "boot: "; boot_state
  echo "For a start before you log in, run once as root: sudo loginctl enable-linger $USER"
}

boot_off() {
  [[ -f $QUADLET ]] || { echo "no such file: $QUADLET" >&2; exit 2; }
  sed -i -e '/^\[Install\]$/d' -e '/^WantedBy=default\.target$/d' "$QUADLET"
  sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$QUADLET"   # trim trailing blank lines
  systemctl --user daemon-reload
  echo "removed [Install] from $QUADLET"
  echo -n "boot: "; boot_state
}

case "${1:-}" in
  up)      systemctl --user start "$UNIT.service" ;;
  down)    systemctl --user stop "$UNIT.service" ;;
  restart) systemctl --user restart "$UNIT.service" ;;
  boot)    boot_state ;;
  boot-on) boot_on ;;
  boot-off) boot_off ;;
  update)  podman pull "$IMAGE"
           systemctl --user restart "$UNIT.service" ;;
  logs)    podman logs -f "$UNIT" ;;
  endpoint) echo "$ENDPOINT" ;;
  status)
    echo -n "boot:   "; boot_state
    echo -n "active: "; systemctl --user is-active "$UNIT.service" || true
    echo -n "health: "
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 3 http://127.0.0.1:3001/health 2>/dev/null || true)
    if [[ $code == 2* ]]; then echo "$code"; else echo "unreachable (stopped?)"; fi
    echo -n "tools:  "
    { pi mcp list 2>/dev/null || true; } | grep -E '^drawio:' || echo "pi mcp list unavailable"
    ;;
  *) usage; exit 1 ;;
esac
