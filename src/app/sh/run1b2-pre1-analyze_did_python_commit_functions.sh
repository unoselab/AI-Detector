python -m py_compile \
  src/app/py/analyze_did_python_commit_functions.py

python src/app/py/analyze_did_python_commit_functions.py \
  --dataset-source all \
  --function-event-manifest \
    ../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a-py312/strict/commit_function_detection_manifest.csv \
  --function-source-root \
    ../ai_code_complexity_study_python/ai-code-complexity-study/repo_python/run-py-5a-py312/strict/commit_function_sources \
  --event-id-file \
    ../ai_code_complexity_study_python/python_commit_function_detect/input_compatibility/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312/detector_input_runtime_ast_failures.csv \
  --event-id-file \
    ../ai_code_complexity_study_python/python_commit_function_detect/input_compatibility/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312/detector_input_compatibility_failures.csv \
  --max-function-events 0 \
  --expected-manifest-rows 450548 \
  --expected-selected-events 166 \
  --expected-runtime-ast-failures 124 \
  --expected-tree-sitter-warning-events 42 \
  --output-root \
    ../ai_code_complexity_study_python/python_commit_function_detect/codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/py312-edge-pilot-166-fresh \
  --device cuda:0 \
  --verify-hashes \
  --no-cache \
  --no-resume

