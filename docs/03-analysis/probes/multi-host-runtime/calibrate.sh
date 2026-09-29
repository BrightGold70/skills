#!/usr/bin/env bash

for name in "${!CLAUDE@}"; do
  unset "$name"
done
unset HPW_AGENT_BACKEND

repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 2
sha=${1-}
resolved=$(git -C "$repo" rev-parse --verify -q "$sha^{commit}") || {
  echo 'CALIBRATE: UNREADABLE reason=bad_sha'
  exit 2
}

CA='\b[A-Z][a-z]+([A-Z][a-z]+)*\(|`[A-Z][a-z]+([A-Z][a-z]+)+`|\bCLAUDE[A-Z0-9_]*\b|(~|\$HOME|\$\{HOME\})/\.claude\b'
EX='(Error|Exception|Warning|Expired|Exit|Interrupt)`$'
for f in h-mad/SKILL.md handoff/SKILL.md; do
  git -C "$repo" cat-file -e "$resolved:$f" || exit 2
  echo "== $f"
  lines=$(git -C "$repo" show "$resolved:$f" | grep -o -E "$CA" | grep -v -E "$EX" | sort | uniq -c) || exit 2
  if [[ -n "$lines" ]]; then
    printf '%s\n' "$lines"
  fi
  occurrences=$(printf '%s\n' "$lines" | awk '{n += $1} END {print n + 0}') || exit 2
  distinct=$(printf '%s\n' "$lines" | awk 'NF {n++} END {print n + 0}') || exit 2
  echo "TOTAL $f occurrences=$occurrences distinct=$distinct"
done
echo "CALIBRATE: OK sha=$resolved"
