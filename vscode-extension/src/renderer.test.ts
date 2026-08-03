import { test } from "node:test";
import assert from "node:assert/strict";

import { escapeHtml, renderResult } from "./renderer";

test("escapeHtml escapes HTML metacharacters", () => {
    assert.equal(escapeHtml(`<script>alert("x")&'</script>`), "&lt;script&gt;alert(&quot;x&quot;)&amp;&#039;&lt;/script&gt;");
});

test("renderResult diagnose renders root cause, fixes, and frames", () => {
    const html = renderResult("diagnose", "Diagnose", {
        diagnosis: {
            root_cause: "A null reference at <b>load()</b>",
            location: "src/foo.ts:12",
            explanation: "It crashes.",
            fixes: [
                { description: "Guard the value", file: "src/foo.ts", symbol: "load", suggestion: "if (x == null) return;" },
            ],
        },
        frames: [
            { file: "src/foo.ts", line: 12, function: "load", symbol: "load" },
        ],
        model: "qwen",
        elapsed_ms: 120,
    });

    assert.match(html, /Error Diagnosis/);
    assert.match(html, /&lt;b&gt;load\(\)&lt;\/b&gt;/);
    assert.match(html, /Guard the value/);
    assert.match(html, /if \(x == null\) return;/);
    assert.match(html, /src\/foo\.ts:12/);
    assert.match(html, /model: qwen/);
});

test("renderResult explain renders the answer and escapes the symbol", () => {
    const html = renderResult("explain", "Explain <Foo>", {
        symbol: "<Foo>",
        answer: "It **loads** data.\n\n- first\n- second",
    });

    assert.match(html, /&lt;Foo&gt;/);
    assert.match(html, /<strong>loads<\/strong>/);
    assert.match(html, /<li>first<\/li>/);
});

test("renderResult review renders findings with typed pills", () => {
    const html = renderResult("review", "Review", {
        symbol: "Bar",
        review: {
            summary: "Mostly fine.",
            strengths: ["Clear naming"],
            findings: [
                { type: "bug", issue: "Crash on empty input", evidence: "dereferences without a check", confidence: "high" },
            ],
        },
    });

    assert.match(html, /Mostly fine\./);
    assert.match(html, /Clear naming/);
    assert.match(html, /Crash on empty input/);
    assert.match(html, /class="finding bug"/);
    assert.match(html, /pill red/);
});

test("renderResult json fallback escapes raw data", () => {
    const html = renderResult("json", "Raw", { key: "<script>" });

    assert.match(html, /&lt;script&gt;/);
    assert.doesNotMatch(html, /<script>/);
});
