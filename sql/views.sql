CREATE OR REPLACE VIEW weekly_ai_coverage AS
SELECT
  YEARWEEK(authored_at, 3) AS year_week,
  repo,
  COUNT(DISTINCT CASE WHEN ai_authorship IN ('ai-authored', 'ai-assisted') THEN author END) AS ai_weekly_active_users,
  COUNT(DISTINCT author) AS total_active_users,
  ROUND(100 * COUNT(DISTINCT CASE WHEN ai_authorship IN ('ai-authored', 'ai-assisted') THEN author END) / NULLIF(COUNT(DISTINCT author), 0), 2) AS ai_user_coverage_pct,
  ROUND(100 * SUM(CASE WHEN ai_authorship IN ('ai-authored', 'ai-assisted') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS ai_commit_pct
FROM commit_ai_metrics
GROUP BY YEARWEEK(authored_at, 3), repo;

CREATE OR REPLACE VIEW weekly_ai_contribution AS
SELECT
  YEARWEEK(authored_at, 3) AS year_week,
  repo,
  SUM(lines_changed) AS total_lines,
  SUM(CASE WHEN ai_authorship = 'ai-authored' THEN lines_changed ELSE 0 END) AS ai_authored_lines,
  SUM(CASE WHEN ai_authorship = 'ai-assisted' THEN lines_changed ELSE 0 END) AS ai_assisted_lines,
  SUM(CASE WHEN ai_authorship = 'human' THEN lines_changed ELSE 0 END) AS human_lines,
  ROUND(100 * SUM(CASE WHEN ai_authorship = 'ai-authored' THEN lines_changed ELSE 0 END) / NULLIF(SUM(lines_changed), 0), 2) AS ai_authored_line_pct,
  ROUND(100 * SUM(CASE
    WHEN ai_authorship = 'ai-authored' THEN lines_changed
    WHEN ai_authorship = 'ai-assisted' THEN lines_changed * 0.5
    ELSE 0
  END) / NULLIF(SUM(lines_changed), 0), 2) AS ai_weighted_contribution_pct
FROM commit_ai_metrics
GROUP BY YEARWEEK(authored_at, 3), repo;

CREATE OR REPLACE VIEW weekly_ai_value AS
SELECT
  YEARWEEK(created_at, 3) AS year_week,
  repo,
  ai_authorship,
  COUNT(*) AS total_mrs,
  SUM(CASE WHEN state = 'merged' THEN 1 ELSE 0 END) AS merged_mrs,
  ROUND(100 * SUM(CASE WHEN state = 'merged' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS merge_rate_pct,
  ROUND(AVG(review_rounds), 2) AS avg_review_rounds,
  ROUND(AVG(TIMESTAMPDIFF(HOUR, created_at, merged_at)), 2) AS avg_cycle_time_hours,
  ROUND(100 * SUM(CASE WHEN reverted THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS revert_rate_pct,
  ROUND(AVG(linked_bugs), 2) AS avg_linked_bugs
FROM pr_ai_metrics
GROUP BY YEARWEEK(created_at, 3), repo, ai_authorship;

CREATE OR REPLACE VIEW audit_accuracy AS
SELECT
  DATE(audited_at) AS audit_date,
  repo,
  COUNT(*) AS audited_count,
  ROUND(100 * SUM(CASE WHEN labeled_authorship = true_authorship THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS authorship_accuracy_pct,
  ROUND(AVG(ABS(labeled_ratio - true_ratio)), 4) AS avg_ratio_abs_error
FROM audit_log
GROUP BY DATE(audited_at), repo;
