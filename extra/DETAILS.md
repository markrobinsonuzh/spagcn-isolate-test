# Technical Documentation

## Build Options

### Pre-built Python (Default)

Uses pre-compiled Python from Ubuntu's deadsnakes PPA. Fast builds, excellent coverage (Python 3.6-3.13).

```bash
make docker LEGACY_PYTHON_VERSION=3.8    # Major.minor version
```

**Advantages:**
- Very fast build times (no compilation)
- Proven binaries from trusted source
- Small image size with multi-stage build

### Compile from Source

For precise version control or unavailable versions:

```bash
make docker BUILD_FROM_SOURCE=true LEGACY_PYTHON_VERSION=3.8.18
```

Or use convenience target:

```bash
make docker-from-source LEGACY_PYTHON_VERSION=3.10.13
```

**Advantages:**
- Exact patch version (e.g., 3.8.18 vs 3.8.19)
- Optimized builds (`--enable-optimizations`)
- Multi-stage build keeps final image slim

**Trade-off:** Slower build times (compilation takes 5-15 minutes depending on hardware)

---

## Dependency Management

### Runtime Installation (Default)

Dependencies install when container starts:

```bash
# Edit requirements-module.txt
# Run container
make run-docker
# UV installs packages automatically
```

**Advantages:**
- Change dependencies without rebuilding
- Mount different requirements per project
- Fast with UV cache mounting

**How it works:**
1. Entrypoint checks for `/mnt/requirements-module.txt` (your mounted file)
2. Falls back to `/app/requirements-module.txt` (baked into image at build time)
3. UV installs to system Python with `--system` flag
4. Cache at `/app/.uv-cache` speeds up repeated installs

### Build-Time Installation

For environments without cache mounting (some HPC clusters):

Uncomment in Dockerfile:
```dockerfile
# Install module dependencies at build time (optional, for faster startup)
RUN uv pip install --python python-legacy --system -r /app/requirements-module.txt
```

Then rebuild:
```bash
make docker
```

**Advantages:**
- Faster container startup (no install wait)
- No cache mount needed

**Trade-offs:**
- Must rebuild to change dependencies
- Larger image size
- Less flexible

---

## Multi-Architecture Builds

### Local Multi-Arch

Builds for both AMD64 and ARM64:

```bash
make docker-multiarch-local
```

Creates a multi-platform image locally (slower, for testing).

### Push to Registry

For production multi-arch images:

```bash
make docker-multiarch REGISTRY=docker.io/yourusername
```

Builds and pushes to registry with manifest for both architectures.

---

## Directory Structure

```
/app/                          # Application directory
  requirements-module.txt      # Baked-in requirements (build time)
  .uv-cache/                   # UV package cache
  entrypoint.sh                # Container entrypoint

/mnt/                          # Mounted host directory (runtime)
  run_entrypoint.py            # Your module script
  requirements-module.txt      # Your requirements (overrides /app version)
  
/usr/local/bin/
  python                       # Python 3.12 (main)
  python-legacy                # Your chosen Python version
  uv                           # UV package manager
```

---

## Environment Variables

- `UV_CACHE_DIR=/app/.uv-cache` - UV cache location
- `PATH=/usr/local/bin:...` - Python 3.12 is default

---

## Makefile Targets

| Target | Description |
|--------|-------------|
| `docker` | Build for native architecture |
| `docker-from-source` | Build with Python compiled from source |
| `docker-multiarch` | Build multi-arch and push to registry |
| `docker-multiarch-local` | Build multi-arch locally (testing) |
| `sif` | Convert Docker image to Apptainer SIF |
| `run-docker` | Run with Docker (mounts current directory) |
| `run-apptainer` | Run with Apptainer (mounts current directory) |

---

## Cache Optimization

### Docker

Cache is automatically mounted by `make run-docker` to `$HOME/.cache/uv`.

Manual:
```bash
docker run --rm \
  -v $HOME/.cache/uv:/app/.uv-cache \
  -v $(pwd):/mnt \
  -w /mnt \
  py-multi
```

### Apptainer

```bash
apptainer run \
  --bind $HOME/.cache/uv:/app/.uv-cache \
  --bind $(pwd):/mnt \
  --pwd /mnt \
  py-multi.sif
```

Or set in Makefile:
```make
UV_CACHE_DIR ?= /scratch/uv-cache  # HPC scratch space
```

---

## Troubleshooting

### "Package not found" errors

Check your `requirements-module.txt` syntax. UV uses pip-compatible format.

### Slow repeated installs

Ensure UV cache is mounted. Check:
```bash
docker run --rm py-multi ls -la /app/.uv-cache
```

Should show cached packages, not be empty.

### "Permission denied" on entrypoint

Make `entrypoint.sh` executable:
```bash
chmod +x entrypoint.sh
```

### Platform mismatch warnings

If building on ARM (M1/M2 Mac) for AMD64:
```bash
# Remove --platform flag from Makefile for native builds
# Or use docker-multiarch for both platforms
```

### Python version not available

Pre-built options limited to deadsnakes PPA. For other versions, use:
```bash
make docker BUILD_FROM_SOURCE=true LEGACY_PYTHON_VERSION=3.x.y
```

---

## Advanced: Custom Entrypoint

Replace `entrypoint.sh` or override at runtime:

```bash
docker run --rm \
  --entrypoint /bin/bash \
  py-multi \
  -c "python-legacy --version"
```

---

## Integration with Omnibenchmark

The container is designed to work with omnibenchmark's execution model:

1. Omnibenchmark calls container via Apptainer
2. Container mounts project directory
3. Entrypoint installs dependencies via UV
4. Module script executes with legacy Python
5. Output written to mounted directory
