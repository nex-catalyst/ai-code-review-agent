#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_SKILL_DIR="$REPO_ROOT/.github/skills/code-review-pro"
TARGET_DIR="$HOME/.copilot/skills"
TARGET_LINK="$TARGET_DIR/code-review-pro"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/install_local_skill.sh install
  ./scripts/install_local_skill.sh uninstall
  ./scripts/install_local_skill.sh status
EOF
}

ensure_source() {
  if [[ ! -d "$SOURCE_SKILL_DIR" ]]; then
    echo "Source skill directory not found: $SOURCE_SKILL_DIR"
    exit 1
  fi
}

install_link() {
  ensure_source
  mkdir -p "$TARGET_DIR"

  if [[ -L "$TARGET_LINK" ]]; then
    rm "$TARGET_LINK"
  elif [[ -e "$TARGET_LINK" ]]; then
    echo "Target exists and is not a symlink: $TARGET_LINK"
    echo "Please remove it manually first."
    exit 1
  fi

  ln -s "$SOURCE_SKILL_DIR" "$TARGET_LINK"
  echo "Installed symlink: $TARGET_LINK -> $SOURCE_SKILL_DIR"
}

uninstall_link() {
  if [[ -L "$TARGET_LINK" ]]; then
    rm "$TARGET_LINK"
    echo "Removed symlink: $TARGET_LINK"
  else
    echo "No symlink found at: $TARGET_LINK"
  fi
}

status_link() {
  if [[ -L "$TARGET_LINK" ]]; then
    echo "OK: $TARGET_LINK -> $(readlink "$TARGET_LINK")"
  elif [[ -e "$TARGET_LINK" ]]; then
    echo "WARN: $TARGET_LINK exists but is not a symlink"
  else
    echo "MISSING: $TARGET_LINK"
  fi
}

cmd="${1:-status}"
case "$cmd" in
  install) install_link ;;
  uninstall) uninstall_link ;;
  status) status_link ;;
  *) usage; exit 2 ;;
esac
