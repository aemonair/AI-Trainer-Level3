# Phase 2.2.5-B: Practice Validation

## 目标

验证平台能否支撑真实考试练习，积累真实数据。

---

## 验证清单

### 1. Session 创建

```bash
python scripts/create_timestamped_practice.py 2.1.1
```

检查：
- [ ] `sessions/{session_id}/metadata.json` - chapter 正确
- [ ] `sessions/{session_id}/workspace/practice.ipynb` - 模板正确
- [ ] `sessions/{session_id}/logs/execution_log.json` - 初始化正确

### 2. Logger 记录

练习时观察：
- [ ] 执行 `print("hello")` - 记录成功
- [ ] 执行 `print(xxx)` - 记录 NameError
- [ ] 修复错误后执行 - 记录成功

检查 `execution_log.json`:
```json
[
  {"status": "error", "error": {"type": "NameError"}},
  {"status": "success"}
]
```

### 3. validate_practice 验证

```bash
python scripts/validate_practice.py \
    --session {session_id}
```

检查：
- [ ] `reports/report.json` - 生成成功
- [ ] `reports/summary.md` - 生成成功
- [ ] `metadata.json` - 状态更新为 completed

---

## 问题收集

练习后记录以下问题：

### 问题 1：创建流程
哪里不舒服？

### 问题 2：练习过程
缺什么功能？

### 问题 3：评分系统
哪里不准确？

---

## 已完成的 Session

| Session ID | Chapter | 状态 | 得分 | 问题 |
|------------|---------|------|------|------|
| 20260808_000924_1eebe7_chapter2.1.1 | 2.1.1 | ✅ 完成 | 99 | 无 |

---

## 下一步

积累 5-10 个 Session 后，进入 Phase 2.3：
- 拆分 validate_practice.py
- 迁移 process_auditor
- 实现 Assessment 实体