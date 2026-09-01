import logging
import re
import subprocess
import os
import argparse
import json
import time
import resource

from tqdm import tqdm

log = logging.getLogger('recon')

def run_reconstruction(recon_template, add_sino_path, mult_sino_path, prompts_sino_path, out_image_path,
                        zoom=0.5, iterations=4, subsets=5, threads=None):
    subiterations = iterations * subsets

    recon_env = os.environ.copy()
    if threads is not None:
        recon_env["OMP_NUM_THREADS"] = str(threads)

    with open(recon_template,"r") as f:
        recon_cmd = f.read().strip()

    recon_cmd = recon_cmd.replace("PROMPTS_SINO", prompts_sino_path)
    recon_cmd = recon_cmd.replace("ADD_SINO", add_sino_path)
    recon_cmd = recon_cmd.replace("MULT_SINO", mult_sino_path)
    recon_cmd = recon_cmd.replace("OUT_FILE_PREFIX", out_image_path)
    recon_cmd = recon_cmd.replace("ZOOM", str(zoom))
    recon_cmd = recon_cmd.replace("NUM_SUBSETS", str(subsets))
    recon_cmd = recon_cmd.replace("NUM_SUBITERATIONS", str(subiterations))

    recon_file = os.path.join(os.path.dirname(out_image_path), 'recon.par')
    with open(recon_file, "w") as f:
        f.write(recon_cmd)

    subiteration_re = re.compile(r'OSEM subiteration #(\d+) completed')

    rusage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    subiteration_times = {}
    with subprocess.Popen(['stdbuf', '-oL', 'OSMAPOSL', recon_file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=recon_env) as proc:
        with tqdm(total=subiterations, desc='OSEM subiteration', unit='subit', leave=False) as pbar:
            for line in proc.stdout:
                line = line.rstrip()
                log.debug(line)
                m = subiteration_re.search(line)
                if m:
                    subiteration_times[int(m.group(1))] = round(time.monotonic() - start, 3)
                    pbar.update(int(m.group(1)) - pbar.n)
        proc.wait()
    total_time = round(time.monotonic() - start, 3)
    rusage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu_user_sec = round(rusage_end.ru_utime - rusage_start.ru_utime, 3)
    cpu_sys_sec = round(rusage_end.ru_stime - rusage_start.ru_stime, 3)
    cpu_time_sec = round(cpu_user_sec + cpu_sys_sec, 3)
    peak_rss_mb = round(rusage_end.ru_maxrss / 1024, 1)  # ru_maxrss is KB on Linux

    cumulative = [subiteration_times[i] for i in sorted(subiteration_times)]
    prev = 0.0
    deltas = []
    for t in cumulative:
        deltas.append(round(t - prev, 3))
        prev = t

    benchmark = {
        "total_time_sec": total_time,
        "cpu_time_sec": cpu_time_sec,
        "cpu_user_sec": cpu_user_sec,
        "cpu_sys_sec": cpu_sys_sec,
        "omp_num_threads": recon_env.get("OMP_NUM_THREADS"),
        "peak_rss_mb": peak_rss_mb,
        "returncode": proc.returncode,
        "subiteration_cumulative_sec": cumulative,
        "subiteration_delta_sec": deltas,
    }
    benchmark_path = os.path.join(os.path.dirname(out_image_path), 'benchmark.json')
    with open(benchmark_path, "w") as f:
        json.dump(benchmark, f, indent=2)

    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, proc.args)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="PET reconstruction pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--add-sino",   required=True, help="Add sino file (must end in .hs)")
    parser.add_argument("--mult-sino",  required=True, help="Mult sino file (must end in .hs)")
    parser.add_argument("--prompts-sino", required=True, help="Prompts sino file (must end in .hs)")
    parser.add_argument("--output-dir",  required=True, help="Output directory; pet.nii.gz and intermediates/ will be written here")
    parser.add_argument("--zoom", type=float, default=0.5,
                         help="Reconstruction zoom factor (default: 0.5)")
    parser.add_argument("--iterations", type=int, default=4,
                         help="Number of OSEM iterations (default: 4)")
    parser.add_argument("--subsets", type=int, default=5,
                         help="Number of OSEM subsets; subiterations = iterations * subsets (default: 5)")
    parser.add_argument("--threads", type=int, default=None,
                         help="Set OMP_NUM_THREADS for the reconstruction subprocess (default: inherit environment)")
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="Show output from STIR subprocess calls")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    log.setLevel(logging.DEBUG)
    log.propagate = False

    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(console)

    file_handler = logging.FileHandler(os.path.join(output_dir, "recon.log"))
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(file_handler)

    recon_template = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon_OSEM_template.par")

    log_path = os.path.join(output_dir, "recon.log")
    try:
        run_reconstruction(
            add_sino_path=args.add_sino,
            mult_sino_path=args.mult_sino,
            prompts_sino_path=args.prompts_sino,
            recon_template=recon_template,
            out_image_path=os.path.join(output_dir, "pet"),
            zoom=args.zoom,
            iterations=args.iterations,
            subsets=args.subsets,
            threads=args.threads,
        )
    except Exception:
        if not args.verbose:
            print(f"\nReconstruction failed. Check {log_path} for details, or rerun with -v/--verbose for more output.", flush=True)
        raise