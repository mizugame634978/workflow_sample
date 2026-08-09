.DEFAULT_GOAL := help
SHELL := /bin/bash
PY := backend/.venv/bin/python

.PHONY: help setup setup-backend setup-frontend seed reset dev-backend dev-frontend test test-backend test-frontend e2e screenshots lint build clean

help: ## このヘルプを表示する
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: setup-backend setup-frontend seed ## 依存関係をインストールしてデモデータを投入する

setup-backend: ## Python 仮想環境を作成して依存関係を入れる
	cd backend && (command -v uv >/dev/null && uv venv .venv && uv pip install -e ".[dev]" \
		|| (python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"))

setup-frontend: ## npm 依存関係を入れる
	cd frontend && npm install

seed: ## デモデータを投入する（既存データがあればスキップ）
	cd backend && .venv/bin/python -m app.seed

reset: ## データベースを作り直してデモデータを投入する
	cd backend && .venv/bin/python -m app.seed --reset

dev-backend: ## API サーバーを起動する (http://localhost:8000)
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload --port 8000

dev-frontend: ## フロントエンドを起動する (http://localhost:3000)
	cd frontend && npm run dev

test: test-backend test-frontend ## 単体テストをすべて実行する

test-backend: ## バックエンドのテスト (pytest)
	cd backend && .venv/bin/python -m pytest

test-frontend: ## フロントエンドのユニットテスト (vitest)
	cd frontend && npm test

e2e: ## E2E テスト (Playwright)。サーバーは自動起動される
	cd frontend && npm run e2e

screenshots: ## 全画面のスクリーンショットを frontend/screenshots に出力する
	cd frontend && npx playwright test screenshots

lint: ## 静的解析と型チェック
	cd backend && .venv/bin/python -m ruff check app tests
	cd frontend && npm run typecheck

build: ## フロントエンドの本番ビルド
	cd frontend && npm run build

clean: ## 生成物を削除する
	rm -rf backend/*.db frontend/.next frontend/test-results frontend/playwright-report
