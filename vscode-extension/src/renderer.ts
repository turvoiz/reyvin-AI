export type ResultKind = "explain" | "explainCode" | "review" | "architecture" | "diagnose" | "fix" | "json";

export function escapeHtml(value: string): string {
    return value.replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#039;",
    }[character] ?? character));
}

function asRecord(value: unknown): Record<string, any> {
    return (value && typeof value === "object" ? value : {}) as Record<string, any>;
}

function asArray(value: unknown): any[] {
    return Array.isArray(value) ? value : [];
}

function toText(value: unknown): string {
    if (value === null || value === undefined) {
        return "";
    }
    if (typeof value === "string") {
        return value;
    }
    return JSON.stringify(value);
}

function inlineMarkdown(text: string): string {
    const escaped = escapeHtml(toText(text));
    const codes: string[] = [];
    const withoutCode = escaped.replace(/`([^`]+)`/g, (_match, code) => {
        codes.push(code);
        return `\u0000${codes.length - 1}\u0000`;
    });
    const bolded = withoutCode.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    const italic = bolded.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    return italic.replace(/\u0000(\d+)\u0000/g, (_match, index) => `<code>${codes[Number(index)]}</code>`);
}

function proseBlocks(text: string): string {
    const lines = toText(text).split(/\r?\n/);
    const out: string[] = [];
    let paragraph: string[] = [];
    let listItems: string[] = [];
    let listTag = "";

    const flushParagraph = () => {
        if (paragraph.length) {
            out.push(`<p>${paragraph.map(inlineMarkdown).join("<br/>")}</p>`);
            paragraph = [];
        }
    };

    const flushList = () => {
        if (listItems.length) {
            out.push(`<${listTag}>${listItems.join("")}</${listTag}>`);
            listItems = [];
            listTag = "";
        }
    };

    for (const raw of lines) {
        const line = raw.trimEnd();

        if (line.trim() === "") {
            flushParagraph();
            flushList();
            continue;
        }

        const header = line.match(/^(#{1,3})\s+(.*)$/);
        if (header) {
            flushParagraph();
            flushList();
            const level = header[1].length + 1;
            out.push(`<h${level} class="heading">${inlineMarkdown(header[2])}</h${level}>`);
            continue;
        }

        const bullet = line.match(/^\s*[-*]\s+(.*)$/);
        if (bullet) {
            flushParagraph();
            if (listTag !== "ul") {
                flushList();
                listTag = "ul";
            }
            listItems.push(`<li>${inlineMarkdown(bullet[1])}</li>`);
            continue;
        }

        const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
        if (numbered) {
            flushParagraph();
            if (listTag !== "ol") {
                flushList();
                listTag = "ol";
            }
            listItems.push(`<li>${inlineMarkdown(numbered[1])}</li>`);
            continue;
        }

        flushList();
        paragraph.push(line);
    }

    flushParagraph();
    flushList();
    return out.join("");
}

function renderAnswer(value: unknown): string {
    if (Array.isArray(value)) {
        const items = value.map((item) => `<li>${inlineMarkdown(toText(item))}</li>`).join("");
        return `<ul class="plain-list">${items}</ul>`;
    }
    if (value && typeof value === "object") {
        const rows = Object.entries(value as Record<string, unknown>)
            .map(([key, val]) => `<div class="kv"><span class="kv-key">${escapeHtml(key)}</span><span class="kv-value">${renderAnswer(val)}</span></div>`)
            .join("");
        return `<div class="kv-wrap">${rows}</div>`;
    }
    return proseBlocks(toText(value));
}

function pill(label: string, extraClass = ""): string {
    return `<span class="pill ${extraClass}">${escapeHtml(label)}</span>`;
}

function codeBlock(code: string): string {
    const source = toText(code).trim();
    if (!source) {
        return "";
    }
    return `<pre class="code">${escapeHtml(source)}</pre>`;
}

function section(title: string, body: string, icon = ""): string {
    return `<section class="section"><h2 class="section-title">${icon ? `<span class="section-icon">${escapeHtml(icon)}</span>` : ""}${escapeHtml(title)}</h2>${body}</section>`;
}

function page(title: string, body: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-editor-foreground);
    --muted: var(--vscode-descriptionForeground, #9ca3af);
    --border: var(--vscode-input-border, rgba(127, 127, 127, 0.35));
    --border-soft: var(--vscode-editorWidget-border, rgba(127, 127, 127, 0.18));
    --accent: var(--vscode-textLink-foreground, #4da3ff);
    --code-bg: var(--vscode-textCodeBlock-background, rgba(127, 127, 127, 0.12));
    --card-bg: var(--vscode-editorWidget-background, rgba(127, 127, 127, 0.06));
    --badge-bg: var(--vscode-badge-background, #4da3ff);
    --badge-fg: var(--vscode-badge-foreground, #ffffff);
    --error-bg: color-mix(in srgb, #f14c4c 14%, var(--bg));
    --warning-bg: color-mix(in srgb, #d29922 14%, var(--bg));
    --ok-bg: color-mix(in srgb, #2ea043 14%, var(--bg));
}
* { box-sizing: border-box; }
body {
    margin: 0;
    padding: 20px 24px 32px;
    color: var(--fg);
    background: var(--bg);
    font-family: var(--vscode-font-family, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif);
    font-size: var(--vscode-font-size, 13px);
    line-height: 1.55;
}
h1.title { font-size: 16px; font-weight: 600; margin: 0 0 4px; }
.subtitle { color: var(--muted); font-size: 12px; margin-bottom: 20px; }
.section { margin-top: 18px; }
.section-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin: 0 0 8px;
}
.section-icon { font-size: 12px; }
.heading { margin: 14px 0 6px; font-weight: 600; }
.card {
    background: var(--card-bg);
    border: 1px solid var(--border-soft);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.root-cause {
    background: var(--error-bg);
    border: 1px solid color-mix(in srgb, #f14c4c 40%, transparent);
    border-left: 4px solid #f14c4c;
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 14px;
    font-weight: 600;
}
.location-line { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.pill {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 10px;
    border-radius: 999px;
    background: var(--badge-bg);
    color: var(--badge-fg);
    font-size: 11px;
    font-weight: 600;
    line-height: 1.6;
    white-space: nowrap;
}
.pill.plain { background: var(--code-bg); color: var(--fg); }
.pill.accent { background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--accent); }
.pill.red { background: color-mix(in srgb, #f14c4c 18%, transparent); color: #f14c4c; }
.pill.orange { background: color-mix(in srgb, #d29922 18%, transparent); color: #d29922; }
.pill.amber { background: color-mix(in srgb, #e3b341 18%, transparent); color: #e3b341; }
.pill.blue { background: color-mix(in srgb, #4da3ff 18%, transparent); color: #4da3ff; }
.pill.violet { background: color-mix(in srgb, #9868e0 18%, transparent); color: #9868e0; }
.pill.green { background: color-mix(in srgb, #2ea043 18%, transparent); color: #2ea043; }
.code {
    background: var(--code-bg);
    border: 1px solid var(--border-soft);
    border-radius: 6px;
    padding: 10px 12px;
    overflow-x: auto;
    font-family: var(--vscode-editor-font-family, "SF Mono", Consolas, monospace);
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 6px 0;
}
p { margin: 6px 0; }
ul.plain-list, .section ul { margin: 6px 0; padding-left: 20px; }
li { margin: 3px 0; }
.kv-wrap { display: flex; flex-direction: column; gap: 6px; }
.kv { display: flex; flex-direction: column; gap: 2px; }
.kv-key { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }
.kv-value { color: var(--fg); }
.findings { display: flex; flex-direction: column; gap: 10px; }
.finding { border: 1px solid var(--border-soft); border-left: 4px solid var(--badge-bg); border-radius: 8px; padding: 12px 14px; background: var(--card-bg); }
.finding.bug { border-left-color: #f14c4c; }
.finding.security { border-left-color: #d29922; }
.finding.performance { border-left-color: #e3b341; }
.finding.weakness { border-left-color: #4da3ff; }
.finding.refactor { border-left-color: #9868e0; }
.finding-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 4px; }
.finding-issue { font-weight: 600; }
.finding-evidence { color: var(--muted); margin-top: 6px; }
.strengths { display: flex; flex-wrap: wrap; gap: 6px; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; margin-bottom: 6px; }
.stat { background: var(--card-bg); border: 1px solid var(--border-soft); border-radius: 8px; padding: 10px 12px; }
.stat-value { font-size: 20px; font-weight: 700; }
.stat-label { font-size: 11px; color: var(--muted); margin-top: 2px; }
table.frames { width: 100%; border-collapse: collapse; font-size: 12px; }
table.frames th, table.frames td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--border-soft); vertical-align: top; }
table.frames th { color: var(--muted); font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
table.frames td.mono, .mono { font-family: var(--vscode-editor-font-family, "SF Mono", Consolas, monospace); }
.muted { color: var(--muted); font-size: 12px; }
.footer { margin-top: 22px; padding-top: 12px; border-top: 1px solid var(--border-soft); color: var(--muted); font-size: 11px; display: flex; gap: 12px; flex-wrap: wrap; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.empty { color: var(--muted); font-style: italic; }
</style>
</head>
<body>
${body}
</body>
</html>`;
}

function renderFrames(frames: any[]): string {
    if (!frames.length) {
        return `<div class="empty">No stack frames could be parsed or matched.</div>`;
    }
    const rows = frames.map((frame) => {
        const location = `${toText(frame.file)}:${frame.line ?? 0}`;
        const symbol = frame.symbol ? pill(toText(frame.symbol), "green") : `<span class="muted">no match</span>`;
        return `<tr><td class="mono">${escapeHtml(location)}</td><td class="mono">${escapeHtml(toText(frame.function) || "—")}</td><td>${symbol}</td></tr>`;
    }).join("");
    return `<table class="frames"><thead><tr><th>Location</th><th>Function</th><th>Matched symbol</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function renderDiagnose(title: string, data: unknown): string {
    const record = asRecord(data);
    const diagnosis = asRecord(record.diagnosis);
    const fixes = asArray(diagnosis.fixes);
    const frames = asArray(record.frames);

    const rootCause = toText(diagnosis.root_cause);
    const location = toText(diagnosis.location);
    const explanation = toText(diagnosis.explanation);

    const rootCauseBlock = rootCause
        ? `<section class="section"><h2 class="section-title">Root cause</h2><div class="root-cause">${inlineMarkdown(rootCause)}</div></section>`
        : "";

    const locationBlock = location
        ? `<div class="location-line">${pill(location, "accent")}</div>`
        : "";

    const explanationBlock = explanation
        ? section("Explanation", renderAnswer(explanation))
        : "";

    const fixesBlock = fixes.length
        ? section(
            `Suggested fixes (${fixes.length})`,
            fixes.map((fix) => {
                const fixRecord = asRecord(fix);
                const meta = [toText(fixRecord.file), toText(fixRecord.symbol)].filter(Boolean).join(" · ");
                return `<div class="card">
<div class="finding-issue">${inlineMarkdown(toText(fixRecord.description) || "Untitled fix")}</div>
${meta ? `<div class="muted mono">${escapeHtml(meta)}</div>` : ""}
${codeBlock(toText(fixRecord.suggestion))}
</div>`;
            }).join(""),
        )
        : "";

    const framesBlock = section(`Matched stack frames (${frames.length})`, renderFrames(frames));

    const footer = [
        record.model ? `model: ${toText(record.model)}` : "",
        record.elapsed_ms != null ? `elapsed: ${toText(record.elapsed_ms)} ms` : "",
    ].filter(Boolean).join(" · ");

    return page(title, `
<h1 class="title">Error Diagnosis</h1>
${location ? `<div class="location-line">${pill(location, "accent")}</div>` : ""}
${rootCauseBlock}
${explanationBlock}
${fixesBlock}
${framesBlock}
${footer ? `<div class="footer">${escapeHtml(footer)}</div>` : ""}
`);
}

function renderExplain(title: string, data: unknown): string {
    const record = asRecord(data);

    if (toText(record.error)) {
        return page(title, `
<h1 class="title">${escapeHtml(toText(record.symbol))}</h1>
<div class="root-cause">${escapeHtml(toText(record.error))}</div>
<p class="muted">The symbol could not be found in the indexed workspace. Run <code class="mono">make analyze</code> with the correct workspace path, or check the spelling.</p>
`);
    }

    const answer = record.answer;
    const related = asArray(record.related_symbols);
    const relatedBlock = related.length
        ? section("Related symbols", `<div class="chips">${related.map((name) => pill(toText(name), "plain")).join("")}</div>`)
        : "";

    return page(title, `
<h1 class="title">${escapeHtml(toText(record.symbol || "Selection"))}</h1>
${record.file ? `<div class="subtitle mono">${escapeHtml(toText(record.file))}</div>` : ""}
${section("Explanation", renderAnswer(answer))}
${relatedBlock}
`);
}

function renderReview(title: string, data: unknown): string {
    const record = asRecord(data);
    const review = asRecord(record.review);
    const strengths = asArray(review.strengths);
    const findings = asArray(review.findings);

    const summaryBlock = toText(review.summary)
        ? section("Summary", renderAnswer(review.summary))
        : "";

    const strengthsBlock = strengths.length
        ? section("Strengths", `<div class="strengths">${strengths.map((item) => pill(toText(item), "green")).join("")}</div>`)
        : "";

    const findingsBlock = section(
        `Findings (${findings.length})`,
        findings.length
            ? `<div class="findings">${findings.map((item) => {
                const finding = asRecord(item);
                const type = toText(finding.type) || "finding";
                const confidence = toText(finding.confidence) || "unknown";
                const typeClass = ["bug", "security", "performance", "weakness", "refactor"].includes(type) ? type : "";
                const confidenceClass = confidence === "high" ? "red" : confidence === "medium" ? "amber" : "plain";
                return `<div class="finding ${typeClass}">
<div class="finding-head">
    <span class="finding-issue">${inlineMarkdown(toText(finding.issue) || "Finding")}</span>
    <span>${pill(type, typeClass || "plain")}${pill(confidence, confidenceClass)}</span>
</div>
${toText(finding.evidence) ? `<div class="finding-evidence">${inlineMarkdown(finding.evidence)}</div>` : ""}
</div>`;
            }).join("")}</div>`
            : `<div class="empty">No issues found.</div>`,
    );

    return page(title, `
<h1 class="title">${escapeHtml(toText(record.symbol || "Review"))}</h1>
${summaryBlock}
${strengthsBlock}
${findingsBlock}
`);
}

function renderArchitecture(title: string, data: unknown): string {
    const record = asRecord(data);
    const summary = asRecord(record.summary);

    const languages = asRecord(summary.languages);
    const languageText = Object.entries(languages)
        .map(([lang, count]) => `${escapeHtml(lang)} (${escapeHtml(toText(count))})`)
        .join(" · ");

    const stats = `
<section class="section"><h2 class="section-title">Repository stats</h2>
<div class="stats">
    <div class="stat"><div class="stat-value">${escapeHtml(toText(summary.total_files ?? "—"))}</div><div class="stat-label">Files</div></div>
    <div class="stat"><div class="stat-value">${escapeHtml(toText(summary.total_symbols ?? "—"))}</div><div class="stat-label">Symbols</div></div>
    <div class="stat"><div class="stat-value">${escapeHtml(toText(summary.deadcode_count ?? "—"))}</div><div class="stat-label">Dead code</div></div>
    <div class="stat"><div class="stat-value mono" style="font-size:13px">${languageText || "—"}</div><div class="stat-label">Languages</div></div>
</div></section>`;

    const topFiles = asArray(summary.top_files).length
        ? section("Top files by symbol count", `<ul class="plain-list">${asArray(summary.top_files).map((item) => {
            const entry = Array.isArray(item) ? { file: item[0], count: item[1] } : asRecord(item);
            return `<li class="mono">${escapeHtml(toText(entry.file))} <span class="muted">(${escapeHtml(toText(entry.count))} symbols)</span></li>`;
        }).join("")}</ul>`)
        : "";

    const hotspots = asArray(summary.hotspots).length
        ? section("Hotspots (most called)", `<ul class="plain-list">${asArray(summary.hotspots).map((item) => {
            const hotspot = asRecord(item);
            return `<li><span class="mono">${escapeHtml(toText(hotspot.symbol))}</span> <span class="muted">(${escapeHtml(toText(hotspot.callers))} callers)</span></li>`;
        }).join("")}</ul>`)
        : "";

    const edges = asArray(summary.import_edges).length
        ? section("Import edges", `<pre class="code">${asArray(summary.import_edges).map((item) => {
            const edge = asRecord(item);
            return `${toText(edge.from)} -> ${toText(edge.to)}`;
        }).join("\n")}</pre>`)
        : "";

    return page(title, `
<h1 class="title">Architecture</h1>
<div class="subtitle mono">${escapeHtml(toText(summary.workspace))}</div>
${section("Overview", renderAnswer(record.answer))}
${stats}
${topFiles}
${hotspots}
${edges}
`);
}

function renderFix(title: string, data: unknown): string {
    const record = asRecord(data);
    const applied = toText(record.applied) === "true" || record.applied === true;

    const status = applied
        ? pill("Applied", "green")
        : pill("Failed", "red");

    const file = toText(record.file)
        ? `<div class="subtitle mono">${escapeHtml(toText(record.file))}</div>`
        : "";

    const messageBlock = toText(record.message)
        ? section("Message", renderAnswer(record.message))
        : "";

    const commits = [];
    if (toText(record.checkpoint_commit)) {
        commits.push({ label: "Checkpoint", hash: toText(record.checkpoint_commit) });
    }
    if (toText(record.fix_commit)) {
        commits.push({ label: "Fix commit", hash: toText(record.fix_commit) });
    }

    const commitBlock = commits.length
        ? section("Git history", `<div class="kv-wrap">${commits.map((item) =>
            `<div class="kv"><span class="kv-key">${escapeHtml(item.label)}</span><span class="kv-value mono">${escapeHtml(item.hash)}</span></div>`).join("")}</div>`)
        : "";

    const revertBlock = toText(record.revert)
        ? section("Revert", `<pre class="code">${escapeHtml(toText(record.revert))}</pre>`)
        : "";

    const diffText = toText(record.diff) || toText(record.raw_diff);
    const diffBlock = diffText
        ? section(applied ? "Applied change" : "Generated diff (apply manually)", `<pre class="code">${escapeHtml(diffText)}</pre>`)
        : "";

    return page(title, `
<h1 class="title">Auto-Fix ${status}</h1>
${file}
${messageBlock}
${commitBlock}
${revertBlock}
${diffBlock}
`);
}

function renderJson(title: string, data: unknown): string {
    return page(title, `
<h1 class="title">${escapeHtml(title)}</h1>
<pre class="code">${escapeHtml(JSON.stringify(data, null, 2))}</pre>
`);
}

export function renderResult(kind: ResultKind, title: string, data: unknown): string {
    switch (kind) {
        case "diagnose":
            return renderDiagnose(title, data);
        case "fix":
            return renderFix(title, data);
        case "explain":
        case "explainCode":
            return renderExplain(title, data);
        case "review":
            return renderReview(title, data);
        case "architecture":
            return renderArchitecture(title, data);
        case "json":
        default:
            return renderJson(title, data);
    }
}
