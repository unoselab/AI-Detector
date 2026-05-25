#!/usr/bin/env bash
set -euo pipefail

cd ~/project-workspace/ai_detector

dest="data_all"
mkdir -p "$dest"

files='
src/app/agc_detector.py
src/app/build_mixed_samples.py
src/app/checker_mixed_samples_grid.java
src/app/checker_mixed_samples.java
src/app/run0-build-mixed-samples.sh
src/app/run0a-checker-mixed-samples.sh
src/app/run0b-build-mixed-samples-grid.sh
src/app/run1-agc-detector.sh
src/run0a-generate-starcoder15b.sh
src/run0b-find-validsyntax-mgc.sh
src/run0d-build-complexity-sweep-pairs.sh
src/run1-ast-generator.sh
src/run2-generate-embeddings.sh
src/run3b-split-fixed-eval-data.sh
src/run4a-train-classifiers-allmodels.sh
src/run5a-threshold-sweep-prec.sh
src/code-generation/build_complexity_sweep_pairs.py
src/code-generation/find_validsyntax_mgc.py
src/code-generation/generate_starcoder15b.py
src/code-analyzer-tree-sitter/ast-generator.py
src/code-analyzer-tree-sitter/tree_sitter_ast_python.py
src/code-analyzer-tree-sitter/type_analyzer.py
src/ml_embeddings/aggregate_threshold_sweeps.py
src/ml_embeddings/generate_embeddings.py
src/ml_embeddings/hyperparameter_tuning.py
src/ml_embeddings/plot_agc_precision_curve.py
src/ml_embeddings/split_fixed_eval.py
src/ml_embeddings/test_embedding.py
src/ml_embeddings/threshold_sweep.py
'

count=0

printf '%s\n' "$files" | sed '/^$/d' | while read -r file; do
    if [ -f "$file" ]; then
        echo "$file"
        cp "$file" "$dest/"
        count=$((count + 1))
    else
        echo "MISSING: $file" >&2
    fi
done

echo "Total files copied: $(find "$dest" -maxdepth 1 -type f | wc -l)"

timestamp=$(date '+%Y%m%d_%H%M%S')

{
    echo "dir structure of this project ~/project-workspace/ai_detector"
    echo
    tree .
} > "data_all/dir_structure_${timestamp}.txt"

echo "Saved directory structure to: data_all/dir_structure_${timestamp}.txt"