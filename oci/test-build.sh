#!/bin/bash
set -e

echo "Testing Docker builds locally via bake..."
docker buildx bake all --set '*.platform=linux/amd64' --load
echo "All builds completed successfully!"
