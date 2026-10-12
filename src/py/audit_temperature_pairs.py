#!/usr/bin/env python3
"""Read-only, matched CodeLlama-7B generation-temperature QC audit.

Inputs:
  Original 4,500 HWC/T=0.2 AGC pairs (idx, code, label).
  Original pair-level complexity-stratified split manifest.
  Original validator implementation (find_validsyntax_mgc.py).
  run-x-02 pilot directory: experiment_config.json, pilot_prepared.jsonl,
      pilot_generation.jsonl, pilot_selection.csv, pilot_summary.json.

Outputs (only in a NEW run-x-03 output directory):
  original_t02_qc.csv                One row per original 4,500 pairs.
  pilot_temperature_comparison.csv  One row per paired pilot procedure.
  common_valid_pilot_pairs.csv      Pair IDs valid under both conditions.
  tokenizer_audit.json              Tokenization, truncation, EOS token inspection.
  audit_summary.json                Counts, hashes, integrity and limitations.
  audit_findings.txt                Review-ready report.

This is NOT a new temperature experiment or classifier inference. The original
T=0.2 raw generations are generally unavailable in the 4,500-pair CSV;
consequently original code is checked AS STORED, not re-salvaged from raw text.
T=0.0 generated code is also checked AS STORED, using the SAME direct validator.
The separate T=0.0 raw/salvaged metadata is reported but not relabeled.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def args_parse():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument('--original-pairs', required=True, type=Path)
    p.add_argument('--split-manifest', required=True, type=Path)
    p.add_argument('--validator-script', required=True, type=Path)
    p.add_argument('--pilot-dir', required=True, type=Path)
    p.add_argument('--output-dir', required=True, type=Path)
    p.add_argument('--original-count', type=int, default=4500)
    p.add_argument('--pilot-count', type=int, default=100)
    p.add_argument('--prompt-max-tokens', type=int, default=128)
    p.add_argument('--tokenizer-mode', choices=['auto', 'required', 'skip'], default='auto')
    p.add_argument('--tokenizer-name', default='codellama/CodeLlama-7b-hf')
    p.add_argument('--eos-ids', default='2,822,29871')
    return p.parse_args()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for piece in iter(lambda: f.read(1 << 20), b''):
            h.update(piece)
    return h.hexdigest()


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def load_csv(path: Path):
    csv.field_size_limit(sys.maxsize)
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def load_json(path: Path):
    with path.open(encoding='utf-8') as f:
        return json.load(f)


def load_jsonl(path: Path):
    out = []
    with path.open(encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f'{path.name}:{line_no} invalid JSON: {exc}') from exc
    return out


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def write_csv(path, data, columns):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader()
        w.writerows(data)


def import_validator(path):
    name = 'run_x_03_original_validator'
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Could not import validator: {path}')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    for func in ('syntax_check', 'code_has_required_structure', 'compose_code'):
        if not callable(getattr(module, func, None)):
            raise RuntimeError(f'Original validator lacks {func}')
    return module


def original_pair_map(records, errors):
    groups = defaultdict(dict)
    for row in records:
        idx, label = row.get('idx', ''), row.get('label', '')
        m = re.fullmatch(r'(.+)_(human|lm)', idx)
        if not m or label != m.group(2):
            errors.append(f'Original row has incorrect idx/label: {idx!r}, {label!r}')
            continue
        pid = m.group(1)
        if label in groups[pid]:
            errors.append(f'Duplicate original label for pair: {pid}/{label}')
        groups[pid][label] = row.get('code', '')
    for pid, pair in groups.items():
        if set(pair) != {'human', 'lm'}:
            errors.append(f'Missing member for original pair: {pid}')
    return dict(groups)


def shared_prefix(human: str, machine: str):
    """Recover the original prompt up to the HWC leading docstring end."""
    lines = human.replace('\r\n', '\n').replace('\r', '\n').splitlines(keepends=True)
    text = ''.join(lines)
    tree = ast.parse(text)
    blocks = [x for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if len(tree.body) != 1 or len(blocks) != 1 or not blocks[0].body:
        raise ValueError('Expected exactly one top-level function/class with body')
    x = blocks[0].body[0]
    if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant) and isinstance(x.value.value, str)):
        raise ValueError('No leading docstring')
    end_line = lines[x.end_lineno - 1]
    n_chars = len(end_line.encode('utf-8')[:x.end_col_offset].decode('utf-8'))
    prefix = ''.join(lines[:x.end_lineno - 1]) + end_line[:n_chars]
    if not machine.startswith(prefix) or not text.startswith(prefix):
        raise ValueError('AGC and HWC do not share recovered prompt')
    return prefix


def check_code(validator, code: str):
    synt = validator.syntax_check(code)
    if not synt.ok:
        return False, 'syntax', synt.error
    ok, reason = validator.code_has_required_structure(code)
    if not ok:
        return False, 'structure', reason
    return True, 'valid', ''


def inspect_tokenizer(name: str, mode: str, prompt_max: int, eos_ids: list[int], pilot_records: list[dict], original_prompts: dict):
    result = {'mode': mode, 'model_name': name, 'loaded': False,
              'prompt_cap': prompt_max, 'eos_ids_expected': eos_ids, 'eos_tokens': [],
              'prompt_truncation': None, 'warnings': [], 'availability_reason': ''}
    if mode == 'skip':
        result['availability_reason'] = 'Tokenizer audit intentionally skipped by operator'
        return result
    try:
        from transformers import AutoTokenizer
        tk = AutoTokenizer.from_pretrained(name, local_files_only=True)
        result['loaded'] = True
        result['tokenizer_eos_token_id'] = tk.eos_token_id
        result['tokenizer_truncation_side'] = tk.truncation_side
        result['tokenizer_class'] = type(tk).__name__
        try:
            def_id = tk('def', add_special_tokens=False).input_ids[0]
            try:
                spaced_def_id = tk('def', add_prefix_space=True, add_special_tokens=False).input_ids[0]
            except (TypeError, ValueError):
                spaced_def_id = tk(' def', add_special_tokens=False).input_ids[0]
            result['rederived_ids'] = [tk.eos_token_id, def_id, spaced_def_id]
            if result['rederived_ids'] != eos_ids:
                result['warnings'].append('EOS token IDs differ from pilot/original configuration')
        except Exception as exc:
            result['warnings'].append('Cannot rederive custom EOS IDs: ' + str(exc))
        for idx in eos_ids:
            token = tk.convert_ids_to_tokens(idx)
            decoded = tk.decode([idx], skip_special_tokens=False)
            result['eos_tokens'].append({'id': idx, 'token': token, 'decoded_repr': repr(decoded),
                                         'is_whitespace_only': bool(decoded.isspace())})
            if decoded.isspace() or token in ('▁', 'Ġ'):
                result['warnings'].append(f'Extra EOS token {idx} is a whitespace/word-boundary token: possible premature stop')
        actual = []
        prompt_record_mismatches = []
        for p in pilot_records:
            pid = p['pair_id']
            prompt = original_prompts[pid]
            full = tk(prompt, truncation=False, add_special_tokens=True).input_ids
            used = tk(prompt, truncation=True, max_length=prompt_max, add_special_tokens=True).input_ids
            generated_input_count = p.get('input_tokens_recorded')
            if generated_input_count is not None and int(generated_input_count) != len(used):
                prompt_record_mismatches.append(pid)
            actual.append({'pair_id': pid, 'split': p['split'], 'tokens_full': len(full),
                           'tokens_used': len(used), 'was_truncated': len(full) > prompt_max,
                           'tokens_removed': max(0, len(full) - len(used))})
        result['prompt_truncation'] = {
            'pairs': len(actual), 'truncated': sum(x['was_truncated'] for x in actual),
            'full_token_max': max((x['tokens_full'] for x in actual), default=0),
            'full_token_median': statistics.median((x['tokens_full'] for x in actual)) if actual else 0,
            'truncated_pair_ids': [x['pair_id'] for x in actual if x['was_truncated']],
            'details': actual, 'input_token_count_mismatches': prompt_record_mismatches}
        if prompt_record_mismatches:
            result['warnings'].append(f'{len(prompt_record_mismatches)} recorded input token counts differ from current tokenizer')
    except Exception as exc:
        result['availability_reason'] = f'{type(exc).__name__}: {exc}'
        result['warnings'].append('Tokenizer audit unavailable from local cache')
        if mode == 'required':
            raise RuntimeError('Required tokenizer audit failed: ' + result['availability_reason']) from exc
    return result


def audit(a):
    files = [a.original_pairs, a.split_manifest, a.validator_script]
    pilot_names = ['experiment_config.json', 'pilot_prepared.jsonl', 'pilot_generation.jsonl',
                   'pilot_selection.csv', 'pilot_summary.json']
    files += [a.pilot_dir / name for name in pilot_names]
    for file in files:
        if not file.is_file():
            raise FileNotFoundError(f'Required input file missing: {file}')
    if a.output_dir.exists():
        raise FileExistsError(f'Refusing to overwrite existing audit directory: {a.output_dir}')
    a.output_dir.mkdir(parents=True)
    errors, warnings = [], []
    config = load_json(a.pilot_dir / 'experiment_config.json')
    pilot_summary = load_json(a.pilot_dir / 'pilot_summary.json')
    provenance_checks = {
        'original_csv_sha256': digest_file(a.original_pairs),
        'split_manifest_sha256': digest_file(a.split_manifest),
        'validator_script_sha256': digest_file(a.validator_script),
    }
    for key, actual in provenance_checks.items():
        expected = config.get(key)
        if not expected or expected != actual:
            errors.append(f'Input provenance mismatch: {key}: expected={expected} actual={actual}')
    if config.get('model') != 'codellama/CodeLlama-7b-hf' or config.get('do_sample') is not False or config.get('temperature') != 0.0 or config.get('top_p') is not None:
        errors.append('Pilot generation decoding/model settings do not match expected T=0.0 greedy protocol')
    if config.get('prompt_max_tokens') != a.prompt_max_tokens:
        errors.append('Prompt token cap differs from pilot configuration')
    if pilot_summary.get('status') != 'PASS' or pilot_summary.get('generated') != a.pilot_count:
        errors.append('Pilot summary does not record a complete passing pilot')
    original_rows = load_csv(a.original_pairs)
    originals = original_pair_map(original_rows, errors)
    manifest = load_csv(a.split_manifest)
    by_manifest = {x['pair_id']: x for x in manifest}
    if len(original_rows) != 2*a.original_count or len(originals) != a.original_count:
        errors.append(f'Original size mismatch: {len(original_rows)} rows and {len(originals)} pairs')
    if len(by_manifest) != a.original_count or len(manifest) != a.original_count or set(originals) != set(by_manifest):
        errors.append('Split manifest pair identity/count mismatch')
    validator = import_validator(a.validator_script)

    print(f'[INFO] Auditing original T=0.2 pairs: {len(originals)}', flush=True)
    original_qc, prompts = [], {}
    for pid in sorted(originals):
        codes = originals[pid]
        if set(codes) != {'human', 'lm'}:
            continue
        old_valid, old_reason, old_detail = check_code(validator, codes['lm'])
        human_valid, human_reason, human_detail = check_code(validator, codes['human'])
        prompt = ''
        prompt_error = ''
        try:
            prompt = shared_prefix(codes['human'], codes['lm'])
            prompts[pid] = prompt
        except Exception as exc:
            prompt_error = str(exc)
        old_hash = digest_text(codes['lm'])
        original_qc.append({'pair_id': pid, 'split': by_manifest.get(pid, {}).get('split', ''),
                            'complexity_block': by_manifest.get(pid, {}).get('complexity_block', ''),
                            't02_agc_valid_direct': old_valid, 't02_agc_reason': old_reason,
                            't02_agc_detail': old_detail, 't02_agc_sha256': old_hash,
                            'hwc_valid_direct': human_valid, 'hwc_reason': human_reason,
                            'hwc_detail': human_detail, 'hwc_sha256': digest_text(codes['human']),
                            'prompt_recoverable': bool(prompt), 'prompt_sha256': digest_text(prompt) if prompt else '',
                            'prompt_error': prompt_error})
    original_qc_cols = list(original_qc[0]) if original_qc else []
    write_csv(a.output_dir / 'original_t02_qc.csv', original_qc, original_qc_cols)
    print(f'[INFO] T=0.2 direct-valid={sum(x["t02_agc_valid_direct"] for x in original_qc)}/{len(original_qc)}', flush=True)

    selected = load_csv(a.pilot_dir / 'pilot_selection.csv')
    prepared = load_jsonl(a.pilot_dir / 'pilot_prepared.jsonl')
    generated = load_jsonl(a.pilot_dir / 'pilot_generation.jsonl')
    if digest_text(canonical_json(prepared)) != config.get('selected_pairs_sha256'):
        errors.append('Pilot selected-pairs SHA-256 differs from experiment_config')
    if digest_text(canonical_json(config)) != pilot_summary.get('config_sha256'):
        errors.append('Pilot configuration SHA-256 differs from pilot_summary')
    for selection_row in selected:
        pid = selection_row['pair_id']
        prep = next((x for x in prepared if x['pair_id'] == pid), None)
        if prep is None:
            continue
        for key in ('pair_id', 'prompt_sha256', 'human_sha256', 'original_agc_sha256', 'split'):
            if str(selection_row.get(key)) != str(prep.get(key)):
                errors.append(f'Pilot selection/prepared {key} mismatch for {pid}')
        if str(selection_row.get('complexity_block')) != str(prep.get('complexity_block')):
            errors.append(f'Pilot selection/prepared complexity block mismatch for {pid}')
    for name, rec in [('selected', selected), ('prepared', prepared), ('generated', generated)]:
        ids = [x['pair_id'] for x in rec]
        if len(ids) != a.pilot_count or len(set(ids)) != a.pilot_count:
            errors.append(f'{name} pilot count or unique ID mismatch: n={len(ids)}, unique={len(set(ids))}')
    selected_ids = {x['pair_id'] for x in selected}
    if selected_ids != {x['pair_id'] for x in prepared} or selected_ids != {x['pair_id'] for x in generated}:
        errors.append('Pilot selected/prepared/generated pair identities differ')
    prepared_by_id = {x['pair_id']: x for x in prepared}
    generated_by_id = {x['pair_id']: x for x in generated}
    original_by_id = {x['pair_id']: x for x in original_qc}
    comparisons, common = [], []
    if pilot_summary.get('valid') != sum(x.get('status') == 'VALID' for x in generated):
        errors.append('Pilot summary valid count differs from generator records')
    for pid in sorted(selected_ids):
        if pid not in originals or pid not in prepared_by_id or pid not in generated_by_id or pid not in original_by_id:
            errors.append(f'Incomplete reference data for selected pair: {pid}')
            continue
        original, prep, gen, old_check = originals[pid], prepared_by_id[pid], generated_by_id[pid], original_by_id[pid]
        old_prompt = prompts.get(pid, '')
        provenance_ok = (old_prompt == prep['prompt'] and
                         digest_text(old_prompt) == prep['prompt_sha256'] == gen['prompt_sha256'] and
                         original['human'] == prep['human_code'] and
                         digest_text(original['human']) == prep['human_sha256'] and
                         digest_text(original['lm']) == prep['original_agc_sha256'] and
                         (gen['split'] == prep['split'] == by_manifest.get(pid, {}).get('split')) and
                         str(gen['complexity_block']) == str(prep['complexity_block']) == str(by_manifest.get(pid, {}).get('complexity_block')) and
                         digest_text(gen['new_agc_code']) == gen['new_agc_sha256'])
        if not provenance_ok:
            errors.append(f'Pilot pair provenance or hash mismatch: {pid}')
        new_valid, new_reason, new_detail = check_code(validator, gen['new_agc_code'])
        old_valid = old_check['t02_agc_valid_direct']
        if new_valid != (gen.get('status') == 'VALID'):
            errors.append(f'T=0.0 direct validator result differs from pilot status for {pid}')
        if gen.get('model') != config['model'] or gen.get('temperature') != 0.0 or gen.get('do_sample') is not False or gen.get('top_p') is not None:
            errors.append(f'Generation record configuration differs from pilot config: {pid}')
        same = digest_text(original['lm']) == digest_text(gen['new_agc_code'])
        if old_valid and new_valid:
            common.append({'pair_id': pid, 'split': prep['split'], 'complexity_block': prep['complexity_block'],
                           'identical_t02_t00_agc': same, 'prompt_sha256': gen['prompt_sha256']})
        comparisons.append({
            'pair_id': pid, 'split': prep['split'], 'complexity_block': prep['complexity_block'],
            't02_direct_valid': old_valid, 't02_reason': old_check['t02_agc_reason'],
            't00_direct_valid': new_valid, 't00_reason': new_reason, 't00_detail': new_detail,
            't00_pilot_status': gen['status'], 't00_pipeline_status': gen['original_pipeline_status'],
            't00_raw_valid': gen['raw_mgc_ok'], 't00_clean_valid': gen['clean_mgc_ok'],
            'identical_t02_t00_agc': same, 'common_valid': old_valid and new_valid,
            'provenance_ok': provenance_ok, 't02_sha256': old_check['t02_agc_sha256'],
            't00_sha256': gen['new_agc_sha256'], 'generated_tokens': gen['generated_tokens'],
            'input_tokens_recorded': gen['input_tokens'],
        })
    # Validate derived run-x-02 products against generation checkpoint, without
    # assuming the old or new syntax validator accepted every generated code.
    derived_qc = a.pilot_dir / 'pilot_qc.csv'
    derived_valid = a.pilot_dir / 'pilot_pairs_valid.csv'
    if not derived_qc.is_file() or not derived_valid.is_file():
        errors.append('Missing run-x-02 derived QC or valid-pair CSV')
    else:
        qc_rows = load_csv(derived_qc)
        valid_rows = load_csv(derived_valid)
        if len(qc_rows) != len(generated):
            errors.append('Pilot QC CSV row count differs from generation checkpoint')
        qc_by_id = {x['pair_id']: x for x in qc_rows}
        for rec in generated:
            if qc_by_id.get(rec['pair_id'], {}).get('status') != rec.get('status'):
                errors.append('Pilot QC CSV status mismatch for ' + rec['pair_id'])
        expected_valid = {x['pair_id'] for x in generated if x.get('status') == 'VALID'}
        valid_groups = original_pair_map(valid_rows, errors)
        if set(valid_groups) != expected_valid or len(valid_rows) != 2*len(expected_valid):
            errors.append('Valid-pair CSV does not match accepted generation checkpoint IDs')
        for pid in set(valid_groups) & expected_valid:
            if valid_groups[pid].get('human') != originals.get(pid, {}).get('human') or valid_groups[pid].get('lm') != generated_by_id[pid].get('new_agc_code'):
                errors.append(f'Valid-pair CSV content differs from checkpoint for {pid}')

    compare_cols = list(comparisons[0]) if comparisons else []
    write_csv(a.output_dir / 'pilot_temperature_comparison.csv', comparisons, compare_cols)
    write_csv(a.output_dir / 'common_valid_pilot_pairs.csv', common,
              ['pair_id', 'split', 'complexity_block', 'identical_t02_t00_agc', 'prompt_sha256'])

    eos_ids = [int(x.strip()) for x in a.eos_ids.split(',') if x.strip()]
    tk_report = inspect_tokenizer(a.tokenizer_name, a.tokenizer_mode, a.prompt_max_tokens,
                                  eos_ids, [dict(p, input_tokens_recorded=generated_by_id.get(p['pair_id'], {}).get('input_tokens')) for p in prepared], prompts)
    write_json(a.output_dir / 'tokenizer_audit.json', tk_report)
    warnings.extend(tk_report['warnings'])
    if a.tokenizer_mode == 'skip':
        warnings.append('Tokenizer audit was deliberately skipped')
    n_diff = sum(not x['identical_t02_t00_agc'] for x in comparisons)
    identical_invalid = [x['pair_id'] for x in comparisons if x['identical_t02_t00_agc'] and not x['t00_direct_valid']]
    if identical_invalid:
        warnings.append(f'{len(identical_invalid)} identical T=0.2/T=0.0 codes fail shared direct structural rules')
    old_valid_total = sum(x['t02_agc_valid_direct'] for x in original_qc)
    common_counts = dict(Counter(x['split'] for x in common))
    cross_table = {
        't02_valid_t00_valid': sum(x['t02_direct_valid'] and x['t00_direct_valid'] for x in comparisons),
        't02_valid_t00_invalid': sum(x['t02_direct_valid'] and not x['t00_direct_valid'] for x in comparisons),
        't02_invalid_t00_valid': sum(not x['t02_direct_valid'] and x['t00_direct_valid'] for x in comparisons),
        't02_invalid_t00_invalid': sum(not x['t02_direct_valid'] and not x['t00_direct_valid'] for x in comparisons),
    }
    original_outcomes = dict(Counter((x['t02_agc_reason'] for x in original_qc)))
    new_outcomes = dict(Counter((x['t00_reason'] for x in comparisons)))
    summary = {
        'experiment': 'run-x-03', 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'FAIL' if errors else ('QC_REVIEW' if warnings else 'PASS'),
        'provenance_checks': provenance_checks,
        'pilot_dir': str(a.pilot_dir), 'validator_script': str(a.validator_script),
        'original_pairs_count': len(originals), 'original_t02_direct_valid': old_valid_total,
        'original_t02_direct_invalid': len(original_qc)-old_valid_total,
        'original_hwc_direct_valid': sum(x['hwc_valid_direct'] for x in original_qc),
        'original_prompt_recoverable': len(prompts),
        'original_direct_reason_counts': original_outcomes,
        'pilot_pairs_count': len(comparisons),
        't00_direct_valid': sum(x['t00_direct_valid'] for x in comparisons),
        't00_direct_reason_counts': new_outcomes,
        'identical_t02_t00': len(comparisons) - n_diff, 'different_t02_t00': n_diff,
        'identical_but_invalid_pair_ids': identical_invalid,
        'validity_crosstab': cross_table, 'common_valid_pairs': len(common),
        'common_valid_split_counts': common_counts,
        'common_valid_identical': sum(x['identical_t02_t00_agc'] for x in common),
        'pilot_512_token_count': sum(int(x['generated_tokens']) >= config['max_new_tokens'] for x in comparisons),
        'pilot_1_or_2_token_count': sum(int(x['generated_tokens']) <= 2 for x in comparisons),
        'tokenizer_loaded': tk_report['loaded'],
        'errors': errors, 'warnings': warnings,
        'interpretation': ('Direct validation is applied to already-saved code at both temperatures. '
                           'The original 4,500 rows are a pre-filtered sample, so this does not '
                           'estimate the unconditional T=0.2 generation acceptance rate. '
                           'Only the common-valid subset supports fully matched validity-filtered comparisons.'),
    }
    write_json(a.output_dir / 'audit_summary.json', summary)
    lines = [
        'Experiment: run-x-03 | matched temperature-pair QC',
        f'Status: {summary["status"]}',
        f'Original 4,500: direct-valid T=0.2 AGC {old_valid_total}/{len(original_qc)}',
        f'Original HWC direct-valid: {summary["original_hwc_direct_valid"]}/{len(original_qc)}',
        f'Original prompt recoverable: {len(prompts)}/{len(original_qc)}',
        f'T=0.0 pilot: direct-valid {summary["t00_direct_valid"]}/{len(comparisons)}',
        f'Identical T=0.2/T=0.0 codes: {summary["identical_t02_t00"]}/{len(comparisons)}',
        f'Different T=0.2/T=0.0 codes: {n_diff}/{len(comparisons)}',
        f'Common-valid: {len(common)}/{len(comparisons)}; split: {common_counts}',
        f'Validity cross-table: {cross_table}',
        f'Identical yet invalid: {len(identical_invalid)} IDs: {identical_invalid}',
        f'Tokenizer loaded: {tk_report["loaded"]}',
        f'Prompt cap: {a.prompt_max_tokens}; truncation: {tk_report.get("prompt_truncation", {}).get("truncated") if tk_report.get("prompt_truncation") else "unknown"}',
        f'EOS token details: {tk_report["eos_tokens"]}',
        f'Errors: {len(errors)}; warnings: {len(warnings)}',
        'LIMITATION: Original T=0.2 data were validity-filtered before this audit.',
        'LIMITATION: Pilot 100 pairs are not sufficient for stable detector AUROC inference.',
        'RECOMMENDATION: Review token-end conditions and common-valid selection before full generation.',
    ]
    lines.extend('[ERROR] ' + s for s in errors)
    lines.extend('[WARNING] ' + s for s in warnings)
    (a.output_dir / 'audit_findings.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('\n'.join(lines), flush=True)
    print(f'[INFO] Results saved in: {a.output_dir}', flush=True)
    return 1 if errors else 0


def main():
    a = args_parse()
    for x in ('original_pairs', 'split_manifest', 'validator_script', 'pilot_dir', 'output_dir'):
        setattr(a, x, getattr(a, x).expanduser().resolve())
    if a.original_count <= 0 or a.pilot_count <= 0 or a.prompt_max_tokens <= 0:
        raise ValueError('Counts and prompt cap must be positive')
    return audit(a)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        print(f'[ERROR] {type(exc).__name__}: {exc}', file=sys.stderr, flush=True)
        raise
