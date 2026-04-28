# AI Coding 推广效果度量方案

> 用于在团队内推广 AI Coding 时，区分 AI 与人类的代码贡献，并系统化度量推广效果。
> 核心原则：**自动化 > 人工申报**，**多维度 > 单一计数**，**过程指标 > 绩效指标**。

---

## 一、整体架构

```text
开发者写代码
   ↓
[Cursor/Copilot] → 提交时自动注入 trailer
   ↓
[Git Hook]      → 校验 trailer 合规
   ↓
[CI/PR Bot]     → 解析 trailer，自动打 PR Label
   ↓
[数据采集]      → 每日同步到数据仓库
   ↓
[指标看板]      → 覆盖度 / 贡献度 / 价值度三层
```

---

## 二、标签规范（三档分类）

### 1. Commit Trailer 规范

每个 commit 末尾必须带：

```text
AI-Authorship: ai-authored | ai-assisted | human
AI-Tool: cursor | copilot | claude-code | none
AI-Model: gpt-5.3-codex | claude-4.6-sonnet | none
Human-Edit-Ratio: 0-100         # 人类修改占比，AI 工具自动估算
```

### 2. 三档定义（必须在团队对齐文档里写死）

| 标签 | 定义 | 量化标准 |
|---|---|---|
| `ai-authored` | AI 主导，人类仅 review 或微调 | 人类修改 ≤ 30% |
| `ai-assisted` | AI 起草 + 人类深度改写 | 人类修改 30%–70% |
| `human` | 纯人写，或 AI 仅做补全/查文档 | 人类修改 ≥ 70%，或未实际生成代码 |

> 边界用 **人类修改占比**（Human-Edit-Ratio）来判定，避免主观争论。

### 3. 分支命名规范（辅助）

- `ai/<topic>`：AI 主导分支
- `feat/<topic>` / `fix/<topic>`：人类主导分支
- 混合分支不强制，看每个 commit 的 trailer

### 4. PR Label（自动打）

CI 解析 PR 内所有 commit 的 trailer，按**代码行数加权**给 PR 打标：

- `ai-authored`：≥70% 行数来自 ai-authored commit
- `ai-assisted`：30%–70%
- `human`：<30%

---

## 三、自动化落地（关键，避免人工申报失真）

### 1. Cursor 侧（推广重点）

通过 `.cursor/rules/commit.mdc` 或 hook 配置，让 Cursor 提交时自动写入 trailer：

```text
AI-Authorship: ai-authored
AI-Tool: cursor
AI-Model: <当前模型>
Human-Edit-Ratio: <Cursor 自己估算>
```

**关键点**：Cursor Agent 模式下生成的 commit，默认全部标 `ai-authored`；用户事后改了多少代码，由后续 hook 重新评估。

### 2. Git Hook 侧（强制兜底）

在仓库 `.githooks/` 放三个 hook：

- **`prepare-commit-msg`**：自动检测
  - 如果 commit 包含 AI 工具的 staged 区改动 → 默认补 `AI-Authorship: ai-assisted`
  - 让用户在编辑器里确认/修改
- **`commit-msg`**：强制校验
  - 没有 `AI-Authorship` trailer → 拒绝提交，给出说明
- **`post-commit`（可选）**：自动估算 Human-Edit-Ratio
  - 对比 AI 工具最近一次写入的内容 vs 实际 commit 的内容，计算编辑距离

### 3. CI / PR Bot 侧

PR 创建时，机器人脚本：

1. 拉取 PR 所有 commit
2. 解析每个 commit 的 trailer
3. 按行数加权计算 PR 的总 Authorship
4. 自动打 GitHub/GitLab Label
5. 校验：如果有 commit 缺 trailer → PR check failed
6. 在 PR 描述里贴一份"AI 贡献摘要"

### 4. 数据采集

每天定时任务（cron / GitHub Actions）：

- 拉取所有 merged PR
- 提取 trailer + Label + 行数 + review 数据
- 写入数据仓库（哪怕是一张 Google Sheet 起步也行）

---

## 四、指标看板（三层）

### 第 1 层：覆盖度（推广广度）

| 指标 | 计算方式 | 目标值（示例） |
|---|---|---|
| AI 周活跃用户数 | 本周提交过 ai-authored/ai-assisted commit 的人 | ≥ 80% 团队 |
| AI PR 占比 | (ai-authored + ai-assisted) PR / 总 PR | ≥ 50% |
| AI commit 占比 | 同上，commit 维度 | ≥ 60% |
| 团队覆盖率 | 至少用过 1 次 AI 的人 / 团队总人数 | ≥ 95% |

### 第 2 层：贡献度（AI 真实产出）

| 指标 | 计算方式 |
|---|---|
| AI 代码行数占比 | ai-authored 行数 / 总行数（核心指标） |
| AI 加权贡献 | Σ(行数 × 权重)，ai-authored=1.0, ai-assisted=0.5, human=0 |
| 平均 PR 大小 | AI PR vs 人类 PR 的 changed lines 中位数 |
| AI 工具分布 | cursor / copilot / claude-code 各占比 |
| 模型分布 | 哪些模型被用得多 |

### 第 3 层：价值度（效果验证，最重要）

| 指标 | 计算方式 | 含义 |
|---|---|---|
| AI PR 合入率 | merged AI PR / 提交的 AI PR | 质量信号 |
| AI PR review 轮次 | AI PR 平均 review iteration 数 vs 人类 PR | 一次过比例 |
| AI PR 周期时间 | 创建 → 合入耗时，AI vs 人类 | 效率信号 |
| 30 天 churn 率 | AI 代码 30 天内被改/删的比例 | 代码寿命 |
| 缺陷反馈率 | AI PR 引入 bug 数 / AI PR 总数 | 质量底线 |
| 人均周 PR 数 | 推广前 vs 推广后 | 真实 ROI |
| 人均周 changed lines | 推广前 vs 推广后 | 真实 ROI |

---

## 五、看板示例字段表（可直接建表）

### 表：`pr_ai_metrics`

```text
pr_id              string
repo               string
author             string
created_at         datetime
merged_at          datetime
state              enum: open/merged/closed
ai_authorship      enum: ai-authored/ai-assisted/human
ai_tool            string
ai_model           string
total_lines_added  int
total_lines_deleted int
ai_lines           int     -- 来自 ai-authored commit 的行数
ai_assisted_lines  int
human_lines        int
review_rounds      int
first_review_at    datetime
reverted           bool
reverted_at        datetime
linked_bugs        int     -- 关联的缺陷单数量
```

### 表：`commit_ai_metrics`

```text
commit_sha         string
pr_id              string
author             string
authored_at        datetime
ai_authorship      enum
ai_tool            string
ai_model           string
human_edit_ratio   float   -- 0~1
lines_changed      int
```

有了这两张表，所有上面的指标都能用 SQL 算出来。

---

## 六、推广路线图（4 阶段）

### 阶段 1：规范 + 工具（第 1-2 周）

- 团队对齐三档分类定义
- 部署 Git Hook + Cursor 配置
- 建数据采集脚本，跑通端到端
- **目标**：trailer 覆盖率 ≥ 95%

### 阶段 2：覆盖度爬坡（第 3-6 周）

- 看板上线，每周同步
- 重点看：周活跃用户、AI PR 占比
- 抽样 10% PR 人工校验标签准确性
- **目标**：AI PR 占比 ≥ 30%

### 阶段 3：贡献度深化（第 7-12 周）

- 加入代码行数加权指标
- 开始看质量信号（合入率、review 轮次）
- 识别"AI 不擅长的场景"，反向优化推广策略
- **目标**：AI 加权贡献 ≥ 40%，AI PR 合入率不低于人类 PR

### 阶段 4：价值验证（第 13-24 周）

- 对比推广前后的人均交付速度、缺陷率
- 出 ROI 报告：节省了多少人天
- 形成"AI Coding 适用场景手册"
- **目标**：人均周交付 PR 数 +30%，缺陷率不上升

---

## 七、避坑清单（强烈建议提前对齐）

1. **明确"这是过程指标，不是绩效指标"**
   写进团队公约、推广文档、Kickoff 会议。否则数据全是噪声。
2. **不要按"AI PR 数量"排名个人**
   只看团队/小组级别趋势，避免冲指标。
3. **设质量红线**
   如果某月 AI PR 缺陷率比人类 PR 高 50%，自动触发复盘，调整推广策略。
4. **每月抽样审计**
   随机抽 10-20 个 PR，人工核对 trailer 是否真实，公示审计结果。
5. **保留 opt-out 通道**
   敏感模块（密钥、安全相关、合规相关）允许标 `human` 并跳过 AI。
6. **数据脱敏**
   看板对外只展示团队聚合数据，个人数据仅本人和直接 leader 可见。

---

## 八、最小启动版本（本周即可跑起来）

如果不想一上来就搞全套，**最小可用版本只需要 3 件事**：

1. **Commit trailer 规范 + Git Hook 强制校验**（半天工作量）
2. **每周用 `git log --grep` 跑个脚本**，统计 ai-authored / ai-assisted / human 三档的 commit 数和行数（半天）
3. **每周对齐会贴一次数据**（持续）

剩下的（PR Label、看板、CI 自动化）等团队习惯了再上。**先让标签先转起来，比一次性追求完美架构更重要。**

---

## 九、后续物料清单

- [ ] 三档分类对齐文档模板（团队 Kickoff 用）
- [ ] Git Hook 脚本设计（`prepare-commit-msg` / `commit-msg` / `post-commit`）
- [ ] CI 解析 + 自动打 Label 脚本（GitHub Actions / GitLab CI）
- [ ] 看板 SQL 查询集（基于上面两张表，覆盖三层全部指标）
- [ ] 推广 Kickoff 会话术 + FAQ（应对"被监视"心理顾虑）

---

## 附录 A：常用查询示例

### A.1 本周 AI PR 占比

```sql
SELECT
  ai_authorship,
  COUNT(*) AS pr_count,
  ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM pr_ai_metrics
WHERE created_at >= DATE_TRUNC('week', CURRENT_DATE)
GROUP BY ai_authorship;
```

### A.2 AI 加权代码贡献

```sql
SELECT
  DATE_TRUNC('week', authored_at) AS week,
  SUM(CASE ai_authorship
        WHEN 'ai-authored' THEN lines_changed * 1.0
        WHEN 'ai-assisted' THEN lines_changed * 0.5
        ELSE 0
      END) AS ai_weighted_lines,
  SUM(lines_changed) AS total_lines,
  ROUND(100.0 * SUM(CASE ai_authorship
                      WHEN 'ai-authored' THEN lines_changed * 1.0
                      WHEN 'ai-assisted' THEN lines_changed * 0.5
                      ELSE 0
                    END) / NULLIF(SUM(lines_changed), 0), 2) AS ai_contribution_pct
FROM commit_ai_metrics
GROUP BY 1
ORDER BY 1 DESC;
```

### A.3 AI vs 人类 PR 合入率对比

```sql
SELECT
  ai_authorship,
  COUNT(*) AS total_prs,
  SUM(CASE WHEN state = 'merged' THEN 1 ELSE 0 END) AS merged_prs,
  ROUND(100.0 * SUM(CASE WHEN state = 'merged' THEN 1 ELSE 0 END) / COUNT(*), 2) AS merge_rate,
  AVG(review_rounds) AS avg_review_rounds
FROM pr_ai_metrics
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY ai_authorship;
```

---

## 附录 B：Trailer 校验正则（供 Hook 使用）

```text
^AI-Authorship:\s*(ai-authored|ai-assisted|human)\s*$
^AI-Tool:\s*(cursor|copilot|claude-code|none)\s*$
^AI-Model:\s*[\w\-\.]+\s*$
^Human-Edit-Ratio:\s*(100|[1-9]?\d)\s*$
```
