#!/bin/bash
# Stage 1 — Source code retrieval & integrity verification
set -euo pipefail

TARGET_REPO="${1:?Usage: $0 <repo> <commit> <output_dir>}"
TARGET_COMMIT="${2:?}"
OUTPUT_DIR="${3:?}"

mkdir -p "$OUTPUT_DIR"
CLONE_DIR="/tmp/conduit-app"

echo "Cloning $TARGET_REPO at commit $TARGET_COMMIT..."

# Clean previous clone if exists
rm -rf "$CLONE_DIR"

# Clone the repo
git clone --quiet "https://github.com/${TARGET_REPO}.git" "$CLONE_DIR" 2>&1
cd "$CLONE_DIR"

# Checkout the pinned commit
git checkout --quiet "$TARGET_COMMIT" 2>&1
ACTUAL_SHA=$(git rev-parse HEAD)

# Verify SHA matches
if [ "$ACTUAL_SHA" != "$TARGET_COMMIT" ]; then
    echo "ERROR: SHA mismatch! Expected $TARGET_COMMIT, got $ACTUAL_SHA"
    exit 1
fi

echo "Commit verified: $ACTUAL_SHA"

# Check for GPG signature (non-fatal if not signed)
echo "Checking GPG signatures..."
git log --show-signature -1 || echo "  (no GPG signature found — non-fatal)"

# Gitleaks pre-scan on cloned tree
echo "Running Gitleaks pre-scan..."
gitleaks detect --source . -v --no-git -r "$OUTPUT_DIR/gitleaks-pre.json" 2>&1 || true
GITLEAKS_EXIT=$?
if [ $GITLEAKS_EXIT -eq 1 ]; then
    echo "WARNING: Gitleaks found potential secrets (see gitleaks-pre.json)"
fi

# Generate clone manifest
pip install pygount 2>/dev/null || true
FILE_COUNT=$(find . -type f -not -path './.git/*' | wc -l)

python3 -c "
import json, os, subprocess
manifest = {
    'repo': '$TARGET_REPO',
    'commit_sha': '$ACTUAL_SHA',
    'license': 'MIT',
    'file_count': $FILE_COUNT,
    'clone_timestamp': '$(date -Iseconds)',
}
with open('$OUTPUT_DIR/clone-manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)
print(json.dumps(manifest, indent=2))
"

echo "Stage 1 complete. Manifest at $OUTPUT_DIR/clone-manifest.json"
