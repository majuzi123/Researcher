#!/bin/bash
# 简化版节点捕获脚本

START=33
END=44
QUEUE="abaca"
WAIT_TIME=1

echo "开始尝试节点 $START 到 $END..."

for node in $(seq $START $END); do
    echo "尝试节点 esterel$node..."

    # 提交作业并获取作业ID
    output=$(oarsub -q $QUEUE -p "esterel$node" -I -t besteffort 2>&1 | head -5)
    job_id=$(echo "$output" | grep -o "OAR_JOB_ID=[0-9]*" | cut -d'=' -f2)

    if [ -z "$job_id" ]; then
        echo "节点 esterel$node 提交失败，继续下一个..."
        continue
    fi

    echo "作业 $job_id 已提交，等待启动..."

    # 等待作业启动
    sleep_pid=$!
    for i in $(seq 1 $WAIT_TIME); do
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

    echo "等待超时，删除作业 $job_id 并尝试下一个节点..."
    oardel $job_id 2>/dev/null
    kill $sleep_pid 2>/dev/null
done

echo "所有节点尝试完毕，均未成功。"
exit 1