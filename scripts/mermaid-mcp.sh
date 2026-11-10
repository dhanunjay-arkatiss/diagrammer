#!/usr/bin/env bash
# mcp-mermaid.sh — manage the self-hosted Mermaid MCP server (Quadlet-managed),
# and rebuild its image from the pinned upstream tag when needed.
#
# The unit is ON-DEMAND: it has no [Install] section, so it is never started at
# boot or at login. Start it when you need it, stop it when you don't.
set -euo pipefail

UNIT=mcp-mermaid
ENDPOINT=http://127.0.0.1:1122/mcp
IMAGE=localhost/mcp-mermaid:0.4.1
TAG=0.4.1
SRC=${SRC:-/tmp/mcp-mermaid-src}
QUADLET=${QUADLET_DIR:-$HOME/.config/containers/systemd}/$UNIT.container

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

  up        Start the container now (on demand)
  down      Stop the container
  restart   Restart the container
  status    Show unit status, autostart policy, health and Pi tool list
  logs      Follow container logs
  build     Clone tag $TAG and rebuild $IMAGE
  renders   List PNGs written by outputType=file
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
  logs)    podman logs -f "$UNIT" ;;
  endpoint) echo "$ENDPOINT" ;;
  renders) ls -lt "$HOME/work/projects/diagrams/renders" | head -20 ;;
  build)
    rm -rf "$SRC"
    git clone --depth 1 --branch "$TAG" https://github.com/hustcc/mcp-mermaid.git "$SRC"
    podman build -t "$IMAGE" -f "$SRC/Dockerfile" "$SRC"
    echo "Rebuilt $IMAGE from tag $TAG. Restart with: $(basename "$0") restart"
    ;;
  status)
    echo -n "boot:   "; boot_state
    echo -n "active: "; systemctl --user is-active "$UNIT.service" || true
    podman ps --filter "name=$UNIT" --format 'container: {{.Status}} {{.Ports}}' || true
    echo -n "tools:  "
    { pi mcp list 2>/dev/null || true; } | grep -E '^mermaid:' || echo "pi mcp list unavailable"
    ;;
  *) usage; exit 1 ;;
esac
