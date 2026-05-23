cd /home/user1-system12/project-workspace/ai_detector/src/app

cp run1-agc-detector.sh bak/run1-agc-detector.sh.bak_$(date +%Y%m%d_%H%M%S)

python - <<'PY'
from pathlib import Path

p = Path("run1-agc-detector.sh")
s = p.read_text()

# Insert editable detector configuration after cd "${REPO_ROOT}"
old = '''cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
'''
new = '''cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Editable detector configuration
# -----------------------------------------------------------------------------
# Default target for the current app-level mixed-code evaluation.
INPUT_DIR="${INPUT_DIR:-src/app/mixed_samples_50x6}"

# Paper-aligned high-confidence AGC mode:
#   embedding = AST
#   threshold = -1.3439
#
# Set USE_HIGH_CONF_THRESHOLD=0 if you want the classifier default threshold
# instead of the high-confidence threshold.
EMBEDDING="${EMBEDDING:-ast}"
USE_HIGH_CONF_THRESHOLD="${USE_HIGH_CONF_THRESHOLD:-1}"
HIGH_CONF_THRESHOLD="${HIGH_CONF_THRESHOLD:--1.3439}"

if [ "${USE_HIGH_CONF_THRESHOLD}" = "1" ] && [ -z "${THRESHOLD:-}" ]; then
  THRESHOLD="${HIGH_CONF_THRESHOLD}"
fi

OUT_DIR="${OUT_DIR:-${INPUT_DIR}/predictions}"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
'''
if old not in s:
    raise SystemExit("[ERROR] cd/logging block not found")
s = s.replace(old, new)

# Update default input glob.
s = s.replace(
    'DEFAULT_INPUT_GLOB="src/app/mixed_samples/mixed_sample_*.py"',
    'DEFAULT_INPUT_GLOB="${INPUT_DIR}/mixed_sample_*.py"'
)

# Update default find directory.
s = s.replace(
    "done < <(find src/app/mixed_samples -maxdepth 1 -name 'mixed_sample_*.py' -print0 2>/dev/null | sort -z)",
    'done < <(find "${INPUT_DIR}" -maxdepth 1 -name \'mixed_sample_*.py\' -print0 2>/dev/null | sort -z)'
)

# Remove old OUT_DIR default line if still present. It is now set in editable config.
s = s.replace(
    'OUT_DIR="${OUT_DIR:-src/app/mixed_samples/predictions}"\nmkdir -p "${OUT_DIR}"',
    'mkdir -p "${OUT_DIR}"'
)

# Add input dir to banner if not already present.
old = '''echo "   inputs       : ${#INPUTS[@]} file(s)"
echo "   model pickle : ${MODEL_PICKLE:-<default: latest SVM>}"
'''
new = '''echo "   input dir    : ${INPUT_DIR}"
echo "   inputs       : ${#INPUTS[@]} file(s)"
echo "   model pickle : ${MODEL_PICKLE:-<default: latest SVM>}"
'''
if old not in s:
    raise SystemExit("[ERROR] banner block not found")
s = s.replace(old, new)

p.write_text(s)
print("patched:", p)
PY