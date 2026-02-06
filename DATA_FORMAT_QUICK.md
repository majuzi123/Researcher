# 📄 评估结果数据格式 - 快速参考

## 🎯 核心要点

**文件格式**: JSONL (每行一个 JSON 对象)  
**每条记录**: 一个论文变体的完整评估结果  
**总记录数**: 100 篇论文 × 6 变体 = 600 条记录

---

## 📊 单条记录结构

```json
{
  "paper_id": "论文记录ID",
  "base_paper_id": "基础论文ID（同一篇论文的所有变体共享）",
  "title": "论文标题",
  "variant_type": "original | no_abstract | no_introduction | ...",
  "evaluation": {
    "avg_rating": 7.5,              // 平均评分 (0-10)
    "paper_decision": "Accept",     // 决策: Accept/Reject
    "originality": 8,               // 原创性 (0-10)
    "quality": 7,                   // 质量 (0-10)
    "clarity": 7,                   // 清晰度 (0-10)
    "significance": 8,              // 重要性 (0-10)
    "confidence": 4,                // 置信度 (1-5)
    "strength": ["优点1", ...],     // 优点列表
    "weaknesses": ["缺点1", ...],   // 缺点列表
    "meta_review": "综合评审..."    // 综合评审意见
  },
  "text_length": 37352,             // 文本长度
  "evaluation_timestamp": "2026-02-06T22:14:05"
}
```

---

## 🔑 关键字段

| 字段 | 说明 | 用途 |
|------|------|------|
| **variant_type** | 6种变体之一 | 对比不同变体的效果 |
| **avg_rating** | 平均评分 (0-10) | 主要评价指标 |
| **paper_decision** | Accept/Reject | 二分类结果 |
| **originality/quality/clarity/significance** | 4个维度评分 | 详细分析 |

---

## 💻 快速读取代码

```python
import json

# 读取所有结果
results = []
with open('evaluation_results_YYYYMMDD_HHMMSS.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        results.append(json.loads(line))

# 访问数据
for r in results:
    print(f"{r['title'][:40]} | {r['variant_type']}")
    print(f"  评分: {r['evaluation']['avg_rating']}")
    print(f"  决策: {r['evaluation']['paper_decision']}")
```

---

## 📁 生成的文件

| 文件 | 说明 | 何时生成 |
|------|------|----------|
| `*_incremental.jsonl` | 增量保存 | 实时（每评估一个） |
| `*.jsonl` | 最终结果 | 完成后 |
| `*_summary.json` | 统计摘要 | 完成后 |

---

## 🔍 查看示例

运行示例脚本：
```bash
python scripts/example_read_results.py
```

会显示：
- 基础统计
- 变体对比
- 最高/最低评分论文
- 原始 vs 变体对比
- 导出为 CSV

---

## 📖 详细文档

完整数据格式说明: `docs/DATA_FORMAT.md`

---

## ✅ 总结

- **格式**: JSONL（每行一个 JSON）
- **记录数**: 600 条（100 篇 × 6 变体）
- **核心字段**: variant_type, avg_rating, paper_decision
- **读取**: 用 Python `json` 模块或 `pandas`

