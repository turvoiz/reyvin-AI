# Reyvin API Workspace Intelligence Engine

## Project Goal

AI-powered code intelligence engine that understands an entire repository.

Long-term goals:
- CLI developer assistant
- REST API service
- VS Code Extension
- AI code review workflow


# Current Status

## Live / Self-use ✅

- Backend running locally (`http://127.0.0.1:8000`) with the reyvin-api repo indexed (229 symbols)
- Ollama models available: `qwen3:8b` (default) and `deepseek-r1:8b`
- VS Code extension installed and verified end-to-end against the live API (explain, review, impact, knowledge, explain-code, architecture all confirmed working with real LLM output)
- `.vsix` package buildable via `npm run package`

## Phase 1 - Workspace Intelligence Core ✅

Implemented:
- Source code indexing
- Symbol extraction
- Symbol matching
- Call graph analysis
- Context retrieval
- Context ranking
- Context compression
- AI explanation
- AI code review
- Evidence-based review validation


# Architecture

```
app/

├── services/
│   ├── workspace_ai_service.py
│   ├── explain_service.py
│   ├── review_service.py
│   ├── code_service.py
│   ├── architecture_service.py
│   ├── insight_service.py
│   └── ai_service.py
│
├── api/v1/
│   ├── developer.py
│   └── workspace.py
│
├── workspace/
│   ├── js_call_graph.py
│   ├── project_registry.py
│   ├── search/symbol_search.py
│   ├── retrieval/
│   │   ├── workspace_retriever.py
│   │   └── symbol_expander.py
│   │
│   ├── ranking/
│   │   └── workspace_ranker.py
│   │
│   ├── context/
│   │   ├── context_assembler.py
│   │   ├── context_compressor.py
│   │   └── context_formatter.py
│   │
│   └── review/
│       ├── review_validator.py
│       ├── evidence_validator.py
│       └── summary_validator.py
```


# Current Flow

```
Request
  |
Planner
  |
Symbol Matcher
  |
Retriever
  |
Context Ranker
  |
Context Compressor
  |
Prompt Builder
  |
LLM
  |
Validator
  |
Response
```


# Features

## Explain

Example:

GET /workspace/explain/{symbol}

Provides:
- Function purpose
- Parameters
- Call flow
- Dependencies
- Callers
- Related source evidence


## Review

Example:

GET /workspace/review/{symbol}

Provides:
- Strengths
- Weaknesses
- Bugs
- Security issues
- Refactor suggestions
- Evidence


Rules:
- No unsupported assumptions
- Findings require evidence
- Confidence scoring


# Roadmap

## Phase 2 - Stabilization

Status: ✅ Complete

- Removed the stale retriever import and consolidated the AI context pipeline
- Added safe handling for unmatched symbols and regression coverage
- Added `WORKSPACE_ROOT` configuration and workspace-scoped snapshots
- Fixed incremental rebuilds for changed and deleted files


## Phase 3 - Multi Project Support

Status: ✅ Core complete

Goal:
Analyze any repository.

Features:
- Repository indexing through a project registry
- Incremental updates for changed and removed source files
- Python, JavaScript, JSX, TypeScript, and TSX symbol/import indexing
- Project-selectable workspace endpoints
- Call graph analysis for Python and JavaScript/TypeScript (cross-module calls and `this.method` resolution)


## Phase 4 - Developer API

Status: ✅ Complete

Endpoints (all under `/api/v1`, API-key protected when `API_KEY` is set):

```
POST /analyze
GET  /symbol/{name}
GET  /explain/{symbol}
GET  /review/{symbol}
GET  /impact/{symbol}
POST /explain-code          # explain arbitrary selected code
POST /diagnose-error        # paste a stack trace -> root cause + fix suggestions
GET  /knowledge/{symbol}    # calls / callers / dependencies / trace
GET  /search?q=             # related-code search
GET  /architecture          # repo-level architecture explanation
```


## Phase 5 - VS Code Extension

Status: ✅ Core complete - packaged as .vsix, installed and verified live for private/self use

Features:

- Explain selected code
- AI code review
- Impact analysis
- Dependency navigation

Implemented:
- Explain / Review / Impact / Explain Selection / Navigate Dependencies / Find Related Code / Explain Architecture / Diagnose Error commands wired to the Developer API
- `POST /explain-code` endpoint: explains arbitrary selected source, enriching context from symbols that match the selection range or appear in the code
- `POST /diagnose-error` endpoint: parses a stack trace, matches frames (file:line -> indexed symbol, incl. suffix matching for relative paths), assembles workspace context, and returns a root cause + fix suggestions
- `GET /knowledge/{symbol}`, `GET /search`, and `GET /architecture` added to the Developer API
- JavaScript/TypeScript call graph analysis: cross-module calls and `this.method` resolution linked against indexed symbols
- Optional API key auth: `reyvin.apiToken` setting sent as `X-API-Key`, enforced server-side when `API_KEY` is configured
- Testable API client module (`src/client.ts`) with unit tests via Node's test runner
- `npm run package` builds `reyvin-workspace-*.vsix` via vsce

Tuning / testing fixes:
- Fixed project ID validation rejecting `-` and `_` (underscore broke `isalnum()`)
- Fixed dead code analysis reading relative paths against CWD instead of the workspace root
- Extended the JS/TS parser to extract class methods for call graph support
- Centralized `get_project_cache` into `app/api/v1/dependencies.py` (removed duplication across routers)
- Graceful fallback message when the LLM returns an empty response (explain, explain-code, architecture)
- Added `reyvin.model` / `reyvin.thinking` settings so the LLM model and reasoning mode are selectable from the extension
- Added backend regression coverage for project ID validation, API key enforcement, code explain, knowledge, search, architecture, JS/TS call graphs, and empty-LLM fallbacks


Architecture:

```
VS Code Extension

        |

Workspace API

        |

AI Engine

        |

Repository Knowledge Graph
```


# Final Vision

Create an AI teammate that understands a complete codebase.

```
Repository

    |

Code Intelligence Engine

    |

Explain / Review / Impact

    |

VS Code Assistant
```


# Checkpoint

Branch:

refactor/workspace-service

Latest commit:

d7c5b52

Message:

Improve workspace AI review pipeline with context ranking and evidence validation

Working tree: Phase 5 extension features implemented and verified live (uncommitted work on top of d7c5b52)


# Next Session

1. Broaden JS/TS call resolution (imported symbol mapping, instance type inference)
2. Extend language support toward Golang and Java
3. End-to-end extension integration tests against a live API
4. Optional: publish the extension to the VS Code Marketplace (currently used privately as a local .vsix)
