cd ~/project-workspace/ai_detector

python - <<'PY'
from pathlib import Path
import re

path = Path("src/run0a-generate-llm-api-more.sh")
text = path.read_text()

# Remove log_ts function.
text = re.sub(
    r'\nlog_ts\(\) \{\n  awk .*?\| tee -a "\$\{LOG_FILE\}"\n\}\n',
    '\n',
    text,
    flags=re.DOTALL,
)

# First config block should create/overwrite log.
text = text.replace("} | log_ts", '} | tee "${LOG_FILE}"', 1)

# Main command should append.
text = text.replace("2>&1 | log_ts", '2>&1 | tee -a "${LOG_FILE}"')

# Final block should append.
text = text.replace("} | log_ts", '} | tee -a "${LOG_FILE}"')

path.write_text(text)
print("[OK] Simplified wrapper logging.")
PY