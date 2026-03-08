#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SUBMODULES=(
  "https://github.com/gitroomhq/postiz-app vendor/postiz-app"
  "https://github.com/ClimenteA/social-media-posts-scheduler vendor/django-social-scheduler"
  "https://github.com/Masterjx9/socialmediascheduler vendor/socialmediascheduler"
  "https://github.com/ayrshare/social-media-api vendor/ayrshare-js"
  "https://github.com/ayrshare/social-post-api-python vendor/ayrshare-python"
)

print_expected_commands() {
  for row in "${SUBMODULES[@]}"; do
    local url="${row%% *}"
    local path="${row#* }"
    echo "git submodule add $url $path"
  done
}

if ! command -v git >/dev/null 2>&1; then
  echo "git is not installed or not available in PATH."
  exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "This folder is not inside a git repository."
  echo "Expected commands:"
  print_expected_commands
  echo "git submodule update --init --recursive"
  echo "git submodule foreach --recursive 'git pull origin main'"
  exit 0
fi

TOP_LEVEL="$(git rev-parse --show-toplevel)"
if [[ "$TOP_LEVEL" != "$ROOT_DIR" ]]; then
  echo "Safety stop: $ROOT_DIR is not the active git top-level."
  echo "Detected git top-level: $TOP_LEVEL"
  echo "Skipping automatic submodule add to avoid writing outside this project folder."
  echo "Expected commands:"
  print_expected_commands
  echo "git submodule update --init --recursive"
  echo "git submodule foreach --recursive 'git pull origin main'"
  exit 0
fi

mkdir -p vendor

for row in "${SUBMODULES[@]}"; do
  url="${row%% *}"
  path="${row#* }"

  if [[ -e "$path" ]]; then
    echo "Skipping existing path: $path"
    echo "Expected command: git submodule add $url $path"
    continue
  fi

  git submodule add "$url" "$path"
done

git submodule update --init --recursive

git submodule foreach --recursive '
branch="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed "s#^origin/##")"
if [ -z "$branch" ]; then branch="main"; fi
echo "Updating $name using $branch"
git pull origin "$branch" || true
'

echo "Current submodules:"
git submodule status --recursive
