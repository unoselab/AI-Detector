python - <<'PY'
import pandas as pd

base = pd.read_csv(
    "../ai_code_complexity_study_python/ai-code-complexity-study/"
    "repo_python/run-py-5a-py312/strict/repo_month_function_event_counts.csv"
)
detector = pd.read_csv(
    "../ai_code_complexity_study_python/python_commit_function_detect/"
    "codellama-7b_4500_complexity_stratified_maxlen2048_svm_ast/strict/"
    "py312-full-450548-fresh/repo_month_function_event_summary_all.csv"
)

panel = base[["dataset_source", "repo_name", "time"]].merge(
    detector[[
        "dataset_source", "repo_name", "time",
        "function_change_events_scored",
        "function_change_events_failed",
        "agc_function_change_events",
        "hwc_function_change_events",
        "added_agc_function_events",
        "added_hwc_function_events",
        "modified_agc_function_events",
        "modified_hwc_function_events",
    ]],
    on=["dataset_source", "repo_name", "time"],
    how="left",
)

count_cols = [
    "function_change_events_scored",
    "function_change_events_failed",
    "agc_function_change_events",
    "hwc_function_change_events",
    "added_agc_function_events",
    "added_hwc_function_events",
    "modified_agc_function_events",
    "modified_hwc_function_events",
]
panel[count_cols] = panel[count_cols].fillna(0).astype(int)

# Zero-event repository-months get an explicitly missing (NA) ratio, not 0/0,
# consistent with how agc_top_level_block_ratio was handled in run-py-3b.
panel["agc_function_change_event_ratio"] = (
    panel["agc_function_change_events"] / panel["function_change_events_scored"]
).where(panel["function_change_events_scored"] > 0)

assert len(panel) == 1633, f"expected 1633 rows, got {len(panel)}"
assert panel[["dataset_source", "repo_name", "time"]].duplicated().sum() == 0
assert (panel["function_change_events_scored"] == 0).sum() == 344
assert panel["agc_function_change_event_ratio"].isna().sum() == 344

panel.to_csv("repo_month_function_event_panel_full_py312.csv", index=False)
print("OK:", len(panel), "rows,", panel["agc_function_change_event_ratio"].notna().sum(), "with non-missing ratio")
PY


(aidetector) OISSE-IST173C01:ai_detector$ 
(aidetector) OISSE-IST173C01:ai_detector$ ./xrun.sh 
OK: 1633 rows, 1289 with non-missing ratio
(aidetector) OISSE-IST173C01:ai_detector$ 
