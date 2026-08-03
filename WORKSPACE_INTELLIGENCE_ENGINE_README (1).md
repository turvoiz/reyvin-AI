# Workspace Intelligence Engine

AI-powered code intelligence engine that understands an entire repository.

## Product Vision

Build an AI Software Engineer Assistant, not just an AI chatbot.

The system should understand:

- repository structure
- architecture
- module relationships
- class/function responsibilities
- dependency graph
- data flow
- business logic

The final goal:

```
Repository

    |

Code Intelligence Engine

    |

Explain / Review / Impact Analysis

    |

VS Code Assistant
```

---

# Current Status

## Phase 1 - Workspace Intelligence Core ✅

Implemented:

- source code indexing
- symbol extraction
- symbol matching
- call graph analysis
- caller/callee relationship
- context retrieval
- context ranking
- context compression
- AI explanation
- AI code review
- evidence validation

---

# Current Architecture

```
app/

├── services/
│   ├── workspace_ai_service.py
│   ├── explain_service.py
│   └── review_service.py

├── workspace/
│   ├── retrieval/
│   │   ├── workspace_retriever.py
│   │   └── symbol_expander.py
│   │
│   ├── ranking/
│   │   └── context_ranker.py
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

---

# Pipeline

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

---

# Features

## Explain

Endpoint:

```
GET /workspace/explain/{symbol}
```

Provides:

- function purpose
- parameters
- call flow
- dependencies
- callers
- related source evidence


Example:

Input:

```
AIService.chat
```

Engine discovers:

```
AIService.choose_model

get_provider

WorkspaceAIService.run

InsightAIService.run

WorkspaceService.ask
```

---

## Review

Endpoint:

```
GET /workspace/review/{symbol}
```

Provides:

- summary
- strengths
- findings
- evidence
- confidence

Review principles:

- no generic best practice complaints
- no unsupported assumptions
- findings require code evidence
- confidence scoring

---

# Current Problems

## Duplicate Architecture

Need cleanup:

```
app/workspace/retrieval/workspace_retriever.py
```

and:

```
app/workspace/retriever/workspace_retriever.py
```

Need final architecture decision before expanding.

---

# Roadmap

## Phase 2 - Stabilization

Goals:

- remove duplicate modules
- improve folder boundaries
- add automated tests
- create workspace configuration
- separate core engine and API layer


## Phase 3 - Multi Project Support

Create abstractions:

### Project

```
name
path
language
configuration
```

### Repository

```
files
symbols
dependency graph
knowledge graph
```

### Workspace

```
active project
cache
index
```

Target languages:

```
Python
JavaScript
TypeScript
Golang
Java
```

---

## Phase 4 - Developer API

Target:

```
POST /analyze

GET /symbol/{name}

GET /explain/{symbol}

GET /review/{symbol}

GET /impact/{symbol}
```

---

## Phase 5 - VS Code Extension

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

Features:

- Explain selected code
- AI review
- Impact analysis
- Dependency navigation
- Find related code
- Explain architecture

---

# Final Goal

Create an AI teammate for software engineers.

Not:

```
AI that writes code
```

But:

```
AI engineer that understands the project
```

The system should help developers:

- understand unfamiliar codebases
- debug problems
- review changes
- analyze impact
- improve architecture

---

# Checkpoint

Branch:

```
refactor/workspace-service
```

Latest commit:

```
9c8b468
```

Commit:

```
Improve workspace AI review pipeline with context ranking and evidence validation
```

---

# Next Session

1. Remove duplicate retriever module
2. Stabilize architecture boundaries
3. Create Project / Repository / Workspace abstraction
4. Design internal engine protocol
5. Prepare VS Code Extension architecture
