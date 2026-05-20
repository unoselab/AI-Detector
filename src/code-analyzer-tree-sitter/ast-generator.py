import os
import argparse
import pandas as pd
from glob import glob
from tree_sitter import Language, Parser

from tree_sitter_ast_cpp    import F as F_cpp,    remove_comments as R_cpp,    replace_function_names as RF_cpp,    rename_variables as RV_cpp
from tree_sitter_ast_java   import F as F_java,   remove_comments as R_java,   replace_method_names   as RF_java,   rename_variables as RV_java
from tree_sitter_ast_python import F as F_python, remove_comments as R_python, replace_function_names as RF_python, rename_variables as RV_python


CPP_LANGUAGE  = Language('build/my-languages.so', 'cpp')
JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
PY_LANGUAGE   = Language('build/my-languages.so', 'python')

cpp_parser    = Parser(); cpp_parser.set_language(CPP_LANGUAGE)
java_parser   = Parser(); java_parser.set_language(JAVA_LANGUAGE)
python_parser = Parser(); python_parser.set_language(PY_LANGUAGE)

providers = {
    "cpp":    {"parser": cpp_parser,    "generator": F_cpp,    "comment_remover": R_cpp,    "function_replacer": RF_cpp,    "variable_replacer": RV_cpp},
    "java":   {"parser": java_parser,   "generator": F_java,   "comment_remover": R_java,   "function_replacer": RF_java,   "variable_replacer": RV_java},
    "python": {"parser": python_parser, "generator": F_python, "comment_remover": R_python, "function_replacer": RF_python, "variable_replacer": RV_python},
}


# ---------- transformations ----------

def change_variable_names(code, lang):
    try:
        tree = providers[lang]['parser'].parse(bytes(code, "utf8"))
        return providers[lang]['variable_replacer'](tree, code)
    except Exception as e:
        print("[ERROR] [CHANGE_VARIABLE_NAMES]:", e); return None

def change_function_names(code, lang):
    try:
        tree = providers[lang]['parser'].parse(bytes(code, "utf8"))
        return providers[lang]['function_replacer'](tree, code)
    except Exception as e:
        print("[ERROR] [CHANGE_FUNCTION_NAMES]:", e); return None

def remove_comments(code, lang):
    try:
        tree = providers[lang]['parser'].parse(bytes(code, "utf8"))
        return providers[lang]['comment_remover'](tree, code)
    except Exception as e:
        print("[ERROR] [REMOVE_COMMENTS]:", e); return None

def generate_ast_sequence(code, lang):
    code = str(code)
    try:
        tree = providers[lang]['parser'].parse(bytes(code, "utf8"))
        AST  = providers[lang]['generator'](tree.root_node, bytes(code, 'utf8'))
        return ' '.join(AST)
    except Exception as e:
        print("[ERROR] [GENERATE AST]:", e); return None


# ---------- modes ----------

MODE_TRANSFORM = {
    "baseline":              None,
    "uniform_variables_name": change_variable_names,
    "uniform_methods_name":   change_function_names,
    "no_comments":            remove_comments,
}

DEFAULT_OUTPUT_DIR = {
    "baseline":              "data_main",
    "uniform_variables_name": "data_ablation_study_code_embedding/uniform_variables_name",
    "uniform_methods_name":   "data_ablation_study_code_embedding/uniform_methods_name",
    "no_comments":            "data_ablation_study_code_embedding/no_comments",
}


def language_inference_from_path(file_path):
    parts = os.path.basename(file_path).split('_')
    return parts[2].lower()


def process_csv_files(input_dir, output_dir, mode):
    os.makedirs(output_dir, exist_ok=True)
    transform = MODE_TRANSFORM[mode]

    for csv_file in glob(input_dir + '/**/*.csv', recursive=True):
        print(f"Processing {csv_file}  [mode={mode}]")

        data = pd.read_csv(csv_file)
        # data['idx'] = data.index
        if 'idx' not in data.columns:
            data['idx'] = data.index
        else:
            data['idx'] = data['idx'].astype(str)
            
        data = data.dropna(subset=['code']).copy()
        data['code'] = data['code'].astype(str)

        language      = language_inference_from_path(csv_file)
        original_size = len(data)

        if transform is None:
            # baseline: AST straight from the original code
            data['ast'] = data['code'].apply(lambda c: generate_ast_sequence(c, language))
            keep_cols   = ['idx', 'code', 'ast', 'label']
        else:
            # ablation: transform the code, then AST the transformed code
            data['new_code'] = data['code'].apply(lambda c: transform(c, language))
            data['ast']      = data['new_code'].apply(lambda c: generate_ast_sequence(c, language))
            keep_cols        = ['idx', 'code', 'new_code', 'ast', 'label']

        data.dropna(subset=['ast'], inplace=True)
        print(f"{csv_file} not parsed: {original_size - len(data)}/{original_size}")

        output_path = csv_file.replace(input_dir, output_dir)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data[keep_cols].to_csv(output_path, index=False)


def parse_args():
    p = argparse.ArgumentParser(
        description="Generate AST sequences from source code CSVs. "
                    "Default mode 'baseline' is for RQ2-D (original code). "
                    "Other modes apply RQ3 ablation transformations."
    )
    p.add_argument("--mode", choices=list(MODE_TRANSFORM.keys()), default="baseline",
                   help="Transformation to apply before AST generation (default: baseline).")
    p.add_argument("--input-dir", default="data_temp1",
                   help="Directory containing input CSVs (default: data_temp1).")
    p.add_argument("--output-dir", default=None,
                   help="Directory for output CSVs. Defaults per mode "
                        "(baseline -> data_main, ablations -> data_ablation_study_code_embedding/<mode>).")
    args = p.parse_args()
    if args.output_dir is None:
        args.output_dir = DEFAULT_OUTPUT_DIR[args.mode]
    return args


if __name__ == "__main__":
    args = parse_args()
    process_csv_files(args.input_dir, args.output_dir, args.mode)