for file in docs/*.md; do
    date=$(git log --follow --diff-filter=A --date=format:'%Y-%m-%d %H:%M:%S' --format="%ad" -- "$file" | tail -1)
    
    if [ ! -z "$date" ]; then
        printf "%s : %s\n" "$date" "$file"
    fi
done | sort

# prev_date=""; count=0; echo "2026-05-20 21:41:49 : docs/EMBEDDING_CSV_EXPLAINED.md
# 2026-05-20 22:53:39 : docs/CODESEARCHNET_STARCODER2_7B_RESULTS.md
# 2026-05-21 01:31:58 : docs/STARCODER2-15B-GENERATION.md
# 2026-05-21 23:01:31 : docs/CODESEARCHNET_STARCODER2_15B_INST_RESULTS.md
# 2026-05-22 00:05:17 : docs/TRESHOLD_SWEEP.md
# 2026-05-23 02:40:04 : docs/BLOCK_SIZE_GRID.md
# 2026-05-23 16:56:49 : docs/TEST_1024_AST_ONLY.md
# 2026-05-23 20:37:42 : docs/2026_05_23_MAXLEN_2048.md" | while read -r line; do
#     date=$(echo "$line" | awk '{print $1}')
#     file=$(echo "$line" | awk '{print $4}')
#     dir=$(dirname "$file")
#     base=$(basename "$file")
    
#     total_on_date=$(echo "2026-05-20 21:41:49 : docs/EMBEDDING_CSV_EXPLAINED.md
# 2026-05-20 22:53:39 : docs/CODESEARCHNET_STARCODER2_7B_RESULTS.md
# 2026-05-21 01:31:58 : docs/STARCODER2-15B-GENERATION.md
# 2026-05-21 23:01:31 : docs/CODESEARCHNET_STARCODER2_15B_INST_RESULTS.md
# 2026-05-22 00:05:17 : docs/TRESHOLD_SWEEP.md
# 2026-05-23 02:40:04 : docs/BLOCK_SIZE_GRID.md
# 2026-05-23 16:56:49 : docs/TEST_1024_AST_ONLY.md
# 2026-05-23 20:37:42 : docs/2026_05_23_MAXLEN_2048.md" | grep -c "^$date")
    
#     if [ "$date" = "$prev_date" ]; then
#         ((count++))
#     else
#         count=0
#         prev_date="$date"
#     fi
    
#     # 같은 날짜에 여러 개가 있으면 알파벳(a, b, c...)을 생성합니다.
#     if [ "$total_on_date" -gt 1 ]; then
#         suffix=$(printf "\\$(printf '%03o' $((97 + count)))")
#     else
#         suffix=""
#     fi
    
#     new_file="${dir}/${date}${suffix}-${base}"
    
#     echo "Renaming: $file -> $new_file"
#     git mv "$file" "$new_file"
# done