#!/bin/bash
#
# 全自动评估脚本 - 自动申请节点、运行评估、监控、崩溃重试
#
# 使用方法:
#   screen -S eval
#   bash scripts/auto_eval.sh
#   # Ctrl+A, D 断开
#
# 功能:
#   - 自动申请 GPU 节点 (oarsub)
#   - 自动配置环境
#   - 自动运行评估脚本
#   - 监控任务状态，崩溃后自动重试
#   - 支持断点续跑
#

set -o pipefail

# ========== 配置 ==========
WORK_DIR="$HOME/Researcher"
SCRIPT="scripts/batch_evaluate_papers.py"
GENERATE_SCRIPT="scripts/generate_variant_dataset.py"
MAX_RETRIES=9999999999999  # 近似无限重试
RETRY_DELAY=5
CHECK_INTERVAL=60
TARGET_COUNT=600

# OAR 配置
OAR_QUEUE="besteffort"
OAR_WALLTIME="12:00:00"
OAR_RESOURCES="host=1/gpu=1"

# 节点轮询列表（按优先顺序）
NODE_LIST=("esterel35" "esterel38" "esterel37" "esterel44" "esterel42" "esterel17" "esterel33" "esterel34" "esterel36" "esterel39" "esterel40" "esterel41" "esterel43")
NODE_INDEX=0
NODE_COUNT=${#NODE_LIST[@]}

# 日志
LOG_DIR="$WORK_DIR/evaluation_logs"
mkdir -p "$LOG_DIR"
MASTER_LOG="$LOG_DIR/auto_eval_$(date +%Y%m%d_%H%M%S).log"

# ========== 函数 ==========

log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$MASTER_LOG"
}

get_completed_count() {
    local f=$(ls -t "$WORK_DIR/evaluation_results"/evaluation_results_*_incremental.jsonl 2>/dev/null | head -1)
    if [ -n "$f" ] && [ -f "$f" ]; then
        wc -l < "$f" | tr -d ' '
    else
        echo "0"
    fi
}

check_dataset_exists() {
    local train_file="$WORK_DIR/util/train_with_variants.jsonl"
    local test_file="$WORK_DIR/util/test_with_variants.jsonl"

    if [ -f "$train_file" ] && [ -f "$test_file" ]; then
        return 0
    else
        return 1
    fi
}

generate_dataset() {
    log "生成论文变体数据集..."
    cd "$WORK_DIR"
    python "$GENERATE_SCRIPT"
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log "✓ 数据集生成成功"
        return 0
    else
        log "❌ 数据集生成失败 (exit: $exit_code)"
        return 1
    fi
}

is_done() {
    local count=$(get_completed_count)
    [ "$count" -ge "$TARGET_COUNT" ]
}

get_next_node() {
    local current_node=${NODE_LIST[$NODE_INDEX]}
    echo "$current_node"
}

create_job_script() {
    local job_script="$1"
    cat > "$job_script" << 'EOFSCRIPT'
#!/bin/bash
#OAR -n eval_papers
#OAR -O /home/bma/Researcher/evaluation_logs/oar_stdout_%jobid%.log
#OAR -E /home/bma/Researcher/evaluation_logs/oar_stderr_%jobid%.log

echo "=========================================="
echo "Job started at: $(date)"
echo "Node: $(hostname)"
echo "=========================================="

# 配置环境
cd ~/Researcher
module load conda
conda activate /home/bma/conda_envs/conda_envs/reviewer

# 显示 GPU 信息
echo "GPU Info:"
nvidia-smi

# 运行评估脚本
echo "=========================================="
echo "Starting evaluation..."
echo "=========================================="

python scripts/batch_evaluate_papers.py

EXIT_CODE=$?

echo "=========================================="
echo "Job finished at: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
EOFSCRIPT
    chmod +x "$job_script"
}

submit_job() {
    local OAR_PARTITION="$1"
    local job_script=$(mktemp "$LOG_DIR/job_XXXXXX.sh")
    create_job_script "$job_script"

    log "提交 OAR 任务..."
    log "  队列: $OAR_QUEUE"
    log "  节点: $OAR_PARTITION (index: $NODE_INDEX/${NODE_COUNT})"
    log "  资源: $OAR_RESOURCES"
    log "  时长: $OAR_WALLTIME"

    local submit_output=$(oarsub -q "$OAR_QUEUE" \
                                 -p "$OAR_PARTITION" \
                                 -l "$OAR_RESOURCES,walltime=$OAR_WALLTIME" \
                                 -S "$job_script" 2>&1)

    local submit_exit=$?
    log "oarsub 输出: $submit_output"

    if [ $submit_exit -ne 0 ]; then
        log "❌ 任务提交失败 (exit code: $submit_exit)"
        rm -f "$job_script"
        return 1
    fi

    # 提取 job ID
    local job_id=""
    job_id=$(echo "$submit_output" | grep -oP 'OAR_JOB_ID=\K\d+' | head -1)
    if [ -z "$job_id" ]; then
        job_id=$(echo "$submit_output" | grep -oE '^[0-9]+$' | head -1)
    fi
    if [ -z "$job_id" ]; then
        job_id=$(echo "$submit_output" | grep -oE '[0-9]{6,}' | head -1)
    fi

    if [ -z "$job_id" ]; then
        log "❌ 无法获取 Job ID"
        rm -f "$job_script"
        return 1
    fi

    log "✓ 任务已提交: Job ID = $job_id"
    sleep 2

    # 监控任务
    log "监控任务 $job_id ..."
    local last_count=$(get_completed_count)
    local waiting_time=0

    while true; do
        sleep $CHECK_INTERVAL

        local status=$(oarstat -j "$job_id" -s 2>/dev/null | grep -oE '(Running|Waiting|Finishing|Terminated|Error)' | head -1)
        if [ -z "$status" ]; then
            status="Unknown"
        fi

        local current_count=$(get_completed_count)
        local new_count=$((current_count - last_count))
        last_count=$current_count

        log "  状态: $status | 完成: $current_count / $TARGET_COUNT (+$new_count)"

        if is_done; then
            log "✓ 评估完成！达到目标数量 $TARGET_COUNT"
            rm -f "$job_script"
            return 0
        fi

        case "$status" in
            Terminated|Error|Unknown)
                log "任务结束，状态: $status"
                rm -f "$job_script"
                return 2
                ;;
            Waiting)
                waiting_time=$((waiting_time + CHECK_INTERVAL))
                if [ $waiting_time -ge 60 ]; then
                    log "Waiting 超过1分钟，自动结束任务并切换节点"
                    oardel "$job_id"
                    rm -f "$job_script"
                    return 2
                fi
                ;;
            Running|Finishing)
                waiting_time=0
                ;;
        esac
    done
}

# ========== 主流程 ==========

log "=========================================="
log "全自动评估脚本"
log "=========================================="
log "工作目录: $WORK_DIR"
log "评估脚本: $SCRIPT"
log "目标数量: $TARGET_COUNT"
log "Master日志: $MASTER_LOG"
log ""

# 检查并生成数据集
log "检查论文变体数据集..."
if ! check_dataset_exists; then
    log "数据集不存在，开始生成..."
    if ! generate_dataset; then
        log "❌ 无法生成数据集，退出"
        exit 1
    fi
else
    log "✓ 数据集已存在"
    train_count=$(wc -l < "$WORK_DIR/util/train_with_variants.jsonl" | tr -d ' ')
    test_count=$(wc -l < "$WORK_DIR/util/test_with_variants.jsonl" | tr -d ' ')
    log "  Train: $train_count papers"
    log "  Test:  $test_count papers"
fi

# 检查初始进度
initial_count=$(get_completed_count)
log ""
log "初始进度: $initial_count / $TARGET_COUNT"

if is_done; then
    log "✓ 评估已完成，无需继续"
    exit 0
fi

# 主循环：提交任务、监控、重试
retry=0
while [ $retry -lt $MAX_RETRIES ]; do
    retry=$((retry + 1))

    current_node=$(get_next_node)
    log ""
    log "=========================================="
    log "第 $retry / $MAX_RETRIES 次尝试"
    log "下一个节点: $current_node (index: $NODE_INDEX/${NODE_COUNT})"
    log "=========================================="

    current_count=$(get_completed_count)
    remaining=$((TARGET_COUNT - current_count))
    log "当前进度: $current_count / $TARGET_COUNT (剩余 $remaining)"

    if is_done; then
        log "✓ 评估完成！"
        break
    fi

    submit_job "$current_node"
    submit_result=$?

    NODE_INDEX=$((NODE_INDEX + 1))
    if [ $NODE_INDEX -ge $NODE_COUNT ]; then
        NODE_INDEX=0
    fi

    current_count=$(get_completed_count)
    log "本次完成: $((current_count - initial_count)) 篇 (总计: $current_count / $TARGET_COUNT)"

    if [ $submit_result -eq 0 ]; then
        log "✓ 全部评估完成！"
        break
    fi

    if is_done; then
        log "✓ 达到目标数量，评估完成！"
        break
    fi

    log "等待 ${RETRY_DELAY}s 后重新申请节点..."
    sleep $RETRY_DELAY
done

# 最终统计
log ""
log "=========================================="
log "最终统计"
log "=========================================="
final_count=$(get_completed_count)
log "总评估数: $final_count / $TARGET_COUNT"
log "重试次数: $retry"

if [ $final_count -ge $TARGET_COUNT ]; then
    log "状态: ✓ 成功完成"
else
    log "状态: ⚠️  未完成 (已完成 $final_count)"
fi

log "=========================================="
log "脚本结束: $(date)"
log "=========================================="
