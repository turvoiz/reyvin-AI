export type ApiConfig = {
    apiBaseUrl: string;
    project: string;
    apiToken?: string;
    model?: string;
    thinking?: boolean;
};

export function normalizeBaseUrl(baseUrl: string): string {
    return baseUrl.trim().replace(/\/+$/, "");
}

export function buildUrl(baseUrl: string, path: string, project: string): string {
    const base = normalizeBaseUrl(baseUrl);
    const separator = path.includes("?") ? "&" : "?";
    return `${base}${path}${separator}project=${encodeURIComponent(project)}`;
}

export function llmQuery(config: ApiConfig): string {
    const params = new URLSearchParams();

    if (config.model) {
        params.set("model", config.model);
    }

    if (config.thinking) {
        params.set("thinking", "true");
    }

    const serialized = params.toString();

    return serialized ? `?${serialized}` : "";
}

export function createClient(config: ApiConfig) {
    async function request<T>(path: string): Promise<T> {
        const url = buildUrl(config.apiBaseUrl, path, config.project);

        const headers: Record<string, string> = {
            Accept: "application/json",
        };

        if (config.apiToken) {
            headers["X-API-Key"] = config.apiToken;
        }

        const response = await fetch(url, { headers });

        if (!response.ok) {
            const body = await response.text();
            throw new Error(`Reyvin API ${response.status}: ${body}`);
        }

        return response.json() as Promise<T>;
    }

    async function post<T>(path: string, body: unknown): Promise<T> {
        const url = buildUrl(config.apiBaseUrl, path, config.project);

        const headers: Record<string, string> = {
            Accept: "application/json",
            "Content-Type": "application/json",
        };

        if (config.apiToken) {
            headers["X-API-Key"] = config.apiToken;
        }

        const response = await fetch(url, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorBody = await response.text();
            throw new Error(`Reyvin API ${response.status}: ${errorBody}`);
        }

        return response.json() as Promise<T>;
    }

    return {
        get: request,
        post,
        getSymbol: <T>(name: string) => request<T>(`/symbol/${encodeURIComponent(name)}`),
        explain: (symbol: string) => request(`/explain/${encodeURIComponent(symbol)}${llmQuery(config)}`),
        review: (symbol: string) => request(`/review/${encodeURIComponent(symbol)}${llmQuery(config)}`),
        impact: (symbol: string) => request(`/impact/${encodeURIComponent(symbol)}`),
        explainCode: (code: string, file: string, startLine: number, endLine: number) =>
            post(`/explain-code${llmQuery(config)}`, {
                code,
                file,
                start_line: startLine,
                end_line: endLine,
                model: config.model ?? "qwen",
                thinking: config.thinking ?? false,
            }),
        diagnoseError: (error: string, file: string) =>
            post(`/diagnose-error${llmQuery(config)}`, {
                error,
                file,
                model: config.model ?? "qwen",
                thinking: config.thinking ?? false,
            }),
        knowledge: <T>(symbol: string) => request<T>(`/knowledge/${encodeURIComponent(symbol)}`),
        search: <T>(query: string) => request<T>(`/search?q=${encodeURIComponent(query)}`),
        architecture: <T>() => request<T>(`/architecture${llmQuery(config)}`),
    };
}
