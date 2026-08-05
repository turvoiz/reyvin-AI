import * as vscode from "vscode";

import { createClient, type ApiConfig, type ChatTurn } from "./client";
import { escapeHtml, renderResult, type ResultKind } from "./renderer";

type SymbolInfo = {
    name: string;
    file: string;
    start_line: number;
};

type Impact = {
    affected_symbols: string[];
    risk: string;
};

type Knowledge = {
    symbol: SymbolInfo;
    calls: { call: string }[];
    callers: { caller: string }[];
    dependencies: string[];
};

type SearchResult = {
    symbol: string;
    file: string;
    type: string;
    score: number;
};

type DiagnoseFix = {
    description: string;
    file?: string;
    symbol?: string;
    suggestion?: string;
};

type DiagnoseResult = {
    diagnosis?: {
        status?: "question" | "diagnosed";
        question?: string;
        fixes?: DiagnoseFix[];
    };
    history?: ChatTurn[];
};

type ApplyFixResult = {
    applied: boolean;
    needs_confirmation?: boolean;
    file: string;
    method?: string;
    diff?: string;
    raw_diff?: string;
    checkpoint_commit?: string;
    fix_commit?: string;
    revert?: string;
    message?: string;
    verification?: { reason?: string; confidence?: string };
};

interface NavItem extends vscode.QuickPickItem {
    target?: string;
    module?: string;
}

function configuration(): ApiConfig {
    const config = vscode.workspace.getConfiguration("reyvin");
    return {
        apiBaseUrl: config.get<string>("apiBaseUrl", "http://127.0.0.1:8000/api/v1"),
        project: config.get<string>("project", "default"),
        apiToken: config.get<string>("apiToken", ""),
        model: config.get<string>("model", "qwen"),
        thinking: config.get<boolean>("thinking", false),
    };
}

async function selectedSymbol(): Promise<string | undefined> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return vscode.window.showInputBox({
            prompt: "Enter the Reyvin symbol to inspect",
            placeHolder: "Example: AIService.chat",
        });
    }

    const selected = editor.document.getText(editor.selection).trim();

    if (selected && !/\s/.test(selected)) {
        return selected;
    }

    const word = editor.document.getText(editor.document.getWordRangeAtPosition(editor.selection.active));
    if (word) {
        return word;
    }

    return vscode.window.showInputBox({
        prompt: "Enter the Reyvin symbol to inspect",
        placeHolder: "Example: AIService.chat",
    });
}

async function selectedCode(): Promise<{ code: string; file: string; startLine: number; endLine: number } | undefined> {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.selection.isEmpty) {
        return undefined;
    }

    const code = editor.document.getText(editor.selection).trim();

    if (!code) {
        return undefined;
    }

    return {
        code,
        file: vscode.workspace.asRelativePath(editor.document.uri),
        startLine: editor.selection.start.line + 1,
        endLine: editor.selection.end.line + 1,
    };
}

async function reportedError(): Promise<{ text: string; file: string } | undefined> {
    const editor = vscode.window.activeTextEditor;
    let file = "";

    if (editor && !editor.selection.isEmpty) {
        const selected = editor.document.getText(editor.selection).trim();
        if (selected) {
            return {
                text: selected,
                file: vscode.workspace.asRelativePath(editor.document.uri),
            };
        }
    }

    const text = await vscode.window.showInputBox({
        prompt: "Paste the error message or stack trace",
        placeHolder: "TypeError: ... at src/screens/HomeScreen.tsx:45:13",
    });

    if (!text) {
        return undefined;
    }

    return { text, file };
}

// Loops the diagnose-error call: whenever the AI responds with a
// clarifying question instead of a diagnosis, prompt the user for an
// answer and re-send the same error with the growing conversation
// history, until the AI is confident enough to give a final diagnosis
// (or the user cancels).
async function diagnoseWithClarification(
    client: ReturnType<typeof createClient>,
    errorText: string,
    file: string,
): Promise<DiagnoseResult | undefined> {
    let history: ChatTurn[] = [];

    for (;;) {
        const result = await withProgress("Reyvin: diagnosing error...", () =>
            client.diagnoseError(errorText, file, history),
        ) as DiagnoseResult;

        const diagnosis = result.diagnosis;

        if (diagnosis?.status !== "question" || !diagnosis.question) {
            return result;
        }

        const answer = await vscode.window.showInputBox({
            prompt: diagnosis.question,
            placeHolder: "Your answer (Esc to cancel diagnosis)",
            ignoreFocusOut: true,
        });

        if (!answer) {
            return undefined;
        }

        history = [...(result.history ?? []), { role: "user", content: answer }];
    }
}

function showResult(kind: ResultKind, title: string, content: unknown) {
    const panel = vscode.window.createWebviewPanel(
        "reyvin.result",
        title,
        vscode.ViewColumn.Beside,
        { enableScripts: false },
    );
    panel.webview.html = renderResult(kind, title, content);
}

async function openSymbol(client: ReturnType<typeof createClient>, symbol: string) {
    const info = await client.getSymbol<SymbolInfo>(symbol);
    const root = vscode.workspace.workspaceFolders?.[0]?.uri;

    if (!root) {
        throw new Error("Open the repository folder in VS Code before navigating symbols.");
    }

    const document = await vscode.workspace.openTextDocument(vscode.Uri.joinPath(root, info.file));
    const position = new vscode.Position(Math.max(info.start_line - 1, 0), 0);
    await vscode.window.showTextDocument(document, { selection: new vscode.Range(position, position) });
}

async function withProgress<T>(title: string, task: () => Promise<T>): Promise<T> {
    return vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title },
        task,
    );
}

async function findRelatedSymbol(client: ReturnType<typeof createClient>, initialQuery: string) {
    const query = await vscode.window.showInputBox({
        prompt: "Search symbols related to",
        value: initialQuery,
    });

    if (!query) {
        return;
    }

    const results = await client.search<SearchResult[]>(query);

    if (!results.length) {
        vscode.window.showInformationMessage(`No symbols matched "${query}".`);
        return;
    }

    const choice = await vscode.window.showQuickPick(
        results.map((result) => ({
            label: result.symbol,
            description: `${result.type} - ${result.file}`,
        })),
        { placeHolder: `Choose a related symbol for "${query}"` },
    );

    if (choice) {
        await openSymbol(client, choice.label);
    }
}

async function presentDependencies(
    client: ReturnType<typeof createClient>,
    knowledge: Knowledge,
    symbol: string,
) {
    const items: NavItem[] = [];

    if (knowledge.callers.length) {
        items.push({ label: "Callers", kind: vscode.QuickPickItemKind.Separator });
        for (const caller of knowledge.callers) {
            items.push({ label: `$(arrow-up) ${caller.caller}`, description: "caller", target: caller.caller });
        }
    }

    if (knowledge.calls.length) {
        items.push({ label: "Calls", kind: vscode.QuickPickItemKind.Separator });
        for (const call of knowledge.calls) {
            items.push({ label: `$(arrow-down) ${call.call}`, description: "callee", target: call.call });
        }
    }

    if (knowledge.dependencies.length) {
        items.push({ label: "Imports / dependencies", kind: vscode.QuickPickItemKind.Separator });
        for (const dependency of knowledge.dependencies) {
            items.push({ label: `$(package) ${dependency}`, description: "import", module: dependency });
        }
    }

    if (!items.length) {
        vscode.window.showInformationMessage(`No dependencies found for ${symbol}.`);
        return;
    }

    const picked = await vscode.window.showQuickPick(items, {
        placeHolder: `Dependencies of ${symbol}`,
        matchOnDescription: true,
    });

    if (!picked) {
        return;
    }

    if (picked.target) {
        await openSymbol(client, picked.target);
    } else if (picked.module) {
        await findRelatedSymbol(client, picked.module);
    }
}

export function activate(context: vscode.ExtensionContext) {
    context.subscriptions.push(
        vscode.commands.registerCommand("reyvin.explainSymbol", async () => {
            const symbol = await selectedSymbol();
            if (!symbol) {
                return;
            }

            const client = createClient(configuration());

            try {
                const result = await withProgress(`Reyvin: explaining ${symbol}...`, () => client.explain(symbol));
                showResult("explain", `Reyvin: Explain ${symbol}`, result);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.explainSelection", async () => {
            const selection = await selectedCode();

            if (!selection) {
                vscode.window.showInformationMessage("Select code first, then run Reyvin: Explain Selection.");
                return;
            }

            const client = createClient(configuration());

            try {
                const result = await withProgress("Reyvin: explaining selection...", () =>
                    client.explainCode(selection.code, selection.file, selection.startLine, selection.endLine),
                );
                showResult("explainCode", "Reyvin: Explain Selection", result);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.reviewSymbol", async () => {
            const symbol = await selectedSymbol();
            if (!symbol) {
                return;
            }

            const client = createClient(configuration());

            try {
                const result = await withProgress(`Reyvin: reviewing ${symbol}...`, () => client.review(symbol));
                showResult("review", `Reyvin: Review ${symbol}`, result);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.showImpact", async () => {
            const symbol = await selectedSymbol();
            if (!symbol) {
                return;
            }

            const client = createClient(configuration());

            try {
                const impact = await withProgress(`Reyvin: analyzing impact of ${symbol}...`, () =>
                    client.impact(symbol),
                );
                const target = await vscode.window.showQuickPick((impact as Impact).affected_symbols, {
                    placeHolder: `Impact risk: ${(impact as Impact).risk}. Choose a symbol to open.`,
                });

                if (target) {
                    await openSymbol(client, target);
                }
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.navigateDependencies", async () => {
            const symbol = await selectedSymbol();
            if (!symbol) {
                return;
            }

            const client = createClient(configuration());

            try {
                const knowledge = await withProgress(`Reyvin: loading dependencies of ${symbol}...`, () =>
                    client.knowledge<Knowledge>(symbol),
                );
                await presentDependencies(client, knowledge, symbol);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.findRelated", async () => {
            const symbol = (await selectedSymbol()) ?? "";

            const client = createClient(configuration());

            try {
                await withProgress("Reyvin: searching related symbols...", () => findRelatedSymbol(client, symbol));
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.explainArchitecture", async () => {
            const client = createClient(configuration());

            try {
                const result = await withProgress("Reyvin: explaining architecture...", () =>
                    client.architecture(),
                );
                showResult("architecture", "Reyvin: Explain Architecture", result);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.diagnoseError", async () => {
            const error = await reportedError();
            if (!error) {
                return;
            }

            const client = createClient(configuration());

            try {
                const result = await diagnoseWithClarification(client, error.text, error.file);

                if (!result) {
                    return;
                }

                showResult("diagnose", "Reyvin: Diagnose Error", result);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.applyFix", async () => {
            const error = await reportedError();
            if (!error) {
                return;
            }

            const client = createClient(configuration());

            try {
                const result = await diagnoseWithClarification(client, error.text, error.file);

                if (!result) {
                    return;
                }

                const fixes = result.diagnosis?.fixes ?? [];

                if (!fixes.length) {
                    vscode.window.showInformationMessage("No suggested fixes were produced for this error.");
                    return;
                }

                const choice = await vscode.window.showQuickPick(
                    fixes.map((fix, index) => ({
                        label: `$(wrench) ${fix.description || `Fix ${index + 1}`}`,
                        description: fix.file || fix.symbol || "",
                        detail: fix.suggestion,
                        fix,
                    })),
                    { placeHolder: "Choose a fix to apply (a git checkpoint commit is created first)" },
                );

                if (!choice) {
                    return;
                }

                const target = choice.fix.file || choice.fix.symbol || "the file";
                const confirm = await vscode.window.showWarningMessage(
                    `Reyvin will modify ${target}: create a git checkpoint commit, apply the change, and commit it.`,
                    { modal: true },
                    "Apply",
                    "Cancel",
                );

                if (confirm !== "Apply") {
                    return;
                }

                let applied = await withProgress("Reyvin: applying fix...", () =>
                    client.applyFix(choice.fix, error.text),
                ) as ApplyFixResult;

                if (applied.needs_confirmation) {
                    const proceed = await vscode.window.showWarningMessage(
                        applied.message ?? "The AI has low confidence in this fix. Apply it anyway?",
                        { modal: true },
                        "Apply anyway",
                        "Cancel",
                    );

                    if (proceed !== "Apply anyway") {
                        return;
                    }

                    applied = await withProgress("Reyvin: applying fix...", () =>
                        client.applyFix(choice.fix, error.text, true),
                    ) as ApplyFixResult;
                }

                showResult("fix", "Reyvin: Apply Fix", applied);
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
        vscode.commands.registerCommand("reyvin.revertFix", async () => {
            const client = createClient(configuration());

            try {
                const result = await withProgress("Reyvin: reverting last fix...", () =>
                    client.revertFix(),
                );
                vscode.window.showInformationMessage(
                    `Reyvin: workspace reset to ${(result as { checkpoint?: string }).checkpoint ?? "checkpoint"}.`,
                );
            } catch (error) {
                vscode.window.showErrorMessage(String(error));
            }
        }),
    );
}

export function deactivate() {}
