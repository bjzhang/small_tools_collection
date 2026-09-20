# Skill：Commit Message 规范（草稿）

> 状态：草稿（2026-09-20，基于 W38 gap 目录批次入库多轮 message 修订经验提炼）
> [OMO生成·review完成]（用户 2026-09-20 review）
> 适用：life-logs 主仓 + bosc 子模块的 RFC/OMO 前缀提交

## 标题行

格式：`RFC/OMO: {type}({scope}): {描述}`

- 描述枚举本批次**全部主要成分**，用「 + 」串联，成分并列可见（例：`docs(gap): gap 分析目录批次入库 — 模拟器系列 F29-F34 + F14/F35/F36 补齐 + F37 中断数量预算 + Gate 术语按中文习惯修正`）
- type/scope 参照既有历史（docs/chore；gap/t348/w38/t381…）
- 子模块指针提交：`RFC/OMO: chore(bosc): bump submodule pointer — {对应 bosc 提交摘要}`

## 正文结构（信息量自足，不读 diff 也能懂）

1. **内容统计**：`内容（N 文件，+X/−Y）：`
2. **新增/修改分解**：逐项列出，每项一句话定位与关键结论
3. **状态标注**：review 状态显式声明（见下表）
4. **术语/口径修正节**（如涉及）：改了什么、为什么、新旧对照——正文是术语修正的唯一权威解释处

## 状态标注纪律（OMO 内容分级）

| 场景 | 标注 |
|---|---|
| OMO 生成、未经用户 review | `[OMO生成·未经review]`（文件头同步此标） |
| OMO 生成、用户 review 完成 | `[OMO生成review完成]`；文件头 `[OMO生成·未经review]` → `[OMO生成·review完成]` |
| 用户自供材料未 review | 文件号级标注，如 `[F29/F30 未经review]` |

## 用语规范

- 用「**缺失**」，不用「跳空」等股市术语（例：「补齐了缺失的 F14」）
- 英文项目管理术语按中文习惯翻译后再用：Gate→目标版本（评审语境用「评审门」）；revision=修订版本 ≠ 评审阶段
- 版本号与评审活动分开表述；里程碑不由版本编号自动定义

## 提交纪律

- **分批**：按逻辑单元分批，不混合多主题
- **顺序**：bosc 子模块先行 commit，主仓指针后行
- **红线**：.DS_Store/zip/PDF 永不入库；`git add` 指定路径，禁止 `add -A`（工作区常有并行挂起内容）
- **不 push**（默认本地）

## Amend 纪律（仅 HEAD、仅 message）

- 仅各仓 HEAD 可 amend；message-only 修订必须验证新旧 commit tree diff 为空
- amend bosc 后，主仓须重新 `git add bosc` 并一并 amend 指针提交
- 多行 message 用文件传入（`-F`）+ `--cleanup=verbatim`，避免尾部空行噪音

## 模板

    RFC/OMO: docs({scope}): {批次名} — {成分1} + {成分2} + {成分n}

    内容（N 文件，+X/−Y）：
    - 新增 M：{逐项：名称（一句话定位/关键结论）}
    - 修改 K：{改动性质}（详见下节）
    - 状态标注：{未经 review 清单}；{OMO 标注}

    {术语修正节（如涉及）：
    - 语义更正：…
    - 字段改名：…
    - 正文措辞同步：…
    - 注记：本次更正不代表原有建议已批准}
