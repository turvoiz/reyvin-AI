import assert from "node:assert/strict";
import { createServer, type Server } from "node:http";
import { after, before, test } from "node:test";

import { buildUrl, createClient, llmQuery, normalizeBaseUrl } from "./client";

test("normalizeBaseUrl strips trailing slashes", () => {
    assert.equal(normalizeBaseUrl("http://host:8000/api/v1/"), "http://host:8000/api/v1");
    assert.equal(normalizeBaseUrl("  http://host/api//  "), "http://host/api");
});

test("buildUrl appends the project query parameter", () => {
    const url = buildUrl("http://host:8000/api/v1", "/explain/AIService.chat", "default");
    assert.equal(url, "http://host:8000/api/v1/explain/AIService.chat?project=default");
});

test("buildUrl preserves existing query parameters", () => {
    const url = buildUrl("http://host/api", "/explain/AIService.chat?model=qwen", "frontend");
    assert.equal(url, "http://host/api/explain/AIService.chat?model=qwen&project=frontend");
});

test("buildUrl encodes the project value", () => {
    const url = buildUrl("http://host/api", "/symbol/a.b", "my project");
    assert.equal(url, "http://host/api/symbol/a.b?project=my%20project");
});

test("llmQuery appends model and thinking when configured", () => {
    assert.equal(llmQuery({ apiBaseUrl: "x", project: "p", model: "deepseek", thinking: true }), "?model=deepseek&thinking=true");
    assert.equal(llmQuery({ apiBaseUrl: "x", project: "p", model: "qwen" }), "?model=qwen");
    assert.equal(llmQuery({ apiBaseUrl: "x", project: "p" }), "");
});

let server: Server;
let requests: { url: string; method?: string; headers: Record<string, string>; body?: string }[] = [];
let status = 200;
let payload: Record<string, unknown> = { ok: true };

before(async () => {
    server = createServer((request, response) => {
        const chunks: Buffer[] = [];
        request.on("data", (chunk: Buffer) => chunks.push(chunk));
        request.on("end", () => {
            requests.push({
                url: request.url ?? "",
                method: request.method,
                headers: request.headers as Record<string, string>,
                body: Buffer.concat(chunks).toString("utf-8"),
            });
            response.writeHead(status, { "Content-Type": "application/json" });
            response.end(JSON.stringify(payload));
        });
    });
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
});

after(async () => {
    await new Promise<void>((resolve, reject) =>
        server.close((error) => (error ? reject(error) : resolve())),
    );
});

function baseUrl(): string {
    const address = server.address();
    if (typeof address === "string" || address === null) {
        throw new Error("Server is not listening on a TCP port");
    }
    return `http://127.0.0.1:${address.port}/api/v1`;
}

test("client sends the project and X-API-Key header", async () => {
    requests = [];
    const client = createClient({ apiBaseUrl: baseUrl(), project: "frontend", apiToken: "secret" });

    const result = await client.get<{ ok: boolean }>("/symbol/Foo.bar");

    assert.deepEqual(result, { ok: true });
    assert.equal(requests.length, 1);
    assert.ok(requests[0].url.endsWith("/symbol/Foo.bar?project=frontend"));
    assert.equal(requests[0].headers["x-api-key"], "secret");
});

test("client omits the X-API-Key header when no token is configured", async () => {
    requests = [];
    const client = createClient({ apiBaseUrl: baseUrl(), project: "default" });

    await client.get("/symbol/NoToken");

    assert.equal(requests[0].headers["x-api-key"], undefined);
});

test("client method helpers target the expected endpoints", async () => {
    const client = createClient({ apiBaseUrl: baseUrl(), project: "p" });
    const endpoints = [
        client.getSymbol("A.b"),
        client.explain("A.b"),
        client.review("A.b"),
        client.impact("A.b"),
        client.explainCode("print('x')", "module.py", 1, 2),
        client.diagnoseError("TypeError: boom", "module.py"),
        client.knowledge("A.b"),
        client.search("helper"),
        client.architecture(),
    ];

    await Promise.all(endpoints);

    const urls = requests.map((request) => request.url);
    assert.ok(urls.some((url) => url.includes("/symbol/A.b?")));
    assert.ok(urls.some((url) => url.includes("/explain/A.b?")));
    assert.ok(urls.some((url) => url.includes("/review/A.b?")));
    assert.ok(urls.some((url) => url.includes("/impact/A.b?")));
    assert.ok(urls.some((url) => url.includes("/explain-code?project=p")));
    assert.ok(urls.some((url) => url.includes("/diagnose-error?project=p")));
    assert.ok(urls.some((url) => url.includes("/knowledge/A.b?")));
    assert.ok(urls.some((url) => url.includes("/search?q=helper&project=p")));
    assert.ok(urls.some((url) => url.includes("/architecture?project=p")));
});

test("explainCode sends the code, file, and line range as JSON", async () => {
    requests = [];
    const client = createClient({ apiBaseUrl: baseUrl(), project: "p", apiToken: "token" });

    await client.explainCode("return 'x'", "module.py", 3, 5);

    assert.equal(requests[0].method, "POST");
    assert.equal(requests[0].headers["content-type"], "application/json");
    assert.equal(requests[0].headers["x-api-key"], "token");
    assert.deepEqual(JSON.parse((requests[0] as { body?: string }).body ?? "{}"), {
        code: "return 'x'",
        file: "module.py",
        start_line: 3,
        end_line: 5,
        model: "qwen",
        thinking: false,
    });
});

test("explainCode sends the configured model and thinking", async () => {
    requests = [];
    const client = createClient({
        apiBaseUrl: baseUrl(),
        project: "p",
        model: "deepseek",
        thinking: true,
    });

    await client.explainCode("return 'x'", "module.py", 3, 5);

    assert.deepEqual(JSON.parse((requests[0] as { body?: string }).body ?? "{}").model, "deepseek");
    assert.equal(JSON.parse((requests[0] as { body?: string }).body ?? "{}").thinking, true);
    assert.ok(requests[0].url.endsWith("/explain-code?model=deepseek&thinking=true&project=p"));
});

test("diagnoseError sends the error and file as JSON", async () => {
    requests = [];
    const client = createClient({ apiBaseUrl: baseUrl(), project: "p", apiToken: "token" });

    await client.diagnoseError("TypeError: boom\n    at greet (module.ts:2:10)", "module.ts");

    assert.equal(requests[0].method, "POST");
    assert.equal(requests[0].headers["content-type"], "application/json");
    assert.equal(requests[0].headers["x-api-key"], "token");
    assert.deepEqual(JSON.parse((requests[0] as { body?: string }).body ?? "{}"), {
        error: "TypeError: boom\n    at greet (module.ts:2:10)",
        file: "module.ts",
        model: "qwen",
        thinking: false,
        history: [],
    });
});

test("diagnoseError forwards conversation history", async () => {
    requests = [];
    const client = createClient({ apiBaseUrl: baseUrl(), project: "p", apiToken: "token" });

    const history = [
        { role: "assistant" as const, content: "Which SDK does this app use?" },
        { role: "user" as const, content: "react-native-purchases" },
    ];

    await client.diagnoseError("TypeError: boom", "module.ts", history);

    assert.deepEqual(JSON.parse((requests[0] as { body?: string }).body ?? "{}"), {
        error: "TypeError: boom",
        file: "module.ts",
        model: "qwen",
        thinking: false,
        history,
    });
});

test("client throws a descriptive error on non-2xx responses", async () => {
    status = 404;
    payload = { detail: "Symbol not found" };

    const client = createClient({ apiBaseUrl: baseUrl(), project: "p" });

    await assert.rejects(
        () => client.get("/symbol/Missing"),
        /Reyvin API 404: {"detail":"Symbol not found"}/,
    );

    status = 200;
    payload = { ok: true };
});
