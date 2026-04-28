#!/usr/bin/env bash

AI_AUTHORSHIP_REGEX='^AI-Authorship:[[:space:]]*(ai-authored|ai-assisted|human)[[:space:]]*$'
AI_TOOL_REGEX='^AI-Tool:[[:space:]]*(cursor|copilot|claude-code|none)[[:space:]]*$'
AI_MODEL_REGEX='^AI-Model:[[:space:]]*[A-Za-z0-9_.-]+[[:space:]]*$'
HUMAN_EDIT_RATIO_REGEX='^Human-Edit-Ratio:[[:space:]]*(100|[1-9]?[0-9])[[:space:]]*$'
AI_MODE_REGEX='^AI-Mode:[[:space:]]*(auto|manual|hybrid)[[:space:]]*$'
AUDIT_STATUS_REGEX='^Audit-Status:[[:space:]]*(pending|passed|failed)[[:space:]]*$'

has_trailer() {
  local file="$1"
  local regex="$2"
  grep -qE "$regex" "$file"
}

append_missing_trailer() {
  local file="$1"
  local key="$2"
  local value="$3"
  if ! grep -qE "^${key}:" "$file"; then
    printf "%s: %s\n" "$key" "$value" >> "$file"
  fi
}

replace_or_append_trailer() {
  local file="$1"
  local key="$2"
  local value="$3"
  if grep -qE "^${key}:" "$file"; then
    sed -i.bak -E "s|^${key}:.*$|${key}: ${value}|" "$file"
    rm -f "${file}.bak"
  else
    printf "%s: %s\n" "$key" "$value" >> "$file"
  fi
}

validate_required_trailers() {
  local file="$1"
  has_trailer "$file" "$AI_AUTHORSHIP_REGEX" || return 1
  has_trailer "$file" "$AI_TOOL_REGEX" || return 1
  has_trailer "$file" "$AI_MODEL_REGEX" || return 1
  has_trailer "$file" "$HUMAN_EDIT_RATIO_REGEX" || return 1
  has_trailer "$file" "$AI_MODE_REGEX" || return 1
  has_trailer "$file" "$AUDIT_STATUS_REGEX" || return 1
}
