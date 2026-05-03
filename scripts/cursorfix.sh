#!/usr/bin/env bash
set -euo pipefail

# Rewrites commits authored/committed by Cursor Agent to your identity.
# GitHub username (e.g. rosspeili) is not used in git metadata; only name + email matter.
#
# Usage:
#   ./scripts/cursorfix.sh git@github.com:ORG/REPO.git
# Or override:
#   TARGET_NAME="Vladimiros Peilivanidis" TARGET_EMAIL="vpeilivanidis@gmail.com" ./scripts/cursorfix.sh git@github.com:ORG/REPO.git
#
# Optional:
#   CURSOR_EMAILS="cursoragent@users.noreply.github.com,cursoragent@cursor.com"
#   CURSOR_NAMES="cursoragent,Cursor Agent"
#   CURSOR_SUBSTRINGS="cursoragent,cursor agent,@cursor.com"
#   WORKDIR=/path/to/mirror.git

REPO_URL="${1:-}"
CURSOR_EMAILS="${CURSOR_EMAILS:-cursoragent@users.noreply.github.com,cursoragent@cursor.com}"
CURSOR_NAMES="${CURSOR_NAMES:-cursoragent,Cursor Agent,Cursoragent}"
CURSOR_SUBSTRINGS="${CURSOR_SUBSTRINGS:-cursoragent,cursor agent,@cursor.com}"
WORKDIR="${WORKDIR:-/tmp/repo-clean-$$.git}"

# Prefer explicit env, then global git config, then maintainer defaults.
TARGET_NAME="${TARGET_NAME:-}"
if [[ -z "$TARGET_NAME" ]]; then
  TARGET_NAME="$(git config --global --get user.name 2>/dev/null || true)"
fi
if [[ -z "$TARGET_NAME" ]]; then
  TARGET_NAME="Vladimiros Peilivanidis"
fi

TARGET_EMAIL="${TARGET_EMAIL:-}"
if [[ -z "$TARGET_EMAIL" ]]; then
  TARGET_EMAIL="$(git config --global --get user.email 2>/dev/null || true)"
fi
if [[ -z "$TARGET_EMAIL" ]]; then
  TARGET_EMAIL="vpeilivanidis@gmail.com"
fi

if [[ -z "$REPO_URL" ]]; then
  echo "ERROR: Missing repository URL."
  echo "Example: $0 git@github.com:ORG/REPO.git"
  exit 1
fi

if [[ -z "$TARGET_NAME" || -z "$TARGET_EMAIL" ]]; then
  echo "ERROR: TARGET_NAME or TARGET_EMAIL is empty."
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed."
  exit 1
fi

if ! git filter-repo -h >/dev/null 2>&1; then
  cat <<'MSG'
ERROR: git-filter-repo is not installed.
Install one of:
  - pipx install git-filter-repo
  - python3 -m pip install --user git-filter-repo
  - brew install git-filter-repo
Then rerun this script.
MSG
  exit 1
fi

if [[ -e "$WORKDIR" ]]; then
  echo "Cleaning existing workdir: $WORKDIR"
  rm -rf "$WORKDIR"
fi

echo "Target identity: $TARGET_NAME <$TARGET_EMAIL>"
echo "Cloning mirror: $REPO_URL"
git clone --mirror "$REPO_URL" "$WORKDIR"

cd "$WORKDIR"

CALLBACK_FILE="$(mktemp)"
cat > "$CALLBACK_FILE" <<PY
target_name = ${TARGET_NAME@Q}.encode("utf-8")
target_email = ${TARGET_EMAIL@Q}.encode("utf-8")
cursor_emails = {e.strip().lower().encode("utf-8") for e in ${CURSOR_EMAILS@Q}.split(",") if e.strip()}
cursor_names = {n.strip().lower().encode("utf-8") for n in ${CURSOR_NAMES@Q}.split(",") if n.strip()}
cursor_substrings = [s.strip().lower().encode("utf-8") for s in ${CURSOR_SUBSTRINGS@Q}.split(",") if s.strip()]

def _looks_like_cursor_identity(name: bytes, email: bytes) -> bool:
    nl = name.lower()
    el = email.lower()
    if el in cursor_emails or nl in cursor_names:
        return True
    return any(sub in nl or sub in el for sub in cursor_substrings)

if _looks_like_cursor_identity(commit.author_name, commit.author_email):
    commit.author_name = target_name
    commit.author_email = target_email

if _looks_like_cursor_identity(commit.committer_name, commit.committer_email):
    commit.committer_name = target_name
    commit.committer_email = target_email
PY

echo "Rewriting history with git filter-repo..."
git filter-repo --force --commit-callback "$(cat "$CALLBACK_FILE")"
rm -f "$CALLBACK_FILE"

if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REPO_URL"
fi

echo "Force pushing rewritten refs to origin..."
git push --force --mirror origin

echo "Done. GitHub Contributors can take some time to refresh contributor cache."
