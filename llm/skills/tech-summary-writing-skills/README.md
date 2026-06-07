# 技术写作 Skill & Prompt 工具包

来源：底软动态（2026-05-02 ~ 2026-05-17）多轮修订经验提炼  
整理日期：2026-06-07

---

## 文件列表

### Skill（完整工作流规范）

| 文件 | 用途 |
|---|---|
| `skill-tech-weekly-writing.md` | 技术周报写作完整规范：结构、语言风格、发布前检查清单 |
| `skill-spec-benchmark-table.md` | SPEC 跑分表格：格式标准、换算规则（×9）、交叉验证要求、硅验证核实 |

### Prompt（单项任务指令）

| 文件 | 用途 |
|---|---|
| `prompt-language-style-check.md` | 语言习惯检查：禁忌句式、情绪古文表达、英文引文翻译要求 |
| `prompt-citation-quality-check.md` | 引用质量检查：URL 可访问性、正文与脚注数字一致性、孤儿脚注检测 |
| `prompt-footnote-renumber.md` | 脚注重新编号：Python 脚本，按正文首次出现顺序重排，自动清理孤儿脚注 |
| `prompt-data-source-tagging.md` | 数据来源分类标注：✅硅后实测 / ⚠️厂商发布指标 / 推算 / 估算 |

---

## 快速使用

**写新文章前**：读 `skill-tech-weekly-writing.md`

**处理跑分表格**：读 `skill-spec-benchmark-table.md` + `prompt-data-source-tagging.md`

**发布前检查**：依次跑
1. `prompt-language-style-check.md`
2. `prompt-citation-quality-check.md`
3. `prompt-footnote-renumber.md`（Python 脚本）
