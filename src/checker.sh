python - <<'PY'
from pathlib import Path

p = Path("code-generation/find_validsyntax_mgc.py")
s = p.read_text()

start = s.index("def clean_output(output: str) -> str:")
end = s.index("\ndef compose_code", start)

new_block = r'''def _indent_width(line: str) -> int:
    """Count leading spaces. Tabs are expanded first for safety."""
    line = line.expandtabs(4)
    return len(line) - len(line.lstrip(" "))


def _expected_body_indent(prompt: str) -> int:
    """
    Infer the indentation level expected for the generated continuation.

    Most prompts are:
        def foo(...):
            """docstring"""
    so the generated continuation should align with the docstring block.
    """
    lines = normalize_newlines(prompt).splitlines()
    nonempty = [line for line in lines if line.strip()]

    if not nonempty:
        return 4

    last = nonempty[-1]
    last_indent = _indent_width(last)

    # If prompt ends immediately after a function/class signature, body starts one level deeper.
    if last.rstrip().endswith(":"):
        return last_indent + 4

    # If prompt ends after a docstring/comment inside the function, continue at same block level.
    return last_indent


def _strip_repeated_signature_tail(output: str) -> str:
    """
    Some instruct-model outputs repeat the tail of the function signature before
    writing the body, e.g.

        available_routes: List['RouteState'],
        ...
    ) -> Optional[NettingChannelState]:
        for route in available_routes:

    This removes only that initial repeated-signature block.
    """
    lines = normalize_newlines(output).splitlines()

    first = None
    for i, line in enumerate(lines):
        if line.strip():
            first = i
            break

    if first is None:
        return "\n"

    first_text = lines[first].strip()

    signature_like = (
        first_text.endswith(",")
        or first_text.startswith(")")
        or "->" in first_text
    )

    if not signature_like:
        return output

    limit = min(len(lines), first + 30)
    for j in range(first, limit):
        text = lines[j].strip()
        if text.endswith(":") and (text.startswith(")") or "->" in text or j > first):
            rest = "\n".join(lines[j + 1:]).lstrip("\n")
            return "\n" + rest if rest else "\n"

    return output


def _normalize_continuation_indent(prompt: str, output: str) -> str:
    """
    Shift generated continuation right when it is shallower than the prompt body.

    This fixes common StarCoder2-Instruct cases like:

        def run(self, messages):
                """docstring"""
            contents = {}

    where the model generated 4-space body indentation but the prompt's
    docstring block uses 8 spaces.
    """
    expected = _expected_body_indent(prompt)
    lines = normalize_newlines(output).splitlines()

    nonempty_indices = [i for i, line in enumerate(lines) if line.strip()]
    if not nonempty_indices:
        return "\n"

    current_min = min(_indent_width(lines[i]) for i in nonempty_indices)

    if expected > current_min:
        delta = expected - current_min
        lines = [
            (" " * delta + line if line.strip() else line)
            for line in lines
        ]

    result = "\n".join(lines).rstrip()

    if result and not result.startswith("\n"):
        result = "\n" + result

    return result + "\n"


def clean_output(prompt: str, output: str) -> str:
    """
    Conservatively trim over-generation and normalize indentation after the
    intended function body.

    This does not rewrite program logic. It only:
      1. removes obvious over-generation tails;
      2. removes repeated signature tails;
      3. shifts continuation indentation to match the prompt body.
    """
    s = normalize_newlines(output)

    # Hard stop: model continues into repository/file context.
    s = s.split("<file_sep>", 1)[0]

    # Hard stop: markdown/prose tail.
    s = s.split("```", 1)[0]

    # Cut when a next top-level definition/class or dangling definition appears.
    patterns = [
        r"\n\n(?=def\s+\w+\s*\()",
        r"\n\n(?=async\s+def\s+\w+\s*\()",
        r"\n\n(?=class\s+\w+)",
        r"\n\s{4}def\s*$",
        r"\n\s{4}async\s+def\s*$",
        r"\n\s{4}class\s*$",
        r"\n\s*def\s*$",
        r"\n\s*async\s+def\s*$",
        r"\n\s*class\s*$",
    ]

    cut = len(s)
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            cut = min(cut, m.start())

    s = s[:cut].rstrip() + "\n"
    s = _strip_repeated_signature_tail(s)
    s = _normalize_continuation_indent(prompt, s)

    return s
'''

s = s[:start] + new_block + s[end:]

s = s.replace(
    "clean = clean_output(raw_output)",
    "clean = clean_output(prompt, raw_output)"
)

p.write_text(s)
print("patched", p)
PY