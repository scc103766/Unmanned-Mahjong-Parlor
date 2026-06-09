#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"
PROJECT_NAME="$(basename "${PROJECT_ROOT}")"
PROJECT_HASH="$(printf '%s' "${PROJECT_ROOT}" | sha256sum | awk '{print substr($1, 1, 12)}')"
PROJECT_SLUG="${CODEX_PROJECT_SLUG:-${PROJECT_NAME}-${PROJECT_HASH}}"
PROJECT_HOME_BASE="${CODEX_PROJECT_HOME_BASE:-${HOME}/.codex-projects}"
PROJECT_CODEX_HOME="${CODEX_PROJECT_HOME:-${PROJECT_HOME_BASE}/${PROJECT_SLUG}}"
GLOBAL_CODEX_HOME="${CODEX_GLOBAL_HOME:-${HOME}/.codex}"

escape_toml_string() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "${value}"
}

init_project_codex_home() {
  mkdir -p "${PROJECT_CODEX_HOME}"

  if [[ ! -e "${PROJECT_CODEX_HOME}/auth.json" && -e "${GLOBAL_CODEX_HOME}/auth.json" ]]; then
    ln -s "${GLOBAL_CODEX_HOME}/auth.json" "${PROJECT_CODEX_HOME}/auth.json"
  fi

  if [[ ! -e "${PROJECT_CODEX_HOME}/skills" && -e "${GLOBAL_CODEX_HOME}/skills" ]]; then
    ln -s "${GLOBAL_CODEX_HOME}/skills" "${PROJECT_CODEX_HOME}/skills"
  fi

  if [[ ! -e "${PROJECT_CODEX_HOME}/config.toml" ]]; then
    local escaped_project_root
    escaped_project_root="$(escape_toml_string "${PROJECT_ROOT}")"
    cat >"${PROJECT_CODEX_HOME}/config.toml" <<CONFIG
model = "${CODEX_MODEL:-gpt-5.5}"
model_reasoning_effort = "${CODEX_REASONING_EFFORT:-xhigh}"
service_tier = "${CODEX_SERVICE_TIER:-fast}"

[projects."${escaped_project_root}"]
trust_level = "trusted"
CONFIG
    chmod 600 "${PROJECT_CODEX_HOME}/config.toml"
  fi
}

print_env() {
  cat <<INFO
PROJECT_ROOT=${PROJECT_ROOT}
PROJECT_SLUG=${PROJECT_SLUG}
CODEX_HOME=${PROJECT_CODEX_HOME}
GLOBAL_CODEX_HOME=${GLOBAL_CODEX_HOME}
INFO
}

case "${1:-}" in
  --print-env)
    print_env
    exit 0
    ;;
  --init-only)
    init_project_codex_home
    print_env
    exit 0
    ;;
esac

init_project_codex_home
export CODEX_HOME="${PROJECT_CODEX_HOME}"

echo "Using project-scoped CODEX_HOME=${CODEX_HOME}" >&2
echo "Project=${PROJECT_ROOT}" >&2
exec codex "$@"
