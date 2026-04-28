# 配置参考

配置文件：`.ai-coding-config.yml`

## authorship

```yaml
authorship:
  mode: auto
  default_tool: cursor
  default_model: none
```

- `mode`: `auto`、`manual` 或 `hybrid`。
- `default_tool`: 缺省工具名。
- `default_model`: 缺省模型名。

## heuristic

```yaml
heuristic:
  weights:
    commit_message_keywords: 0.4
    diff_volume: 0.3
    stylometry: 0.3
  thresholds:
    ai_authored: 0.7
    ai_assisted: 0.3
```

- `weights`: 三类信号的加权比例。
- `thresholds.ai_authored`: 达到该概率时归为 `ai-authored`。
- `thresholds.ai_assisted`: 达到该概率时归为 `ai-assisted`。

## audit

```yaml
audit:
  enabled: true
  sample_rate: 0.1
  minimum_samples_per_week: 10
```

- `sample_rate`: MR 抽样比例。
- `minimum_samples_per_week`: 小样本团队建议设置最低审计量。

## database

ETL 默认读取环境变量：

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
