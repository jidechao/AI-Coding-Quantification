SELECT
  year_week,
  repo,
  ai_weekly_active_users,
  total_active_users,
  ai_user_coverage_pct,
  ai_commit_pct
FROM weekly_ai_coverage
ORDER BY year_week DESC, repo;
