# Skill：内核补丁描述规范

## 适用场景
在技术文章或周报中描述 Linux 内核补丁的状态、来源、依赖关系。

---

## 补丁状态描述

### 核心区分

| 状态 | 描述用词 | 含义 |
|---|---|---|
| 已合入主线 | 完成基本补丁 | 补丁已进入 linux-mm / linux-next 或主线 |
| 审查中 | 正在 review | 补丁在邮件列表讨论，未合入 |
| 已提交未审查 | 已提交，待 review | 刚发出，尚无实质性讨论 |
| 概念验证 | RFC | Request for Comments，征求意见稿，不一定会合入 |

**禁用「审查」作为动词状态**（「正在审查」语义模糊），统一用「正在 review」。

### 会议来源区分

| 来源类型 | 描述用词 | 示例 |
|---|---|---|
| 会议议题（讨论中） | XX 会议议题确认的前置条件 | LPC 2025 Live Update MC 议题确认的前置条件 |
| 会议结论（已决定） | XX 会议结论 | LSFMM 2026 会议确认的待办事项 |
| 会议「待办」 | 会议「待办」 | 峰会现场确认的三件事 |

**不用「硬要求」**（隐含强制性，实为技术前置条件）。

---

## 补丁引用格式

```markdown
[作者, "补丁标题", 版本（RFC v1/v2 等）, 补丁数量, 提交日期. lore URL]
```

示例：
```markdown
Pratyush Yadav, "[PATCH 00/12] kho: make boot time huge page allocation work nicely with KHO",
v1, 12 patches, 2026-04-29. https://lore.kernel.org/linux-mm/20260429133928.850721-1-pratyush@kernel.org/
```

---

## 数字推导透明化

当文章引用的数字（如停顿时长、内存大小）不来自补丁原文时：

1. **在正文注明来源性质**：「按 DDR5 写带宽 25–40 GB/s 推算」
2. **在脚注说明**：「该数字未出现在补丁 cover letter 中，属各阶段公开基准合成估算」
3. **在代码块展示推导过程**：

```
scratch_scale = 200（即 200%，×2 是 200÷100 的化简）
scratch 需求 = RSRV_KERN × scratch_scale / 100 = 240 × 2 = 480 GiB
物理内存上限 = 256 GiB → 分配失败
```

---

## 补丁名词解释规范

| 英文术语 | 处理方式 |
|---|---|
| 专有名词（rte_mempool、KHO） | 保留英文，首次出现时括号解释 |
| 技术概念（scratch、handover） | 保留英文，正文解释含义 |
| 机构缩写（KEV、FCEB） | 首次出现时括号展开全称 + 一句话解释 |
| 会议名（LSFMM、LPC） | 首次出现时展开全称 |

---

## cover letter 引用规范

直接引用 cover letter 原文时：

```markdown
> "scratch size will blow up and fail to allocate."
> （scratch 大小会暴增，导致分配失败。）
```

- 不用概括性断语替代原文（「这意味着……」之类）
- 英文原文必须附中文译文
- 注明 Message-ID 或 lore 链接
