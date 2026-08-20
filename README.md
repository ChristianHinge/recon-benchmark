# recon-benchmark

PET reconstruction (OSEM via STIR's `OSMAPOSL`) with basic benchmarking.

## Python

```bash
python main.py \
  --add-sino add.hs \
  --mult-sino mult.hs \
  --prompts-sino prompts.hs \
  --output-dir ./output \
  [--zoom 0.5] [--iterations 4] [--subsets 5] [-v]
```

Writes to `--output-dir`:
- `pet_20.hv` — reconstructed image
- `recon.log` — full log
- `benchmark.json` — total time, peak RAM, and per-subiteration timings, e.g.:

```json
{
  "total_time_sec": 84.2,
  "peak_rss_mb": 2143.5,
  "returncode": 0,
  "subiteration_cumulative_sec": [4.1, 8.3, "...", 84.2],
  "subiteration_delta_sec": [4.1, 4.2, "...", 4.0]
}
```

## Docker

```bash
docker run --rm \
  -v /path/to/input:/data/input \
  -v /path/to/output:/data/output \
  [-e ZOOM=0.5] [-e ITERATIONS=4] [-e SUBSETS=5] [-e VERBOSE=0] \
  ghcr.io/christianhinge/recon
```

Expects `/data/input/add.hs`, `/data/input/mult.hs`, `/data/input/prompts.hs`; writes results to `/data/output`. All env vars are optional (defaults: `ZOOM=0.5`, `ITERATIONS=4`, `SUBSETS=5`, `VERBOSE` unset).
