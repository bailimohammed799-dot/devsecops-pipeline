#!/bin/bash
# Stage 6 — Docker image build + Trivy scan + push to local registry
set -euo pipefail

OUTPUT_DIR="${1:?Usage: $0 <output_dir>}"
PROJECT_DIR="/tmp/conduit-app"
BUILD_DIR="/tmp/conduit-build"
REGISTRY="${REGISTRY_URL:-localhost:5000}"
IMAGE_TAG="${REGISTRY}/conduit:$(date +%Y%m%d-%H%M%S)"
IMAGE_LATEST="${REGISTRY}/conduit:latest"

mkdir -p "$OUTPUT_DIR"

# Copy project to build context
echo "Preparing build context..."
rm -rf "$BUILD_DIR"
cp -r "$PROJECT_DIR" "$BUILD_DIR"

# Copy Dockerfile into build context
cp docker/Dockerfile "$BUILD_DIR/Dockerfile"

GIT_SHA=$(cd "$PROJECT_DIR" && git rev-parse --short HEAD)
BUILD_TIME=$(date -Iseconds)

echo "Building Docker image: $IMAGE_TAG"
docker build \
    --label "org.opencontainers.image.revision=$GIT_SHA" \
    --label "org.opencontainers.image.created=$BUILD_TIME" \
    --label "org.opencontainers.image.version=1.0" \
    -t "$IMAGE_TAG" \
    -t "$IMAGE_LATEST" \
    "$BUILD_DIR" 2>&1 | tee "$OUTPUT_DIR/build.log"

echo "Running Trivy filesystem scan on build context..."
trivy fs --format json --output "$OUTPUT_DIR/trivy-fs.json" \
    --severity HIGH,CRITICAL \
    "$BUILD_DIR" 2>&1 | tee "$OUTPUT_DIR/trivy-fs.log" || true

echo "Running Trivy image scan..."
trivy image --format json --output "$OUTPUT_DIR/trivy-image.json" \
    --severity HIGH,CRITICAL \
    "$IMAGE_TAG" 2>&1 | tee "$OUTPUT_DIR/trivy-image.log" || true

echo "Pushing to local registry: $IMAGE_TAG"
docker push "$IMAGE_TAG" 2>&1 | tee -a "$OUTPUT_DIR/push.log"
docker push "$IMAGE_LATEST" 2>&1 | tee -a "$OUTPUT_DIR/push.log"

# Generate image metadata
python3 -c "
import json
meta = {
    'image': '$IMAGE_TAG',
    'latest': '$IMAGE_LATEST',
    'registry': '$REGISTRY',
    'git_sha': '$GIT_SHA',
    'build_time': '$BUILD_TIME',
    'labels': {
        'revision': '$GIT_SHA',
        'created': '$BUILD_TIME',
        'version': '1.0',
    }
}
with open('$OUTPUT_DIR/image-metadata.json', 'w') as f:
    json.dump(meta, f, indent=2)
print(json.dumps(meta, indent=2))
"

# Generate summary
python3 -c "
import json, os
outdir = '$OUTPUT_DIR'

trivy_image_count = 0
try:
    with open(os.path.join(outdir, 'trivy-image.json')) as f:
        data = json.load(f)
    trivy_image_count = len(data.get('Results', []))
except: pass

trivy_fs_count = 0
try:
    with open(os.path.join(outdir, 'trivy-fs.json')) as f:
        data = json.load(f)
    trivy_fs_count = len(data.get('Results', []))
except: pass

summary = f'''# Image Scan Summary

| Check | Findings |
|-------|----------|
| Trivy filesystem | {trivy_fs_count} result groups ([trivy-fs.json](trivy-fs.json)) |
| Trivy image | {trivy_image_count} result groups ([trivy-image.json](trivy-image.json)) |

**Image:** \`$IMAGE_TAG\`
**Registry:** \`$REGISTRY\`
**Git SHA:** \`$GIT_SHA\`
'''
with open(os.path.join(outdir, 'image-scan-summary.md'), 'w') as f:
    f.write(summary)
print(summary)
"

echo "Stage 6 complete."
