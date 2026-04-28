SELECT
  year_week,
  repo,
  ai_authorship,
  total_mrs,
  merged_mrs,
  merge_rate_pct,
  avg_review_rounds,
  avg_cycle_time_hours,
  revert_rate_pct,
  avg_linked_bugs
FROM weekly_ai_value
ORDER BY year_week DESC, repo, ai_authorship;
