# 目录结构重组方案

> 创建时间：2026-08-06  
> 状态：待执行  
> 目标：实现每次练习独立运行，互不影响

---

## 📋 核心需求

1. **模板化管理**：每个章节有一个template目录，包含所有需要的数据文件（CSV、模型、图片等）
2. **独立练习**：每次创建练习时，从template复制一个完整的新目录
3. **互不干扰**：每次练习有独立的日志、生成的数据文件，不会影响其他练习
4. **易于对比**：不同练习版本可以方便对比

---

## 📁 新的目录结构

```
人工智能训练师_3级_sucai/
│
├── 📚 templates/                    # 新增：模板目录
│   ├── 1.1.1/                      # 章节1.1.1的模板
│   │   ├── 1.1.1.ipynb            # 模板notebook（含填空）
│   │   ├── patient_data.csv       # 原始数据文件
│   │   ├── 1.1.1_guide.md         # 代码详解
│   │   └── ...                     # 其他需要的文件
│   │
│   ├── 2.1.1/
│   │   ├── 2.1.1.ipynb
│   │   ├── auto-mpg.csv
│   │   ├── 2.1.1.docx
│   │   └── 2.1.1_guide.md
│   │
│   ├── 3.2.5/
│   │   ├── 3.2.5.ipynb
│   │   ├── version-RFB-320.onnx   # 模型文件
│   │   ├── voc-model-labels.txt
│   │   ├── imgs/                   # 图片目录
│   │   └── vision/                 # 其他依赖
│   │
│   └── ...                         # 其他章节
│
├── 📝 practices/                    # 新增：练习目录
│   ├── 1.1.1_202608062300/         # 第一次练习（时间戳标识）
│   │   ├── 1.1.1_practice.ipynb   # 练习文件
│   │   ├── patient_data.csv       # 从template拷贝的数据
│   │   ├── 1.1.1_guide.md         # 参考答案
│   │   ├── output.csv             # 练习生成的新文件
│   │   ├── execution_log.json     # 本次练习的执行日志
│   │   ├── manifest.json          # 练习元数据
│   │   └── scoring_result.json    # 评分结果（如有）
│   │
│   ├── 1.1.1_202608071500/         # 第二次练习（完全独立）
│   │   ├── 1.1.1_practice.ipynb
│   │   ├── patient_data.csv
│   │   ├── output.csv
│   │   └── ...
│   │
│   └── ...
│
├── 📂 *-materials/                 # 现有目录，暂时不动
│   ├── 1.1.1-materials/
│   ├── 2.1.1-materials/
│   └── ...
│
├── 📚 source-materials/            # 新增：原始题目来源
│   ├── pdf/                        # PDF文件
│   ├── doc/                        # DOC/DOCX文件
│   └── extracted/                  # 从PDF/DOC提取的文本
│
├── ✅ answers/                     # 答案文件（已有，需整理）
│
├── 📏 scoring/                     # 评分标准（已有）
│
├── 🌐 html-demos/                 # 新增：静态HTML操作界面
│
├── 🛠️ scripts/                    # 工具脚本（已有）
│   ├── create_timestamped_practice.py  # 需修改
│   ├── execution_logger.py
│   ├── scoring_validator.py
│   └── aggregate_reviews.py
│
├── 📈 reports/                    # 复盘报告（已有）
│
└── 📓 sessions/                   # 会话记录（已有）
```

---

## 🔄 工作流程

### 1. 准备阶段（手动）

```bash
# 将现有materials目录中的文件整理到templates
# 示例：
mkdir -p templates/1.1.1
cp 1.1.1-materials/1.1.1.ipynb templates/1.1.1/
cp 1.1.1-materials/patient_data.csv templates/1.1.1/
cp 1.1.1-materials/1.1.1_guide.md templates/1.1.1/
# ... 其他章节类似
```

### 2. 创建练习（自动化）

```bash
# 运行创建脚本
python3 scripts/create_timestamped_practice.py 1.1.1
```

**脚本自动执行：**
1. 从 `templates/1.1.1/` 复制整个目录到 `practices/1.1.1_202608062300/`
2. 重命名 `1.1.1.ipynb` → `1.1.1_practice.ipynb`
3. 注入执行日志初始化代码
4. 生成 `manifest.json` 和 `execution_log.json`
5. 输出练习目录路径

### 3. 练习阶段

```bash
# 在Jupyter中打开练习文件
cd practices/1.1.1_202608062300/
jupyter notebook 1.1.1_practice.ipynb
```

**练习过程中：**
- 读取的数据文件来自template拷贝（如 `patient_data.csv`）
- 生成的新文件保存在当前目录（如 `output.csv`、`cleaned_data.csv`）
- 执行日志自动记录到 `execution_log.json`
- 不影响其他练习或template

### 4. 对比不同练习

```bash
# 对比两次练习的结果
diff practices/1.1.1_202608062300/output.csv practices/1.1.1_202608071500/output.csv

# 查看执行日志
cat practices/1.1.1_202608062300/execution_log.json
```

---

## 🛠️ 脚本修改要点

### create_timestamped_practice.py

**当前逻辑：**
```python
# 在materials目录中创建practice文件
item_dir = ROOT / f'{chapter}-materials'
practice_nb = item_dir / f'{chapter}_practice_{now_str}.ipynb'
```

**修改后逻辑：**
```python
# 从templates复制整个目录到practices
template_dir = ROOT / 'templates' / chapter
practice_dir = ROOT / 'practices' / f'{chapter}_{now_str}'

# 复制整个目录
import shutil
shutil.copytree(template_dir, practice_dir)

# 重命名notebook
old_nb = practice_dir / f'{chapter}.ipynb'
practice_nb = practice_dir / f'{chapter}_practice.ipynb'
old_nb.rename(practice_nb)

# 注入日志代码、生成manifest等...
```

**关键变化：**
- 源目录：`templates/{chapter}/`
- 目标目录：`practices/{chapter}_{timestamp}/`
- 复制方式：整个目录（包括所有数据文件）
- 日志文件：在练习目录内生成

---

## 📦 迁移步骤（后续执行）

### Phase 1: 创建目录结构
```bash
mkdir -p templates
mkdir -p practices
mkdir -p source-materials/{pdf,doc,extracted}
mkdir -p html-demos
```

### Phase 2: 迁移模板文件
```bash
# 示例：迁移1.1.1
mkdir -p templates/1.1.1
cp 1.1.1-materials/1.1.1.ipynb templates/1.1.1/
cp 1.1.1-materials/patient_data.csv templates/1.1.1/
cp 1.1.1-materials/1.1.1_guide.md templates/1.1.1/

# 示例：迁移2.1.1
mkdir -p templates/2.1.1
cp 2.1.1-materials/2.1.1.ipynb templates/2.1.1/
cp 2.1.1-materials/auto-mpg.csv templates/2.1.1/
cp 2.1.1-materials/2.1.1.docx templates/2.1.1/
cp 2.1.1-materials/2.1.1_guide.md templates/2.1.1/

# ... 其他章节类似
```

### Phase 3: 修改脚本
- 修改 `create_timestamped_practice.py`
- 更新路径引用
- 测试创建流程

### Phase 4: 验证
- 创建测试练习
- 确认文件复制正确
- 确认日志独立
- 确认生成的文件不影响其他练习

### Phase 5: 清理（可选）
- 备份旧的 `*-materials` 目录
- 确认新流程稳定后删除旧目录

---

## ⚠️ 注意事项

1. **template目录只读**：template中的文件不应被修改，只作为复制源
2. **练习目录可写**：每次练习在独立目录中，可以自由修改和生成文件
3. **时间戳格式**：使用 `YYYYMMDDHHMM` 格式，如 `202608062300`
4. **大文件处理**：模型文件（如 `.onnx`）较大，复制时注意磁盘空间
5. **路径兼容**：notebook中的相对路径需要保持一致（从template复制后路径结构相同）

---

## 📊 优势对比

| 维度 | 旧方案（materials） | 新方案（templates + practices） |
|------|-------------------|-------------------------------|
| 数据隔离 | ❌ 所有练习共享数据 | ✅ 每次练习独立数据 |
| 日志管理 | ❌ 日志混在一起 | ✅ 每次练习独立日志 |
| 生成文件 | ❌ 输出文件混在materials | ✅ 输出文件在练习目录 |
| 对比难度 | ❌ 难以对比不同版本 | ✅ 直接diff对比 |
| 清理难度 | ❌ 需要手动筛选 | ✅ 删除整个练习目录 |
| 模板保护 | ❌ 可能误改模板 | ✅ template只读保护 |

---

## 🎯 后续任务清单

- [ ] 创建 `templates/` 目录结构
- [ ] 创建 `practices/` 目录结构
- [ ] 创建 `source-materials/` 目录结构
- [ ] 创建 `html-demos/` 目录结构
- [ ] 迁移所有章节的模板文件到 `templates/`
- [ ] 修改 `create_timestamped_practice.py` 脚本
- [ ] 测试新创建流程
- [ ] 更新相关脚本的路径引用
- [ ] 整理 `answers/` 目录
- [ ] 迁移PDF/DOC到 `source-materials/`
- [ ] 验证完整工作流程
- [ ] 清理旧的 `*-materials` 目录（可选）

---

## 📝 备注

- 现有 `*-materials` 目录暂时不动，等新流程稳定后再处理
- 本方案记录在此，后续准备执行
- 执行前建议先备份整个项目