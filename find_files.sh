#!/usr/bin/env bash
set -euo pipefail

cd ~/project-workspace/ai_detector

dest="data_all"
mkdir -p "$dest"

files='
run0a-generate-starcoder15b.sh
run0a-generate.sh
run0b-find-validsyntax-mgc.sh
run1-ast-generator.sh
run2-generate-embeddings.sh
run3-split-data.sh
run4-train-classifiers.sh
run4a-train-classifiers-allmodels.sh
run5-threshold-sweep.sh
run5a-threshold-sweep-prec.sh
run6-plot-threshold-curve.sh
run6a-plot-threshold-curve-prec.sh
src/code-generation/find_validsyntax_mgc.py
src/code-generation/generate.py
src/code-generation/generate_starcoder15b.py
src/code-analyzer-tree-sitter/ast-generator.py
src/code-analyzer-tree-sitter/code-feature-extractor.py
src/code-analyzer-tree-sitter/tree-sitter-test.py
src/code-analyzer-tree-sitter/tree_sitter_ast_python.py
src/code-analyzer-tree-sitter/type_analyzer.py
src/ml_embeddings/aggregate_threshold_sweeps.py
src/ml_embeddings/generate_embeddings.py
src/ml_embeddings/hyperparameter_tuning.py
src/ml_embeddings/hyperparameter_tuning_org.py
src/ml_embeddings/plot_agc_precision_curve.py
src/ml_embeddings/plot_threshold_curve.py
src/ml_embeddings/split_data.py
src/ml_embeddings/test_embedding.py
src/ml_embeddings/test_embedding_org.py
src/ml_embeddings/threshold_sweep.py
'

count=0

printf '%s\n' "$files" | sed '/^$/d' | while read -r file; do
    if [ -f "$file" ]; then
        echo "$file"
        cp --parents "$file" "$dest/"
        count=$((count + 1))
    else
        echo "MISSING: $file" >&2
    fi
done

found_count=$(find "$dest" -type f | wc -l)
echo "Total files copied: $found_count"