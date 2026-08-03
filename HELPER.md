# HELPER — Panduan Cepat Reyvin Workspace AI

Backend FastAPI + Ollama, dikontrol lewat Makefile, dipakai dari VS Code.

## 1. Struktur

```
reyvin-api/              backend (FastAPI, port 8000)
├── app/
├── tests/
└── Makefile             semua perintah ada di sini
vscode-extension/        extension Reyvin (7 command)
```

## 2. Menjalankan

```bash
make install              # install deps backend + extension (sekali saja)
make run-bg               # jalankan backend background (log: /tmp/reyvin-server.log)
make stop                 # stop backend
make status               # cek backend + Ollama sekaligus
make run                  # backend foreground (Ctrl+C untuk berhenti)
```

Syarat: Ollama jalan (`make ollama` untuk cek), model `qwen3:8b` + `deepseek-r1:8b`.

## 3. Daftar project

```bash
make analyze WORKSPACE=/home/reyvin/NAMA-REPO PROJECT=nama
```

Setiap repo baru yang mau dipakai → `make analyze` dulu.

## 4. Pakai dari terminal

```bash
make explain SYMBOL=AIService.chat            # jelaskan symbol (model default qwen)
make explain SYMBOL=AIService.chat MODEL=deepseek
make review SYMBOL=AIService.chat             # AI code review
make impact SYMBOL=AIService.chat             # siapa yang terpengaruh
make architecture                             # arsitektur repo
make analyze WORKSPACE=/path/to/repo PROJECT=name
```

### Diagnose error dari terminal
```bash
# 1. tempel stack trace ke file
nano /tmp/reyvin-error.txt
# 2. jalankan
make diagnose PROJECT=finvoiz
# atau dari stdin:
cat error.log | scripts/diagnose.sh -
```
Hasil: frames yang di-match (file:line -> symbol), root cause, lokasi, dan saran fix. Tanpa VS Code sama sekali.

### Auto-fix dari terminal (curl)
Untuk error library/version/policy, backend otomatis **search internet (DuckDuckGo)** dan memasukkan hasilnya ke prompt sebagai web evidence (misal: versi minimum, jalur upgrade, file yang harus berubah).

```bash
# 1. Diagnose dulu
curl -s -X POST http://127.0.0.1:8000/api/v1/diagnose-error \
  -H "Content-Type: application/json" \
  -d '{"project":"finvoiz","error":"...error text..."}' > /tmp/diag.json

# 2. Apply fix yang disarankan (git checkpoint + commit)
curl -s -X POST http://127.0.0.1:8000/api/v1/apply-fix \
  -H "Content-Type: application/json" \
  -d '{"project":"finvoiz","fix":{"description":"...","file":"package.json","symbol":"...","suggestion":"..."}}'

# 3. Kalau salah, revert ke checkpoint
curl -s -X POST "http://127.0.0.1:8000/api/v1/revert-fix?project=finvoiz" \
  -H "Content-Type: application/json" -d '{}'
```

Alur `apply-fix`: commit checkpoint `reyvin: checkpoint before auto-fix` → LLM generate patch → `git apply` (fallback: tulis ulang file) → commit `reyvin: apply fix - ...`. `.workspace_snapshot.json` otomatis di-ignore (`.git/info/exclude`).

## 5. Pakai dari VS Code

1. Buka folder repo yang sudah di-analyze.
2. Settings (`Ctrl+,`) → cari `reyvin`:
   - `reyvin.apiBaseUrl`: `http://127.0.0.1:8000/api/v1`
   - `reyvin.project`: `nama` (sama dengan PROJECT saat analyze)
   - `reyvin.model`: `qwen` / `deepseek`
   - `reyvin.thinking`: true (untuk model reasoning)
3. Kalau extension belum terpasang:
   ```bash
   make install-extension   # build .vsix + pasang ke VS Code
   ```

### Shortcut (keybindings.json)

| Shortcut       | Command                        | Fungsi                     |
|----------------|--------------------------------|----------------------------|
| `Ctrl+Alt+E`   | Reyvin: Explain Symbol         | kursor di nama fungsi/class |
| `Ctrl+Alt+S`   | Reyvin: Explain Selection      | jelaskan blok kode terpilih |
| `Ctrl+Alt+R`   | Reyvin: Review Symbol          | AI code review              |
| `Ctrl+Alt+I`   | Reyvin: Show Symbol Impact     | siapa yang terpengaruh      |
| `Ctrl+Alt+N`   | Reyvin: Navigate Dependencies  | lompat ke caller/callee     |
| `Ctrl+Alt+D`   | Reyvin: Diagnose Error         | tempel/select stack trace   |
| `Ctrl+Alt+F`   | Reyvin: Auto-Fix Error         | diagnose + pilih fix + apply (git checkpoint) |
| `(kosong)`     | Reyvin: Revert Last Fix        | reset ke checkpoint         |
| `(kosong)`     | Reyvin: Find Related Code      | cari kode terkait           |
| `(kosong)`     | Reyvin: Explain Architecture   | gambaran arsitektur repo    |

Semua command juga bisa dipanggil via `Ctrl+Shift+P` → ketik `Reyvin`.

File keybindings: `~/.config/Code/User/keybindings.json`.

## Fix bug dengan Diagnose Error (`Ctrl+Alt+D`)

1. Kena error / stack trace → blok teks errornya di editor, atau paste di input box.
2. Tekan `Ctrl+Alt+D`.
3. AI:
   - cocokkan baris stack trace dengan symbol ter-index (file:line → fungsi)
   - cari akar masalah (root cause)
   - kasih lokasi error + saran fix
4. Hasil `frames` = daftar file:line yang di-match (klik quick-pick untuk lompat ke kode, bila dipilih dari panel).

Note: project registry in-memory — setelah `make stop`/restart, jalankan `make analyze ...` lagi.

## 6. Test & quality

```bash
make test              # semua test (backend + extension)
make test-backend      # pytest
make test-extension    # node --test
make check             # tsc typecheck extension
make lint              # ruff check
```

## 7. Troubleshooting

| Masalah | Solusi |
|---|---|
| Backend DOWN di `make status` | `make run-bg`, pastikan Ollama jalan |
| `make analyze` gagal / index kosong | cek path WORKSPACE benar, folder valid |
| Response kosong / error LLM | cek `make ollama`; ganti `MODEL` / setting `reyvin.model` |
| Extension tidak muncul | `make install-extension`, reload VS Code |
| `Auto-Fix Error` error "git repository" | target repo harus git (bukan folder biasa) |
| Fix salah / mau batal | `Reyvin: Revert Last Fix` atau `git reset --hard <checkpoint>` |
| `apply-fix` 422 / not found | project belum di-analyze (registry in-memory) → `make analyze` dulu |
| Log error | `tail -f /tmp/reyvin-server.log` |
