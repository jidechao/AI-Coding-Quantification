SELECT
  year_week,
  repo,
  total_lines,
  ai_authored_lines,
  ai_assisted_lines,
  human_lines,
  ai_authored_line_pct,
  ai_weighted_contribution_pct
FROM weekly_ai_contribution
ORDER BY year_week DESC, repo;
