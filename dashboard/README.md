# Metabase Dashboards

Start the local stack:

```bash
docker compose up -d mysql metabase
```

Open `http://localhost:3000`, create the first admin user, then add a MySQL database:

- Host: `mysql`
- Port: `3306`
- Database: `ai_metrics`
- User: `ai_metrics`
- Password: `ai_metrics`

The JSON files in `metabase/dashboards/` are dashboard specifications consumed by `metabase/import_dashboards.py`.

Recommended dashboards:

- `coverage.json`: adoption breadth.
- `contribution.json`: AI code contribution.
- `value.json`: delivery and quality signals.
- `audit.json`: heuristic accuracy and audit queue health.

Import them after Metabase is initialized and the MySQL database is added:

```bash
set METABASE_USER=admin@example.com
set METABASE_PASSWORD=your-password
set METABASE_DATABASE=ai_metrics
python dashboard/metabase/import_dashboards.py
```
