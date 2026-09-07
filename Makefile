.PHONY: build up down test calibrate blind demo \
       attack-all attack-forgery-a attack-forgery-b attack-replay \
       attack-impersonation attack-unauthorized attack-channel \
       attack-ledger verify-ledger logs ps

# ── Docker lifecycle ──────────────────────────────────────────
build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs --tail=50

logs-api:
	docker compose logs --tail=100 qsentinel-api

logs-attacker:
	docker compose logs --tail=100 qsentinel-attacker

logs-dashboard:
	docker compose logs --tail=100 qsentinel-dashboard

# ── Tests ─────────────────────────────────────────────────────
test:
	docker compose exec qsentinel-api pytest tests/ -v

# ── Calibration & Evaluation ─────────────────────────────────
calibrate:
	docker compose exec qsentinel-api python -m src.calibration.grid_search

blind:
	docker compose exec qsentinel-api python -m experiments.blind_eval

# ── Attack Harness ────────────────────────────────────────────
attack-all:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack all

attack-forgery-a:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack forgery-a

attack-forgery-b:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack forgery-b

attack-replay:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack replay

attack-impersonation:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack impersonation

attack-unauthorized:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack unauthorized

attack-channel:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack channel

attack-ledger:
	docker compose exec qsentinel-attacker python -m attacker.runner --attack ledger-tamper

verify-ledger:
	docker compose exec qsentinel-attacker python -c \
		"from attacker.client import verify_chain; import json; print(json.dumps(verify_chain(), indent=2))"

# ── Demo ──────────────────────────────────────────────────────
demo:
	@echo "Dashboard:  http://localhost:8501"
	@echo "RDP/Webtop: http://localhost:3389"
	@echo "API docs:   http://qsentinel-api:8000/docs  (from inside RDP)"
