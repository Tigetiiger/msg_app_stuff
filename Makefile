# optionally load .env so $(POSTGRES_*) vars are available to Makefile too
.PHONY: up down logs psql migrate seed
ifneq (,$(wildcard .env))
include .env
export
endif

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f db

psql:
	docker compose exec db sh -lc 'psql -U "$(POSTGRES_USER)" -d "$(POSTGRES_DB)"'

migrate:
	docker compose run --rm flyway

seed:
	docker compose exec -T db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -f /dev/stdin' < seed/dev_seed.sql
