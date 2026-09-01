# recon-benchmark

PET reconstruction (OSEM via STIR's `OSMAPOSL`) with basic benchmarking.

## Python

```bash
python main.py \
  --add-sino add.hs \
  --mult-sino mult.hs \
  --prompts-sino prompts.hs \
  --output-dir ./output \
  [--zoom 0.5] [--iterations 4] [--subsets 5] [--threads N] [-v]
```

Writes to `--output-dir`:
- `pet_20.hv` — reconstructed image
- `recon.log` — full log
- `benchmark.json` — wall-clock time, CPU time, peak RAM, and per-subiteration timings, e.g.:

```json
{
  "total_time_sec": 84.2,
  "cpu_time_sec": 81.9,
  "cpu_user_sec": 79.4,
  "cpu_sys_sec": 2.5,
  "omp_num_threads": "4",
  "peak_rss_mb": 2143.5,
  "returncode": 0,
  "subiteration_cumulative_sec": [4.1, 8.3, "...", 84.2],
  "subiteration_delta_sec": [4.1, 4.2, "...", 4.0]
}
```

`total_time_sec` is wall-clock (`time.monotonic`); `cpu_time_sec` is the recon subprocess's user + system CPU time (`getrusage(RUSAGE_CHILDREN)`). On a multi-threaded run CPU time can exceed wall time. `omp_num_threads` is the value `--threads` set for the subprocess, or `null` if inherited from the environment.

## Docker

```bash
docker run --rm \
  -v /path/to/input:/data/input \
  -v /path/to/output:/data/output \
  [-e ZOOM=0.5] [-e ITERATIONS=4] [-e SUBSETS=5] [-e THREADS=4] [-e VERBOSE=0] \
  ghcr.io/christianhinge/recon
```

Expects `/data/input/add.[hs,s]`, `/data/input/mult.[hs,s]`, `/data/input/prompts.[hs,s]`; writes results to `/data/output`. All env vars are optional (defaults: `ZOOM=0.5`, `ITERATIONS=4`, `SUBSETS=5`, `THREADS` and `VERBOSE` unset).