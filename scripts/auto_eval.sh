#!/bin/bash
#
# 全自动评估脚本 - 自动申请节点、运行、监控、重试
#
# 使用方法:
#   screen -S eval
#   bash scripts/auto_eval.sh
#   # 然后 Ctrl+A, D 断开去睡觉
#
# 功能:
#   - 自动申请 GPU 节点 (oarsub)
#   - 自动配置环境
#   - 自动运行评估脚本
#   - 监控任务状态，崩溃后自动重新申请节点
#   - 支持断点续跑
#

set -o pipefail

# ========== 配置 ==========
WORK_DIR="$HOME/Researcher"
SCRIPT="scripts/batch_evaluate_papers.py"
MAX_RETRIES=20                    # 最大重试次数
RETRY_DELAY=30                    # 重试前等待秒数
CHECK_INTERVAL=60                 # 检查任务状态间隔（秒）
TARGET_COUNT=600                  # 目标评估数量

# OAR 配置
OAR_QUEUE="besteffort"
OAR_PARTITION="esterel37"
OAR_WALLTIME="12:00:00"
OAR_RESOURCES="host=1/gpu=1"

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

is_done() {
    local count=$(get_completed_count)
    [ "$count" -ge "$TARGET_COUNT" ]
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
    local job_script=$(mktemp "$LOG_DIR/job_XXXXXX.sh")
    create_job_script "$job_script"

    log "提交 OAR 任务..."
    log "  队列: $OAR_QUEUE"
    log "  分区: $OAR_PARTITION"
    log "  资源: $OAR_RESOURCES"
    log "  时长: $OAR_WALLTIME"

    # 提交任务并获取 job ID
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

    # 提取 job ID (多种格式尝试)
    local job_id=""
    # 格式1: OAR_JOB_ID=123456
    job_id=$(echo "$submit_output" | grep -oP 'OAR_JOB_ID=\K\d+' | head -1)
    # 格式2: 纯数字行
    if [ -z "$job_id" ]; then
        job_id=$(echo "$submit_output" | grep -oE '^[0-9]+$' | head -1)
    fi
    # 格式3: 任意数字
    if [ -z "$job_id" ]; then
        job_id=$(echo "$submit_output" | grep -oE '[0-9]{6,}' | head -1)
    fi

    if [ -z "$job_id" ]; then
        log "❌ 无法获取 Job ID"
        rm -f "$job_script"
        return 1
    fi

    log "✓ 任务已提交: Job ID = $job_id"

    # 等待一下让任务进入系统
    sleep 2

    echo "$job_id"
    return 0
}

get_job_state() {
    local job_id=$1
    # 尝试多种方式获取状态
    local state=$(oarstat -j "$job_id" -s 2>/dev/null | awk -F: '{print $2}' | tr -d ' ')
    if [ -z "$state" ]; then
        # 备用方法
        state=$(oarstat -j "$job_id" 2>/dev/null | grep -oP 'state\s*=\s*\K\w+' | head -1)
    fi
    if [ -z "$state" ]; then
        echo "Pending"  # 刚提交的任务可能还没有状态
    else
        echo "$state"
    fi
}

wait_for_job() {
    local job_id=$1
    local state
    local prev_state=""
    local completed_before=$(get_completed_count)
    local unknown_count=0
    local max_unknown=10  # 连续 Unknown 状态的最大次数

    log "监控任务 $job_id ..."

    # 先等待几秒让任务进入队列
    log "  等待任务进入队列..."
    sleep 5

    while true; do
        state=$(get_job_state "$job_id")

        if [ "$state" != "$prev_state" ]; then
            log "  任务状态: $state"
            prev_state="$state"
            unknown_count=0  # 状态变化时重置计数
        fi

        # 检查进度
        local completed_now=$(get_completed_count)
        if [ "$completed_now" != "$completed_before" ]; then
            log "  已完成: $completed_now / $TARGET_COUNT"
            completed_before="$completed_now"
        fi

        # 检查是否完成目标
        if is_done; then
            log "✓ 已达到目标数量 $TARGET_COUNT"
            return 0
        fi

        # 检查任务状态
        case "$state" in
            "Terminated"|"Error")
                log "任务结束，状态: $state"
                return 1
                ;;
            "Running"|"Launching"|"toLaunch")
                # 任务正在运行
                unknown_count=0
                ;;
            "Waiting"|"toAckReservation"|"Hold"|"Pending")
                # 任务在等待队列
                unknown_count=0
                ;;
            "Unknown"|"")
                unknown_count=$((unknown_count + 1))
                if [ $unknown_count -ge $max_unknown ]; then
                    log "  连续 $max_unknown 次 Unknown 状态，检查任务是否还存在..."
                    # 检查任务是否还在 oarstat 列表中
                    if ! oarstat -j "$job_id" >/dev/null 2>&1; then
                        log "任务 $job_id 已不存在"
                        return 1
                    fi
                    unknown_count=0
                fi
                ;;
            *)
                log "  其他状态: $state"
                ;;
        esac

        sleep "$CHECK_INTERVAL"
    done
}

# ========== 主程序 ==========

log "=========================================="
log "🚀 全自动评估脚本启动"
log "=========================================="
log "配置:"
log "  工作目录:     $WORK_DIR"
log "  目标数量:     $TARGET_COUNT"
log "  最大重试:     $MAX_RETRIES"
log "  主日志:       $MASTER_LOG"
log ""

# 检查是否已完成
initial_count=$(get_completed_count)
log "当前进度: $initial_count / $TARGET_COUNT"

if is_done; then
    log "✓ 所有 $TARGET_COUNT 篇论文已完成评估！"
    log "无需运行。"
    exit 0
fi

log ""
log "开始自动提交任务循环..."
log ""

retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    retry_count=$((retry_count + 1))

    log "=========================================="
    log "第 $retry_count / $MAX_RETRIES 次尝试"
    log "=========================================="

    current_count=$(get_completed_count)
    remaining=$((TARGET_COUNT - current_count))
    log "当前进度: $current_count / $TARGET_COUNT (剩余 $remaining)"

    if is_done; then
        log ""
        log "=========================================="
        log "🎉 评估完成！"
        log "=========================================="
        log "总计完成: $(get_completed_count) 篇"
        log "结果文件: $WORK_DIR/evaluation_results/"
        exit 0
    fi

    # 提交任务
    log "正在提交任务..."
    job_output=$(submit_job)
    submit_result=$?
    job_id=$(echo "$job_output" | tail -1)  # job_id 在最后一行

    if [ $submit_result -ne 0 ] || [ -z "$job_id" ] || ! [[ "$job_id" =~ ^[0-9]+$ ]]; then
        log "任务提交失败，等待 ${RETRY_DELAY}s 后重试..."
        sleep $RETRY_DELAY
        continue
    fi

    # 等待任务完成
    wait_for_job "$job_id"
    wait_result=$?

    if [ $wait_result -eq 0 ]; then
        # 成功完成
        log ""
        log "=========================================="
        log "🎉 评估完成！"
        log "=========================================="
        log "总计完成: $(get_completed_count) 篇"
        exit 0
    fi

    # 任务结束但未完成
    final_count=$(get_completed_count)
    new_done=$((final_count - current_count))
    log "本次完成: $new_done 篇 (总计: $final_count / $TARGET_COUNT)"

    if [ $retry_count -lt $MAX_RETRIES ]; then
        log "等待 ${RETRY_DELAY}s 后重新申请节点..."
        sleep $RETRY_DELAY
    fi
done

log ""
log "=========================================="
log "❌ 已达到最大重试次数 ($MAX_RETRIES)"
log "=========================================="
log "当前进度: $(get_completed_count) / $TARGET_COUNT"
log "请检查日志并手动处理"
log "日志位置: $LOG_DIR"

exit 1

