# ── Stage 1: Build STIR ──────────────────────────────────────────────────────
FROM ubuntu:24.04 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git cmake build-essential \
    libboost-all-dev libhdf5-dev libfftw3-dev libncurses-dev \
    python3-dev python3-pip \
    swig libinsighttoolkit5-dev nlohmann-json3-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --break-system-packages --no-cache-dir numpy

RUN git clone https://github.com/UCL/STIR \
 && cd STIR

RUN mkdir /build && cd /build \
 && cmake /STIR \
    -DBUILD_SWIG_PYTHON=ON \
    -DSTIR_BUILD_EXECUTABLES=ON \
    -DPython_EXECUTABLE=/usr/bin/python3 \
 && make -j$(nproc) \
 && make install

RUN pip install --break-system-packages --no-cache-dir tqdm

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    libboost-filesystem1.83.0 \
    libboost-program-options1.83.0 \
    libboost-regex1.83.0 \
    libboost-serialization1.83.0 \
    libboost-thread1.83.0 \
    libboost-iostreams1.83.0 \
    libboost-date-time1.83.0 \
    libhdf5-103-1t64 \
    libhdf5-cpp-103-1t64 \
    libfftw3-double3 \
    libinsighttoolkit5.3 \
 && rm -rf /var/lib/apt/lists/*

# Copy STIR install (executables, libs, Python bindings) + pip packages
COPY --from=builder /usr/local /usr/local
RUN ldconfig

WORKDIR /recon
COPY . .

ENV PYTHONPATH="/usr/local/python"
ENV OVERWRITE=""
ENV VERBOSE=""
ENV ZOOM="0.5"
ENV ITERATIONS="4"
ENV SUBSETS="5"

CMD python3 main.py --add-sino /data/input/add.hs --mult-sino /data/input/mult.hs --prompts-sino /data/input/prompts.hs --output-dir /data/output ${ZOOM:+--zoom $ZOOM} ${ITERATIONS:+--iterations $ITERATIONS} ${SUBSETS:+--subsets $SUBSETS} ${VERBOSE:+--verbose}