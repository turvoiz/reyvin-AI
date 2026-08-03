# Reyvin Workspace Intelligence Engine

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOST       ?= 127.0.0.1
PORT       ?= 8000
WORKSPACE  ?= .
PROJECT    ?= default
MODEL      ?= qwen
VERSION    ?= 0.1.0
EXT_DIR    := vscode-extension
VSIX       := $(EXT_DIR)/reyvin-workspace-$(VERSION).vsix
PYTHON     := .venv/bin/python
UVCORN     := .venv/bin/uvicorn
LOG_FILE   := /tmp/reyvin-server.log

API        := http://$(HOST):$(PORT)/api/v1

.PHONY: help install backend-install extension-install run run-bg stop status \
        test test-backend test-extension check lint package install-extension \
        analyze health ollama

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

docs: ## Show the helper guide
	@cat HELPER.md

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

install: backend-install extension-install ## Install backend + extension dependencies

backend-install: ## Install backend dependencies (uv)
	uv sync

extension-install: ## Install extension dependencies (npm)
	cd $(EXT_DIR) && npm install

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

run: ## Run the backend in the foreground (Ctrl+C to stop)
	$(UVCORN) app.main:app --host $(HOST) --port $(PORT)

run-bg: ## Run the backend in the background (logs to $(LOG_FILE))
	@if curl -s $(API)/health >/dev/null 2>&1; then \
		echo "Reyvin API already running on $(API)"; \
	else \
		nohup $(UVCORN) app.main:app --host $(HOST) --port $(PORT) > $(LOG_FILE) 2>&1 & \
		echo "Started Reyvin API on $(API) (PID $$!)"; \
		echo "Logs: $(LOG_FILE)"; \
		sleep 2; \
	fi

stop: ## Stop the background backend
	@PID=$$(lsof -ti tcp:$(PORT) 2>/dev/null); \
	if [ -n "$$PID" ]; then \
		kill $$PID && echo "Stopped Reyvin API (PID $$PID)"; \
	else \
		echo "No Reyvin API running on port $(PORT)"; \
	fi

status: health ollama ## Show backend and LLM status

health: ## Check the backend health
	@if curl -s $(API)/health >/dev/null 2>&1; then \
		echo "Reyvin API: UP ($(API))"; \
		curl -s $(API)/workspace/stats; echo; \
	else \
		echo "Reyvin API: DOWN ($(API)) — run 'make run-bg'"; \
	fi

ollama: ## Check Ollama availability and installed models
	@if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then \
		echo "Ollama: UP"; \
		curl -s http://localhost:11434/api/tags | $(PYTHON) -c \
			"import json,sys; print('Models:', ', '.join(m['name'] for m in json.load(sys.stdin)['models']))"; \
	else \
		echo "Ollama: DOWN — start it with 'ollama serve'"; \
	fi

# ---------------------------------------------------------------------------
# Tests and quality
# ---------------------------------------------------------------------------

test: test-backend test-extension ## Run all tests

test-backend: ## Run backend tests
	$(PYTHON) -m pytest tests/ -q

test-extension: ## Run extension unit tests
	cd $(EXT_DIR) && npm test

check: ## Typecheck the extension
	cd $(EXT_DIR) && npm run check

lint: ## Lint the backend (ruff)
	.venv/bin/ruff check app tests

# ---------------------------------------------------------------------------
# Extension
# ---------------------------------------------------------------------------

package: ## Build the extension .vsix package
	cd $(EXT_DIR) && npm run package

install-extension: package ## Build and install the extension into VS Code
	code --install-extension "$(VSIX)" --force

# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

analyze: ## Register a project: make analyze WORKSPACE=/path/to/repo [PROJECT=name]
	@curl -s -X POST $(API)/analyze \
		-H "Content-Type: application/json" \
		-d '{"project_id":"$(PROJECT)","workspace":"$(WORKSPACE)"}' ; echo

explain: ## Explain a symbol: make explain SYMBOL=Name.method
	@curl -s "$(API)/explain/$(SYMBOL)?model=$(MODEL)&project=$(PROJECT)"; echo

review: ## AI review a symbol: make review SYMBOL=Name.method
	@curl -s "$(API)/review/$(SYMBOL)?model=$(MODEL)&project=$(PROJECT)"; echo

impact: ## Show who is affected: make impact SYMBOL=Name.method
	@curl -s "$(API)/impact/$(SYMBOL)?project=$(PROJECT)"; echo

architecture: ## Explain the whole repo: make architecture
	@curl -s "$(API)/architecture?model=$(MODEL)&project=$(PROJECT)"; echo

diagnose: ## Diagnose an error: paste stack trace in /tmp/reyvin-error.txt, then make diagnose [PROJECT=]
	@if [ -n "$(ERROR)" ]; then printf '%s\n' "$(ERROR)" > /tmp/reyvin-error.txt; fi; \
	bash scripts/diagnose.sh ${DIAGNOSE_FILE}
