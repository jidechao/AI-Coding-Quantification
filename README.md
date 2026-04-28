# AI Coding Metrics

AI Coding Metrics is a GitLab-oriented toolkit for measuring AI coding adoption and outcomes across engineering teams. It provides commit trailers, Git hooks, heuristic authorship estimation, GitLab CI labeling, MySQL ETL jobs, Metabase dashboards, and audit workflows.

This project treats AI metrics as process signals, not individual performance metrics. Team and subgroup trends are the default reporting unit.

## What It Includes

- Git hooks for trailer injection, validation, and heuristic ratio estimation.
- Configurable authorship mode: `auto`, `manual`, or `hybrid`.
- GitLab CI scripts for merge request labeling and audit sampling.
- ETL scripts for syncing GitLab merge request and commit data into MySQL.
- MySQL schema, views, and ready-to-run SQL queries.
- Metabase local stack and dashboard export placeholders.
- Team rollout, deployment, FAQ, config, and audit documentation.

## Quick Start

```bash
make init
cp .ai-coding-config.yml.example .ai-coding-config.yml
docker compose up -d mysql metabase
```

Install hooks into a target repository:

```bash
./githooks/install.sh /path/to/target/repo
```

Run local checks:

```bash
make test
```

## Configuration

The repository-level config is `.ai-coding-config.yml`.

```yaml
authorship:
  mode: auto
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

## Trailer Contract

Every commit should contain:

```text
AI-Authorship: ai-authored | ai-assisted | human
AI-Tool: cursor | copilot | claude-code | none
AI-Model: <model-or-none>
Human-Edit-Ratio: 0-100
AI-Mode: auto | manual | hybrid
Audit-Status: pending | passed | failed
```

## Local Services

The Docker Compose stack starts:

- MySQL at `localhost:3306`
- Metabase at `http://localhost:3000`

Default credentials are development-only and should be changed before any shared deployment.

## Known Limits

The V1 `Human-Edit-Ratio` is a heuristic estimate, not an IDE event log. It combines commit-message signals, diff volume, and stylometry features. Expect imperfect labels and use the audit workflow to tune thresholds over time.
