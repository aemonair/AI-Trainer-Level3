# 项目规则

## Review 规则
- **只记录错误的练习**，正确的不用生成Review
- Review文件名必须和practice文件名时间戳一致（如 `1.1.2_practice_202608011659_review.md`）
- 聚合脚本查找 `*_review.md` 文件
- **判断标准**：只对比 `_guide.md` 中的下划线填空部分，不添加额外要求
- 如果 `_guide.md` 没有 `sort_index()`，就不能以此为由扣分

## 目录命名
- 素材目录使用 `-materials` 后缀（如 `1.1.1-materials`）
- 代码详解文件命名为 `_guide.md`（如 `1.1.1_guide.md`）

## 练习流程
1. 运行 `uv run python3 scripts/create_timestamped_practice.py <章节号>` 创建练习文件
2. 在Jupyter中完成练习
3. 练习后检查，**只有错误时才生成Review文件**

## 复盘流程

### 1. 检查练习结果
- 读取 `*_practice_*.ipynb` 文件
- 检查每个代码单元格的执行结果
- 对比 `_guide.md` 中的标准答案

### 2. 识别错误类型
| 错误类型 | 示例 | 严重程度 |
|---------|------|---------|
| 拼写错误 | `bewteen` → `between` | 低 |
| 参数错误 | `fillna('bfill')` → `fillna(method='bfill')` | 中 |
| 语法错误 | `data(columns=[...])` → `data.drop(columns=[...])` | 高 |
| 逻辑错误 | 错误的groupby条件 | 高 |

### 3. 生成Review文件
```markdown
# {章节号} 练习 Review - {时间戳}

## 练习文件
[文件名](file:///完整路径)

## ❌ 错误记录
### 错误1：{错误类型}
- **错误代码**：`...`
- **正确写法**：`...`
- **原因**：...

## 📊 评分
| 任务 | 满分 | 得分 | 说明 |
|------|------|------|------|
```

### 4. 聚合分析
```bash
uv run python3 scripts/aggregate_reviews.py
```
生成 `reports/reviews_summary.md` 和 `reviews_summary.csv`

### 5. 历史分析
```bash
# 运行题目历史命令分析
# 查看练习次数、错误趋势、进步曲线
```

## 脚本依赖
- `create_timestamped_practice.py`：创建练习文件
- `aggregate_reviews.py`：聚合所有Review文件
- `rename_materials.sh`：批量重命名目录和文件