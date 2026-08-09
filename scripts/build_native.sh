#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -Dpybind11_DIR="$(uv run python -m pybind11 --cmakedir)"
cmake --build build -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu)"
