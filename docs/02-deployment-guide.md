# 部署指南

## 1. 启动本地看板服务

```bash
cp .ai-coding-config.yml.example .ai-coding-config.yml
docker compose up -d mysql metabase
```

打开 `http://localhost:3000` 初始化 Metabase，并连接 MySQL：

- Host: `mysql`
- Port: `3306`
- Database: `ai_metrics`
- User: `ai_metrics`
- Password: `ai_metrics`

## 2. 安装 Git Hooks

在目标仓库执行：

```bash
/path/to/ai-coding-metrics/githooks/install.sh /path/to/target/repo
```

目标仓库根目录放置 `.ai-coding-config.yml`。

## 3. 接入 GitLab CI

复制模板：

```bash
cp ci/.gitlab-ci.yml.template /path/to/target/repo/.gitlab-ci.yml
```

在 GitLab CI 变量中配置：

- `GITLAB_TOKEN`: 有 MR label 更新权限的 token
- `AI_AUDIT_SAMPLE_RATE`: 默认 `0.1`

## 4. 同步数据到 MySQL

```bash
python ci/etl/pull_mr.py --project-id group%2Fproject --output mrs.json
python ci/etl/load_mysql.py --table pr_ai_metrics --input mrs.json

python ci/etl/pull_commit.py --project-id group%2Fproject --ref-name main --output commits.json
python ci/etl/load_mysql.py --table commit_ai_metrics --input commits.json
```

## 5. 创建看板

在 Metabase 中使用 `sql/queries/` 下的 SQL 创建问题，并按 `dashboard/metabase/dashboards/*.json` 的结构组合成 4 个 dashboard。
