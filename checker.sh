cd ~/project-workspace/ai_detector

python - <<'PY'
from pathlib import Path

path = Path("src/run0a-generate-llm-api-more.sh")
text = path.read_text()

old = "python src/code-generate-llm/generate-more.py \\"
new = "PYTHONUNBUFFERED=1 python -u src/code-generate-llm/generate-more.py \\"

if old not in text:
    print("[WARN] Pattern not found. Please edit manually.")
else:
    text = text.replace(old, new, 1)
    path.write_text(text)
    print("[OK] Patched wrapper for unbuffered Python output.")
PY