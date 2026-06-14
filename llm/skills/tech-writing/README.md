# tech-writing

通用技术写作 Skill & Prompt 工具包。  
来源：底软动态（2026-05-02 ~ 2026-05-17）多轮修订经验提炼  
整理日期：2026-06-14

适用于任何技术文章写作场景，不含个人风格偏好。无需扩展即可直接使用。

如需叠加个人风格偏好（如语言禁忌、章节排序习惯、领域写作惯例等），
可新建一个个性化包，在其文件头部声明「依赖 tech-writing」，
只记录在本包基础上的增量规范，两包配合加载即可。

---

## 文件列表

### Skill（完整工作流规范）

| 文件 | 用途 |
|---|---|
| `skill-spec-benchmark-table.md` | SPEC 跑分表格：格式标准、换算规则（×9）、交叉验证要求、硅验证标注 |
| `skill-patch-description.md` | 内核补丁描述规范：状态用词、会议来源区分、引用格式、数字推导透明化 |

### Prompt（单项任务指令）

| 文件 | 用途 |
|---|---|
| `prompt-language-style-check.md` | 语言习惯检查：禁忌句式、情绪古文表达、英文引文翻译要求 |
| `prompt-citation-quality-check.md` | 引用质量检查：URL 可访问性、正文与脚注数字一致性、孤儿脚注检测 |
| `prompt-footnote-renumber.md` | 脚注重新编号：Python 脚本，按正文首次出现顺序重排，自动清理孤儿脚注 |
| `prompt-data-source-tagging.md` | 数据来源分类标注：✅硅后实测 / ⚠️厂商发布指标 / 推算 / 估算 |
| `prompt-tool-capability-verification.md` | 工具能力核实：在文章声称工具支持某能力前，拆解并独立核实边界 |

---

## 快速使用

**处理跑分表格**：读 `skill-spec-benchmark-table.md` + `prompt-data-source-tagging.md`

**描述内核补丁**：读 `skill-patch-description.md`

**涉及工具能力声称**：跑 `prompt-tool-capability-verification.md`

**发布前检查**：依次跑
1. `prompt-language-style-check.md`
2. `prompt-citation-quality-check.md`
3. `prompt-footnote-renumber.md`（Python 脚本）
