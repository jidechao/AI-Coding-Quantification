SELECT
  audit_date,
  repo,
  audited_count,
  authorship_accuracy_pct,
  avg_ratio_abs_error
FROM audit_accuracy
ORDER BY audit_date DESC, repo;
