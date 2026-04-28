# AI Coding 度量系统部署与用户使用指南（产品经理版）

## 1. 这套系统解决什么问题

这套系统用于在团队推广 AI Coding 时，回答三个管理问题：

- **有没有人在用**：团队覆盖率、AI 周活跃用户、AI MR 占比。
- **AI 贡献了多少**：AI 代码行数占比、AI 加权贡献、工具和模型分布。
- **效果好不好**：MR 合入率、review 轮次、交付周期、缺陷反馈、返工信号。

它不是个人绩效工具。所有默认看板应按团队、小组、仓库维度展示，不建议用个人 AI 使用量做排名。

## 2. 角色分工

| 角色 | 主要职责 |
|---|---|
| 产品经理 / 推广负责人 | 定义试点范围、组织 Kickoff、解释指标、主持周度复盘 |
| 技术负责人 | 确认接入仓库、选择配置模式、处理高风险模块例外 |
| DevOps / 平台同学 | 部署 MySQL、Metabase、GitLab CI、定时 ETL |
| 开发者 | 正常提交代码，必要时确认 AI 三档标签 |
| 审计员 | 每周抽样检查标签是否合理，反馈阈值调整建议 |

## 3. 推荐试点节奏

### 第 0 周：准备

- 选择 1-3 个试点仓库。
- 选择 10-50 人范围内的试点团队。
- 明确这套指标只用于过程改进，不用于个人排名。
- 确认 GitLab token、MySQL、Metabase 的部署负责人。

### 第 1 周：接入与试运行

- 安装 Git hooks。
- 接入 GitLab CI。
- 启动 MySQL + Metabase。
- 每天检查数据是否入库。
- 不做团队结论，只看数据链路是否稳定。

### 第 2-4 周：看覆盖度

- 关注 AI 周活跃用户数、AI MR 占比、团队覆盖率。
- 每周抽样审计 10% MR。
- 收集开发者对标签、hook、提交流程的反馈。

### 第 5-8 周：看贡献度和质量

- 增加 AI 加权贡献、MR 合入率、review 轮次、周期时间。
- 对比 AI MR 与 human MR 的质量信号。
- 识别 AI 适合和不适合的场景。

### 第 9 周以后：形成推广策略

- 形成团队 AI Coding 使用手册。
- 输出 ROI 复盘。
- 决定是否扩大到更多仓库或团队。

## 4. 部署前检查清单

### 业务侧确认

- 已确定试点团队和仓库。
- 已向团队说明“不做个人排名”。
- 已确认敏感模块允许标记为 `human`。
- 已指定每周审计负责人。

### 技术侧确认

- GitLab 项目可配置 CI 变量。
- 有可用的 GitLab token，具备读取 MR、读取 commit、更新 MR label 的权限。
- 有 MySQL 实例，或可使用 `docker-compose.yml` 本地启动。
- 有 Metabase 实例，或可使用本地 Docker 启动。
- 试点仓库允许安装 Git hooks。

## 5. 部署步骤

### 步骤 1：启动本地服务

由 DevOps 或平台同学在部署机执行：

```bash
cp .ai-coding-config.yml.example .ai-coding-config.yml
docker compose up -d mysql metabase
```

启动后访问：

- Metabase: `http://localhost:3000`
- MySQL: `localhost:3306`

默认 MySQL 信息：

| 项 | 值 |
|---|---|
| Database | `ai_metrics` |
| User | `ai_metrics` |
| Password | `ai_metrics` |

正式环境需要修改默认密码。

### 步骤 2：初始化 Metabase

1. 打开 `http://localhost:3000`。
2. 创建管理员账号。
3. 添加 MySQL 数据库连接。
4. 数据库连接信息：
   - Host: `mysql`
   - Port: `3306`
   - Database: `ai_metrics`
   - User: `ai_metrics`
   - Password: `ai_metrics`

### 步骤 3：导入看板

配置 Metabase 管理员账号后执行：

```bash
set METABASE_USER=admin@example.com
set METABASE_PASSWORD=your-password
set METABASE_DATABASE=ai_metrics
python dashboard/metabase/import_dashboards.py
```

导入后会生成 4 个看板：

- `AI Coding Coverage`
- `AI Coding Contribution`
- `AI Coding Value`
- `AI Coding Audit`

### 步骤 4：给试点仓库安装 hooks

在每个目标仓库执行：

```bash
/path/to/ai-coding-metrics/githooks/install.sh /path/to/target/repo
```

同时在目标仓库根目录放置 `.ai-coding-config.yml`。

推荐试点初期配置：

```yaml
authorship:
  mode: hybrid
  default_tool: cursor
  default_model: none

heuristic:
  weights:
    commit_message_keywords: 0.4
    diff_volume: 0.3
    stylometry: 0.3
  thresholds:
    ai_authored: 0.7
    ai_assisted: 0.3

audit:
  enabled: true
  sample_rate: 0.1
```

模式说明：

| 模式 | 适合阶段 | 行为 |
|---|---|---|
| `auto` | 稳定运行后 | 系统自动估算三档和人工编辑占比 |
| `manual` | 团队强共识阶段 | 开发者每次提交时手动选择三档 |
| `hybrid` | 试点推荐 | 系统先估算，开发者可确认或覆盖 |

### 步骤 5：接入 GitLab CI

将模板复制到目标仓库：

```bash
cp ci/.gitlab-ci.yml.template /path/to/target/repo/.gitlab-ci.yml
```

在 GitLab CI 变量里配置：

| 变量 | 用途 |
|---|---|
| `GITLAB_TOKEN` | 更新 MR label |
| `AI_AUDIT_SAMPLE_RATE` | 抽样审计比例，建议 `0.1` |
| `MYSQL_HOST` | 可选，配置后 CI 可写入 audit queue |
| `MYSQL_PORT` | 可选，默认 `3306` |
| `MYSQL_DATABASE` | 可选，默认 `ai_metrics` |
| `MYSQL_USER` | 可选 |
| `MYSQL_PASSWORD` | 可选 |

### 步骤 6：配置定时 ETL

每天定时同步 MR 和 commit 数据：

```bash
python ci/etl/pull_mr.py --project-id group%2Fproject --output mrs.json
python ci/etl/load_mysql.py --table pr_ai_metrics --input mrs.json

python ci/etl/pull_commit.py --project-id group%2Fproject --ref-name main --output commits.json
python ci/etl/load_mysql.py --table commit_ai_metrics --input commits.json
```

`project-id` 需要使用 GitLab URL encode，例如 `group/project` 写成 `group%2Fproject`。

## 6. 开发者如何使用

### 日常开发流程

开发者正常写代码、提交 MR，不需要额外填写表单。

提交时系统会自动添加 commit trailer：

```text
AI-Authorship: ai-assisted
AI-Tool: cursor
AI-Model: none
Human-Edit-Ratio: 50
AI-Mode: hybrid
Audit-Status: pending
```

如果使用 `hybrid` 模式，系统会先估算标签，开发者可以接受或覆盖。

### 三档怎么选

| 标签 | 什么时候选 |
|---|---|
| `ai-authored` | AI 生成了大部分实现，人主要 review 和少量修改 |
| `ai-assisted` | AI 参与了设计、起草或改写，但人做了明显重构 |
| `human` | 主要是人写，AI 只用于解释、搜索、少量补全或未参与代码生成 |

### 不确定时怎么办

选择更保守的一档。

例如：

- 不确定 `ai-authored` 还是 `ai-assisted`，选 `ai-assisted`。
- 不确定 `ai-assisted` 还是 `human`，选 `human`。

## 7. 产品经理如何看板

### Coverage 看板：看推广广度

适合每周例会查看。

重点指标：

| 指标 | 怎么解读 |
|---|---|
| AI Weekly Active Users | 本周真正用过 AI Coding 的人数 |
| AI User Coverage % | 团队中有多少人开始使用 AI |
| AI Commit % | commit 维度的 AI 使用占比 |

推荐解读：

- 第 1-2 周只看趋势，不做评价。
- 如果覆盖率低，优先解决工具安装、培训、场景选择问题。
- 如果覆盖率突然异常升高，要结合审计看是否存在标签失真。

### Contribution 看板：看 AI 贡献

适合第 3 周以后查看。

重点指标：

| 指标 | 怎么解读 |
|---|---|
| AI Weighted Contribution % | AI 加权贡献，`ai-authored=1.0`，`ai-assisted=0.5` |
| AI Authored Line % | AI 主导代码行数占比 |
| Lines by Authorship | AI、人类、混合贡献分布 |

推荐解读：

- 不要只看行数，行数不是价值。
- 如果 AI 行数很高但 review 轮次也很高，说明质量或适用场景需要复盘。
- 如果 AI 贡献集中在少数仓库，要分析是场景差异还是推广不均。

### Value 看板：看效果

适合第 5 周以后查看。

重点指标：

| 指标 | 怎么解读 |
|---|---|
| Merge Rate % | AI MR 是否能稳定合入 |
| Average Review Rounds | AI MR 是否增加 review 成本 |
| Average Cycle Time Hours | AI 是否缩短从创建到合入的时间 |
| Revert Rate % | AI MR 是否带来更多返工 |

推荐解读：

- AI MR 合入率不应明显低于 human MR。
- AI MR review 轮次如果长期偏高，说明提示词、任务拆分或测试不足。
- 周期时间下降但返工上升，不能视为推广成功。

### Audit 看板：看数据可信度

适合推广负责人和技术负责人查看。

重点指标：

| 指标 | 怎么解读 |
|---|---|
| Authorship Accuracy % | 自动/人工标签与审计结果的一致率 |
| Average Ratio Error | `Human-Edit-Ratio` 的平均偏差 |
| Audited Count | 已审计样本量 |

推荐解读：

- 准确率低于 70% 时，不建议对外汇报细粒度结论。
- 样本量太小时，只能看趋势，不能下强结论。
- 审计结果要用于调阈值，而不是追责个人。

## 8. 周会使用模板

建议每周固定 20 分钟：

1. 看 Coverage：本周是否有更多人开始使用 AI。
2. 看 Contribution：AI 贡献是否来自真实开发任务。
3. 看 Value：合入率、review 轮次、周期时间是否健康。
4. 看 Audit：数据是否可信，有没有标签偏差。
5. 确定下周动作：培训、场景选择、阈值调整或风险复盘。

周报可以使用以下结构：

```text
本周 AI Coding 推广结论：
- 覆盖度：
- 贡献度：
- 质量与效率：
- 审计发现：
- 下周动作：
```

## 9. 风险与处理方式

| 风险 | 表现 | 处理方式 |
|---|---|---|
| 指标被误解为绩效 | 开发者担心被监控 | Kickoff 明确只看团队趋势，不做个人排名 |
| 标签失真 | AI 占比异常升高 | 增加抽样审计，调低自动信任度 |
| AI PR 质量差 | review 轮次高、返工率高 | 收敛到更适合 AI 的任务类型 |
| 敏感代码误用 AI | 安全或合规模块使用 AI | 允许 opt-out，标 `human` 并说明原因 |
| 看板无数据 | ETL 未运行或 GitLab token 权限不足 | 检查 CI 变量、ETL 日志、MySQL 连接 |

## 10. 验收标准

产品经理可以按下面清单确认系统是否完成上线：

- 试点仓库 commit 能自动带 AI trailer。
- 创建 MR 后能自动打 `ai-authorship::*` label。
- MySQL 中有 `pr_ai_metrics` 和 `commit_ai_metrics` 数据。
- Metabase 中 4 个看板可以正常打开。
- 每周能生成审计样本。
- 团队已完成三档定义对齐。
- 周会能基于 Coverage、Contribution、Value、Audit 四类看板讨论。

## 11. 推荐管理原则

- 先看趋势，再看结论。
- 先看团队，再看个人。
- 先看质量，再看数量。
- 先试点，再推广。
- 先承认误差，再优化算法。

这套系统的价值不在于精确判断每一行代码是谁写的，而在于持续回答：AI Coding 是否被团队采用、是否贡献了真实产出、是否没有牺牲质量。
