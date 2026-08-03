# Reyvin Workspace Intelligence for VS Code

Configure `reyvin.apiBaseUrl` with the running Reyvin API URL and `reyvin.project` with a registered project ID. If the API enforces authentication (an `API_KEY` is set on the server), configure `reyvin.apiToken`; it is sent as the `X-API-Key` header. Choose the LLM with `reyvin.model` (`qwen` or `deepseek`) and enable reasoning with `reyvin.thinking`.

Commands:

- **Reyvin: Explain Symbol** - explain a selected symbol or the word at the cursor
- **Reyvin: Explain Selection** - explain selected code (not just a symbol)
- **Reyvin: Review Symbol** - AI code review of a symbol
- **Reyvin: Show Symbol Impact** - impact analysis, then jump to an affected symbol
- **Reyvin: Navigate Dependencies** - browse callers, callees, and imports; jump to related code
- **Reyvin: Find Related Code** - search symbols across the project
- **Reyvin: Explain Architecture** - repo-level architecture explanation

## Development

Run `npm install` followed by `npm run compile` before launching the extension with VS Code's Extension Development Host.

- `npm run check` - typecheck without emitting
- `npm test` - compile and run unit tests with Node's test runner
- `npm run package` - build a `reyvin-workspace-*.vsix` installable package
