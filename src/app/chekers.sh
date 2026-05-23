cd /home/user1-system12/project-workspace/ai_detector/src/app

python - <<'PY'
from pathlib import Path

p = Path("build_mixed_samples.py")
s = p.read_text()

# 1. Insert build_sample_specs() before the Helpers section.
if "def build_sample_specs(" not in s:
    marker = "\n\n# -----------------------------------------------------------------------------\n# Helpers\n# -----------------------------------------------------------------------------"
    fn = r'''

def build_sample_specs(
    num_samples: Optional[int],
    blocks_per_sample: Optional[int],
    lm_ratio: float,
    include_corners: bool,
) -> List[Dict]:
    """
    Build sample specifications.

    If num_samples and blocks_per_sample are omitted, use the original
    hardcoded SAMPLE_SPECS list.

    Otherwise, generate mixed_sample_001 ... mixed_sample_N.
    """
    if num_samples is None and blocks_per_sample is None:
        return SAMPLE_SPECS

    n = num_samples if num_samples is not None else len(SAMPLE_SPECS)
    k = blocks_per_sample if blocks_per_sample is not None else 6

    if n <= 0:
        raise SystemExit("[ERROR] --num-samples must be > 0")
    if k <= 0:
        raise SystemExit("[ERROR] --blocks-per-sample must be > 0")
    if not (0.0 <= lm_ratio <= 1.0):
        raise SystemExit("[ERROR] --lm-ratio must be between 0.0 and 1.0")

    n_lm = int(round(k * lm_ratio))
    n_lm = max(0, min(k, n_lm))
    n_human = k - n_lm

    specs: List[Dict] = []
    for i in range(1, n + 1):
        specs.append({
            "name": f"mixed_sample_{i:03d}",
            "n_human": n_human,
            "n_lm": n_lm,
        })

    if include_corners and n >= 2:
        specs[0]["n_human"], specs[0]["n_lm"] = k, 0
        specs[1]["n_human"], specs[1]["n_lm"] = 0, k

    return specs
'''
    if marker not in s:
        raise SystemExit("[ERROR] Helpers marker not found")
    s = s.replace(marker, fn + marker)

# 2. Add CLI args.
if "--num-samples" not in s:
    old = '''    ap.add_argument("--seed",       type=int, default=42)
    ap.add_argument("--no-split-filter", action="store_true",
                    help="Draw from all rows in --src-csv, not just test split.")
    return ap.parse_args()
'''
    new = '''    ap.add_argument("--seed",       type=int, default=42)
    ap.add_argument("--num-samples", type=int, default=None,
                    help="Number of mixed .py files to generate. If omitted, use legacy SAMPLE_SPECS.")
    ap.add_argument("--blocks-per-sample", type=int, default=None,
                    help="Number of top-level blocks per generated mixed file.")
    ap.add_argument("--lm-ratio", type=float, default=0.5,
                    help="Fraction of blocks sampled from lm/AGC rows in generated mode.")
    ap.add_argument("--include-corners", action="store_true",
                    help="In generated mode, make sample 001 all-human and sample 002 all-lm.")
    ap.add_argument("--allow-reuse", action="store_true",
                    help="Allow the same source row to appear in multiple mixed samples.")
    ap.add_argument("--no-split-filter", action="store_true",
                    help="Draw from all rows in --src-csv, not just test split.")
    return ap.parse_args()
'''
    if old not in s:
        raise SystemExit("[ERROR] parse_args block not found")
    s = s.replace(old, new)

# 3. Create sample_specs in main().
if "sample_specs = build_sample_specs(" not in s:
    old = '''    args = parse_args()
    rng = random.Random(args.seed)

    if not os.path.exists(args.src_csv):
'''
    new = '''    args = parse_args()
    rng = random.Random(args.seed)
    sample_specs = build_sample_specs(
        args.num_samples,
        args.blocks_per_sample,
        args.lm_ratio,
        args.include_corners,
    )

    if not os.path.exists(args.src_csv):
'''
    if old not in s:
        raise SystemExit("[ERROR] main args/rng block not found")
    s = s.replace(old, new)

# 4. Replace hardcoded SAMPLE_SPECS usage.
s = s.replace(
    'n_human_total = sum(s["n_human"] for s in SAMPLE_SPECS)',
    'n_human_total = sum(s["n_human"] for s in sample_specs)'
)
s = s.replace(
    'n_lm_total    = sum(s["n_lm"]    for s in SAMPLE_SPECS)',
    'n_lm_total    = sum(s["n_lm"]    for s in sample_specs)'
)
s = s.replace(
    'for spec in SAMPLE_SPECS:',
    'for spec in sample_specs:'
)

# 5. Add allow-reuse behavior.
old = '''        h_rows, l_rows = sample_rows(df, spec["n_human"], spec["n_lm"], used, rng)
        used.update(r["idx"] for r in h_rows)
        used.update(r["idx"] for r in l_rows)
'''
new = '''        used_for_sampling = set() if args.allow_reuse else used
        h_rows, l_rows = sample_rows(df, spec["n_human"], spec["n_lm"], used_for_sampling, rng)

        if not args.allow_reuse:
            used.update(r["idx"] for r in h_rows)
            used.update(r["idx"] for r in l_rows)
'''
if old in s:
    s = s.replace(old, new)
elif "used_for_sampling = set() if args.allow_reuse else used" not in s:
    raise SystemExit("[ERROR] sampling block not found")

p.write_text(s)
print("patched:", p)
PY