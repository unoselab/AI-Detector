date;
for gpu in 0 1 2; do
    case "$gpu" in
        0) tag=t02 ;;
        1) tag=t04 ;;
        2) tag=t06 ;;
    esac

    log="logs/run-x-a-01/run-x-a-01-v2-full-20261016-233806-8357-${tag}-gpu${gpu}.log"

    echo "=== GPU ${gpu} (${tag}) ==="

    grep -E '^\[(WORKER|MODEL|GENERATE|ERROR)\]|Traceback|CUDA out of memory|RuntimeError' \
        "$log" | tail -n 8

    echo
done
