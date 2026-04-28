CREATE TABLE IF NOT EXISTS pr_ai_metrics (
  pr_id VARCHAR(128) NOT NULL,
  repo VARCHAR(255) NOT NULL,
  author VARCHAR(255) NOT NULL,
  created_at DATETIME NULL,
  merged_at DATETIME NULL,
  state ENUM('open', 'merged', 'closed') NOT NULL DEFAULT 'open',
  ai_authorship ENUM('ai-authored', 'ai-assisted', 'human') NOT NULL DEFAULT 'human',
  ai_tool VARCHAR(64) NOT NULL DEFAULT 'none',
  ai_model VARCHAR(128) NOT NULL DEFAULT 'none',
  total_lines_added INT NOT NULL DEFAULT 0,
  total_lines_deleted INT NOT NULL DEFAULT 0,
  ai_lines INT NOT NULL DEFAULT 0,
  ai_assisted_lines INT NOT NULL DEFAULT 0,
  human_lines INT NOT NULL DEFAULT 0,
  review_rounds INT NOT NULL DEFAULT 0,
  first_review_at DATETIME NULL,
  reverted BOOLEAN NOT NULL DEFAULT FALSE,
  reverted_at DATETIME NULL,
  linked_bugs INT NOT NULL DEFAULT 0,
  ai_mode ENUM('auto', 'manual', 'hybrid') NOT NULL DEFAULT 'auto',
  audit_status ENUM('pending', 'passed', 'failed') NOT NULL DEFAULT 'pending',
  synced_at DATETIME NULL,
  PRIMARY KEY (repo, pr_id),
  INDEX idx_pr_created_at (created_at),
  INDEX idx_pr_ai_authorship (ai_authorship),
  INDEX idx_pr_author (author)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS commit_ai_metrics (
  commit_sha VARCHAR(64) NOT NULL,
  pr_id VARCHAR(128) NULL,
  repo VARCHAR(255) NOT NULL,
  author VARCHAR(255) NOT NULL,
  authored_at DATETIME NULL,
  ai_authorship ENUM('ai-authored', 'ai-assisted', 'human') NOT NULL DEFAULT 'human',
  ai_tool VARCHAR(64) NOT NULL DEFAULT 'none',
  ai_model VARCHAR(128) NOT NULL DEFAULT 'none',
  human_edit_ratio DECIMAL(5,4) NOT NULL DEFAULT 1.0000,
  lines_changed INT NOT NULL DEFAULT 0,
  ai_mode ENUM('auto', 'manual', 'hybrid') NOT NULL DEFAULT 'auto',
  synced_at DATETIME NULL,
  PRIMARY KEY (commit_sha),
  INDEX idx_commit_repo_time (repo, authored_at),
  INDEX idx_commit_author (author),
  INDEX idx_commit_authorship (ai_authorship)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_queue (
  repo VARCHAR(255) NOT NULL,
  pr_id VARCHAR(128) NOT NULL,
  sampled_at DATETIME NOT NULL,
  status ENUM('pending', 'assigned', 'completed', 'skipped') NOT NULL DEFAULT 'pending',
  assignee VARCHAR(255) NULL,
  reason VARCHAR(255) NULL,
  PRIMARY KEY (repo, pr_id),
  INDEX idx_audit_status (status, sampled_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGINT NOT NULL AUTO_INCREMENT,
  repo VARCHAR(255) NOT NULL,
  pr_id VARCHAR(128) NOT NULL,
  auditor VARCHAR(255) NOT NULL,
  labeled_authorship ENUM('ai-authored', 'ai-assisted', 'human') NOT NULL,
  true_authorship ENUM('ai-authored', 'ai-assisted', 'human') NOT NULL,
  labeled_ratio DECIMAL(5,4) NOT NULL,
  true_ratio DECIMAL(5,4) NOT NULL,
  audited_at DATETIME NOT NULL,
  notes TEXT NULL,
  PRIMARY KEY (id),
  INDEX idx_audit_log_pr (repo, pr_id),
  INDEX idx_audit_log_time (audited_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
