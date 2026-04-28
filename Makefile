PYTHON ?= python
PIP ?= pip

.PHONY: init test lint compose-up compose-down schema

init:
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

lint:
	$(PYTHON) -m compileall githooks/lib ci tests

compose-up:
	docker compose up -d mysql metabase

compose-down:
	docker compose down

schema:
	mysql -h 127.0.0.1 -P 3306 -u "$${MYSQL_USER:-ai_metrics}" -p"$${MYSQL_PASSWORD:-ai_metrics}" "$${MYSQL_DATABASE:-ai_metrics}" < sql/schema.sql
	mysql -h 127.0.0.1 -P 3306 -u "$${MYSQL_USER:-ai_metrics}" -p"$${MYSQL_PASSWORD:-ai_metrics}" "$${MYSQL_DATABASE:-ai_metrics}" < sql/views.sql
