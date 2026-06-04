cd ~/project-workspace/ai_detector

python - <<'PY'
from pathlib import Path
import sys

SRC_DIR = Path("src").resolve()
sys.path.insert(0, str(SRC_DIR))

from code_generation import find_validsyntax_mgc as validsyntax

print("Imported:", validsyntax.__file__)
print("Has process_obj:", hasattr(validsyntax, "process_obj"))
print("Has syntax_check:", hasattr(validsyntax, "syntax_check"))
print("Has has_exactly_one_top_level_block:", hasattr(validsyntax, "has_exactly_one_top_level_block"))
print("Has has_non_empty_body_after_docstring:", hasattr(validsyntax, "has_non_empty_body_after_docstring"))
print("Has code_has_required_structure:", hasattr(validsyntax, "code_has_required_structure"))

code_docstring_only = '''
def f():
    """only docstring"""
'''

code_real_body = '''
def f():
    """docstring"""
    return 1
'''

print("docstring only:", validsyntax.syntax_check(code_docstring_only).ok, validsyntax.code_has_required_structure(code_docstring_only))
print("real body:", validsyntax.syntax_check(code_real_body).ok, validsyntax.code_has_required_structure(code_real_body))
PY