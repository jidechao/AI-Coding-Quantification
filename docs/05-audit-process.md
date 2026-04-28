# 抽样审计流程

## 目标

抽样审计用于校准启发式估算，不用于追责个人。

## 每周流程

1. 从 `audit_queue` 中筛选 `pending` 项。
2. 审计员阅读 MR diff、commit message 和开发者说明。
3. 标注真实三档：`ai-authored`、`ai-assisted`、`human`。
4. 估算真实 `Human-Edit-Ratio`。
5. 写入 `audit_log`。
6. 每月根据准确率和偏差调整 `.ai-coding-config.yml` 阈值。

## 审计判定建议

- 如果大部分结构、函数、测试由 AI 一次性生成，标 `ai-authored`。
- 如果 AI 产出被明显重构、拆分或改写，标 `ai-assisted`。
- 如果 AI 只用于解释、补全少量片段或查资料，标 `human`。

## 质量红线

- 三档准确率连续两周低于 70%，暂停用该数据做推广汇报。
- AI PR 缺陷率高于 human PR 50% 以上，触发专项复盘。
- 审计样本不足时，禁止对外展示细粒度结论。
