#!/bin/bash
# Optimized Docker build script using uv and BuildKit

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
IMAGE_NAME="verba"
TAG="latest"
TARGET="production"
CACHE_FROM=""
CACHE_TO=""
PUSH=false
PLATFORM="linux/amd64"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Build Docker image with uv optimizations

OPTIONS:
    -n, --name NAME         Image name (default: verba)
    -t, --tag TAG          Image tag (default: latest)
    --target TARGET        Build target (default: production)
    --cache-from CACHE     Cache source (e.g., type=registry,ref=image:cache)
    --cache-to CACHE       Cache destination (e.g., type=registry,ref=image:cache)
    --platform PLATFORM   Target platform (default: linux/amd64)
    --push                 Push image after build
    -h, --help             Show this help message

EXAMPLES:
    # Basic build
    $0

    # Build with registry cache
    $0 --cache-from type=registry,ref=myregistry/verba:cache \\
       --cache-to type=registry,ref=myregistry/verba:cache

    # Build for multiple platforms
    $0 --platform linux/amd64,linux/arm64

    # Build and push
    $0 --push --tag v2.0.0
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        --cache-from)
            CACHE_FROM="$2"
            shift 2
            ;;
        --cache-to)
            CACHE_TO="$2"
            shift 2
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Ensure we're in the project root
if [[ ! -f "pyproject.toml" ]]; then
    print_error "pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Enable BuildKit
export DOCKER_BUILDKIT=1

# Build the image
print_status "Building Docker image: ${IMAGE_NAME}:${TAG}"
print_status "Target: ${TARGET}"
print_status "Platform: ${PLATFORM}"

# Construct build command
BUILD_CMD="docker buildx build"
BUILD_CMD+=" --target ${TARGET}"
BUILD_CMD+=" --platform ${PLATFORM}"
BUILD_CMD+=" --tag ${IMAGE_NAME}:${TAG}"

# Add cache options if provided
if [[ -n "${CACHE_FROM}" ]]; then
    BUILD_CMD+=" --cache-from ${CACHE_FROM}"
    print_status "Using cache from: ${CACHE_FROM}"
fi

if [[ -n "${CACHE_TO}" ]]; then
    BUILD_CMD+=" --cache-to ${CACHE_TO}"
    print_status "Saving cache to: ${CACHE_TO}"
fi

# Add push option if requested
if [[ "${PUSH}" == "true" ]]; then
    BUILD_CMD+=" --push"
    print_status "Will push image after build"
else
    BUILD_CMD+=" --load"
fi

# Add build context
BUILD_CMD+=" ."

# Execute build
print_status "Executing: ${BUILD_CMD}"
eval "${BUILD_CMD}"

if [[ $? -eq 0 ]]; then
    print_status "Build completed successfully!"
    
    # Show image info if not pushing
    if [[ "${PUSH}" != "true" ]]; then
        print_status "Image details:"
        docker images "${IMAGE_NAME}:${TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    fi
else
    print_error "Build failed!"
    exit 1
fi