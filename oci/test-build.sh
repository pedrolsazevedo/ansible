#!/bin/bash

set -e

IMAGES=(alpine ubuntu ubi suse node oraclelinux)

echo "Testing Docker builds locally..."

for image in "${IMAGES[@]}"; do
    echo "Building $image..."
    docker build -f "./build/Dockerfile.$image" -t "test-$image" .
    echo "✓ $image build successful"
done

echo "All builds completed successfully!"
