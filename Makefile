# Default legacy Python version (must be >= 3.8 for uv compatibility)
# For pre-built: use major.minor (e.g., 3.8, 3.9, 3.10, 3.11) - fast, uses deadsnakes PPA
# For source: use full version (e.g., 3.8.18, 3.10.13) - slower, any precise version
LEGACY_PYTHON_VERSION ?= 3.8

# Build from source flag (set to true for precise version control)
# Default: false (uses pre-built from deadsnakes PPA for fast builds)
BUILD_FROM_SOURCE ?= false

# Default cache directory for uv packages
UV_CACHE_DIR ?= $(HOME)/.cache/uv

# Docker registry for multi-arch builds (set to your registry)
REGISTRY ?= docker.io/yourusername

docker:
	docker buildx build --no-cache \
		--load \
		--build-arg LEGACY_PYTHON_VERSION=$(LEGACY_PYTHON_VERSION) \
		--build-arg BUILD_FROM_SOURCE=$(BUILD_FROM_SOURCE) \
		-t py-multi .

docker-from-source:
	$(MAKE) docker BUILD_FROM_SOURCE=true LEGACY_PYTHON_VERSION=$(LEGACY_PYTHON_VERSION)

# Multi-arch build (requires pushing to registry)
docker-multiarch:
	docker buildx build --no-cache \
		--platform linux/amd64,linux/arm64 \
		--build-arg LEGACY_PYTHON_VERSION=$(LEGACY_PYTHON_VERSION) \
		--build-arg BUILD_FROM_SOURCE=$(BUILD_FROM_SOURCE) \
		--push \
		-t $(REGISTRY)/py-multi:latest .

# Multi-arch build for local testing (creates manifest, slower)
docker-multiarch-local:
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--build-arg LEGACY_PYTHON_VERSION=$(LEGACY_PYTHON_VERSION) \
		--build-arg BUILD_FROM_SOURCE=$(BUILD_FROM_SOURCE) \
		-t py-multi .

docker-with-cache:
	docker buildx build \
		--load \
		--build-arg LEGACY_PYTHON_VERSION=$(LEGACY_PYTHON_VERSION) \
		--build-arg BUILD_FROM_SOURCE=$(BUILD_FROM_SOURCE) \
		--cache-from type=registry,ref=py-multi:buildcache \
		--cache-to type=registry,ref=py-multi:buildcache \
		-t py-multi .

sif:
	apptainer build py-multi.sif docker-daemon://py-multi:latest

run-docker:
	docker run --rm \
		-v $(UV_CACHE_DIR):/app/.uv-cache \
		-v $(PWD):/mnt \
		-w /mnt \
		py-multi

run-apptainer:
	apptainer run \
		--bind $(UV_CACHE_DIR):/app/.uv-cache \
		py-multi.sif
