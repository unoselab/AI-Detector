mkdir -p logs

TS="$(date +'%Y%m%d_%H%M%S')"
LOGDIR="logs/rq2d_full_run_${TS}"
mkdir -p "$LOGDIR"

echo "Log dir: $LOGDIR"

# 1. Missing data check
{
  echo "============================================================"
  echo "Missing data check"
  echo "Started: $(date -Is)"
  echo "Command:"
  echo "find src/astnn/classification -type f | grep -E 'starcoder|codesearchnet|cpp|c\\+\\+|humaneval' | sort"
  echo "============================================================"
  find src/astnn/classification -type f | grep -E 'starcoder|codesearchnet|cpp|c\+\+|humaneval' | sort
  echo
  echo "Finished: $(date -Is)"
} 2>&1 | tee "$LOGDIR/missing_data_check_${TS}.log"

# 2. Train all model families
SUMMARY="$LOGDIR/model_run_summary_${TS}.tsv"
echo -e "model\tstatus\tstart_time\tend_time\tseconds\tlog_file" > "$SUMMARY"

set -o pipefail

for m in lr svm mlp rf gb xgb knn dt; do
  MODEL_TS="$(date +'%Y%m%d_%H%M%S')"
  MODEL_LOG="$LOGDIR/run4_${m}_${MODEL_TS}.log"
  START_ISO="$(date -Is)"
  START_SEC="$(date +%s)"

  echo "============================================================"
  echo "Running model: $m"
  echo "Started: $START_ISO"
  echo "Log: $MODEL_LOG"
  echo "============================================================"

  if MODEL="$m" N_ITER=30 bash src/run4-train-classifiers.sh 2>&1 | tee "$MODEL_LOG"; then
    STATUS="OK"
  else
    STATUS="FAIL"
  fi

  END_ISO="$(date -Is)"
  END_SEC="$(date +%s)"
  ELAPSED="$((END_SEC - START_SEC))"

  echo -e "${m}\t${STATUS}\t${START_ISO}\t${END_ISO}\t${ELAPSED}\t${MODEL_LOG}" >> "$SUMMARY"

  echo "Finished model: $m"
  echo "Status: $STATUS"
  echo "Elapsed seconds: $ELAPSED"
  echo
done

echo "============================================================"
echo "All done"
echo "Log dir: $LOGDIR"
echo "Summary: $SUMMARY"
echo "============================================================"
cat "$SUMMARY"