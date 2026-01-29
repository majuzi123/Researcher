#!/bin/bash
# 简化版节点捕获脚本

START=2
END=44
QUEUE="abaca"
WAIT_TIME=10
OARSUB_TIMEOUT=10  # seconds to wait for oarsub to return
JOB_DURATION=3600  # seconds the job will sleep to hold the node

echo "开始尝试节点 $START 到 $END..."

for node in $(seq $START $END); do
    echo "尝试节点 esterel$node..."

    # Create a temporary job script that will sleep to reserve the node
    job_script=$(mktemp /tmp/oarsub_job.XXXXXX.sh)
    cat > "$job_script" <<EOF
#!/bin/bash
# oarsub job to reserve node esterel${node}
sleep ${JOB_DURATION}
EOF
    chmod +x "$job_script"

    # 提交作业并获取作业ID
    # Submit the job script file so oarsub has a script to run (avoids Usage error)
    output=$(timeout ${OARSUB_TIMEOUT}s oarsub -q "$QUEUE" -p "esterel$node" -t besteffort "$job_script" 2>&1 | head -5)
    job_id=$(echo "$output" | grep -o "OAR_JOB_ID=[0-9]*" | cut -d'=' -f2)

    # remove temporary job script
    rm -f "$job_script"

    if [ -z "$job_id" ]; then
        echo "节点 esterel$node 提交失败，输出："
        echo "$output"
        echo "继续下一个..."
        continue
    fi

    echo "作业 $job_id 已提交，等待启动..."

    # 等待作业启动（使用 SECONDS 计时以避免未使用变量警告）
    start_time=$SECONDS
    while [ $((SECONDS - start_time)) -lt $WAIT_TIME ]; do
        status=$(oarstat -u $USER 2>/dev/null | grep "^$job_id" | awk '{print $5}')

        if [ "$status" = "Running" ]; then
            echo "================================="
            echo "成功！已连接到节点 esterel$node"
            echo "作业ID: $job_id"
            echo "================================="
            exit 0
        fi

        sleep 1
        echo -n "."
    done

    echo "\n等待超时，删除作业 $job_id 并尝试下一个节点..."
    oardel $job_id 2>/dev/null
done

echo "所有节点尝试完毕，均未成功。"
exit 1