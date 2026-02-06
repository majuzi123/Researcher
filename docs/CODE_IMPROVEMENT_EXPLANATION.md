# 代码改进说明 - 逐行扫描方法

## 问题诊断

你这次运行的结果和之前几乎一样：
- **no_references**: 仍然 0% ❌
- **no_methods**: 27-36% ❌  
- **no_formulas**: 9% ❌
- **no_figures**: 1-4% ❌

这说明**正则表达式方法不够可靠**，因为论文格式太多样化。

## 新方法：逐行扫描

我已经改成了**更简单但更可靠**的逐行扫描方法：

### 原理

```python
# 1. 按行分割文本
lines = text.split('\n')

# 2. 找到章节标题所在的行号
for i, line in enumerate(lines):
    if re.search(r'^\s*REFERENCES\s*$', line, re.I):
        start_idx = i
        break

# 3. 找到下一个章节（或文档末尾）
for i in range(start_idx + 1, len(lines)):
    if is_next_section(lines[i]):
        end_idx = i
        break

# 4. 删除这个范围的行
result = '\n'.join(lines[:start_idx] + lines[end_idx:])
```

### 优势

✅ **更精确**: 逐行处理，不会误匹配  
✅ **更可靠**: 不依赖复杂的正则表达式  
✅ **更灵活**: 容易调整匹配规则  
✅ **更直观**: 代码逻辑清晰易懂

### 匹配规则

**章节标题必须**：
1. 单独成行
2. 可以有编号（如 `5. CONCLUSION`）
3. 可以全大写或首字母大写
4. 行首/行尾只有空格

**下一个章节的特征**：
1. 编号开头（如 `5. Results`）
2. 全大写标题（如 `APPENDIX`，至少3个大写字母）

## 为什么 References 仍然失败？

可能的原因：

1. **标题格式不标准**
   - 可能是 `References:` 而不是 `REFERENCES`
   - 可能在行中间，不是单独一行
   - 可能有其他字符

2. **论文没有 References 章节**
   - 有些论文可能真的没有参考文献部分
   - 或者用其他名称（如 "Bibliography", "Citations"）

3. **References 不是单独的章节**
   - 可能直接跟在正文后面，没有标题

## 下一步建议

### 选项 1: 接受当前结果 ✅

**理由**：
- 你已经有 1,899 个训练样本（目标 3,762 的 50%）
- Abstract 和 Introduction 覆盖率很好（93-100%）
- 可以先用这些数据做实验

**适用场景**：
- 时间紧迫，需要快速开始实验
- 主要关注 abstract 和 introduction 的影响

### 选项 2: 调试 References 匹配 🔧

我可以帮你：
1. 检查实际论文中 References 的格式
2. 调整正则表达式以匹配更多格式
3. 添加更多章节名称变体

**需要时间**：约 30分钟

### 选项 3: 放宽标准 📊

**修改策略**：
- 对于 references/formulas/figures，降低期望
- 只要能匹配到一部分就够了
- 重点保证 abstract/introduction/conclusion 的高覆盖率

## 当前代码状态

✅ **已改进**: 使用逐行扫描，比正则表达式更可靠  
⚠️ **待验证**: 需要重新运行看效果  
❌ **已知问题**: References 匹配率仍然很低

## 建议运行测试

```bash
# 重新生成数据集
python scripts/generate_variant_dataset.py

# 查看结果
python diagnose_variants.py
```

重点观察 `no_references` 的成功率是否有提升。如果还是 0%，说明论文格式确实很特殊，需要人工检查样例。

---

**你想要我做什么？**

A. 接受当前结果，继续使用 (最快)  
B. 帮我深入调试 References 匹配 (需要时间)  
C. 先重新运行看看效果如何 (推荐)

