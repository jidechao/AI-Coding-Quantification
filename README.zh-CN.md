# AI Coding Metrics

AI Coding Metrics 是一套面向 GitLab 团队的 AI Coding 推广度量工具，用于统计团队在使用 Cursor、Copilot、Claude Code 等工具时的采用情况、代码贡献和交付质量信号。

这套系统的定位是**过程指标工具**，不是个人绩效工具。默认建议按团队、小组、仓库维度看趋势，不建议用个人 AI 使用量做排名。

## 功能概览

- Git Hooks：自动注入、校验 commit trailer，并估算 `Human-Edit-Ratio`。
- 三种标注模式：`auto`、`manual`、`hybrid`。
- 启发式估算：结合 commit message、diff 体量和代码风格信号判断 AI 参与程度。
- GitLab CI：自动解析 commit trailer，给 MR 打 `ai-authorship::*` label。
- 抽样审计：按比例抽样 MR，校准自动估算的准确性。
- ETL：从 GitLab 拉取 MR 和 commit 数据，写入 MySQL。
- SQL 与看板：提供 MySQL 表结构、视图、查询和 Metabase dashboard。
- 文档：包含团队对齐、部署、FAQ、配置、审计和产品经理使用指南。

## 快速开始

### 1. 创建配置

```bash
cp .ai-coding-config.yml.example .ai-coding-config.yml
```

### 2. 启动本地服务

```bash
docker compose up -d mysql metabase
```

默认服务：

- MySQL: `localhost:3306`
- Metabase: `http://localhost:3000`

默认 MySQL 账号：

| 项 | 值 |
|---|---|
| Database | `ai_metrics` |
| User | `ai_metrics` |
| Password | `ai_metrics` |

正式环境请修改默认密码。

### 3. 安装依赖

建议使用虚拟环境：

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. 运行测试

```bash
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
```

## 接入目标仓库

### 安装 Git Hooks

在目标仓库执行：

```bash
./githooks/install.sh /path/to/target/repo
```

安装后，目标仓库的 commit 会被要求包含以下 trailer：

```text
AI-Authorship: ai-authored | ai-assisted | human
AI-Tool: cursor | copilot | claude-code | none
AI-Model: <model-or-none>
Human-Edit-Ratio: 0-100
AI-Mode: auto | manual | hybrid
Audit-Status: pending | passed | failed
```

### 配置 GitLab CI

复制模板到目标仓库：

```bash
cp ci/.gitlab-ci.yml.template /path/to/target/repo/.gitlab-ci.yml
```

需要配置的 GitLab CI 变量：

| 变量 | 说明 |
|---|---|
| `GITLAB_TOKEN` | 用于更新 MR label |
| `AI_AUDIT_SAMPLE_RATE` | 抽样审计比例，默认 `0.1` |
| `MYSQL_HOST` | 可选，配置后可写入审计队列 |
| `MYSQL_PORT` | 可选，默认 `3306` |
| `MYSQL_DATABASE` | 可选，默认 `ai_metrics` |
| `MYSQL_USER` | 可选 |
| `MYSQL_PASSWORD` | 可选 |

## 配置说明

仓库级配置文件是 `.ai-coding-config.yml`。

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

### 三种模式

| 模式 | 说明 | 推荐场景 |
|---|---|---|
| `auto` | 系统自动估算三档和人工编辑占比 | 稳定运行后 |
| `manual` | 开发者提交时手动选择三档 | 团队强共识或高准确率要求 |
| `hybrid` | 系统先估算，开发者可确认或覆盖 | 试点阶段推荐 |

## 三档定义

| 标签 | 定义 | 参考标准 |
|---|---|---|
| `ai-authored` | AI 主导生成，人类主要 review、微调和验收 | 人类修改占比约 0%-30% |
| `ai-assisted` | AI 起草或辅助，人类进行了明显改写和补充 | 人类修改占比约 30%-70% |
| `human` | 主要由人类完成，AI 仅用于补全、查询、解释或未实际生成代码 | 人类修改占比约 70%-100% |

不确定时建议选择更保守的一档。

## 数据同步

同步 MR 数据：

```bash
python ci/etl/pull_mr.py --project-id group%2Fproject --output mrs.json
python ci/etl/load_mysql.py --table pr_ai_metrics --input mrs.json
```

同步 commit 数据：

```bash
python ci/etl/pull_commit.py --project-id group%2Fproject --ref-name main --output commits.json
python ci/etl/load_mysql.py --table commit_ai_metrics --input commits.json
```

`project-id` 需要使用 GitLab URL encode，例如 `group/project` 写成 `group%2Fproject`。

## Metabase 看板

启动 Metabase 后，先在网页中完成初始化并添加 MySQL 数据库，然后导入看板：

```bash
set METABASE_USER=admin@example.com
set METABASE_PASSWORD=your-password
set METABASE_DATABASE=ai_metrics
python dashboard/metabase/import_dashboards.py
```

系统提供 4 类看板：

- `AI Coding Coverage`：覆盖度，看团队是否开始使用 AI。
- `AI Coding Contribution`：贡献度，看 AI 对代码产出的贡献。
- `AI Coding Value`：价值度，看合入率、review 轮次、周期时间和返工信号。
- `AI Coding Audit`：审计，看自动估算是否可信。

## 主要目录

```text
.
├── githooks/                 # Git hooks 与启发式估算
├── ci/                       # GitLab CI、MR label、抽样审计、ETL
├── sql/                      # MySQL DDL、视图和查询
├── dashboard/                # Metabase dashboard 配置与导入脚本
├── docs/                     # 团队对齐、部署、FAQ、审计、PM 指南
├── tests/                    # 单元测试和端到端 fixture
├── docker-compose.yml        # MySQL + Metabase 本地服务
└── .ai-coding-config.yml.example
```

## 推荐阅读

- `docs/01-team-alignment.md`：团队三档定义对齐。
- `docs/02-deployment-guide.md`：工程部署步骤。
- `docs/03-faq.md`：常见问题。
- `docs/04-config-reference.md`：配置项说明。
- `docs/05-audit-process.md`：抽样审计流程。
- `docs/06-pm-deployment-user-guide.md`：面向产品经理的部署与使用指南。

## 已知限制

- V1 的 `Human-Edit-Ratio` 是启发式估算，不是 IDE 事件级精确记录。
- 启发式结果会有误差，需要通过抽样审计持续校准。
- Git hooks 需要在每个目标仓库安装。
- Metabase 看板需要先完成数据库连接后再导入。

## 管理原则

- 这是过程指标，不是绩效指标。
- 不按个人 AI PR 数或 AI 行数排名。
- 先看团队趋势，再看具体问题。
- 先看质量，再看数量。
- 标签不确定时选择保守档位。
